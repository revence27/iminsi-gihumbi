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

  def copy_presence(self, source, cols):
    for col in cols:
      ncol  = col
      ocol  = col
      if type(col) == type(('', '')):
        ocol  = col[0]
        ncol  = col[1]
      self.set(ncol, False if (source[ocol] is None) else True)
    return self

MOTHER_MIGRATIONS = [
  ('pregnancies', 0),
  ('patient_id', '1198670116338016'),
  ('handwashing', True),
  ('no_handwashing', True),
  ('miscarries', True),
  ('surgeries', True),
  ('toilet', True),
  ('no_toilet', True),
  ('old', True),
  ('young_mother', True),
  ('prev_home_deliv', True),
  ('chronic_disease', True)
]
class Mother(R1000Object):
  def load(self, nid):
    gat = orm.ORM.query(self.table, {'patient_id = %s': nid}, migrations = MOTHER_MIGRATIONS)
    self['patient_id']  = nid
    if not gat.count():
      self['pregnancies'] = 1
      self.save()
      return self.load(nid)
    self['indexcol']    = gat[0]['indexcol']
    return self

BABY_MIGRATIONS = [
  ('pregnancy', 0),
  ('weight', 0.0),
  ('height', 0.0),
  ('cnumber', 0.0),
  ('cnumber', 0.0),
  ('muac', 0.0),
  ('birth_date', datetime.today()),
  ('girl', True),
  ('boy', True),
  ('abnormal_fontanelle', True),
  ('cord_infection', True),
  ('congenital_malformation', True),
  ('ibibari', True),
  ('disabled', True),
  ('stillborn', True),
  ('no_problem', True)
]
class Baby(R1000Object):
  def load(self, pid):
    gat = orm.ORM.query(self.table, {'pregnancy = %s': pid}, migrations = BABY_MIGRATIONS)
    self['pregnancy'] = pid
    if not gat.count():
      self.save()
      return self.load(pid)
    self['indexcol']    = gat[0]['indexcol']
    self['birth_date']  = gat[0]['birth_date']
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

ADATA_MIGRATIONS = [
  ('baby', 1),
  ('exc_breast', True),
  ('no_breast', True),
  ('comp_breast', True),
  ('height', 1.0),
  ('weight', 1.0),
  ('muac', 1.0),
  ('birth_date', datetime.today())
]
class AData(R1000Object):
  def load(self, bub):
    gat = orm.ORM.query(self.table, {'baby = %s': bub}, migrations = ADATA_MIGRATIONS)
    self['baby']  = bub
    if not gat.count():
      self.save()
      return self.load(bub)
    # self['indexcol']      = gat[0]['indexcol']
    return self

PREGNANCY_MIGRATIONS  = [
  ('lmp', datetime.today()),
  ('mother', 1),
  ('at_clinic', True),
  ('at_home', True),
  ('at_hospital', True),
  ('en_route', True),
  ('no_problem', True),
  ('no_prev_risks', True),
  ('rapid_breathing', True),
  ('multiples', True),
  ('mother_well', True),
  ('young_mother', True),
  ('asm_advice', True),
  ('vomiting', True),
  ('previous_serious_case', True),
  ('severe_anaemia', True),
  ('previous_haemorrhage', True),
  ('mother_sick', True),
  ('coughing', True),
  ('malaria', True),
  ('referred', True),
  ('diarrhoea', True),
  ('previous_convulsion', True),
  ('oedema', True),
  ('fever', True),
  ('stiff_neck', True),
  ('jaundice', True),
  ('pneumonia', True),
  ('hypothermia', True)
]
class Pregnancy(R1000Object):
  def load_latest(self, mum):
    gat = orm.ORM.query(self.table, {'mother = %s': mum}, cols = ['lmp'], sort = ('lmp', False), migrations = PREGNANCY_MIGRATIONS)
    if not gat.count():
      raise Exception, ('No recorded pregnancy for %s#%d' % (self.table, mum))
    return self.load(mum, gat[0]['lmp'])

  def load(self, mum, lmp):
    gat = orm.ORM.query(self.table, {'mother = %s': mum, 'lmp = %s': lmp}, migrations = PREGNANCY_MIGRATIONS)
    self['mother']  = mum
    self['lmp']     = lmp
    if not gat.count():
      self.save()
      her = orm.ORM.query('ig_mothers', {'indexcol = %s':mum})[0]
      # orm.ORM.store('ig_mothers', {'indexcol': mum, 'pregnancies': her['pregnancies'] + 1})
      return self.load(mum, lmp)
    self['indexcol']    = gat[0]['indexcol']
    return self

