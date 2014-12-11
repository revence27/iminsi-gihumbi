from ectomorph import orm

class EntityNonExistent(Exception):
  pass

class IncompleteEntity(Exception):
  pass

class UninitialisedEntity(Exception):
  pass

class MistakenOneToOne(Exception):
  pass

class Entity:
  table       = 'rw_objects'
  required    = []
  unique      = []
  replaces    = False
  can_have    = lambda _: []
  belongs_to  = None

  def __init__(self):
    self.fs   = {}
    self.b4   = []
    self.live = None

  def column(self):
    return str(self.__class__).split('.')[-1].lower()

  def replace_conditions(self):
    klass = self.__class__
    return klass.replaces or (klass.unique and not self.is_unique())

  def is_unique(self):
    klass = self.__class__
    hsh   = {}
    for un in klass.unique:
      hsh['%s = %%s' % (un, )] = self.fs[un]
    return orm.ORM.query(klass.table, hsh, cols = ['COUNT(*) AS total'])[0]['total'] < 1

  def link(self, objs):
    self.b4.extend(objs)
    return self.b4

  def links(self):
    ans   = {}
    dem   = []
    mods  = []
    klass = self.__class__
    for it in self.b4:
      if not it.live:
        raise UninitialisedEntity, ('Failed auto-linking %s' % (str(it), ))
      crass = it.__class__
      ihm   = it.can_have()
      sb2   = self.belongs_to() if klass.belongs_to else None
      shm   = self.can_have()
      ib2   = it.belongs_to() if crass.belongs_to else None
      ans['%s_id' % (it.column(), )]  = it.live
      parent  = '%s_id' % (self.column(), )
      # XXX: For now, linking all prior objects.
      if klass == ib2:
        mods.append((it, parent))
      # XXX: For now, no inexplicit many-to-many relationships.
      # dem.append(('%s_%s' % (it.column(), self.column()), {('%s_id' % (it.column(), )):it.live}, parent))
    ans.update(self.fs)
    return (ans, dem, mods)

  def process(self, key, data):
    self.fs[key]  = data

  def fetch(self, msg):
    if self.live:
      return live
    self.live = self.load(msg)
    return self.live

  def load(self, _):
    raise EntityNonExistent, ('Load what? (%s)' % (str(self)))

  def sufficient_data(self):
    for r in self.__class__.required:
      if not (r in self.fs):
        return False
    return True

  def save(self):
    if self.live:
      return (self.live, set())
    klass = self.__class__
    if not self.sufficient_data():
      raise IncompleteEntity, ('Requires: %s' % (klass.required, ))
    dat, dem, mods  = self.links()
    tbls  = set([klass.table])
    self.live = orm.ORM.store(klass.table, dat)
    for tbl, it, coln in dem:
      it.update({coln: self.live})
      orm.ORM.store(tbl, it)
      tbls.add(tbl)
    for obj, fld in mods:
      obj.process(fld, self.live)
      _, tbs  = obj.save()
      tbls    = tbls.union(tbs)
    return (self.live, tbls)

class UniqueEntity(Entity):
  def id_fields(self, msg):
    if not self.__class__.unique:
      raise Exception, 'What uniqueness fields?'
    return self.__class__.unique

  def get_identifiers(self, msg, ents):
    '''type: [(string, value)]

[('indangamuntu', ents['indangamuntu']), ('lmp', ents['daymonthyear'] - timedelta(days = 270))]'''
    raise Exception, str(u'Return workable identifiers.\r\n' % (str(__doc__)))

  def identifier(self, msg):
    ans         = []
    lks, _, _ = self.links()
    try:
      for x in self.id_fields(msg):
        ans.append((x, lks[x]))
    except KeyError, e:
      return self.get_identifiers(msg, lks)
    return ans

  def load(self, msg):
    hsh   = {}
    mig   = []
    cols  = ['indexcol']
    for k, v  in  self.identifier(msg):
      hsh['%s = %%s' % (k, )] = v
      mig.append((k, v))
      cols.append(k)
    got = orm.ORM.query(self.__class__.table, hsh, migrations = mig, cols = cols)
    for ans in got.list():
      for k in cols:
        self.process(k, ans[k])
    try:
      return self.fs['indexcol']
    except KeyError:
      raise EntityNonExistent, str(hsh)

def process_entities(msg, enthash):
  objs, tbls  = load_dependencies(msg, enthash)
  for ent in enthash.get('initialises', []):
    tbls.add(ent.table)
    obj   = ent()
    obj.link(objs)
    data  = msg.data()
    collate_data(obj, data)
    try:
      obj.fetch(msg)
      if obj.replace_conditions():
        _, ntbls  = obj.save()
        tbls      = tbls.union(ntbls)
    except EntityNonExistent, ene:
      _, ntbls  = obj.save()
      tbls      = tbls.union(ntbls)
    objs.append(obj)
  return tbls

def load_dependencies(msg, enthash):
  deps  = []
  tbls  = set()
  for dep in enthash.get('uses', []):
    tbls.add(dep.table)
    obj   = dep()
    obj.link(deps)
    data  = msg.data()
    collate_data(obj, data)
    deps.append(obj.fetch(msg))
  return (deps, tbls)

def collate_data(obj, data, cle = None):
  if type(data) == type({}):
    for fld in data:
      thg = data[fld]
      if type(thg) == type([]):
        collate_data(obj, thg, fld)
      else:
        obj.process(fld, thg)
  elif type(data) == type([]):
    for thg in data:
      obj.process('%s_%s' % (cle, thg.lower()), thg)
