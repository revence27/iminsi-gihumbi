# encoding: utf-8
# vim: expandtab ts=2

import copy
import datetime
from decimal import Decimal
import psycopg2
import re
from sys import stderr
from StringIO import StringIO

class Row:
  '''Wrapper for the tuple (.value) of the row. Allows classes-based responses to Django template protocols (__getitem__).'''
  def __init__(self, query, value = None, **kwargs):
    self.query  = query
    self.hooks  = kwargs.get('hooks', {})
    self.kwargs = kwargs
    self.value  = value

  def set_row(self, r):
    '''Imperative style is bad style. But this is Python, anyway.'''
    self.value  = r

  def __setitem__(self, k, v):
    '''Don't use.'''
    raise Exception, 'Read-only, man. :-p'

  def __getitem__(self, k):
    '''Django calls this. Would execute the lazy query.
Hooks are used thus:

  row = ORM.query('pre_table', 'SELECT 70 AS lxx', hooks = {'septuagint':lambda x, y: x['lxx'] + 2})[0]
  # row.septuagint
  print 'LXX:', row['septuagint'] # LXX: 72
  
x is this row object, and y is the same key at which the callable hos been found.
If the hook is a {hash:table}, it is considered as a mere lazy specialisation of this same query, permitting things like:

  query.subquery.subsubquery

which are defined declaratively, and delayed in specialisation and execution.
'''
    try:
      if not self.query.cols:
        self.query.load_description()
        return self[k]
      return self.value[self.query.cols[k]]
    except KeyError:
      hk  = self.hooks[k]
      hkt = type(hk)
      if hkt == type({}):
        return self.query.specialise(hk)
      if callable(hk):
        return hk(self, k)
      return hk