GENERAL_ATTRIBUTES  = [
]
LOCATION_ATTRIBUTES = [
  ('cl_bool', 'at_clinic'),
  ('ho_bool', 'at_home'),
  ('hp_bool', 'at_hospital'),
  ('or_bool', 'en_route')
  # TODO: Always collapse the above into an enum? XXX
]
class Pregancies:
  def handle(self, entry, row, hst):
    mum = Mother('ig_mothers')
    mum.load(entry['patient_id'])
    mum.save()
    rep = Reporter('ig_reporters')
    rep.load(entry['reporter_phone'])
    rep.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'sector_pk', 'cell_pk', 'village_pk'])
    rep.save()
    mum['reporter'] = rep['indexcol']
    prg = Pregnancy('ig_pregnancies')
    prg.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'sector_pk', 'cell_pk', 'village_pk', 'report_date', 'lmp'])
    prg.load(mum['indexcol'], entry['lmp'])
    prg.copy_presence(row, LOCATION_ATTRIBUTES + [
      ('np_bool', 'no_problem'),
      ('nr_bool', 'no_prev_risks'),
      ('rb_bool', 'rapid_breathing'),
      ('mu_bool', 'multiples'),
      ('mw_bool', 'mother_well'),
      ('yg_bool', 'young_mother'),
      ('aa_bool', 'asm_advice'),
      ('vo_bool', 'vomiting'),
      ('yj_bool', 'previous_serious_case'),
      ('sa_bool', 'severe_anaemia'),
      ('lz_bool', 'previous_haemorrhage'),
      ('ms_bool', 'mother_sick'),
      ('ch_bool', 'coughing'),
      ('ma_bool', 'malaria'),
      ('pr_bool', 'referred'),
      ('di_bool', 'diarrhoea'),
      ('kx_bool', 'previous_convulsion'),
      ('oe_bool', 'oedema'),
      ('fe_bool', 'fever'),
      ('ns_bool', 'stiff_neck'),
      ('ja_bool', 'jaundice'),
      ('pc_bool', 'pneumonia'),
      ('hy_bool', 'hypothermia'),
    ])
    prg.save()
    mum.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'sector_pk', 'cell_pk', 'village_pk', 'report_date', 'lmp']).copy(row,   [
      ('mother_weight_float', 'weight'),
      ('mother_height_float', 'height'),
      ('parity_float', 'parity'),
      ('gravity_float', 'gravidity'),
      ('indexcol', 'former_id')
    ]).copy_presence(row, [
      ('hw_bool', 'handwashing'),
      ('nh_bool', 'no_handwashing'),
      ('rm_bool', 'miscarries'),
      ('gs_bool', 'surgeries'),
      ('to_bool', 'toilet'),
      ('nt_bool', 'no_toilet'),
      ('ol_bool', 'old'),
      ('yg_bool', 'young_mother'),
      ('hd_bool', 'prev_home_deliv'),
      ('ds_bool', 'chronic_disease'),
    ])
    mum.save()

