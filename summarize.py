#!  /usr/bin/env python
# encoding: utf-8
# vim: ts=2 expandtab

from ectomorph import orm

orm.ORM.connect(dbname  = 'thousanddays', user = 'thousanddays', host = 'localhost', password = 'thousanddays')

class Record(object):
 def __init__(self, cursor, registro):
  for (attr, val) in zip((d[0] for d in cursor.description), registro) :
   setattr(self, attr, val)


def fetch_data(cursor):
 ans = []
 for row in cursor.fetchall() :
  r = Record(cursor, row)
  ans.append(r)
 return ans

def fetch_data_cursor(orm, query_string):
 curseur = orm.ORM.cursor()
 curseur.execute(query_string)
 return curseur

def build_fields(fields):
 fs = []
 for f in fields:
  if 'alias' and 'table' in f.keys(): fs.append("%s.%s AS %s" % (f['table'], f['value'], f['alias']))
  elif 'alias' in f.keys() and 'table' not in f.keys(): fs.append("%s AS %s" % (f['value'], f['alias']))
  elif 'alias' and 'table' not in f.keys(): fs.append("%s" % (f['value']))
  else: fs.append("%s.%s" % (f['table'], f['value']))
 if fs!= []:
  fss = ''.join("%s, " % an for an in fs)
  return fss[0:len(fss)-2]
 return ''

def build_extracts(extracts):
 exs = []
 for ex in extracts:
  if 'alias' in ex.keys(): exs.append("(EXTRACT(%s FROM %s.%s)) AS %s" % (ex['value'], ex['table'], ex['field'], ex['alias']))
  else: exs.append("(EXTRACT(%s FROM %s.%s))" % (ex['value'], ex['table'], ex['field']) )
 if exs!= []:
  exss = ''.join("%s, " % an for an in exs)
  return exss[0:len(exss)-2]
 return ''

def build_inners(primary_table, inner_joins):
 injs = []
 for inj in inner_joins: injs.append("INNER JOIN %s ON (%s.%s = %s.%s)" % (inj['table'], primary_table, inj['outer_field'], inj['table'], inj['field']))
 if injs!= []:
  injss  = ''.join("%s " % an for an in injs)
  return injss 
 return '' 

def build_group_by(group_by):
 if group_by != []:
  gs  = ''.join("%s, " % an for an in group_by)
  return "GROUP BY %s " % gs[0:len(gs)-2]
 return ''

def build_order_by(order_by):
 if order_by != []:
  ors  = ''.join("%s, " % an for an in order_by)
  return "ORDER BY %s " % ors[0:len(ors)-2]
 return ''

def build_tables(tables):
 if tables != []:
  ts  = ''.join("%s, " % an for an in tables)
  return " %s " % ts[0:len(ts)-2]
 return ''

def build_query( fields = [], extracts = [], primary_table = '', tables = [], inner_joins = [], where_clause = '', group_by = [], order_by = []):
  qs = ''
  fields = build_fields(fields)
  extracts = build_extracts(extracts)
  tables = build_tables(tables)
  inner_joins = build_inners(primary_table, inner_joins)
  group_by = build_group_by(group_by)
  order_by = build_order_by(order_by)
  if fields != '' and primary_table != '':
    if extracts != '':
     qs = ' SELECT %s, %s FROM %s %s %s %s %s' % (fields, extracts, primary_table, inner_joins, where_clause, group_by, order_by)
     if tables != '': qs = ' SELECT %s, %s FROM %s, %s %s %s %s %s' % (fields, extracts, primary_table, tables, inner_joins, where_clause, group_by, order_by)
    else:
     qs = ' SELECT %s FROM %s %s %s %s %s' % (fields, primary_table, inner_joins, where_clause, group_by, order_by)
  return qs
  
def summarize_by_location(primary_table = 'pre_table', tables = [], where_clause = [] , nationwide = True, province = None, district = None, location = None):

 fields = []
 inner_joins = []
 group_by = []
 
 if nationwide:
  fields.append( {'value': 'indexcol', 'alias': 'province_id', 'table': 'chws__province'})
  fields.append( {'value': 'name', 'alias': 'province_name', 'table': 'chws__province'} )
  inner_joins.append({'table': 'chws__province', 'field': 'indexcol' , 'outer_field': 'province_pk'})
  group_by.append('province_name')
  group_by.append('province_id')
  if province:
    if where_clause == []: where_clause.append(' WHERE %s.province_pk = %d ' % ( primary_table, int(province)))
    else: where_clause.append(' AND %s.province_pk = %d ' % ( primary_table, int(province)))

 if province:
  fields.append( {'value': 'indexcol', 'alias': 'district_id', 'table': 'chws__district'})
  fields.append( {'value': 'name', 'alias': 'district_name', 'table': 'chws__district'} )
  inner_joins.append({'table': 'chws__district', 'field': 'indexcol' ,  'outer_field': 'district_pk'})
  group_by.append('district_name')
  group_by.append('district_id')
  if district:
    if where_clause == []: where_clause.append(' WHERE %s.district_pk = %d ' % ( primary_table, int(district)))
    else: where_clause.append(' AND %s.district_pk = %d ' % ( primary_table, int(district)))

 if district:
  fields.append( {'value': 'indexcol', 'alias': 'location_id', 'table': 'chws__healthcentre'})
  fields.append( {'value': 'name', 'alias': 'location_name', 'table': 'chws__healthcentre'} )
  inner_joins.append({'table': 'chws__healthcentre', 'field': 'indexcol' , 'outer_field': 'health_center_pk'})
  group_by.append('location_name')
  group_by.append('location_id')
  if location:
    if where_clause == []: where_clause.append(' WHERE %s.health_center_pk = %d ' % ( primary_table, int(location)))
    else: where_clause.append(' AND %s.health_center_pk = %d ' % ( primary_table, int(location)))

 fields.append( {'value': 'COUNT(*)', 'alias': 'total'} )
 
 if where_clause != []:
  qs = build_query( fields = fields, extracts = [], primary_table = primary_table, tables = [],
                  inner_joins = inner_joins, where_clause = ''.join( ' %s' % w for w in where_clause), group_by = group_by, order_by = [])
 else:
  qs = build_query( fields = fields, extracts = [], primary_table = primary_table, tables = [],
                    inner_joins = inner_joins, where_clause = '', group_by = group_by, order_by = [])

 if qs != '':
  curz = fetch_data_cursor(orm, qs)
  data = fetch_data(curz)
  return data
 
 return []

