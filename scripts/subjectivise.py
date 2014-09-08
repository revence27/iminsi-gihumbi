#!  /usr/bin/env python

import cherrypy
import copy
from datetime import datetime, timedelta
from ectomorph import orm
import os, sys, thread
import re
import settings
import subprocess

orm.ORM.connect(dbname  = 'thousanddays', user = 'thousanddays', host = 'localhost', password = 'thousanddays')

class R1000Object:
  def __init__(self, tbl):
    self.table    = tbl
    self.attrs    = {}

  def save(self):
    # sys.stderr.write("%s\n" % (str(self.attrs), ))
    got = orm.ORM.store(self.table, self.attrs)
    # sys.stderr.write('%d: %s\r' % (got, str(self.attrs.keys())[0:75]))
    return got

  def set(self, key, val):
    self.attrs[key] = val

  def get(self, key):
    return self.attrs[key]

  def __setitem__(self, key, val):
    return self.set(key, val)

  def __getitem__(self, key):
    return self.get(key)

  def copy(self, source, cols):
    for col in cols:
      ncol  = col
      ocol  = col
      if type(col) == type(('', '')):
        ocol  = col[0]
        ncol  = col[1]
      self.set(ncol, source[ocol])
    return self

MOTHER_MIGRATIONS = [
  ('patient_id', '1198670116338016')
]
class Mother(R1000Object):
  def load(self, nid):
    gat = orm.ORM.query(self.table, {'patient_id = %s': nid}, migrations = MOTHER_MIGRATIONS)
    self['patient_id']  = nid
    if not gat.count():
      self.save()
      return self.load(nid)
    self['indexcol']    = gat[0]['indexcol']
    return self

REPORTER_MIGRATIONS = [
  ('phone_number', '+250780123456')
]
class Reporter(R1000Object):
  def load(self, phn):
    gat = orm.ORM.query(self.table, {'phone_number = %s': phn}, migrations = REPORTER_MIGRATIONS)
    self['phone_number']  = phn
    if not gat.count():
      self.save()
      return self.load(phn)
    self['indexcol']      = gat[0]['indexcol']
    return self

PREGNANCY_MIGRATIONS  = [
  ('lmp', datetime.today())
]
class Pregnancy(R1000Object):
  def load(self, mum, lmp):
    gat = orm.ORM.query(self.table, {'indexcol = %s': mum, 'lmp = %s': lmp}, migrations = PREGNANCY_MIGRATIONS)
    self['mother']  = mum
    self['lmp']     = lmp
    if not gat.count():
      self.save()
      return self.load(mum, lmp)
    self['indexcol']    = gat[0]['indexcol']
    return self

class Pregancies:
  def handle(self, entry, row, hst):
    mum = Mother('ig_mothers')
    mum.load(entry['patient_id'])
    rep = Reporter('ig_reporters')
    rep.load(entry['reporter_phone'])
    mum['reporter'] = rep['indexcol']
    prg = Pregnancy('ig_pregnancies')
    prg.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'report_date', 'lmp'])
    prg.load(mum['indexcol'], entry['lmp'])
    mum.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'report_date', 'lmp']).copy(row,   [
      ('mother_weight_float', 'weight'),
      ('mother_height_float', 'height'),
      ('parity_float', 'parity'),
      ('gravity_float', 'gravidity'),
      ('indexcol', 'former_id'),
      ('hw_bool', 'handwashing'),
      ('to_bool', 'toilet')
    ])
    # .copy(row, ['log_id', 'cl_bool', 'np_bool', 'nr_bool', 'nh_bool', 'rm_bool', 'gs_bool', 'nt_bool', 'hp_bool', 'ol_bool', 'rb_bool', 'mu_bool', 'mw_bool', 'yg_bool', 'hd_bool', 'ds_bool', 'ho_bool', 'aa_bool', 'vo_bool', 'yj_bool', 'sa_bool', 'lz_bool', 'ms_bool', 'pm_bool', 'ch_bool', 'anc2_bool', 'ma_bool', 'pr_bool', 'dth_bool', 'sb_bool', 'af_bool', 'di_bool', 'kx_bool', 'cw_bool', 'cs_bool', 'nb_bool', 'oe_bool', 'fe_bool', 'ns_bool', 'or_bool', 'ja_bool', 'pc_bool', 'anc_bool', 'hy_bool', 'bo_bool', 'db_bool', 'ci_bool', 'ib_bool'])
    mum.save()

class Nutrition:
  def handle(self, entry, row, hst):
    raise Exception, row['report_date']

class InterventionResult:
  def handle(self, entry, row, hst):
    raise Exception, row['report_date']

class Birth:
  def handle(self, entry, row, hst):
    raise Exception, row['report_date']

HANDLERS  = {
  'PRE' : Pregancies(),
  'BIR' : Birth(),
  'CBN' : Nutrition(),
  'RES' : InterventionResult(),
}

def transfer_objects(reps, tbl):
  rdx = None
  qry = orm.ORM.query(tbl, {'report_type IS NOT NULL': ''}, sort = ('report_date', True))
  # sys.stderr.write('%d: %s\n' % (qry.count(), qry.query))
  for rpt in qry.list():
    idx = rpt['indexcol']
    ltp = rpt['report_type']
    ent = orm.ORM.query(reps, {'indexcol = %s': rpt['log_id']})[0]
    hdl = None
    try:
      hdl = HANDLERS[ltp]
    except KeyError:
      raise Exception, ('Who handles "%s" reports?' % (ltp, ))
    hdl.handle(ent, rpt, rdx)
    orm.ORM.store(tbl, {'indexcol':idx, 'objprocess': datetime.today()})
  sys.stderr.write('\n')
  return 1

def rwabugiri_main(argv):
  if len(argv) < 3:
    sys.stderr.write('%s log_table report_table\n' % (argv[0], ))
    return 1
  return transfer_objects(argv[1], argv[2])

if __name__ == '__main__':
  bottom  = sys.exit(rwabugiri_main(sys.argv))
