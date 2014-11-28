#!  /usr/bin/env python
# encoding: utf-8
import cherrypy
import copy
from datetime import datetime, timedelta
from ectomorph import orm
from jinja2 import Environment, FileSystemLoader
import json
import migrations
import random
import re
import settings
import queries
import sha
import sys
import urllib2, urlparse
from summarize import *
from mapval import *
from pygrowup import helpers, Calculator

def child_status(weight = None, height = None, date_of_birth = None, sex = None):
 status = {}
 valid_gender = helpers.get_good_sex( sex )
 valid_age = helpers.date_to_age_in_months(date_of_birth)
 cg = Calculator(adjust_height_data=False, adjust_weight_scores=False)

 try:
  wfa = cg.zscore_for_measurement('wfa', weight, valid_age, valid_gender) if weight and valid_age and valid_gender else None
  if wfa and wfa <= -2: status.update({'underweight': 'UNDERWEIGHT'})
 except Exception, e: pass
 try: 
  hfa = cg.zscore_for_measurement('hfa', height , valid_age, valid_gender) if height and valid_age and valid_gender else None
  if hfa and hfa <= -2: status.update({'stunted': 'STUNTED'})
 except Exception, e: pass
 try:
  wfh = cg.zscore_for_measurement('wfh', weight, valid_age, valid_gender, height) if weight and height and valid_age and valid_gender else None
  if wfh and wfh <= -2: status.update({'wasted': 'WASTED'})
 except Exception, e: pass        

 if status == {}:
  status.update({'normal': 'NORMAL'})
 return status

def get_display(value):
 if type(value) == bool:
  if value == True: return 'Yes'
  else: return ''
 elif value is None: return ''
 else: return value
 return value

def neat_numbers(num):
  pcs = divided_num(str(num), 3)
  return ','.join(pcs)

def first_cap(s):
  if not s: return s
  return ' '.join([x[0].upper() + x[1:] for x in re.split(r'\s+', s)])

def divided_num(num, mx = 3):
  if len(num) < (mx + 1):
    return [num]
  lft = num[0:-3]
  rgt = num[-3:]
  return divided_num(lft) + [rgt]

class ThousandLocation:
  def __init__(self, loc, tp, nav, lmt, ttl, chop  = None):
    self.location   = loc
    self.loctype    = tp
    self.navigator  = nav
    self.title      = ttl
    self.limits     = lmt
    self.chop       = chop

  def __unicode__(self):
    nom = self.location['name']
    return u'%s %s' % (nom if not self.chop else self.chop(nom), self.title)

  @property
  def name(self):
    nom = self.location['name']
    return nom if not self.chop else self.chop(nom)

  def link(self, ref):
    pcs, qrs  = self.navigator.pre_link(self.navigator.link(ref))
    for l in self.limits:
      try:              del qrs[l]
      except KeyError:  pass
    return urlparse.urlunsplit((pcs[0], pcs[1], pcs[2], '&'.join(['%s=%s' % (k, urllib2.quote(qrs[k])) for k in qrs if qrs[k]]), pcs[4]))

class ThousandAuth:
  def __init__(self, usn):
    if not usn:
      raise cherrypy.HTTPRedirect('/')
    self.usern  = usn

  def username(self):
    return self.usern

  def check(self, pwd):
    him = orm.ORM.query('ig_admins', {'address = %s': self.usern})
    if him.count() < 1:
      return False
    him = him[0]
    slt = him['salt']
    shp = sha.sha('%s%s' % (slt, pwd)).hexdigest()
    return shp == him['sha1_pass']

  def conditions(self):
    ans = {}
    him = orm.ORM.query('ig_admins', {'address = %s': self.usern})[0]
    if him['province_pk']:
      ans['province_pk = %s'] = him['province_pk']
    if him['district_pk']:
      ans['district_pk = %s'] = him['district_pk']
    if him['health_center_pk']:
      ans['health_center_pk = %s'] = him['health_center_pk']
    return ans

  def checked_conditions(self, pwd):
    if not self.check(pwd):
      raise Exception, 'Access denied.'
    return self.conditions()

  def him(self):
    return orm.ORM.query('ig_admins', {'address = %s': self.usern})[0]

class ThousandNavigation:
  def __init__(self, auth, *args, **kw):
    self.args   = args
    self.kw     = kw
    self.auth   = auth
    td          = datetime.today()
    self.fin    = datetime(year = td.year, month = td.month, day = td.day)
    self.gap    = timedelta(days = 1000 - 1)

  def pages(self, qry, limit = 100):
    tot, etc  = divmod(qry.count(), limit)
    if etc:
      tot = tot + 1
    cpg = int(self.kw.get('page', '0'))
    crg = cpg * limit
    pgs = xrange(tot)
    return (cpg, (crg, crg + limit), pgs)

  def __unicode__(self):
    them  = self.listing
    them.reverse()
    return ', '.join([unicode(x) for x in them])

  @property
  def listing(self):
    dem = [ThousandLocation(self.nation(), 'nation', self, ['province', 'district', 'hc', 'page'], '')]
    pcs = {
      'province':{
        'area'  : lambda _: self.province(),
        'miss'  :['district', 'hc'],
        'title' : 'Province',
        'trx'   : lambda x: first_cap(re.sub(u' PROVINCE', '', x).lower())
      },
      'district':{
        'area'  : lambda _: self.district(),
        'miss'  : ['hc'],
        'title' : 'District'
      },
      'hc':{
        'area'  : lambda _: self.hc(),
        'miss'  : [],
        'title' : 'Health Centre'
      }
    }
    # for pc in ['province', 'district', 'hc']:
    for pc in [(self.has_province(), 'province'),
               (self.has_district(), 'district'),
               (self.has_hc(), 'hc')]:
      # if self.kw.get(pc):
      if pc[0]:
        it  = pcs[pc[1]]
        dem.append(ThousandLocation(it['area'](None), pc[1], self, it['miss'], it['title'], it['trx'] if 'trx' in it else None))
    return dem

  @property
  def hierarchy(self):
    prv = self.has_province()
    dst = self.has_district()
    ans = []
    if self.has_district():
      return [{'province': self.province()}, {'district':self.district()}]
    if self.has_province():
      return [{'province': self.province()}]
    return []

  def nation(self):
    gat = orm.ORM.query('chws__nation', {'indexcol = 1':''})[0]
    return gat

  def __has_details(self, prv = None):
    return orm.ORM.query('ig_admins', {'address = %s': self.auth.username()})[0]

  def has_province(self, prv = None):
    num = prv or self.kw.get('province')
    if num:
      return int(num)
    return self.__has_details(prv)['province_pk']

  def province(self, prv = None):
    num = self.has_province(prv)
    gat = orm.ORM.query('chws__province', {'indexcol = %s': num})[0]
    return gat

  def has_district(self, prv = None):
    num = prv or self.kw.get('district')
    if num:
      return int(num)
    return self.__has_details(prv)['district_pk']

  def district(self, dst = None):
    num = self.has_district(dst)
    gat = orm.ORM.query('chws__district', {'indexcol = %s': num})[0]
    return gat

  def has_hc(self, prv = None):
    num = prv or self.kw.get('hc')
    if num:
      return int(num)
    return self.__has_details(prv)['health_center_pk']

  def hc(self, h = None):
    num = self.has_hc(h)
    gat = orm.ORM.query('chws__healthcentre', {'indexcol = %s': num})[0]
    return gat

  @property
  def child(self):
    if self.has_hc():       return ''
    if self.has_district(): return 'hc'
    if self.has_province(): return 'district'
    return 'province'

  @property
  def subarea(self):
    return ['province', 'district', 'hc'][len(self.hierarchy)]

  @property
  def childareas(self):
    if self.has_hc():
      return []
    if self.has_district():
      return self.areas('hc')
    if self.has_province():
      return self.areas('district')
    return self.areas('province')

  def areas(self, level = None):
    tbl, sel, etc = {
      'province'  : lambda _: ('chws__province', [self.province()] if self.has_province() else [], {}),
      'district'  : lambda _: ('chws__district', [self.district()] if self.has_district() else [], {'province = %s': self.province()['indexcol']}),
      'hc'        : lambda _: ('chws__healthcentre', [], {'province = %s':self.province()['indexcol'], 'district = %s':self.district()['indexcol']})
    }[level or self.subarea](None)
    prvq      = orm.ORM.query(tbl, etc,
      cols  = ['*'] + ['indexcol = %d AS selected' % (s['indexcol'], ) for s in sel],
      sort  = ('name', 'DESC')
    )
    return prvq.list()

  def conditions(self, tn, ini = None):
    ans = ini.conditions() if ini else {}
    if tn:
      ans.update({
        (tn + ' >= %s')  : self.start,
        (tn + ' <= %s')  : self.finish
      })
    if 'province' in self.kw:
      ans['province_pk = (SELECT old_pk FROM chws__province WHERE indexcol = %s LIMIT 1)']  = self.kw.get('province')
    if 'district' in self.kw:
      ans['district_pk = (SELECT old_pk FROM chws__district WHERE indexcol = %s LIMIT 1)']  = self.kw.get('district')
    if 'hc' in self.kw:
      ans['health_center_pk = (SELECT old_pk FROM chws__healthcentre WHERE indexcol = %s LIMIT 1)']  = self.kw.get('hc')
    return ans

  @property
  def start(self):
    gat = self.kw.get('start', '')
    if not gat:
      return self.fin - self.gap
    return self.make_time(gat)

  @property
  def finish_date(self):
    return self.text_date(self.finish)

  @property
  def start_date(self):
    return self.text_date(self.start)

  def text_date(self, dt):
    return dt.strftime('%d/%m/%Y')

  @property
  def finish(self):
    gat = self.kw.get('finish', '')
    if not gat:
      return self.fin
    return self.make_time(gat)

  def make_time(self, txt):
    '''dd/mm/yyyy'''
    pcs = [int(x) for x in re.split(r'\D', txt)]
    return datetime(year = pcs[2], month = pcs[1], day = pcs[0])

  def pre_link(self, url):
    pcs = urlparse.urlsplit(url)
    qrs = urlparse.parse_qs(pcs[3])
    qrs.update(self.kw)
    return (pcs, qrs)

  def link(self, url, **kw):
    if not self.kw and not kw:
      return url
    pcs, qrs  = self.pre_link(url)
    miss      = kw.pop('minus', [])
    qrs.update(kw)
    return urlparse.urlunsplit((pcs[0], pcs[1], pcs[2], '&'.join(['%s=%s' % (k, urllib2.quote(str(qrs[k]))) for k in qrs if qrs[k] and (not k in miss)]), pcs[4]))

class Application:
  def __init__(self, templates, statics, static_path, app_data, **kw):
    self.templates    = templates
    self.statics      = statics
    self.static_path  = static_path
    self.kw           = kw
    self.app_data     = app_data
    self.jinja        = Environment(loader = FileSystemLoader(templates))
    self.jinja.filters.update({
      'neat_numbers'  : neat_numbers,
      'get_display'  : get_display
    })
    self.__set_locations()

  def village(self, pk):
    try:
     num = int(pk) if pk else 'IS NULL'
     gat = orm.ORM.query('chws__village', {'indexcol = %s': num})[0]
     return gat
    except: return None

  def cell(self, pk):
    try:
     num = int(pk) if pk else 'IS NULL'
     gat = orm.ORM.query('chws__cell', {'indexcol = %s': num})[0]
     return gat
    except: return None

  def sector(self, pk):
    try:
     num = int(pk) if pk else 'IS NULL'
     gat = orm.ORM.query('chws__sector', {'indexcol = %s': num})[0]
     return gat
    except: return None

  def __set_locations(self):
    self.provinces  = {}
    self.districts  = {}
    self.hcs        = {}
    for prv in orm.ORM.query('chws__province', {}).list():
      self.provinces[str(prv['indexcol'])]  = prv['name']
    for dst in orm.ORM.query('chws__district', {}).list():
      self.districts[str(dst['indexcol'])]  = dst['name']
    for hc in orm.ORM.query('chws__healthcentre', {}).list():
      self.hcs[str(hc['indexcol'])]  = hc['name']

  def match(self, url):
    got = url[1:].replace('/', '_') or 'index'
    sys.stderr.write('%40s:\t%s\n' % (url, got))
    return url[1:].replace('/', '_') or 'index'

  def dynamised(self, chart, mapping = {}, *args, **kw):
    info  = {}
    info.update({
      'ref'           : re.sub(r'_table$', '', chart),
      'locations'     : ['TODO'],
      'args'          : kw,
      'nav'           : mapping.get('navb', None),
      'static_path'   : self.static_path
    })
    info.update(self.app_data)
    info.update(kw)
    mapping.pop('self', None)
    info.update({'display': mapping})
    return self.jinja.get_template('%s.html' % (chart, )).render(*args, **info)

  @cherrypy.expose
  def index(self, *args, **kw):
    flash = cherrypy.session.pop('flash', '')
    user  = cherrypy.session.get('user', '')
    return self.dynamised('index', mapping = locals(), *args, **kw)