class Nutrition:
  def handle(self, entry, row, hst):
    mum = Mother('ig_mothers')
    mum.load(entry['patient_id'])
    prg = Pregnancy('ig_pregnancies')
    try:
      prg.load_latest(mum['indexcol'])
    except Exception, e:
      # TODO:
      # For now, just skip the faulty ones.
      return
      prg.load(mum['indexcol'], entry['lmp'] - timedelta(days = settings.GESTATION))
      return self.handle(entry, row, hst)
    bub = Baby('ig_babies')
    bub.load(prg['indexcol'])
    adt = AData('ig_adata')
    if row['child_height_float']:
      bub['height'] = row['child_height_float']
      bub.save()
    try:
      adt['birth_date'] = bub['birth_date']
    except:
      return
    adt.load(bub['indexcol'])
    adt.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'sector_pk', 'cell_pk', 'village_pk', 'report_date']).copy(row, [
      ('child_weight_float', 'weight'),
      ('child_height_float', 'height'),
      ('muac_float', 'muac')
    ]).copy_presence(row, [
      ('ebf_bool', 'exc_breast'),
      ('cbf_bool', 'comp_breast'),
      ('nb_bool', 'no_breast')
    ])
    adt.save()

class InterventionResult:
  def handle(self, entry, row, hst):
    raise Exception, row['report_date']

class Birth:
  def handle(self, entry, row, hst):
    mum = Mother('ig_mothers')
    mum.load(entry['patient_id'])
    prg = Pregnancy('ig_pregnancies')
    try:
      prg.load_latest(mum['indexcol'])
    except Exception, e:
      prg.load(mum['indexcol'], entry['lmp'] - timedelta(days = settings.GESTATION))
      return self.handle(entry, row, hst)
    mum.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'sector_pk', 'cell_pk', 'village_pk', 'report_date'])
    mum.save()
    prg.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'sector_pk', 'cell_pk', 'village_pk', 'report_date'])
    prg.copy_presence(row, LOCATION_ATTRIBUTES)
    prg.save()
    bub = Baby('ig_babies')
    bub.load(prg['indexcol'])
    bub.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'sector_pk', 'cell_pk', 'village_pk']).copy(row, [
      ('child_weight_float', 'weight'),
      ('child_number_float', 'cnumber'),
      ('ht_float', 'height'),
      # ('wt_float', 'weight'),
      ('lmp', 'birth_date'),
      ('muac_float', 'muac')
    ]).copy_presence(row, [
      ('gi_bool', 'girl'),
      ('bo_bool', 'boy')
    ] + LOCATION_ATTRIBUTES + [
      ('af_bool', 'abnormal_fontanelle'),
      ('ci_bool', 'cord_infection'),
      ('cm_bool', 'congenital_malformation'),
      ('ib_bool', 'ibibari'),
      # ('db_bool', 'disabled'),
      ('sb_bool', 'stillborn'),
      ('bf1_bool', 'breast1hr'),
      ('np_bool', 'no_problem')
      # TODO: Get from DB list.
    ])
    bub.save()

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
  pos = 0
  for rpt in qry.list():
    pos = pos + 1
    idx = rpt['indexcol']
    ltp = rpt['report_type']
    ent = orm.ORM.query(reps, {'indexcol = %s': rpt['log_id']})[0]
    hdl = None
    try:
      hdl = HANDLERS[ltp]
    except KeyError:
      raise Exception, ('Who handles "%s" reports?' % (ltp, ))
    hdl.handle(ent, rpt, rdx)
    sys.stderr.write('\r%d: %s#%d' % (pos, tbl, idx))
    sys.stderr.flush()
    orm.ORM.store(tbl, {'indexcol':idx, 'objprocess': datetime.today()})
  sys.stderr.write('\n')
  return 0

def rwabugiri_main(argv):
  if len(argv) < 3:
    sys.stderr.write('%s log_table report_table\n' % (argv[0], ))
    return 1
  ans = 0
  for tbl in argv[2:]:
    ans = transfer_objects(argv[1], tbl)
    if ans != 0: break
  return ans

if __name__ == '__main__':
  bottom  = sys.exit(rwabugiri_main(sys.argv))
