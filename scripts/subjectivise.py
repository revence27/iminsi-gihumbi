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
    return orm.ORM.store(self.table, self.attrs)

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
    if not gat.count():
      self.create(nid)
      return self.load(nid)
    self['indexcol']  = gat[0]['indexcol']
    return self

  def create(self, nid):
    return orm.ORM.store(self.table, {'patient_id':nid})

class Pregancies:
  def handle(self, entry, row, hst):
    mum = Mother('ig_mothers')
    mum.load(entry['patient_id'])
    mum.copy(entry, ['province_pk', 'district_pk', 'health_center_pk', 'report_date', 'lmp']).copy(row,   [
      ('mother_weight_float', 'weight'),
      ('mother_height_float', 'height'),
      ('parity_float', 'parity'),
      ('gravity_float', 'gravidity')
    ])
    raise Exception, str(mum.attrs)
    mum.save()
    raise Exception, str(entry.value)

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
  sys.stderr.write('%d: %s\n' % (qry.count(), qry.query))
  try:
    for rpt in qry.list():
      idx = rpt['indexcol']
      ltp = rpt['report_type']
      ent = orm.ORM.query(reps, {'indexcol = %s': rpt['log_id']})[0]
      rdx = HANDLERS[ltp].handle(ent, rpt, rdx)
      orm.ORM.store(tbl, {'indexcol':idx, 'objprocess': datetime.today()})
  except KeyError:
    raise Exception, ('Who handles "%s" reports?' % (tbl, ))
  sys.stderr.write('\n')
  return 1

def rwabugiri_main(argv):
  if len(argv) < 3:
    sys.stderr.write('%s log_table report_table\n' % (argv[0], ))
    return 1
  return transfer_objects(argv[1], argv[2])

if __name__ == '__main__':
  bottom  = sys.exit(rwabugiri_main(sys.argv))