##### START OF ALL LOCATIONS FILTERING

  @cherrypy.expose
  def locs(self):
    import json
    my_locs = []
    data = orm.ORM.query('chws__healthcentre', {} ).list()
    for d in data:
       #print d['name'], d['district'], d['province']
       dst = orm.ORM.query('chws__district', {'indexcol = %s' : d['district']})[0]
       prv = orm.ORM.query('chws__province', {'indexcol = %s' : d['province']})[0]
       if prv and dst:	my_locs.append( 
			{
				'id': d['indexcol'], 'name': d['name'], 'code': d['code'],
			 	'district_name': dst['name'], 'district_id': dst['indexcol'], 'district_code': dst['code'],
			 	'province_name': prv['name'], 'province_id': prv['indexcol'], 'province_code': prv['code']
			}
		      )
    return json.dumps(my_locs)

##### END OF ALL LOCATIONS FILTERING

  @cherrypy.expose
  def charts(self, *args, **kw):
    return ':-\\'

  @cherrypy.expose
  def dashboards_failures(self, *args, **kw):
    auth  = ThousandAuth(cherrypy.session.get('email'))
    navb  = ThousandNavigation(auth, *args, **kw)
    cnds  = navb.conditions(None, auth)
    cnds.update({'NOT success':''})
    nat = orm.ORM.query('treated_messages', cnds, cols = ['oldid'], migrations = migrations.TREATED)
    cpg, (sttit, endit), pgs = navb.pages(nat)
    msgs  = []
    for tm in nat[sttit:endit]:
      msq = orm.ORM.query('failed_transfers', {'oldid = %s': tm['oldid']}, cols = ['failcode'], sort = ('failpos', True), migrations = migrations.FAILED)
      msg = orm.ORM.query('messagelog_message', {'id = %s': tm['oldid']}, cols = ['text', 'contact_id', 'id'])
      msgs.append({'failures':msq, 'message':msg[0]})
    return self.dynamised('failures', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_messages(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions(None, auth)
    msgs    = orm.ORM.query('treated_messages', cnds,
      cols      = ['COUNT(*) AS total'],
      extended  = {
        'failed':     ('COUNT(*)', 'NOT success'),
        'succeeded':  ('COUNT(*)', 'success')
      },
      migrations = migrations.TREATED
    )
    nat       = msgs[0]
    total     = nat['total']
    succeeded = nat['succeeded']
    failed    = nat['failed']
    succpc    = 0.0
    failpc    = 0.0
    if total:
      succpc  = '%.2f' % ((float(succeeded) / float(total)) * 100.0, )
      failpc  = '%.2f' % ((float(failed) / float(total)) * 100.0, )
    return self.dynamised('messages', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_newborn(self, *args, **kw):
    return self.dynamised('newborn', *args, **kw)

  @cherrypy.expose
  def dashboards_death(self, *args, **kw):
    return self.dynamised('death', *args, **kw)

  NUT_DESCR = [
      # ('weight', 'Weight'),
      # ('height', 'Height'),
      # ('muac', 'MUAC'),
      ('stunting', 'Stunting'),
      ('underweight', 'Underweight'),
      ('wasting', 'Wasting'),
      ('exc_breast', 'Exclusive Breastfeeding'),
      ('comp_breast', 'Complimentary Breastfeeding'),
      ('no_breast', 'Not Breastfeeding')
    ]
  @cherrypy.expose
  def dashboards_nut(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('birth_date', auth)
    attrs   = self.NUT_DESCR
    nat     = self.civilised_fetch('ig_babies_adata', cnds, attrs)
    total   = nat[0]['total']
    adata   = []
    return self.dynamised('nut', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_nutr(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      ('lmp',            'Date Of Birth'),
      
    ] , *args, **kw)
    DESCRI = []
    INDICS = []
    cnds.update({queries.CBN_DATA['query_str']: ''})
    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     kw.update({'compare': ' IS NOT'})
     kw.update({'value': ' NULL'})
    else:
     INDICS = queries.CBN_DATA['attrs']
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []

     wcl.append({'field_name': '(%s)' % queries.CBN_DATA['query_str'], 'compare': '', 'value': '', 'extra': True})
     
     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = 'cbn_view', MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						start =  navb.start,
						end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/childgrowth?pid=%s">%s</a>' % (x, x),
      'wt_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    attrs = []
    
    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query('cbn_view', cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp) AS dob', 'Date Of Birth'),
 
					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Nutrition %s' % (' (%s)' % (self.find_descr(DESCRI + queries.CBN_DATA['attrs'], 
						sc ) or 'ALL', 
					) )
    return self.dynamised('cbn_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def old_tables_nutr(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = queries.PATIENT_DETAILS , *args, **kw)
    attrs = []
    nat   = orm.ORM.query('cbn_table', cnds,
      cols  = [x[0] for x in (cols + queries.CBN_DATA['cols']) if x[0][0] != '_'],
      sort  = ('report_date', False),
    )
    patient = nat[0]  
    return self.dynamised('cbn_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_nutr(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    nut = orm.ORM.query('cbn_view', cnds,
      cols      = ['COUNT(*) AS allnuts'],
      extended  = {
        'nb_bool':('COUNT(*)', 'nb_bool IS NOT NULL'),
        'ebf_bool':('COUNT(*)', 'ebf_bool IS NOT NULL'),
        'cbf_bool':('COUNT(*)', 'cbf_bool IS NOT NULL'),
        # 'unknown':('COUNT(*)', 'cbf_bool IS NULL AND ebf_bool IS NULL AND nb_bool IS NULL'),
        'stunting_bool':('COUNT(*)', 'stunting_bool'),
        'underweight_bool':('COUNT(*)', 'underweight_bool'),
        'wasting_bool':('COUNT(*)', 'wasting_bool')
      }
    )
    # raise Exception, nut.query
    total   = nut[0]['allnuts']
    return self.dynamised('nutr', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_redalert(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    attrs   = self.PREGNANCIES_DESCR
    # nat     = self.civilised_fetch('red_table', cnds, attrs)
    nat     = orm.ORM.query('red_table', cnds)
    # raise Exception, str(nat.query)
    # total   = nat[0]['total']
    fields  = queries.RED_ALERT_FIELDS
    return self.dynamised('redalert', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_pnc(self, *args, **kw):
    return self.dynamised('pnc', *args, **kw)

  @cherrypy.expose
  def dashboards_anc(self, *args, **kw):
    return self.dynamised('anc', *args, **kw)

  @cherrypy.expose
  def dashboards_ccm(self, *args, **kw):
    return self.dynamised('ccm', *args, **kw)

  def locals_for_births(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    pcnds   = copy.copy(cnds)
    pcnds[("lmp + ('%d DAYS' :: INTERVAL)" % (settings.GESTATION, )) + ' <= %s']  = navb.finish
    delivs  = orm.ORM.query('bir_table', cnds,
      extended  = {
        'home'      : ('COUNT(*)', 'ho_bool IS NOT NULL'),
        'clinic'    : ('COUNT(*)', 'cl_bool IS NOT NULL'),
        'hospital'  : ('COUNT(*)', 'hp_bool IS NOT NULL'),
        'allbirs'   : ('COUNT(*)', 'TRUE'),
        'enroute'   : ('COUNT(*)', 'or_bool IS NOT NULL'),
        'boys'      : ('COUNT(*)', 'bo_bool IS NOT NULL AND gi_bool IS NULL'),
        'girls'     : ('COUNT(*)', 'gi_bool IS NOT NULL AND bo_bool IS NULL'),
        'prema'     : ('COUNT(*)', 'pm_bool IS NOT NULL'),
        'bfeed'     : ('COUNT(*)', 'bf1_bool IS NOT NULL'),
        'nbfeed'    : ('COUNT(*)', 'nb_bool IS NOT NULL')
      },
      cols  = ['patient_id']  # , 'COUNT(*) AS allbirs']
    )
    congs     = []
    for mum in delivs.list():
      congs.append(mum['patient_id'])
    exped   = orm.ORM.query('pre_table', pcnds,
      extended  = {
        # 'alldelivs' : 'COUNT(*)',
        'untracked' : (
          'COUNT(*)', 
            'RANDOM() <= 0.5'
            # 'delivered'
            #'patient_id NOT IN %s'
          )
      },
      cols  = ['COUNT(*) AS alldelivs']
    )
    ttl       = orm.ORM.query('anc_table', cnds,
      cols      = ['COUNT(*) AS allancs'],
      extended  = {
        'anc1'    : ('COUNT(*)', 'anc_bool IS NOT NULL'),
        'anc2'    : ('COUNT(*)', 'anc2_bool IS NOT NULL'),
        'anc3'    : ('COUNT(*)', 'anc3_bool IS NOT NULL'),
        'anc4'    : ('COUNT(*)', 'anc4_bool IS NOT NULL')
      }
    )[0]
    ancs      = range(4)
    tous      = ttl['allancs']
    tousf     = float(tous)
    dmax      = float(max([ttl['anc1'], ttl['anc2'], ttl['anc3'], ttl['anc4']]))
    for a in ancs:
      cpt     = ttl['anc%d' % (a + 1, )]
      rpc     = 0.0
      pc      = 0.0
      if tous > 0:
        pc  = 100.0 * (float(cpt) / tous)
      if dmax > 0:
        rpc = 100.0 * (float(cpt) / float(dmax))
      ancs[a] = {'total':cpt, 'pc':pc, 'rpc':rpc}
    expected  = exped[0]['alldelivs']
    births    = delivs[0]['allbirs']
    unknowns  = exped[0]['untracked']
    boys      = delivs[0]['boys']
    girls     = delivs[0]['girls']
    boyspc    = 0.0
    girlspc   = 0.0
    if births > 0:
      boyspc  = (float(boys) / float(births)) * 100.0
      girlspc = (float(girls) / float(births)) * 100.0
    locations = delivs[0]
    plain     = orm.ORM.query('pre_table', pcnds,
      cols  = ['COUNT(*) AS allpregs']
    )
    thinq     = plain.specialise({'mother_weight_float < %s': settings.MIN_WEIGHT})
    fatq      = plain.specialise({'mother_weight_float > %s': settings.MAX_WEIGHT})
    fats      = fatq[0]['allpregs']
    thins     = thinq[0]['allpregs']
    fatpc     = 0.0
    thinpc    = 0.0
    midweight = expected - (fats + thins)
    midpc     = 0.0
    expf      = float(max([midweight, fats, thins]))
    if expf > 0:
      fatpc   = (float(fats) / expf) * 100.0
      thinpc  = (float(thins)  / expf) * 100.0
      midpc   = (float(midweight)  / expf) * 100.0
    return locals()

  @cherrypy.expose
  def dashboards_birthreport(self, *args, **kw):
    return self.dynamised('birthreport', mapping = self.locals_for_births(*args, **kw), *args, **kw)

  @cherrypy.expose
  def dashboards_childhealth(self, *args, **kw):
    return self.dynamised('childhealth', mapping = self.locals_for_births(*args, **kw), *args, **kw)

  @cherrypy.expose
  def dashboards_nbc(self, *args, **kw):
    return self.dynamised('nbc', mapping = self.locals_for_births(*args, **kw), *args, **kw)

  @cherrypy.expose
  def dashboards_delivery(self, *args, **kw):
    return self.dynamised('delivery', mapping = self.locals_for_births(*args, **kw), *args, **kw)

  @cherrypy.expose
  def dashboards_vaccination(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    vacced  = orm.ORM.query('chi_table', cnds,
      cols  = ['COUNT(*) AS allkids'],
      extended  = {
        'v1'      : ('COUNT(*)', 'v1_bool IS NOT NULL'),
        'v2'      : ('COUNT(*)', 'v2_bool IS NOT NULL'),
        'v3'      : ('COUNT(*)', 'v3_bool IS NOT NULL'),
        'v4'      : ('COUNT(*)', 'v4_bool IS NOT NULL'),
        'v5'      : ('COUNT(*)', 'v5_bool IS NOT NULL'),
        'v6'      : ('COUNT(*)', 'v6_bool IS NOT NULL'),
        'fully'   : ('COUNT(*)', 'vc_bool IS NOT NULL'),
        'partly'  : ('COUNT(*)', 'vi_bool IS NOT NULL'),
        'never'   : ('COUNT(*)', 'nv_bool IS NOT NULL')
      }
    )
    fully     = vacced[0]['fully']
    never     = vacced[0]['never']
    partly    = vacced[0]['partly']
    totvacc   = fully + partly
    allkids   = vacced[0]['allkids']
    vaccs     = []
    fullypc   = 0.0
    partlypc  = 0.0
    if totvacc > 0:
      fullypc   = 100.0 * (float(fully) / float(totvacc))
      partlypc  = 100.0 * (float(partly) / float(totvacc))
    if allkids > 0:
      vs    = [vacced[0]['v%d' % (vc + 1)] for vc in range(6)]
      kmax  = max(vs)
      pos   = 0
      prv   = 0
      for it in vs:
        pos       = pos + 1
        fit       = float(it)
        dat       = {'value': it, 'rpc': 100.0 * (float(fit) / float(kmax)), 'pc': 100.0 * (float(fit) / float(allkids))}
        if pos > 1:
          gap         = prv - it
          dat['diff'] = gap
          pc          = 0.0
          if prv > 0:
            pc  = 100.0 * (float(gap) / float(prv))
          dat['dpc']  = pc
        prv = it
        vaccs.append(dat)
    return self.dynamised('vaccination', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_nutrition(self, *args, **kw):
    nut = orm.ORM.query('cbn_table',
      cols      = ['COUNT(*) AS allnuts'],
      extended  = {
        'notbreast':('COUNT(*)', 'nb_bool IS NOT NULL'),
        'breast':('COUNT(*)', 'ebf_bool IS NOT NULL OR cbf_bool IS NOT NULL'),
        'unknown':('COUNT(*)', 'cbf_bool IS NULL AND ebf_bool IS NULL AND nb_bool IS NULL')
      }
    )
    weighed = orm.ORM.query('pre_table', {
      'mother_height_float > 100.0 AND mother_weight_float > 15.0':''
      },
      cols      = ['COUNT(*) AS mums'],
      extended  = {
        'short':('COUNT(*)', 'mother_height_float < 150.0'),
      }
    )
    thins   = weighed.specialise({'(mother_weight_float / ((mother_height_float * mother_height_float) / 10000.0)) < %s': settings.BMI_MIN})
    fats    = weighed.specialise({'(mother_weight_float / ((mother_height_float * mother_height_float) / 10000.0)) > %s': settings.BMI_MAX})
    bir = orm.ORM.query('bir_table',
      cols      = ['COUNT(*) AS allbirs'],
      extended  = {
        'hour1':('COUNT(*)', 'bf1_bool IS NOT NULL')
      }
    )
    return self.dynamised('nutrition', mapping = locals(), *args, **kw)

  def tables_preg_extras(self, dest, *args, **kw):
    navb, cnds, cols    = self.tables_in_general(*args, **kw)
    upds  = {'pregcough':'coughing', 'pregdiarrhea':'diarrhoea', 'pregfever':'fever', 'pregmalaria':'malaria', 'pregvomit':'vomiting', 'pregstill':'stillb', 'pregedema':'oedema', 'pregjaundice':'jaun', 'pregpneumonia':'pneumo', 'pregdisability':'disab', 'preganemia':'anaemia', 'pregcord':'cordi', 'pregneck':'necks', 'preghypothemia':'hypoth'}
    exts  = {queries.PREGNANCY_MATCHES[upds[dest]][1]:''}
    cnds.update(exts)
    nat     = orm.ORM.query('pre_table', cnds,
      cols  = [x[0] for x in cols if x[0][0] != '_'],
    )
    desc    = kw.pop('desc', '')
    return self.dynamised('pregnancy_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_risks(self, *args, **kw):
    navb, cnds, cols    = self.tables_in_general(*args, **kw)
    cnds.update(queries.RISK_MOD)
    nat     = orm.ORM.query('pre_table', cnds,
      cols  = [x[0] for x in cols if x[0][0] != '_'],
    )
    desc = 'High-Risk Mothers'
    return self.dynamised('pregnancy_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_pregcough(self, *args, **kw):
    return self.tables_preg_extras('pregcough', desc = 'Mothers With Cough', *args, **kw)

  @cherrypy.expose
  def tables_pregdiarrhea(self, *args, **kw):
    return self.tables_preg_extras('pregdiarrhea', desc = 'Mothers With Diarrhœa', *args, **kw)

  @cherrypy.expose
  def tables_pregfever(self, *args, **kw):
    return self.tables_preg_extras('pregfever', desc = 'Mothers With a Fever', *args, **kw)

  @cherrypy.expose
  def tables_pregmalaria(self, *args, **kw):
    return self.tables_preg_extras('pregmalaria', desc = 'Mothers With Malaria', *args, **kw)


  @cherrypy.expose
  def tables_pregvomit(self, *args, **kw):
    return self.tables_preg_extras('pregvomit', desc = 'Vomiting Mothers', *args, **kw)

  @cherrypy.expose
  def tables_pregstill(self, *args, **kw):
    return self.tables_preg_extras('pregstill', desc = 'Mothers With Still Births', *args, **kw)

  @cherrypy.expose
  def tables_pregedema(self, *args, **kw):
    return self.tables_preg_extras('pregedema', desc = u'Mothers With Œdema', *args, **kw)

  @cherrypy.expose
  def tables_pregjaundice(self, *args, **kw):
    return self.tables_preg_extras('pregjaundice', desc = 'Mothes With Jaundice', *args, **kw)

  @cherrypy.expose
  def tables_pregpneumonia(self, *args, **kw):
    return self.tables_preg_extras('pregpneumonia', desc = 'Mothers With Pneumonia', *args, **kw)

  @cherrypy.expose
  def tables_preganemia(self, *args, **kw):
    return self.tables_preg_extras('preganemia', desc = u'Mothers With Anæmia', *args, **kw)

  @cherrypy.expose
  def tables_pregdisability(self, *args, **kw):
    return self.tables_preg_extras('pregdisability', desc = 'Mothers With Disabled Children', *args, **kw)

  @cherrypy.expose
  def tables_preghypothemia(self, *args, **kw):
    return self.tables_preg_extras('preghypothemia', desc = 'Cool Mothers', *args, **kw)

  @cherrypy.expose
  def tables_pregcord(self, *args, **kw):
    return self.tables_preg_extras('pregcord', desc = 'Mothers Whose Babies Have Infected Cords', *args, **kw)

  @cherrypy.expose
  def tables_pregneck(self, *args, **kw):
    return self.tables_preg_extras('pregneck', desc = 'Mothers With Neck-Stiffness', *args, **kw)

  @cherrypy.expose
  def tables_delivery(self, *args, **kw):
    navb, cnds, cols    = self.tables_in_general(*args, **kw)
    nat     = orm.ORM.query('bir_table', cnds,
      cols  = [x[0] for x in cols if x[0][0] != '_'],
    )
    desc  = 'Delivery Reports'
    return self.dynamised('delivery_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_pregnancy(self, *args, **kw):
    navb, cnds, cols    = self.tables_in_general(*args, **kw)
    nat     = orm.ORM.query('pre_table', cnds,
      cols  = [x[0] for x in cols if x[0][0] != '_'],
    )
    desc  = 'Pregnancy Reports'
    return self.dynamised('pregnancy_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_pregnancies(self, *args, **kw):
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 'compare': '', 'value': ''}] if kw.get('subcat') else []
     locateds = summarize_by_location(primary_table = 'ig_pregnancies', where_clause = wcl, 
						province = province,
						district = district,
						location = location 
											
						);

    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('report_date',       'Date'),
      ('mother',            'Mother ID'),
    ], *args, **kw)
    sc      = kw.get('subcat')
    markup  = {
      'reporter': lambda x, _, __: '<a href="/tables/reporters?id=%s">%s</a>' % (x, x),
      'patient_id': lambda x, _, __: '<a href="/tables/mothers?pid=%s">%s</a>' % (x, x),
      'mother': lambda x, _, __: '<a href="/tables/mothers?id=%s">%s</a>' % (x, x),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), )
    }
    if sc:
      cnds[sc]  = ''
    attrs = self.PREGNANCIES_DESCR
    nat     = orm.ORM.query('ig_pregnancies', cnds,
      cols  = [x[0] for x in (cols + attrs) if x[0][0] != '_'],
    )
    desc  = 'Pregnancies%s' % (' (%s)' % (self.find_descr(self.PREGNANCIES_DESCR, sc), ) if sc else '', )
    return self.dynamised('pregnancies_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_nut(self, *args, **kw):
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
    navb, auth, cnds, cols    = self.neater_tables(sorter = 'birth_date', basics = [
      ('indexcol',          'Entry ID'),
      ('birth_date',        'Birth Date'),
      ('height',            'Height'),
      ('weight',            'Weight'),
      ('baby',              'Baby ID'),
      ('muac',              'MUAC')
    ], *args, **kw)
    sc      = kw.get('subcat')
    markup  = {
      'reporter': lambda x, _, __: '<a href="/tables/reporters?id=%s">%s</a>' % (x, x),
      'baby': lambda x, _, __: '<a href="/tables/child?id=%s">%s</a>' % (x, x),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), )
    }
    if sc:
      cnds[sc]  = ''
    attrs   = self.NUT_DESCR
    nat     = orm.ORM.query('ig_babies_adata', cnds,
      cols  = [x[0] for x in (cols + attrs) if x[0][0] != '_'],
    )
    desc  = 'Nutrition%s' % (' (%s)' % (self.find_descr(self.NUT_DESCR, sc), ) if sc else '', )
    return self.dynamised('babies_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_babies(self, *args, **kw):
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 'compare': '', 'value': ''}] if kw.get('subcat') else []
     locateds = summarize_by_location(primary_table = 'ig_babies', where_clause = wcl, 
						province = province,
						district = district,
						location = location 
											
						);
    navb, auth, cnds, cols    = self.neater_tables(sorter = 'birth_date', basics = [
      ('indexcol',          'Entry ID'),
      ('birth_date',        'Birth Date'),
      ('height',            'Height'),
      ('weight',            'Weight'),
      ('cnumber',           'Child Number'),
      ('pregnancy',         'Pregnancy ID')
    ], *args, **kw)
    sc      = kw.get('subcat')
    markup  = {
      'reporter': lambda x, _, __: '<a href="/tables/reporters?id=%s">%s</a>' % (x, x),
      'patient_id': lambda x, _, __: '<a href="/tables/mothers?pid=%s">%s</a>' % (x, x),
      'pregnancy': lambda x, _, __: '<a href="/tables/pregnancies?id=%s">%s</a>' % (x, x),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), )
    }
    if sc:
      cnds[sc]  = ''
    attrs   = self.BABIES_DESCR
    nat     = orm.ORM.query('ig_babies', cnds,
      cols  = [x[0] for x in (cols + attrs) if x[0][0] != '_'],
    )
    desc  = 'Babies%s' % (' (%s)' % (self.find_descr(self.BABIES_DESCR, sc), ) if sc else '', )
    return self.dynamised('babies_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_mothers(self, *args, **kw):
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 'compare': '', 'value': ''}] if kw.get('subcat') else []
     locateds = summarize_by_location(primary_table = 'ig_mothers', where_clause = wcl, 
						province = province,
						district = district,
						location = location 
											
						);

    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('report_date',       'Date'),
      ('patient_id',        'Patient ID'),
      ('reporter',          'Reporter ID'),
      ('height',            'Height'),
      ('weight',            'Weight'),
      # ('reporter',          'Reporter ID'),
      ('pregnancies',       'Pregnancies')
    ], *args, **kw)
    sc      = kw.get('subcat')
    markup  = {
      'reporter': lambda x, _, __: '<a href="/tables/reporters?id=%s">%s</a>' % (x, x),
      'patient_id': lambda x, _, __: '<a href="/tables/mothers?pid=%s">%s</a>' % (x, x),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), )
    }
    if sc:
      cnds[{'withprev':'pregnancies > 1'}.get(sc, sc)]  = ''
    attrs   = self.MOTHERS_DESCR
    nat     = orm.ORM.query('ig_mothers', cnds,
      cols  = [x[0] for x in (cols + attrs) if x[0][0] != '_'],
    )
    #raise Exception, nat.query
    desc  = 'Mothers%s' % (' (%s)' % (self.find_descr(self.MOTHERS_DESCR, sc), ) if sc else '', )
    return self.dynamised('mothers_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_reports(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('report_date',       'Date'),
      ('reporter_pk',       'Reporter ID'),
      ('reporter_phone',    'Reporter Phone'),
      ('report_type',       'Report Type')
    ], *args, **kw)
    desc    = 'Reports'
    sc      = kw.get('subcat')
    markup  = {}
    if sc:
      cnds.update({'report_type = %s': sc})
      desc  = '%s (%s Reports)' % (desc, sc)
    nat     = orm.ORM.query('thousanddays_reports', cnds,
      cols  = [x[0] for x in cols if x[0][0] != '_'],
      sort  = ('report_date', False)
    )
    return self.dynamised('reports_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_reporters(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(
      sorter  = None,
      basics  = [
        ('indexcol',          'Entry ID'),
        ('phone_number',      'Phone Number'),
        ('province_pk',       'Date'),
        ('district_pk',       'District')
        # ('health_center_pk',  'Health Centre')
      ], *args, **kw)
    markup  = {
      'indexcol': lambda x, _, __: '<a href="/tables/reporters?id=%s">%s</a>' % (x, x),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), )
    }
    nat     = orm.ORM.query('ig_reporters', cnds,
      cols  = [x[0] for x in cols if x[0][0] != '_'],
      sort  = ('created_at', False)
    )
    desc  = 'Reports'
    return self.dynamised('reporter_table', mapping = locals(), *args, **kw)

  def find_descr(self, desc, key):
    for k, d in desc:
      if k == key: return d
    return None

  def neater_tables(self, sorter = 'report_date', basics = [], extras = [], *args, **kw):
    return self.tables_in_general(sorter, basics, extras, *args, **kw)

  def tables_in_general(self, sorter = 'report_date', basics = [
      ('indexcol',          'Report ID'),
      ('report_date',       'Date'),
      ('reporter_phone',    'Reporter'),
      ('reporter_pk',       'Reporter ID')
    ], extras = [
      ('patient_id',        'Mother ID'),
      ('lmp',               'LMP')
    ], *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = {}
    pid     = kw.get('pid')
    tid     = kw.get( 'id')
    if pid:
      cnds  = {'patient_id = %s': pid}
    elif tid:
      cnds  = {'indexcol  = %s':  tid}
    else:
      cnds  = navb.conditions(sorter, auth)
    cols  = (basics + (([] if 'province' in kw else [('province_pk',       'Province')]) +
     ([] if 'district' in kw else [('district_pk',       'District')]) +
     ([] if 'hc' in kw else [('health_center_pk',  'Health Centre')])) + extras)
    return (navb, auth, cnds, cols)

  @cherrypy.expose
  def dashboards_home(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    return self.dynamised('home', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def authentication(self, *args, **kw):
    eml                       = kw.get('addr')
    pwd                       = kw.get('pwd')
    auth                      = ThousandAuth(eml)
    cherrypy.session['user']  = eml
    if kw.get('logout'):
      cherrypy.session.pop('email', '')
      raise cherrypy.HTTPRedirect('/')
    if auth.check(pwd):
      cherrypy.session['email'] = eml
    else:
      cherrypy.session['flash'] = 'Access Denied'
      raise cherrypy.HTTPRedirect('/')
    if kw.get('next'):
      raise cherrypy.HTTPRedirect(kw.get('next'))
    raise cherrypy.HTTPRedirect(settings.AUTH_HOME)

  EXPORT_MIGS = [
    ('total', 0),
    ('sofar', 0)
  ]
  # TODO:
  # 1.  Data type specification
  # 2.  DB-validated tracking of current position
  @cherrypy.expose
  def exports_general(self, *args, **kw):
    auth      = ThousandAuth(cherrypy.session.get('email'))
    navb      = ThousandNavigation(auth, *args, **kw)
    tbl, srt  = settings.EXPORT_KEYS.get(kw.get('key', '_'))
    cnds  = navb.conditions(srt or 'report_date', auth)
    btc   = 5000
    pos   = int(kw.get('pos', '0'))
    eid   = kw.get('eid')
    tot   = 0
    beg   = False
    if not eid:
      toq = orm.ORM.query(tbl, cnds, cols = ['COUNT(*) AS total'])
      tot = toq[0]['total']
      eid = orm.ORM.store('exports_table', {'total': tot, 'sofar': 0})
      beg = True
    else:
      eid = int(eid)
      toq = orm.ORM.query('exports_table', {'indexcol = %s': eid})
      tot = toq[0]['total']
    pgs, rmd  = divmod(tot, btc)
    pgs       = pgs + (1 if rmd else rmd)
    dst       = 'frontend/static/downloads/%d.xls' % (eid, )
    stt       = pos * btc
    if pos > pgs:
      with open(dst, 'a') as fch:
        fch.write('E\n')
      # cherrypy.response.headers['Content-Type']         = 'application/vnd.ms-excel; charset=UTF-8'
      # cherrypy.response.headers['Content-Disposition']  = 'attachment; filename=download-%d.xls' % (eid, )
      raise cherrypy.HTTPRedirect(dst)
    with open(dst, 'a') as fch:
      nat = orm.ORM.query(tbl, cnds, sort = ('indexcol', True))
      nat[0]
      if beg:
        fch.write('ID;P\n')
        stt = stt + 1
        xps = 0
        for hd in nat.cursor.description:
          xps = xps + 1
          fch.write('C;Y%d;X%d;K%s\n' % (stt, xps, json.dumps(hd.name)))
        pass
      rng = pos * btc
      for row in nat[rng : rng + btc]:
        stt = stt + 1
        xps = 0
        for hd in nat.cursor.description:
          xps = xps + 1
          fch.write('C;Y%d;X%d;K%s\n' % (stt, xps, json.dumps(str(row[hd.name]))))
    # raise cherrypy.HTTPRedirect('/exports/general?pos=%d&eid=%d' % (pos + 1, eid))
    cherrypy.response.headers['Content-Type'] = 'application/json'
    cherrypy.response.headers['Location']     = '/exports/general?lmt=%d&pos=%d&eid=%d' % (pgs, pos + 1, eid)
    cherrypy.response.status                  = 303
    return json.dumps({'total': tot, 'id': eid, 'pos': pos + 1, 'limit': pgs})

  @cherrypy.expose
  def exports_delivery(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    nat     = orm.ORM.query('bir_table', cnds)
    nat[0]
    raise Exception, str(nat.cursor.description)
    raise Exception, str(nat.cols)
    raise Exception, str(nat.query)

  @cherrypy.expose
  def dashboards_reporting(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions(None, auth)
    nat     = orm.ORM.query('ig_reporters', cnds, cols = ['COUNT(*) AS total'])
    total   = nat[0]['total']
    rps     = orm.ORM.query('thousanddays_reports', cnds, cols = ['COUNT(*) AS total'])
    reptot  = rps[0]['total']
    ncnds   = copy.copy(cnds)
    ncnds.update({'report_type IS NOT NULL':''})
    rpts    = orm.ORM.query('thousanddays_reports', ncnds, cols = ['DISTINCT report_type', "(report_type || ' Reports') AS nom"], sort = ('report_type', True)).list()
    return self.dynamised('reporting', mapping = locals(), *args, **kw)

  PREGNANCIES_DESCR = [
      # ('soon', 'Clinic'),
      # ('at_clinic', 'Confirmed at Clinic'),
      # ('at_home', 'Confirmed at Home'),
      # ('at_hospital', 'Confirmed at Hospital'),
      # ('en_route', 'Confirmed en route'),
      ('no_problem', 'Pregnancy Without Risk'),
      ('no_prev_risks', 'No Previous Risks'),
      ('rapid_breathing', 'Rapid Breathing'),
      ('multiples', 'Multiples'),
      ('young_mother', 'Young Mother'),
      ('asm_advice', 'ASM Advice Given'),
      ('malaria', 'With Malaria'),
      ('vomiting', 'Vomiting'),
      ('coughing', 'Coughing'),
      ('referred', 'Referred'),
      ('diarrhoea', u'With Diarrhœa'),
      ('oedema', u'With Œdema'),
      ('fever', 'With Fever'),
      ('stiff_neck', 'With Stiff Neck'),
      ('jaundice', 'With Jaundice'),
      ('pneumonia', 'With Pneumonia'),
      ('hypothermia', 'With Hypothermia'),
      ('previous_serious_case', 'With History of Serious Cases'),
      ('severe_anaemia', u'With Severe Anæmia'),
      ('previous_haemorrhage', u'With History of Hæmorrhage'),
      ('mother_sick', 'With Unspecifed Sickness'),
      ('previous_convulsion', 'With History of Convulsions'),
    ]
  @cherrypy.expose
  def dashboards_pregnancies(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    attrs   = self.PREGNANCIES_DESCR
    nat     = self.civilised_fetch('ig_pregnancies', cnds, attrs)
    total   = nat[0]['total']
    return self.dynamised('pregnancies', mapping = locals(), *args, **kw)

##### START OF NEW UZD #####
  #### START OF PREGNANCY ###
  @cherrypy.expose
  def dashboards_predash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT PREGNANCY, AND LET THE USER GO BACK AND FORTH
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) : ''})
    #cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.finish) : ''})

    exts = {}
    total = orm.ORM.query(  'pre_table', 
			  cnds,
                          cols = ['COUNT(*) AS total'],
			)[0]['total']
    if kw.get('group') == 'no_risk':
      title = 'No Risk'
      group = 'no_risk'
      cnds.update({queries.NO_RISK['query_str']: ''})
      nat = orm.ORM.query(  'pre_table', 
			  cnds,
                          cols = ['COUNT(*) AS total'],
			)
    elif kw.get('group') == 'at_risk':
      title = 'At Risk'
      group = 'at_risk'
      cnds.update({queries.RISK['query_str']: ''})
      attrs = [(x.split()[0], dict(queries.RISK['attrs'])[x]) for x in dict (queries.RISK['attrs'])]
      exts.update(dict([(x.split()[0], ('COUNT(*)',x)) for x in dict (queries.RISK['attrs'])]))
      nat = orm.ORM.query(  'pre_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = exts,
			)
    elif kw.get('group') == 'high_risk':
      title = 'High Risk'
      group = 'high_risk'
      cnds.update({queries.HIGH_RISK['query_str']: ''})
      attrs = [(x.split()[0], dict(queries.HIGH_RISK['attrs'])[x]) for x in dict (queries.HIGH_RISK['attrs'])]
      exts.update(dict([(x.split()[0], ('COUNT(*)',x)) for x in dict (queries.HIGH_RISK['attrs'])]))
      nat = orm.ORM.query(  'pre_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = exts,
			)
    else:
      nat = orm.ORM.query(  'pre_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = {'no_risk': ('COUNT(*)', queries.NO_RISK['query_str']), 
					'at_risk': ('COUNT(*)', queries.RISK['query_str']),
					'high_risk': ('COUNT(*)', queries.HIGH_RISK['query_str']),
					}
			)
    return self.dynamised('predash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_predash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      
    ] + queries.PREGNANCY_DATA , *args, **kw)
    DESCRI = []
    INDICS = []

    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT PREGNANCY, AND LET THE USER GO BACK AND FORTH
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) : ''})
    #cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.finish) : ''})
    
    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     if kw.get('group'):
      if kw.get('group') == 'no_risk':
       cnds.update({'(%s)' % queries.NO_RISK['query_str']: ''})
      else:
       kw.update({'compare': ' IS NOT'})
       kw.update({'value': ' NULL'})
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []
     if kw.get('subcat') is None:
      if kw.get('group') == 'no_risk':
       wcl.append({'field_name': '(%s)' % queries.NO_RISK['query_str'], 'compare': '', 'value': '', 'extra': True})
       INDICS = []
      if kw.get('group') == 'at_risk':
       wcl.append({'field_name': '(%s)' % queries.RISK['query_str'], 'compare': '', 'value': '', 'extra': True})
       INDICS = queries.RISK['attrs']
      if kw.get('group') == 'high_risk':
       wcl.append({'field_name': '(%s)' % queries.HIGH_RISK['query_str'], 'compare': '', 'value': '', 'extra': True})
       INDICS = queries.HIGH_RISK['attrs']
      if kw.get('group') is None:
       INDICS = [('no_risk', 'No Risk', '(%s)' % queries.NO_RISK['query_str'] ), 
		('at_risk', 'At Risk', '(%s)' % queries.RISK['query_str']),
		 ('high_risk', 'High Risk', '(%s)' % queries.HIGH_RISK['query_str']),
		]#; print INDICS

     wcl.append({'field_name': '(%s)' % ("(report_date) <= '%s'" % ( navb.finish) ), 'compare': '', 'value': '', 'extra': True})
     wcl.append({'field_name': '(%s)' % ("(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) ), 'compare': '', 'value': '', 'extra': True})
     
     
     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      #print INDICS
      locateds = summarize_by_location(primary_table = 'pre_table', MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						#start =  navb.start,
						#end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/patient?pid=%s">%s</a>' % (x, x),
      'gravity_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'parity_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'edd': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    attrs = []
    if kw.get('group') == 'no_risk':
     cnds.update({'(%s)' % queries.NO_RISK['query_str']: ''})
     DESCRI.append(('no_risk', 'No Risk'))
    if kw.get('group') == 'at_risk':
     cnds.update({'(%s)' % queries.RISK['query_str']: ''})
     DESCRI.append(('at_risk', 'At Risk'))
    if kw.get('group') == 'high_risk':
     cnds.update({'(%s)' % queries.HIGH_RISK['query_str']: ''})
     DESCRI.append(('high_risk', 'High Risk'))

    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query('pre_table', cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp + INTERVAL \'%d days\') AS edd' % settings.GESTATION, 'EDDate'),
					('(%s) AS at_risky' % queries.RISK['query_str'], 'AtRisky'), 
					('(%s) AS high_risky' % queries.HIGH_RISK['query_str'], 'HighRisky'),
 
					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Pregnancies%s' % (' (%s)' % (self.find_descr(DESCRI + queries.RISK['attrs'] + queries.HIGH_RISK['attrs'], sc or kw.get('group')), 
					) if sc or kw.get('group') else '', )
    return self.dynamised('predash_table', mapping = locals(), *args, **kw)

  ### END OF PREGNANCY ####

  ### START OF ANC ###

  @cherrypy.expose
  def dashboards_ancdash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)

    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT PREGNANCY, AND LET THE USER GO BACK AND FORTH
    pre_cnds    = navb.conditions(None, auth)
    pre_cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    pre_cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) : ''})

    exts = {}
    attrs = [(x.split()[0], dict(queries.ANC_DATA['attrs'])[x]) for x in dict (queries.ANC_DATA['attrs'])]

    pre = orm.ORM.query(  'pre_table', 
			  pre_cnds, 
			  cols = ['COUNT(*) AS total']
			)

    cnds    = navb.conditions(None, auth)
    cnds.update({queries.ANC_DATA['query_str']: ''})
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION - settings.ANC_GAP, navb.start) : ''})
    #print cnds
    exts.update(dict([(x[0].split()[0], ('COUNT(*)', x[0])) for x in queries.ANC_DATA['attrs'] ])) 
    nat = orm.ORM.query(  'anc_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = exts
			);print nat.query
    return self.dynamised('ancdash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_ancdash(self, *args, **kw):
    navb, auth, cnds, cols   = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      
    ] , *args, **kw)
    DESCRI = []
    INDICS = []

    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT PREGNANCY, AND LET THE USER GO BACK AND FORTH
    cnds    = navb.conditions(None, auth)
    cnds.update({queries.ANC_DATA['query_str']: ''})
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION - settings.ANC_GAP, navb.start) : ''})
    primary_table = 'anc_table'

    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     kw.update({'compare': ' IS NOT'})
     kw.update({'value': ' NULL'})
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []
     
     if kw.get('subcat') is None: INDICS = queries.ANC_DATA['attrs']

     if kw.get('group') == 'anc1':
      primary_table = 'pre_table'
      wcl.append({'field_name': '(%s)' % ("(report_date) <= '%s'" % ( navb.finish) ), 'compare': '', 'value': '', 'extra': True})
      wcl.append({'field_name': '(%s)' % ("(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) ), 'compare': '', 'value': '', 'extra': True})
      INDICS = [('no_risk', 'No Risk', '(%s)' % queries.NO_RISK['query_str'] ), 
		('at_risk', 'At Risk', '(%s)' % queries.RISK['query_str']),
		 ('high_risk', 'High Risk', '(%s)' % queries.HIGH_RISK['query_str']),
		]
     else: 
      wcl.append({'field_name': '(%s)' % ("(report_date) <= '%s'" % ( navb.finish) ), 'compare': '', 'value': '', 'extra': True})
      wcl.append({'field_name': '(%s)' % ("(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION - settings.ANC_GAP, navb.start) ), 'compare': '', 'value': '', 'extra': True})
      wcl.append({'field_name': '(%s)' % queries.ANC_DATA['query_str'], 'compare': '', 'value': '', 'extra': True})
      
     
     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      #print INDICS
      locateds = summarize_by_location(primary_table = primary_table, MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						#start =  navb.start,
						#end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/patient?pid=%s">%s</a>' % (x, x),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    # TODO: optimise
    attrs = queries.ANC_DATA['attrs']
    #print cnds
    cols    += queries.LOCATION_INFO
     
    if kw.get('group') == 'anc1':
     navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT PREGNANCY, AND LET THE USER GO BACK AND FORTH
     cnds    = navb.conditions(None, auth)
     cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
     cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) : ''})
     primary_table = 'pre_table'
     attrs = [('(%s) AS at_risky' % queries.RISK['query_str'], 'AtRisky'),]
     DESCRI.append(('anc1', 'Pregnancy'))   
    nat     = orm.ORM.query( primary_table , cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp + INTERVAL \'%d days\') AS edd' % settings.GESTATION, 'EDDate'),
					('(%s) AS high_risky' % queries.HIGH_RISK['query_str'], 'HighRisky'),
 
					] + attrs) if x[0][0] != '_'],
      
    )#;print nat.query
    desc  = 'ANC%s' % (' (%s)' % (self.find_descr(DESCRI + queries.ANC_DATA['attrs'], sc or kw.get('group')), 
					) if sc or kw.get('group') else '', )
    return self.dynamised('ancdash_table', mapping = locals(), *args, **kw)

  ### END OF ANC ###

  #### START OF RED ALERT ###
  @cherrypy.expose
  def dashboards_reddash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions('report_date', auth)
    exts = {}
    
    red_attrs = [(x[0].split()[0], x[1]) for x in queries.RED_DATA['attrs']]
    red_exts = exts
    red_cnds = cnds
    red_cnds.update({queries.RED_DATA['query_str']: ''})
    red_exts.update(dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.RED_DATA['attrs']]))
    red = orm.ORM.query(  'red_table', 
			  red_cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = red_exts,
			)

    rar_attrs = [(x[0].split()[0], x[1]) for x in queries.RAR_DATA['attrs']]
    rar_cnds = navb.conditions('report_date')
    rar_cnds.update({queries.RAR_DATA['query_str']: ''})
    rar_exts = dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.RAR_DATA['attrs']])
    rar = orm.ORM.query(  'rar_table', 
			  rar_cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = rar_exts,
			)

    return self.dynamised('reddash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_reddash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      
    ] , *args, **kw)
    DESCRI = []
    INDICS = []
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) >= '%s'" % (navb.start) : ''})
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    primary_table = 'red_table'
    if kw.get('subcat') and kw.get('subcat') in [x[0].split()[0] for x in queries.RAR_DATA['attrs']]:
     primary_table = 'rar_table'
     cnds.update({queries.RAR_DATA['query_str']: ''})
    else: cnds.update({queries.RED_DATA['query_str']: ''}) 
    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     kw.update({'compare': ' IS NOT'})
     kw.update({'value': ' NULL'})
    else:
     INDICS = queries.RED_DATA['attrs']
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []

     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = primary_table, MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						start =  navb.start,
						end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/patient?pid=%s">%s</a>' % (x, x),
      'wt_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    # TODO: optimise
    attrs = []
    
    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query(primary_table, cnds,
      cols  = [x[0] for x in (cols + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Red Alerts %s' % (' (%s)' % (self.find_descr(DESCRI + queries.RED_DATA['attrs'] + queries.RAR_DATA['attrs'], 
						sc) or 'ALL', 
					) )
    return self.dynamised('reddash_table', mapping = locals(), *args, **kw)


  #### END OF RED ALERT ###

  #### START OF DELIVERY ###

  @cherrypy.expose
  def dashboards_deliverynotdash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    exts = {}
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    pre_cnds    = navb.conditions(None, auth)
    pre_cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    pre_cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) : ''})
    pre = orm.ORM.query(  'pre_table', 
			  pre_cnds, 
			  cols = ['COUNT(*) AS total']
			)
    
    today = datetime.today().date()
    next_monday = today + timedelta(days=-today.weekday(), weeks=1)
    next_sunday = next_monday + timedelta(days = 6)
    next_two_monday = today + timedelta(days=-today.weekday(), weeks=2)
    next_two_sunday = next_two_monday + timedelta(days = 6)

    attrs = [
	('next_week', 'Deliveries in Next Week', "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_monday, next_sunday)),
	('next_two_week', 'Deliveries in Next two Weeks', "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_two_monday, next_two_sunday)),
	]
    exts.update(dict([(x[0], ('COUNT(*)',x[2])) for x in attrs]))
    nat = orm.ORM.query(  'pre_table', 
    			  cnds, 
    			  cols = ['COUNT(*) AS total'],
                          extended = exts, 
    			)#; print nat.query

    details = {}
    for attr in attrs:
     attr_cnds = navb.conditions(None, auth)
     attr_cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
     attr_cnds.update({attr[2]: ''})
     #print attr_cnds
     details.update({ 
			attr[0] :
			orm.ORM.query(  'pre_table', 
			  attr_cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = {'no_risk': ('COUNT(*)', queries.NO_RISK['query_str']), 
					'at_risk': ('COUNT(*)', queries.RISK['query_str']),
					'high_risk': ('COUNT(*)', queries.HIGH_RISK['query_str']),
					}
			) 
		   })
    

    return self.dynamised('deliverynotdash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_deliverynotdash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      ('lmp',            'LMP'),
      
    ] , *args, **kw)

    today = datetime.today().date()
    next_monday = today + timedelta(days=-today.weekday(), weeks=1)
    next_sunday = next_monday + timedelta(days = 6)
    next_two_monday = today + timedelta(days=-today.weekday(), weeks=2)
    next_two_sunday = next_two_monday + timedelta(days = 6)

    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT PREGNANCY, AND LET THE USER GO BACK AND FORTH
    pre_cnds    = navb.conditions(None, auth)
    pre_cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    pre_cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) : ''})

    DESCRI = [('next_week', 'Deliveries in Next Week'), ('next_two_week', 'Deliveries in Next two Weeks')]
    INDICS = [
	('pre', 'Pregnancies', "(report_date <= '%s') AND (lmp + INTERVAL '%s days') >= '%s'" % ( navb.finish, settings.GESTATION , navb.start)),
	('next_week', 'Deliveries in Next Week', "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_monday, next_sunday)),
	('next_two_week', 'Deliveries in Next two Weeks', "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_two_monday, next_two_sunday)),
	
	]

    SUB_INDICS = { 'no_risk': '(%s)' % queries.NO_RISK['query_str'] , 
		   'at_risk': '(%s)' % queries.RISK['query_str'],
		   'high_risk': '(%s)' % queries.HIGH_RISK['query_str'],
		 }
    if kw.get('subgroup'): cnds.update({SUB_INDICS[kw.get('subgroup')]: ''})
    if kw.get('group') == 'next_week':
     INDICS = [
	('next_week', 'Deliveries in Next Week', "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_monday, next_sunday))
	]
     start = next_monday; end = next_sunday
     cnds.update({"(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , start, end): ''})
    elif kw.get('group') == 'next_two_week':
     INDICS = [
	('next_two_week', 'Deliveries in Next two Weeks', "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_two_monday, next_two_sunday)),
	]
     start = next_two_monday; end = next_two_sunday
     cnds.update({"(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , start, end): ''})
    elif kw.get('group') == 'pre':
     INDICS = [
	('pre', 'Pregnancies', "(report_date <= '%s') AND (lmp + INTERVAL '%s days') >= '%s'" % ( navb.finish, settings.GESTATION , navb.start)),
	]
     cnds.update({"(report_date <= '%s') AND (lmp + INTERVAL '%s days') >= '%s'" % ( navb.finish, settings.GESTATION , navb.start): ''})
    else:
     cnds.update({  "%s OR %s" % ( 
			"(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_monday, next_sunday),
			"(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_two_monday, next_two_sunday) 			
			) : ''})

    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []

     if kw.get('group') == 'next_week':
      start = next_monday; end = next_sunday
      wcl.append({'field_name': '(%s)' % "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , start, end),
                  'compare': '', 'value': '', 'extra': True})

     if kw.get('group') == 'next_two_week':
      start = next_two_monday; end = next_two_sunday
      wcl.append({'field_name': '(%s)' % "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , start, end),
                  'compare': '', 'value': '', 'extra': True})

     if kw.get('group') == 'pre':
      wcl.append({'field_name': '(%s)' % ("(report_date) <= '%s'" % ( navb.finish) ), 'compare': '', 'value': '', 'extra': True})
      wcl.append({'field_name': '(%s)' % ("(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.GESTATION, navb.start) ), 'compare': '', 'value': '', 'extra': True})

     if kw.get('subgroup'):	wcl.append({'field_name': '(%s)' % SUB_INDICS[kw.get('subgroup')], 'compare': '', 'value': '', 'extra': True}) 
    
     
     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = 'pre_table', MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						#start =  navb.start,
						#end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/patient?pid=%s">%s</a>' % (x, x),
      'wt_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    # TODO: optimise
    attrs = []
    
    cols    += queries.LOCATION_INFO
    if kw.get('group') == 'pre':
     DESCRI.append(('pre', 'Pregnancies'))
     cnds = pre_cnds   
    nat     = orm.ORM.query('pre_table', cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp + INTERVAL \'%d days\') AS edd' % settings.GESTATION, 'EDDate'),
					('(%s) AS at_risky' % queries.RISK['query_str'], 'AtRisky'), 
					('(%s) AS high_risky' % queries.HIGH_RISK['query_str'], 'HighRisky'),

					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Deliveries Notifications %s' % (' (%s)' % (self.find_descr(DESCRI , 
						sc or kw.get('group') ) or 'ALL', 
					) )
    return self.dynamised('deliverynotdash_table', mapping = locals(), *args, **kw)


  @cherrypy.expose
  def dashboards_deliverydash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions('report_date', auth)
    exts = {}
    
    attrs = [(x[0].split()[0], x[1]) for x in queries.DELIVERY_DATA['attrs']]
    cnds.update({queries.DELIVERY_DATA['query_str']: ''})
    exts.update(dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.DELIVERY_DATA['attrs']]))
    nat = orm.ORM.query(  'bir_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = exts,
			)
    
    today = datetime.today().date()
    next_monday = today + timedelta(days=-today.weekday(), weeks=1)
    next_sunday = next_monday + timedelta(days = 6)
    next_week_cnds = navb.conditions('report_date')
    next_week_cnds.update({"(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_monday, next_sunday): ''})
    next_week = orm.ORM.query(  'pre_table', 
    			  next_week_cnds, 
    			  cols = ['COUNT(*) AS total']
    			)

    next_two_monday = today + timedelta(days=-today.weekday(), weeks=2)
    next_two_sunday = next_two_monday + timedelta(days = 6)
    next_two_week_cnds = navb.conditions('report_date')
    next_two_week_cnds.update({"(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , next_two_monday, next_two_sunday): ''})
    next_two_week = orm.ORM.query(  'pre_table', 
    			  next_two_week_cnds, 
    			  cols = ['COUNT(*) AS total'],
    			)

    return self.dynamised('deliverydash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_deliverydash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      ('lmp',            'Date Of Birth'),
      
    ] , *args, **kw)
    DESCRI = []
    INDICS = []
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) >= '%s'" % (navb.start) : ''})
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    primary_table = 'bir_table'

    if kw.get('group'):
     primary_table = 'pre_table'
     today = datetime.today().date()
     if kw.get('group') == 'next_week': weeks = 1
     if kw.get('group') == 'next_two_week': weeks = 2
     start = today + timedelta(days=-today.weekday(), weeks=weeks)
     end = start + timedelta(days = 6)
     cnds.update({"(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , start, end): ''})
    else:
     cnds.update({queries.DELIVERY_DATA['query_str']: ''})
    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     kw.update({'compare': ' IS NOT'})
     kw.update({'value': ' NULL'})
    else:
     if kw.get('group'): DESCRI = [('next_week', 'Deliveries in Next Week'), ('next_two_week', 'Deliveries in Next two Weeks')]
     else: INDICS = queries.DELIVERY_DATA['attrs']
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []

     if kw.get('group'):
      wcl.append({'field_name': '(%s)' % "(lmp + INTERVAL '%s days') BETWEEN '%s' AND '%s'" % (settings.GESTATION , start, end),
                  'compare': '', 'value': '', 'extra': True})
     else: wcl.append({'field_name': '(%s)' % queries.DELIVERY_DATA['query_str'], 'compare': '', 'value': '', 'extra': True})
     
     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = primary_table, MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						start =  navb.start,
						end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/child?pid=%s">%s</a>' % (x, x),
      'wt_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    # TODO: optimise
    attrs = []
    
    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query(primary_table, cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp) AS dob', 'Date Of Birth'),
 
					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Deliveries %s' % (' (%s)' % (self.find_descr(DESCRI + queries.DELIVERY_DATA['attrs'], 
						sc or kw.get('group') ) or 'ALL', 
					) )
    return self.dynamised('deliverydash_table', mapping = locals(), *args, **kw)


  #### END OF DELIVERY ###


  #### START OF NEWBORN ###
  @cherrypy.expose
  def dashboards_nbcdash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)

    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.NBC_GESTATION, navb.start) : ''})
    exts = {}
    total = orm.ORM.query(  'nbc_table', 
			  cnds,
                          cols = ['COUNT(*) AS total'],
			)[0]['total']
    if kw.get('group') == 'no_risk':
      title = 'No Risk'
      group = 'no_risk'
      cnds.update({queries.NBC_DATA['NO_RISK']['query_str']: ''})
      nat = orm.ORM.query(  'nbc_table', 
			  cnds,
                          cols = ['COUNT(*) AS total'],
			)
    elif kw.get('group') == 'at_risk':
      title = 'At Risk'
      group = 'at_risk'
      cnds.update({queries.NBC_DATA['RISK']['query_str']: ''})
      attrs = [(x.split()[0], dict(queries.NBC_DATA['RISK']['attrs'])[x]) for x in dict (queries.NBC_DATA['RISK']['attrs'])]
      exts.update(dict([(x.split()[0], ('COUNT(*)',x)) for x in dict (queries.NBC_DATA['RISK']['attrs'])]))
      nat = orm.ORM.query(  'nbc_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = exts,
			)
    elif kw.get('group') == 'high_risk':
      title = 'High Risk'
      group = 'high_risk'
      cnds.update({queries.NBC_DATA['HIGH_RISK']['query_str']: ''})
      attrs = [(x.split()[0], dict(queries.NBC_DATA['HIGH_RISK']['attrs'])[x]) for x in dict (queries.NBC_DATA['HIGH_RISK']['attrs'])]
      exts.update(dict([(x.split()[0], ('COUNT(*)',x)) for x in dict (queries.NBC_DATA['HIGH_RISK']['attrs'])]))
      nat = orm.ORM.query(  'nbc_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = exts,
			)
    else:
      nat = orm.ORM.query(  'nbc_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = {'no_risk': ('COUNT(*)', queries.NBC_DATA['NO_RISK']['query_str']), 
					'at_risk': ('COUNT(*)', queries.NBC_DATA['RISK']['query_str']),
					'high_risk': ('COUNT(*)', queries.NBC_DATA['HIGH_RISK']['query_str']),
					}
			)
    return self.dynamised('nbcdash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_nbcdash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      ('lmp',            'Date Of Birth'),
      
    ] , *args, **kw)
    auth    = ThousandAuth(cherrypy.session.get('email'))
    DESCRI = []
    INDICS = []

    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.NBC_GESTATION, navb.start) : ''})

    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     if kw.get('group'):
      if kw.get('group') == 'no_risk':
       cnds.update({'(%s)' % queries.NBC_DATA['NO_RISK']['query_str']: ''})
      else:
       kw.update({'compare': ' IS NOT'})
       kw.update({'value': ' NULL'})
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []
     if kw.get('subcat') is None:
      if kw.get('group') == 'no_risk':
       wcl.append({'field_name': '(%s)' % queries.NBC_DATA['NO_RISK']['query_str'], 'compare': '', 'value': '', 'extra': True})
       INDICS = []
      if kw.get('group') == 'at_risk':
       wcl.append({'field_name': '(%s)' % queries.NBC_DATA['RISK']['query_str'], 'compare': '', 'value': '', 'extra': True})
       INDICS = queries.NBC_DATA['RISK']['attrs']
      if kw.get('group') == 'high_risk':
       wcl.append({'field_name': '(%s)' % queries.NBC_DATA['HIGH_RISK']['query_str'], 'compare': '', 'value': '', 'extra': True})
       INDICS = queries.NBC_DATA['HIGH_RISK']['attrs']
      if kw.get('group') is None:
       INDICS = [('no_risk', 'No Risk', '(%s)' % queries.NBC_DATA['NO_RISK']['query_str'] ), 
		('at_risk', 'At Risk', '(%s)' % queries.NBC_DATA['RISK']['query_str']),
		 ('high_risk', 'High Risk', '(%s)' % queries.NBC_DATA['HIGH_RISK']['query_str']),
		]#; print INDICS

     wcl.append({'field_name': '(%s)' % ("(report_date) <= '%s'" % ( navb.finish) ), 'compare': '', 'value': '', 'extra': True})
     wcl.append({'field_name': '(%s)' % ("(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.NBC_GESTATION, navb.start) ), 'compare': '', 'value': '', 'extra': True})
     
     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = 'nbc_table', MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						#start =  navb.start,
						#end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/nbcchild?pid=%s">%s</a>' % (x, x),
      'wt_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    attrs = []
    if kw.get('group') == 'no_risk':
     cnds.update({'(%s)' % queries.NBC_DATA['NO_RISK']['query_str']: ''})
     DESCRI.append(('no_risk', 'No Risk'))
    if kw.get('group') == 'at_risk':
     cnds.update({'(%s)' % queries.NBC_DATA['RISK']['query_str']: ''})
     DESCRI.append(('at_risk', 'At Risk'))
    if kw.get('group') == 'high_risk':
     cnds.update({'(%s)' % queries.NBC_DATA['HIGH_RISK']['query_str']: ''})
     DESCRI.append(('high_risk', 'High Risk'))

    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query('nbc_table', cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp) AS dob', 'Date Of Birth'),
					('(%s) AS at_risky' % queries.NBC_DATA['RISK']['query_str'], 'AtRisky'), 
					('(%s) AS high_risky' % queries.NBC_DATA['HIGH_RISK']['query_str'], 'HighRisky'),
 
					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Newborn Visits%s' % (' (%s)' % (self.find_descr(DESCRI + queries.NBC_DATA['RISK']['attrs'] + queries.NBC_DATA['HIGH_RISK']['attrs'], 
						sc or kw.get('group')), 
					) if sc or kw.get('group') else '', )
    return self.dynamised('nbcdash_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_nbcchild(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = queries.PATIENT_DETAILS , *args, **kw)
    attrs = [ (' %s AS %s' % (x[0], x[0].split()[0]), x[1]) for x in queries.NBC_DATA['RISK']['attrs'] + queries.NBC_DATA['HIGH_RISK']['attrs'] ]
    indexed_attrs = [ ('%s' % get_indexed_value('name', x[2], x[1], x[0], x[3]), x[3]) for x in queries.INDEXED_VALS['location']]
    nat     = orm.ORM.query('nbc_table', cnds,
      				cols  = [x[0] for x in (cols + indexed_attrs + queries.NBC_DATA['cols'] + attrs) if x[0][0] != '_'],
				sort = ('report_date', False),
    			)
    patient = nat[0]  
    reminders = []
    nbc_reports = [ x for x in nat.list() ]#; print attrs
    cbn_reports =   orm.ORM.query('cbn_table', cnds)
    return self.dynamised('newborn_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def __tables_child(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = queries.PATIENT_DETAILS , *args, **kw)
    attrs = [ (' %s AS %s' % (x[0], x[0].split()[0]), x[1]) for x in queries.NBC_DATA['RISK']['attrs'] + queries.NBC_DATA['HIGH_RISK']['attrs'] ]
    indexed_attrs = [ ('%s' % get_indexed_value('name', x[2], x[1], x[0], x[3]), x[3]) for x in queries.INDEXED_VALS['location']]
    nat     = orm.ORM.query('nbc_table', cnds,
      				cols  = [x[0] for x in (cols + indexed_attrs + queries.NBC_DATA['cols'] + attrs) if x[0][0] != '_'],
				sort = ('report_date', False),
    			)
    patient = nat[0]  
    reminders = []
    nbc_reports = [ x for x in nat.list() ]#; print attrs
    cbn_reports =   orm.ORM.query('cbn_table', cnds)
    return self.dynamised('child_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_childgrowth(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = queries.PATIENT_DETAILS , *args, **kw)
    attrs = [ (' %s AS %s' % (x[0], x[0].split()[0]), x[1]) for x in queries.NBC_DATA['RISK']['attrs'] + queries.NBC_DATA['HIGH_RISK']['attrs'] ]
    indexed_attrs = [ ('%s' % get_indexed_value('name', x[2], x[1], x[0], x[3]), x[3]) for x in queries.INDEXED_VALS['location']]
    nat     = orm.ORM.query('nbc_table', cnds,
      				cols  = [x[0] for x in (cols + indexed_attrs + queries.NBC_DATA['cols'] + attrs) if x[0][0] != '_'],
				sort = ('report_date', False),
    			)
    patient = nat[0]  
    reminders = []
    nbc_reports = [ x for x in nat.list() ]#; print attrs
    cbn_reports =   orm.ORM.query('cbn_table', cnds, cols = [
							"patient_id", 
							"child_number_float",
							"lmp", 
							"report_date",
							"child_weight_float AS weight",  
							"child_height_float AS height",
							],
						 )
    chartData = json.dumps([ {'weight': cbn['weight'] , 'height': cbn['height'], 'age': (cbn['report_date'] - cbn['lmp']).days / 30.4374 } for cbn in cbn_reports.list()])
    print chartData
    
    return self.dynamised('growthchart', mapping = locals(), *args, **kw)

  ### END OF NEWBORN ####

  #### START OF POSTNATAL ###
  @cherrypy.expose
  def dashboards_pncdash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.PNC_GESTATION, navb.start) : ''})
    exts = {}
    total = orm.ORM.query(  'pnc_table', 
			  cnds,
                          cols = ['COUNT(*) AS total'],
			)[0]['total']
    if kw.get('group') == 'no_risk':
      title = 'No Risk'
      group = 'no_risk'
      cnds.update({queries.PNC_DATA['NO_RISK']['query_str']: ''})
      nat = orm.ORM.query(  'pnc_table', 
			  cnds,
                          cols = ['COUNT(*) AS total'],
			)
    elif kw.get('group') == 'at_risk':
      title = 'At Risk'
      group = 'at_risk'
      cnds.update({queries.PNC_DATA['RISK']['query_str']: ''})
      attrs = [(x.split()[0], dict(queries.PNC_DATA['RISK']['attrs'])[x]) for x in dict (queries.PNC_DATA['RISK']['attrs'])]
      exts.update(dict([(x.split()[0], ('COUNT(*)',x)) for x in dict (queries.PNC_DATA['RISK']['attrs'])]))
      nat = orm.ORM.query(  'pnc_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = exts,
			)
    else:
      nat = orm.ORM.query(  'pnc_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = {'no_risk': ('COUNT(*)', queries.PNC_DATA['NO_RISK']['query_str']), 
					'at_risk': ('COUNT(*)', queries.PNC_DATA['RISK']['query_str']),
					}
			)
    return self.dynamised('pncdash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_pncdash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      ('lmp',            'Date Of Birth'),
      
    ] , *args, **kw)
    DESCRI = []
    INDICS = []
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({"(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.PNC_GESTATION, navb.start) : ''})

    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     if kw.get('group'):
      if kw.get('group') == 'no_risk':
       cnds.update({'(%s)' % queries.PNC_DATA['NO_RISK']['query_str']: ''})
      else:
       kw.update({'compare': ' IS NOT'})
       kw.update({'value': ' NULL'})
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []
     if kw.get('subcat') is None:
      if kw.get('group') == 'no_risk':
       wcl.append({'field_name': '(%s)' % queries.PNC_DATA['NO_RISK']['query_str'], 'compare': '', 'value': '', 'extra': True})
       INDICS = []
      if kw.get('group') == 'at_risk':
       wcl.append({'field_name': '(%s)' % queries.PNC_DATA['RISK']['query_str'], 'compare': '', 'value': '', 'extra': True})
       INDICS = queries.PNC_DATA['RISK']['attrs']
      if kw.get('group') is None:
       INDICS = [('no_risk', 'No Risk', '(%s)' % queries.PNC_DATA['NO_RISK']['query_str'] ), 
		('at_risk', 'At Risk', '(%s)' % queries.PNC_DATA['RISK']['query_str']),
		]#; print INDICS
     
     wcl.append({'field_name': '(%s)' % ("(report_date) <= '%s'" % ( navb.finish) ), 'compare': '', 'value': '', 'extra': True})
     wcl.append({'field_name': '(%s)' % ("(lmp + INTERVAL \'%d days\') >= '%s'" % (settings.PNC_GESTATION, navb.start) ), 'compare': '', 'value': '', 'extra': True})

     
     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = 'pnc_table', MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						#start =  navb.start,
						#end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/patient?pid=%s">%s</a>' % (x, x),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    attrs = []
    if kw.get('group') == 'no_risk':
     cnds.update({'(%s)' % queries.PNC_DATA['NO_RISK']['query_str']: ''})
     DESCRI.append(('no_risk', 'No Risk'))
    if kw.get('group') == 'at_risk':
     cnds.update({'(%s)' % queries.PNC_DATA['RISK']['query_str']: ''})
     DESCRI.append(('at_risk', 'At Risk'))

    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query('pnc_table', cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp) AS dob', 'Date Of Birth'),
 
					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Postnatal Visits%s' % (' (%s)' % (self.find_descr(DESCRI + queries.PNC_DATA['RISK']['attrs'], 
						sc or kw.get('group')), 
					) if sc or kw.get('group') else '', )
    return self.dynamised('pncdash_table', mapping = locals(), *args, **kw)


  @cherrypy.expose
  def tables_child(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = queries.PATIENT_DETAILS , *args, **kw)
    attrs = [ (' %s AS %s' % (x[0], x[0].split()[0]), x[1]) for x in queries.NBC_DATA['RISK']['attrs'] + queries.NBC_DATA['HIGH_RISK']['attrs'] ]
    indexed_attrs = [ ('%s' % get_indexed_value('name', x[2], x[1], x[0], x[3]), x[3]) for x in queries.INDEXED_VALS['location']]
    nat     = orm.ORM.query('nbc_table', cnds,
      				cols  = [x[0] for x in (cols + indexed_attrs + queries.NBC_DATA['cols'] + attrs) if x[0][0] != '_'],
				sort = ('report_date', False),
    			)
    patient = nat[0]  
    reminders = []
    nbc_reports = [ x for x in nat.list() ]#; print attrs
    cbn_reports = orm.ORM.query('cbn_table', cnds)
    return self.dynamised('child_table', mapping = locals(), *args, **kw)

  ### END OF POSTNATAL ####

  #### START OF VACCINATION ###
  @cherrypy.expose
  def dashboards_vaccindash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions('report_date', auth)
    exts = {}
    
    vac_comps_attrs = [(x[0].split()[0], x[1]) for x in queries.VAC_DATA['VAC_COMPLETION']['attrs']]
    vac_comps_exts = exts
    vac_comps_exts.update(dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.VAC_DATA['VAC_COMPLETION']['attrs']]))
    vac_comps = orm.ORM.query(  'chi_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = vac_comps_exts,
			)

    vac_series_attrs = [(x[0].split()[0], x[1]) for x in queries.VAC_DATA['VAC_SERIES']['attrs']]
    vac_series_exts = exts
    vac_series_exts.update(dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.VAC_DATA['VAC_SERIES']['attrs']]))
    vac_series = orm.ORM.query(  'chi_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = vac_series_exts,
			)



    return self.dynamised('vaccindash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_vaccindash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      ('lmp',            'Date Of Birth'),
      
    ] , *args, **kw)
    DESCRI = []
    INDICS = []
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) >= '%s'" % (navb.start) : ''})
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})

    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     kw.update({'compare': ' IS NOT'})
     kw.update({'value': ' NULL'})
    else:
     INDICS = queries.VAC_DATA['VAC_COMPLETION']['attrs'] + queries.VAC_DATA['VAC_SERIES']['attrs']
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []

     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = 'chi_table', MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						start =  navb.start,
						end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/child?pid=%s">%s</a>' % (x, x),
      'wt_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    attrs = []
    
    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query('chi_table', cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp) AS dob', 'Date Of Birth'),
 
					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Vaccination %s' % (' (%s)' % (self.find_descr(DESCRI + queries.VAC_DATA['VAC_COMPLETION']['attrs'] + queries.VAC_DATA['VAC_SERIES']['attrs'], 
						sc) or 'ALL', 
					) )
    return self.dynamised('vaccindash_table', mapping = locals(), *args, **kw)


  #### END OF VACCINATION ###

  #### START OF CCM ###
  @cherrypy.expose
  def dashboards_ccmdash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions('report_date')
    exts = {}
    
    ccm_attrs = [(x[0].split()[0], x[1]) for x in queries.CCM_DATA['attrs']]
    ccm_exts = exts
    ccm_cnds = cnds
    ccm_cnds.update({queries.CCM_DATA['query_str']: ''})
    ccm_exts.update(dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.CCM_DATA['attrs']]))
    ccm = orm.ORM.query(  'ccm_table', 
			  ccm_cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = ccm_exts,
			)

    cmr_attrs = [(x[0].split()[0], x[1]) for x in queries.CMR_DATA['attrs']]
    cmr_cnds = navb.conditions('report_date')
    cmr_cnds.update({queries.CMR_DATA['query_str']: ''})
    cmr_exts = dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.CMR_DATA['attrs']])
    cmr = orm.ORM.query(  'cmr_table', 
			  cmr_cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = cmr_exts,
			)

    return self.dynamised('ccmdash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_ccmdash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      ('lmp',            'Date Of Birth'),
      
    ] , *args, **kw)
    DESCRI = []
    INDICS = []
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) >= '%s'" % (navb.start) : ''})
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    primary_table = 'ccm_table'
    if kw.get('subcat') and kw.get('subcat') in [x[0].split()[0] for x in queries.CMR_DATA['attrs']]:
     primary_table = 'cmr_table'
     cnds.update({queries.CMR_DATA['query_str']: ''})
    else: cnds.update({queries.CCM_DATA['query_str']: ''}) 
    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     kw.update({'compare': ' IS NOT'})
     kw.update({'value': ' NULL'})
    else:
     INDICS = queries.CCM_DATA['attrs']
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []

     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = primary_table, MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						start =  navb.start,
						end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/child?pid=%s">%s</a>' % (x, x),
      'wt_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    attrs = []
    
    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query(primary_table, cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp) AS dob', 'Date Of Birth'),
 
					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'CCM %s' % (' (%s)' % (self.find_descr(DESCRI + queries.CCM_DATA['attrs'] + queries.CMR_DATA['attrs'], 
						sc) or 'ALL', 
					) )
    return self.dynamised('ccmdash_table', mapping = locals(), *args, **kw)


  #### END OF CCM ###


  #### START OF DEATH ###

  @cherrypy.expose
  def dashboards_deathdash(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions('report_date', auth)
    exts = {}
    
    attrs = [(x[0].split()[0], x[1]) for x in queries.DEATH_DATA['attrs']]
    cnds.update({queries.DEATH_DATA['query_str']: ''})
    exts.update(dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.DEATH_DATA['attrs']]))
    nat = orm.ORM.query(  'dth_table', 
			  cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = exts,
			)

    bylocs_attrs = [(x[0].split()[0], x[1]) for x in queries.DEATH_DATA['bylocs']['attrs']]
    bylocs_cnds = navb.conditions('report_date')
    bylocs_cnds.update({queries.DEATH_DATA['bylocs']['query_str']: ''})
    bylocs_exts = dict([(x[0].split()[0], ('COUNT(*)',x[0])) for x in queries.DEATH_DATA['bylocs']['attrs']])
    bylocs = orm.ORM.query(  'dth_table', 
			  bylocs_cnds, 
			  cols = ['COUNT(*) AS total'], 
			  extended = bylocs_exts,
			)

    return self.dynamised('deathdash', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_deathdash(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = [
      ('indexcol',          'Entry ID'),
      ('patient_id',            'Mother ID'),
      ('reporter_phone',            'Reporter Phone'),
      ('lmp',            'Date Of Birth'),
      
    ] , *args, **kw)
    DESCRI = []
    INDICS = []
    navb.gap= timedelta(days = 0)## USE THIS GAP OF ZERO DAYS TO DEFAULT TO CURRENT SITUATION
    cnds    = navb.conditions(None, auth)
    cnds.update({"(report_date) >= '%s'" % (navb.start) : ''})
    cnds.update({"(report_date) <= '%s'" % (navb.finish) : ''})
    cnds.update({queries.DEATH_DATA['query_str']: ''})
    if kw.get('subcat') and kw.get('subcat').__contains__('_bool'):
     kw.update({'compare': ' IS NOT'})
     kw.update({'value': ' NULL'})
    else:
     INDICS = queries.DEATH_DATA['attrs'] #+ settings.DEATH_DATA['bylocs']['attrs']
    if kw.get('summary'):
     province = kw.get('province') or auth.him()['province_pk']
     district = kw.get('district') or auth.him()['district_pk']
     location = kw.get('hc') or auth.him()['health_center_pk']
     wcl = [{'field_name': '%s' % kw.get('subcat'), 
		'compare': '%s' % kw.get('compare') if kw.get('compare') else '', 
		'value': '%s' % kw.get('value') if kw.get('value') else '' 
	   }] if kw.get('subcat') else []

     wcl.append({'field_name': '(%s)' % queries.DEATH_DATA['query_str'], 'compare': '', 'value': '', 'extra': True})
     
     if kw.get('view') == 'table' or kw.get('view') != 'log' :
      locateds = summarize_by_location(primary_table = 'dth_table', MANY_INDICS = INDICS, where_clause = wcl, 
						province = province,
						district = district,
						location = location,
						start =  navb.start,
						end = navb.finish,
											
						)
      tabular = give_me_table(locateds, MANY_INDICS = INDICS, LOCS = { 'nation': None, 'province': province, 'district': district, 'location': location } )
      INDICS_HEADERS = dict([ (x[0].split()[0], x[1]) for x in INDICS])

    sc      = kw.get('subcat')
    if kw.get('compare') and kw.get('value'): sc += kw.get('compare') + kw.get('value')
    markup  = {
      'patient_id': lambda x, _, __: '<a href="/tables/child?pid=%s">%s</a>' % (x, x),
      'wt_float': lambda x, _, __: '%s' % (int(x) if x else ''),
      'lmp': lambda x, _, __: '%s' % (datetime.date(x) if x else ''),
      'province_pk': lambda x, _, __: '%s' % (self.provinces.get(str(x)), ),
      'district_pk': lambda x, _, __: '%s' % (self.districts.get(str(x)), ),
      'health_center_pk': lambda x, _, __: '%s' % (self.hcs.get(str(x)), ),
      'sector_pk': lambda x, _, __: '%s' % (self.sector(str(x))['name'] if self.sector(str(x)) else '', ),
      'cell_pk': lambda x, _, __: '%s' % (self.cell(str(x))['name'] if self.cell(str(x)) else '', ),
      'village_pk': lambda x, _, __: '%s' % (self.village(str(x))['name'] if self.village(str(x)) else '', ),
    }
    if sc:
      cnds[sc]  = ''
    attrs = []
    
    cols    += queries.LOCATION_INFO   
    nat     = orm.ORM.query('dth_table', cnds,
      cols  = [x[0] for x in (cols + [
					('(lmp) AS dob', 'Date Of Birth'),
 
					] + attrs) if x[0][0] != '_'],
      
    )
    desc  = 'Death %s' % (' (%s)' % (self.find_descr(DESCRI + queries.DEATH_DATA['attrs'] + queries.DEATH_DATA['bylocs']['attrs'], 
						sc ) or 'ALL', 
					) )
    return self.dynamised('deathdash_table', mapping = locals(), *args, **kw)


  #### END OF DEATH ###


  @cherrypy.expose
  def tables_patient(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = queries.PATIENT_DETAILS , *args, **kw)
    attrs = [ (' %s AS %s' % (x[0], x[0].split()[0]), x[1]) for x in queries.RISK['attrs'] + queries.HIGH_RISK['attrs'] ]
    indexed_attrs = [ ('%s' % get_indexed_value('name', x[2], x[1], x[0], x[3]), x[3]) for x in queries.INDEXED_VALS['location']]
    nat     = orm.ORM.query('pre_table', cnds,
      				cols  = [x[0] for x in (cols + indexed_attrs + queries.PREGNANCY_DATA + attrs) if x[0][0] != '_'],
				sort = ('report_date', False),
    			)
    patient = nat[0]  
    reminders = []
    pre_reports = [ x for x in nat.list() ]
    anc_reports = orm.ORM.query('anc_table', cnds)
    pnc_reports = orm.ORM.query('pnc_table', cnds)
    return self.dynamised('patient_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_patienthistory(self, *args, **kw):
    navb, auth, cnds, cols    = self.neater_tables(basics = queries.PATIENT_DETAILS , *args, **kw)
    data = []
    for key in REPORTS.keys():
     data.append(  [ REPORTS.get(key), FIELDS.get(key), orm.ORM.query('%s_table' % key.lower(),
										 cnds, 
						cols = ['(%s IS NOT NULL) AS %s ' % (x[0], x[0]) if x[0].__contains__('bool') else x[0] for x in FIELDS.get(key) ],
						sort = ('report_date', False), 
								) 
			] 
		)
    #print data
    return self.dynamised('patienthistory', mapping = locals(), *args, **kw)

##### END OF NEW UZD #######

  BABIES_DESCR  = [
    ('boy', 'Male'),
    ('girl', 'Female'),
    ('abnormal_fontanelle', 'Abnormal Fontanelle'),
    ('cord_infection', 'With Cord Infection'),
    ('congenital_malformation', 'With Congenital Malformation'),
    # ('ibirari', 'Bafite Ibibari'),
    ('disabled', 'With Disability'),
    ('stillborn', 'Stillborn'),
    ('no_problem', 'With No Problem')
  ]
  @cherrypy.expose
  def dashboards_babies(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('birth_date', auth)
    attrs   = self.BABIES_DESCR
    nat     = self.civilised_fetch('ig_babies', cnds, attrs)
    total   = nat[0]['total']
    return self.dynamised('babies', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_delivs(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('lmp', auth)
    cnds[("""(lmp + '%d DAYS')""" % (settings.GESTATION, )) + """ >= %s"""] = navb.finish
    attrs   = self.PREGNANCIES_DESCR
    nat     = self.civilised_fetch('ig_pregnancies', cnds, attrs)
    total   = nat[0]['total']
    return self.dynamised('pregnancies', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_admins(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    naddr   = kw.get('addr')
    dadmin  = kw.get('del')
    if dadmin:
      orm.ORM.delete('ig_admins', dadmin)
      raise cherrypy.HTTPRedirect(cherrypy.request.headers.get('Referer') or '/dashboards/admins')
    prv   = kw.get('province')
    dst   = kw.get('district')
    hc    = kw.get('hc')
    if naddr:
      npwd  = kw.get('pwd')
      salt  = str(random.random()).join([str(random.random()) for x in range(settings.SALT_STRENGTH)])
      rslt  = sha.sha('%s%s' % (salt, npwd))
      thing = {'salt': salt, 'address': naddr, 'sha1_pass': rslt.hexdigest(), 'district_pk': dst, 'province_pk': prv, 'health_center_pk': hc}
      orm.ORM.store('ig_admins', thing, migrations  = migrations.ADMIN_MIGRATIONS)
      raise cherrypy.HTTPRedirect(cherrypy.request.headers.get('Referer') or '/dashboards/admins')
    cnds    = navb.conditions(None, auth)
    if not prv:
      cnds['province_pk IS NULL'] = ''
    if not dst:
      cnds['district_pk IS NULL'] = ''
    if not hc:
      cnds['health_center_pk IS NULL'] = ''
    nat     = orm.ORM.query('ig_admins', cnds, sort = ('address', True), migrations = migrations.ADMIN_MIGRATIONS)
    return self.dynamised('admins', mapping = locals(), *args, **kw)

  def civilised_fetch(self, tbl, cnds, attrs):
    exts    = {}
    ncnds   = copy.copy(cnds)
    for ext in attrs:
      if len(ext) > 3:
        for cs in ext[3]:
	  print cs
          ncnds[cs[0]] = cs[1]
      else:
        exts[ext[0]] = ('COUNT(*)' if len(ext) < 3 else ext[2], ext[0])
    return orm.ORM.query(tbl, ncnds, cols = ['COUNT(*) AS total'], extended = exts)

  MOTHERS_DESCR = [
      ('young_mother', 'Under 18'),
      ('old', 'Over 35'),
      ('surgeries', 'With Previous Obstetric Surgery'),
      ('miscarries', 'With Previous Miscarriage'),
      ('prev_home_deliv', 'Previous Home Delivery'),
      ('chronic_disease', 'With Chronic Disease'),
      ('toilet', 'With Toilet'),
      ('no_toilet', 'No Toilet'),
      ('handwashing', 'With Water Tap'),
      ('no_handwashing', 'No Water Tap'),
    ]
  @cherrypy.expose
  def dashboards_mothers(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    pregs   = orm.ORM.query('ig_mothers', cnds, cols = ['(SUM(pregnancies) - COUNT(*)) AS total'])[0]['total']
    attrs   = self.MOTHERS_DESCR
    nat     = self.civilised_fetch('ig_mothers', cnds, attrs)
    total   = nat[0]['total']
    return self.dynamised('mothers', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def dashboards_pregnancy(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    nat     = orm.ORM.query('pre_table', cnds,
      cols      = ['COUNT(*) AS allpregs'],
      extended  = queries.PREGNANCY_MATCHES,
      migrations  = migrations.PREGNANCY_MIGRATIONS
    )
    toi     = nat.specialise({'to_bool IS NOT NULL':''})
    hnd     = nat.specialise({'hw_bool IS NOT NULL':''})
    weighed = nat.specialise({'mother_height_float > 100.0 AND mother_weight_float > 15.0':''})
    thinq   = weighed.specialise({'(mother_weight_float / ((mother_height_float * mother_height_float) / 10000.0)) < %s': settings.BMI_MIN})
    fatq    = weighed.specialise({'(mother_weight_float / ((mother_height_float * mother_height_float) / 10000.0)) > %s': settings.BMI_MAX})
    riskys  = nat.specialise(queries.RISK_MOD)
    info    = nat[0]
    rez     = orm.ORM.query('res_table',
      cnds,
      cols        = ['COUNT(*) AS allreps'],
    )
    recovs  = rez.specialise({'mw_bool IS NOT NULL':''})
    aarecov = recovs.specialise({'aa_bool IS NOT NULL':''})
    prrecov = recovs.specialise({'pr_bool IS NOT NULL':''})
    total   = nat[0]['allpregs']
    totalf  = float(total)
    toilets = toi[0]['allpregs']
    handw   = hnd[0]['allpregs']
    risks   = riskys[0]['allpregs']
    rezes   = rez[0]['allreps']
    thins   = thinq[0]['allpregs']
    fats    = fatq[0]['allpregs']
    rezf    = float(rezes)
    toilpc  = 0.0
    handpc  = 0.0
    riskpc  = 0.0
    rezpc   = 0.0
    aapc    = 0.0
    prpc    = 0.0
    try:
      toilpc  = (float(toilets) / totalf) * 100.0
      handpc  = (float(handw) / totalf) * 100.0
      riskpc  = (float(risks) / totalf) * 100.0
      rezpc   = (rezf / totalf) * 100.0
    except ZeroDivisionError, zde:
      pass
    aa      = aarecov[0]['allreps']
    pr      = prrecov[0]['allreps']
    if rezf > 0.0:
      aapc  = (float(aa) / rezf) * 100.0
      prpc  = (float(pr) / rezf) * 100.0
    qs    = range(12)
    tot   = 0
    dmax  = 0
    cits  = cnds.items()
    for mpos in qs:
      got = orm.ORM.query('pre_table', dict(cits + [('EXTRACT(MONTH FROM report_date) = %s', mpos + 1)]), cols = ['COUNT(*) AS allpregs'])[0]['allpregs']
      qs[mpos]  = got
      tot       = tot + got
      dmax      = max(dmax, got)
    monthavgs = [{'value' : x, 'pc' : (100.0 * (float(x) / tot)) if tot > 0 else 0, 'rpc': (100.0 * (float(x) / dmax)) if dmax > 0 else 0} for x in qs]
    monthavg  = float(tot) / 12.0
    ls    = range(9)
    tot   = 0
    dmax  = 0
    for mpos in ls:
      got       = orm.ORM.query('pre_table', dict(cits + [('EXTRACT(MONTH FROM lmp) = (EXTRACT(MONTH FROM NOW()) - %s)', len(ls) - (mpos + 1))]), cols = ['COUNT(*) AS allpregs'])[0]['allpregs']
      ls[mpos]  = got
      tot       = tot + got
      dmax      = max(dmax, got)
    tot   = float(tot)
    lmps  = [{'value' : x, 'pc' : (100.0 * (float(x) / tot)) if tot > 0 else 0, 'rpc': (100.0 * (float(x) / dmax)) if dmax > 0 else 0} for x in ls]
    return self.dynamised('pregnancy', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def data_reports(self, *args, **kw):
    auth    = ThousandAuth(cherrypy.session.get('email'))
    navb    = ThousandNavigation(auth, *args, **kw)
    cnds    = navb.conditions('report_date', auth)
    cnds.update({'report_type = %s':kw.get('subcat')})
    cherrypy.response.headers['Content-Type'] = 'application/json'
    reps   = orm.ORM.query('thousanddays_reports', cnds, cols = ['COUNT(*) AS total'])[0]['total']
    return json.dumps({'total': neat_numbers(reps)})