class Query:
  '''Query object. Not to be constructed directly by the user; that's why Java reinvented the FactoryFactoryFactory.factoryFactory()
'''
  def __init__(self, pg, djconds, tn, **kwargs):
    '''
The first arg may be a string (the raw query), or an executable (which, when executed with this Query, returns the raw query), or a hash of the query conditions as keys with their interpolation data as values.
The second arg is the table name. The table on which the query operates.
  
  q1  = Query({'weight_float > %s': 50.0}, 'pre_table')
  # Corresponds to SELECT ... FROM pre_table WHERE weight_float > 50.0

The keyword args are all optional:

  table:
    replaces the table-name argument (second).
  cols:
    the columns to which to limit the query.
  migrations:
    description of columns that should be created, if they are missing.
  annotate:
    a hash of subqueries that will be returned by the column-name given in their key, being executed with the conditions of the current query.
      q2  = Query({'weight_float > %s': 50.0}, 'pre_table', annotate = {'total':'COUNT(*)'})
      # Corresponds to SELECT (SELECT COUNT(*) FROM pre_table WHERE weight_float > 50.0) AS total, name FROM pre_table WHERE weight_float > 50.0
    This is meant for use in those cases where such a specialised query is the efficient way to establish record sizes. This may also be needed when named cursors are used.
  precount:
    this is the pre-computed number of records returned from this query; we don't ask where you got it.
  hooks:
    see Row.__getitem__
  optimise:
    a hash that turns on and controls database querying optimisations.
      q3  = Query(... optimise = {'name':'optim1'})
      # q3  is now an optimised query
    The required name field turns on named cursors. These optimised cursors, however, do not have the count of the results. You could use precount, or pass another field with name, counter.
    This is the default counter for optimised queries:

      def default_counter(self, qry):
        nq  = qry.specialise({})
        nq.names  = ['COUNT(*) AS tot']
        nq.kwargs.pop('optimise', None)
        try:
          return nq[0].value[0]
        except Exception, e:
          return 0

      q4  = Query(... optimise = {'name':'optim2', 'counter':default_counter})

    The results of the counter are checked once and cached. (Even precount is cached.)
'''
    self.postgres = pg
    self.djconds  = djconds
    self.kwargs   = copy.copy(kwargs)
    self.tn       = tn
    self.cursor   = None

  @property
  def tablenm(self):
    return self.kwargs.get('table', self.tn)

  @property
  def precount(self):
    return self.kwargs.get('precount')

  @property
  def extended(self):
    return self.kwargs.get('extended', {})

  @property
  def annots(self):
    return self.kwargs.get('annotate', {})

  @property
  def names(self):
    return self.kwargs.get('cols', [])

  def where(self, k, v):
    '''Adds a condition to the ones supplied in the constructor.'''
    self.djconds[k] = v
    return self

  def put_names(self, dat):
    '''Supplies the column names without due consultation. (Be very careful.)'''
    self.names  = dat

  def set_names(self, dat):
    '''Supplies the column names from a hash without due consultation. (Be very careful.)'''
    self.names  = dat.keys()
    self.cols   = dat

  def active_columns(self, qid):
    '''Returns the names of the columns seen for this query (normally info coming from the DB).'''
    return self.names or ORM.active_columns(qid)

  def assemble_sort(self, asc):
    '''Assemble into query the parts that sort (ASC/DESC).'''
    return ORM.assemble_sort(asc)

  def assemble_order(self, limits):
    '''Assemble into query the parts that order (ORDER BY).'''
    return ORM.assemble_order(limits)

  def assemble_limits(self, limits):
    '''Assemble into query the parts that limit sizes (LIMIT).'''
    return ORM.assemble_limits(limits)

  def assemble_conditions(self, conds):
    '''Assemble into query the parts that express conditions (WHERE).'''
    return ORM.assemble_conditions(conds)

  def specialise(self, djconds, **kwargs):
    '''Returns a different copy of this query, with the arguments treated as new conditions.'''
    nova          = copy.copy(self)
    nova.djconds  = copy.copy(self.djconds)
    nova.kwargs   = copy.copy(self.kwargs)
    nova.djconds.update(djconds)
    nova.kwargs.update(kwargs)
    return nova

  def filter(self, **kwargs):
    '''Django ORM backward-compatibility. See Django docs.'''
    nova          = copy.copy(self)
    nova.djconds  = copy.copy(self.djconds)
    for k in kwargs:
      nova.djconds[k] = ORM.alter_condition(kwargs, k)
    return nova

  def distinct(self, *args, **kwargs):
    '''Django ORM backward-compatibility. See Django docs.'''
    return self
    raise Exception, str((args, kwargs))
    pass

  def values(self, *vals, **kwargs):
    '''Django ORM backward-compatibility. See Django docs.'''
    it        = copy.copy(self)
    it.names  = kwargs.get('new', ['orig_%s' % (x,) for x in vals])
    # dem       = it.fetchall()
    # return dem
    # raise Exception, str((it.query, it.cursor.rowcount, it.cursor.query))
    return it

  def extra(self, **kwargs):
    '''Django ORM backward-compatibility. See Django docs.'''
    return self

  def exists(self):
    '''Determines if this query would return anything.'''
    self.execute()
    return max(self.cursor.rowcount, 0) < 1

  def annotate(self, **kwargs):
    '''Django ORM backward-compatibility. See Django docs.'''
    return self.specialise(annotate = kwargs)

  def order_by(self, _, cue = ''):
    '''Django ORM backward-compatibility. See Django docs.'''
    if len(cue) < 1: return self
    asc, gd, etc = False, cue[0], cue[1:]
    if gd != '-':
      asc = True
      etc = cue
    ans       = copy.copy(self)
    ans.sort  = (etc, asc)
    return ans

  def hdl_(self, qry):
    '''Internal optimised query counter implementation.'''
    nq  = qry.specialise({})
    nq.names  = ['COUNT(*) AS tot']
    nq.kwargs.pop('optimise', None)
    try:
      return nq[0].value[0]
    except Exception, e:
      return 0

  def list(self):
    '''Returns a generator over the rows.'''
    for it in range(self.count()):
      yield self[it]

  def count(self):
    '''Number of result rows. It is important to use and respect this, because asking for more rows that we have can return None instead of failing.'''
    if not self.cursor:
      self.execute()
    if not (self.precount is None):
      return self.precount
    minim = 0
    if self.kwargs.get('optimise', {}).get('name'):
      hdl = self.kwargs.get('optimise', {}).get('counter', self.hdl_)
      if self.cursor.rowcount < minim:
        self.precount  = hdl(self)
        return self.count()
    return max(minim, self.cursor.rowcount)

  def __names(self, curz, dft):
   '''Get the column names, as declared by the database. This is reliable.'''
   return [x.name for x in curz.description] if curz.description else dft

  def execute(self, retries = True):
    '''Final ultimate execution. If the query fails, it runs migrations.'''
    if not self.cursor:
      try:
        self.names, self.cursor = self.__execute()
      except psycopg2.ProgrammingError, e:
        if retries:
          self.postgres.commit()
          self.migrate(self.kwargs.get('migrations', []), e)
          try:
            return self.execute(False)
          except psycopg2.ProgrammingError, e:
            self.postgres.commit()
            raise e
        raise e
      self.cols               = self.__set_names()
    # stderr.write('>>>\t%s\r\n' % (self.query, ))
    return self

  def migrate(self, migs, _):
    '''Runs the migrations supplied.'''
    curz = self.postgres.cursor()
    for mig in migs:
      ORM.ensure_column(curz, self.tablenm, *mig)
    curz.close()
    self.postgres.commit()

  def fetchall(self):
    '''Django ORM backward-compatibility. See Django docs.'''
    if not self.cursor:
      self.execute()
      return self.cursor.fetchall()
    return self.cursor.fetchall()

  def fetch(self):
    '''Django ORM backward-compatibility. See Django docs.'''
    if not self.cursor:
      self.execute()
      return self.fetch()
    return self.fetchone()

  def __getitem__(self, them):
    '''Propagates Django protocols and provides truly subscripted access to query rows, which are returned as Row instances.'''
    if not self.cursor:
      self.execute()
      return self[them]
    if type(them) in [type('method'), type(u'method')]:
      raise AttributeError, 'Call the method itself, O foolish and mal-designed Django templates engine!'
      return apply(getattr(self, them))
    if type(them) == type(0):
      try:
        self.cursor.scroll(them, mode = 'absolute')
      except Exception:
        return None
      seul  = self.cursor.fetchone()
      return Row(self, seul, **self.kwargs)
    dem = []
    try:
      self.cursor.scroll(them.start, mode = 'absolute')
      curz  = self.cursor.fetchmany(them.stop - them.start)
      for ent in curz:
        dem.append(Row(self, ent, **self.kwargs))
    except Exception:
      pass
    return dem

  def old__getitem__(self, them):
    if type(them) != slice:
      raise ValueError, ('Should be a slice [column-name:row], not a %s (%s)' % (type(them), str(them)))
    try:
      return them.stop[self.names[them.start]]
    except ValueError:
      raise NameError, ('No column called "%s" (has: %s).' % (colnm, ', '.join(cols)))

  def load_description(self):
    '''To be called in those times when a database-supplied description of the columns in the query is required.'''
    ans = {}
    nms = []
    pos = 0
    if not self.cursor:
      self.__execute()
      return self.load_description()
    if self.cursor.description:
      for dsc in self.cursor.description:
        nms.append(dsc.name)
        ans[dsc.name] = pos
        pos           = pos + 1
    else:
      self.count()
      return self.load_description()
    self.names  = nms
    self.cols   = ans
    return (nms, ans)

  def __set_names(self):
    '''This is a helper that records and returns column information.'''
    self.cols   = {}
    notI        = 0
    for x in (self.names or {}):
      self.cols[x]  = notI
      notI          = notI + 1
    return self.cols

  # TODO: Work with views to ensure closing of cursors?
  def __execute(self):
    '''Runs once per query, open the main cursor and fills out last state data.'''
    qry   = self.query
    curz  = None
    optim = self.kwargs.get('optimise', {})
    if optim:
      curn  = optim['name']
      curz  = self.postgres.cursor(curn)
    else:
      curz  = self.postgres.cursor()
    curz.execute(qry)
    cols  = self.__names(curz, optim.get('cols', self.kwargs.get('cols')))
    return (cols, curz)

  def close(self):
    '''Should run once per query, and close the main cursor.'''
    if not self.cursor: return
    return self.cursor.close()

  def __enter__(self):
    pass  # For now.

  def __exit__(self, *args):
    self.close()

  def __apply_extensions(self):
    them  = self.extended
    cnds  = self.djconds.items()
    rez   = {}
    for k in them:
      q, c    = them[k]
      rez[k]  = (q, dict(cnds + [(c, '')]))
    return rez

  @property
  def query(self):
    '''A string of the raw query as it would be executed.'''
    if type(self.djconds) in [type('str'), type(u'unicode')]:
      return self.djconds
    if type(self.djconds) == type(lambda x: x):
      return self.djconds(self)
    qry   = u'%s%s%s' % (self.assemble_conditions(self.djconds), self.assemble_sort(self.kwargs.get('sort', None)), self.assemble_limits(self.kwargs))
    cols  = u', '.join(self.kwargs.get('cols', self.active_columns(self.kwargs.get('qid')) or ['*']))
    annot = []
    parts = copy.copy(self.annots)
    parts.update(self.__apply_extensions())
    for k in parts:
      it  = parts[k]
      q   = qry
      if type(it) ==  type(('query', 'conds')):
        q   = u'%s%s' % (self.assemble_conditions(it[1]), self.assemble_limits(self.kwargs))
        it  = it[0]
      annot.append(u'(SELECT %s FROM %s%s) AS %s' % (it, self.tablenm, q, k))
      # annot.append(u'(SELECT %s %s) AS %s' % (it, q, k))
    annot.append(u'%s FROM %s%s' % (cols, self.tablenm, qry))
    qry = u', '.join(annot)
    return u' '.join([u'SELECT', qry])

  def __unicode__(self):
    return self.query

class ORM:
  'The base class for all models.'
  created   = False
  columned  = False
  postgres  = None

  @classmethod
  def connect(self, *args, **kwargs):
    self.postgres = psycopg2.connect(*args, **kwargs)

  @classmethod
  def migrate(self, curz, tn, migs):
    '''Runs the migrations supplied.'''
    for mig in migs:
      ORM.ensure_column(curz, tn, *mig)

  @classmethod
  def alter_condition(self, conds, ok):
    '''A way to plug new DB layout into the old code's expectation.'''
    if not ok in conds:
      return ok, None
    idem    = lambda x: x
    newks   = {
      'type': ('report_type = %s', lambda x: NAME_MATCHING[x.name]),
      'type__name': ('report_type = %s', lambda x: NAME_MATCHING[x]),
      'nation__id': ('nation_pk = %s', idem),
      'created__lte': ('created_at <= %s', idem),
      'created__gte': ('created_at >= %s', idem),
      'type__name__in': ('report_type IN (%s)', lambda dem: ', '.join([NAME_MATCHING[x] for x in (dem or [''])])),
    }
    try:
      nk, nv  = newks[ok]
      return (nk, nv(conds[ok]) if type(nv) == type(idem) else nv)
    except KeyError:
      raise Exception, ('Specify adapter for %s (%s)' % (ok, conds[ok]))

  @classmethod
  def assemble_order(self, order):
    '''Assemble into query the parts that order (ORDER BY).'''
    od  = order.get('order', None)
    if not od: return ''
    return u' ORDER BY ' + od

  @classmethod
  def assemble_limits(self, lims):
    '''Assemble into query the parts that limit (LIMIT).'''
    limits  = lims.get('limit', None)
    offset  = lims.get('offset', None)
    if not any([limits, offset]): return ''
    return u'%s%s' % (u' LIMIT %d' % (limits, ) if limits else u'', u' OFFSET %d' % (offset, ) if offset else u'')

  @classmethod
  def assemble_conditions(self, cnds):
    '''Assemble into query the conditions (WHERE).
If 'Invert Query' is supplied as one of the condition keys, the entire set of conditions will be negated.'''
    curz  = self.postgres.cursor()
    conds = copy.copy(cnds)
    ans   = []
    neg   = False
    if type(conds) in [type(''), type(u'')]:
      ans = [conds]
    else:
      neg   = conds.pop('Invert Query', False)
      for cond in conds:
        dat = None
        rez = conds[cond]
        if type(rez)  ==  type((1, 2)):
          dat = curz.mogrify(cond, rez)
        else:
          if hasattr(rez, '__iter__'):
            # dat = curz.mogrify(cond, (rez,))
            dat = u'(%s)' % ((u', '.join([curz.mogrify(u'%s', (it, )) for it in rez])), )
            dat = cond % (dat, )
          else:
            dat = curz.mogrify(cond, (rez, ))
        ans.append(u'(%s)' % (dat, ))
      curz.close()
    return (u' WHERE ' if conds else u'') + ((u'NOT (%s)' if neg else u'%s') % (u' AND '.join(ans)))

  @classmethod
  def assemble_sort(self, dem):
    '''Assemble into query the parts that sort (ORDER BY).'''
    if not dem: return u''
    cn, dr = dem
    return u' ORDER BY %s %s/*ENDING*/' % (cn, u'ASC' if dr else u'DESC')

  seen_actives  = {}
  @classmethod
  def active_columns(self, qid = None):
    '''List of active columns.'''
    if not qid: return qid
    if not qid in self.seen_actives: return None
    return seen_actives[qid]

  @classmethod
  def record_activity(self, qid, qnom):
    '''Facility to cache table-column status.'''
    if not qid in self.seen_actives:
      self.seen_actives[qid] = set()
      return self.record_activity(qid, qnom)
    us  = self.seen_actives[qid]
    us.add(qnom)
    return us

  @classmethod
  def connection(self):
    'Returns the current connection.'
    return self.postgres

  @classmethod
  def cursor(self):
    'Returns a cursor for the current connection.'
    return self.connection().cursor()

  @classmethod
  def raw_query(self, q):
    'Runs this query against a new cursor of the current connection, returning the raw result.'
    return self.cursor().execute(q)

  @classmethod
  def query(self, tn, djconds = {}, **kwargs):
    '''SELECT * FROM pre_table
  ORM.query('pre_table')

SELECT * FROM pre_table WHERE x > 4
  ORM.query('pre_table', {'x > %s': 4})

SELECT (SELECT COUNT(*) FROM pre_table FROM pre_table WHERE ch_bool) AS total, * FROM pre_table WHERE ch_bool
  ORM.query('pre_table', {'ch_bool':''}, annotate = {'total':'COUNT(*)'})

print ORM.query('pre_table', {'created_at > %s':datetime.datetime.today(), 'Invert Query':True}).query
Prints:
   u"SELECT * FROM pre_table WHERE NOT (created_at > '1900-07-15T11:15:31.850252'::timestamp)"
'''
    tbl = self.ensure_table(tn)
    return Query(self.postgres, djconds, tn, **kwargs)

  @classmethod
  def find_matching_type(self, val, ctyp, cn = None):
    '''Matches sample value `val` to an SQL type (defaulting to `ctyp`). For error-reporting, cn is the name of the column for which this information is being collected.'''
    try:
      return {
        str:                ctyp,
        unicode:            ctyp,
        int:                u'INTEGER /*NOT NULL*/',
        long:               u'INTEGER /*NOT NULL*/',
        float:              u'FLOAT /*NOT NULL*/',
        bool:               u'BOOLEAN /*NOT NULL*/',
        Decimal:            u'FLOAT /*NOT NULL*/',
        datetime.datetime:  u'TIMESTAMP',
        datetime.date:      u'TIMESTAMP WITHOUT TIME ZONE',
        datetime.time:      u'TIMESTAMP'
      }[type(val)]
    except KeyError:
      raise Exception, (u'Supply type for column %s (has a %s, %s)?' % (cn, str(type(val)), str(val)))

  @classmethod
  def decide_type(self, vl, cn = None):
    '''Matches sample value `vl` to an SQL type. For error-reporting, cn is the name of the column for which this information is being collected.
If `vl` is a hash, then 'type' is the SQL type, 'default' the SQL default, 'null' the nullability of the column, and 'value' would, if provided, be a replacement for `vl`.'''
    ctyp  = u'TEXT DEFAULT NULL'
    dval  = vl
    if type(vl) == type((None, u'INTEGER DEFAULT NULL')):
      ctyp  = vl[1]
      dval  = vl[0]
    elif type(vl) == type({'type':'INTEGER', 'null':False, 'default':'', 'value':None}):
      dval  = vl.get('value')
      ddef  = vl.get('default')
      dstr  = u'%s %s%s' % (vl.get('type') or self.find_matching_type(dval, ctyp, cn), u'' if vl.get('null') else u'NOT NULL', (u' DEFAULT ' + ddef if ddef else u''))
      return self.decide_type((dval, dstr), cn)
    else:
      ctyp  = self.find_matching_type(vl, ctyp, cn)
      return self.decide_type((dval, ctyp), cn)
    return ctyp, dval

  @classmethod
  def delete(self, tn, i):
    curz    = self.postgres.cursor()
    curz.execute(u'DELETE FROM %s WHERE indexcol = %s' % (tn, i))

  @classmethod
  def store(self, tn, d, **kw):
    '''Stores in the table `tn` (creating it, if necessary) the hash provided in `dat`. The hash keyword item `indexcol` is treated as the ID of the object.
Keywords:
  This integer is the ID of the object. Provide it, if you have it.
'''
    if not d: return None
    kwargs  = copy.copy(kw)
    dat     = copy.copy(d)
    vals    = []
    curz    = self.postgres.cursor()
    tbl     = self.ensure_table(tn)
    ans     = dat.pop('indexcol', None)
    cols    = dat.keys()
    escer   = {
      type(lambda x: x) : lambda c, s, f: f[0](c, s)
    }
    escer.update(kwargs.pop('escapist', {}))
    self.migrate(curz, tn, kwargs.get('migrations', []))
    self.postgres.commit()
    for col in cols:
      dval  = dat[col]
      col   = self.ensure_column(curz, tbl, col, dval)
      self.postgres.commit()
      elval = None
      try:
        him   = escer[type(dval)]
        elval = him(curz, u'%s', (dval, ))
      except KeyError:
        elval = curz.mogrify(u'%s', (dval, ))
      vals.append(elval.decode('utf-8'))
    if not ans:
      qry = (u'INSERT INTO %s (%s) VALUES (%s) RETURNING indexcol;' % (tbl, u', '.join(cols), u', '.join(vals)))
      curz.execute(qry)
      ans = curz.fetchone()[0]
    else:
      dem = []
      for k in dat:
        dval  = dat[k]
        elval = None
        try:
          him   = escer[type(dval)]
          elval = him(curz, u'%s', (dval, ))
        except KeyError:
          elval = curz.mogrify(u'%s', (dval, ))
        dem.append(u'%s = %s' % (k, elval.decode('utf-8')))
      bzt = (u'UPDATE %s SET %s WHERE indexcol = %s;' % (tbl, u', '.join(dem), curz.mogrify(u'%s', (ans, ))))
      curz.execute(bzt)
    self.postgres.commit()
    curz.close()
    return ans

  seen_columns  = {}
  @classmethod
  def ensure_column(self, curz, tbl, col, dval, opts = {}):
    '''Using `curz` as cursor, creates (if necessary) the column `col` in the table `tbl`, using `dval` as the sample value.'''
    sncs  = self.seen_columns.get(tbl, set())
    if not col in sncs:
      curz.execute(u'SELECT TRUE FROM information_schema.columns WHERE table_name = %s AND column_name = %s', (tbl, col))
      if not curz.fetchone():
        word    = None
        # Unscheduled migrations; have to be idempotent.
        prepper = opts.get('prepper')
        if prepper:
          word  = prepper(tbl, col, dval)
        else:
          ctyp, dval  = self.decide_type(dval, col)
          word        = u'ALTER TABLE %s ADD COLUMN %s %s;' % (tbl, col, ctyp)
        curz.execute(word)
        sncs.add(col)
    self.seen_columns[tbl] = sncs
    return col

  seen_tables = set()
  @classmethod
  def ensure_table(self, tbl):
    '''Creates the table `tbl`, if necessary.'''
    try:
      if tbl in self.seen_tables: return tbl
      curz  = self.postgres.cursor()
      curz.execute(u'SELECT TRUE FROM information_schema.tables WHERE table_name = %s', (tbl,))
      if not curz.fetchone():
        curz.execute(u'CREATE TABLE %s (indexcol SERIAL NOT NULL, created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW());' % (tbl,))
        curz.close()
      self.postgres.commit()
      self.seen_tables.add(tbl)
      return tbl
    except Exception, e:
      raise Exception, ('Table creation: ' + str(e))
