#!  /usr/bin/env python
import cherrypy
import copy
from datetime import datetime, timedelta
from ectomorph import orm
from jinja2 import Environment, FileSystemLoader
import re
import settings
import sys
import urllib2, urlparse

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
  def __init__(self, loc, nav, lmt, ttl, chop  = None):
    self.location   = loc
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

class ThousandNavigation:
  def __init__(self, *args, **kw):
    self.args   = args
    self.kw     = kw
    td          = datetime.today()
    self.fin    = datetime(year = td.year, month = td.month, day = td.day)
    self.gap    = timedelta(days = 1000 - 1)

  def pages(self, qry, limit = 25):
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
    dem = [ThousandLocation(self.nation(), self, ['province', 'district', 'hc', 'page'], '')]
    if self.kw.get('province'):
      dem.append(ThousandLocation(self.province(), self, ['district', 'hc', 'page'], 'Province', lambda x: first_cap(re.sub(u' PROVINCE', '', x).lower())))
    if self.kw.get('district'):
      dem.append(ThousandLocation(self.district(), self, ['hc', 'page'], 'District'))
    if self.kw.get('hc'):
      dem.append(ThousandLocation(self.hc(), self, ['page'], 'Health Centre'))
    return dem

  @property
  def hierarchy(self):
    prv = self.kw.get('province')
    dst = self.kw.get('district')
    ans = []
    if self.kw.get('district'):
      return [{'province': self.province()}, {'district':self.district()}]
    if self.kw.get('province'):
      return [{'province': self.province()}]
    return []

  def nation(self):
    gat = orm.ORM.query('chws__nation', {'indexcol = 1':''})[0]
    return gat

  def province(self, prv = None):
    num = int(prv or self.kw.get('province'))
    gat = orm.ORM.query('chws__province', {'indexcol = %s': num})[0]
    return gat

  def district(self, dst = None):
    num = int(dst or self.kw.get('district'))
    gat = orm.ORM.query('chws__district', {'indexcol = %s': num})[0]
    return gat

  def hc(self, h = None):
    num = int(h or self.kw.get('hc'))
    gat = orm.ORM.query('chws__healthcentre', {'indexcol = %s': num})[0]
    return gat

  @property
  def child(self):
    if self.kw.get('hc'):       return ''
    if self.kw.get('district'): return 'hc'
    if self.kw.get('province'): return 'district'
    return 'province'

  @property
  def subarea(self):
    return ['province', 'district', 'hc'][len(self.hierarchy)]

  @property
  def childareas(self):
    if self.kw.get('hc'):
      return []
    if self.kw.get('district'):
      return self.areas('hc')
    if self.kw.get('province'):
      return self.areas('district')
    return self.areas('province')

  def areas(self, level = None):
    tbl, sel, etc = {
      'province'  : lambda _: ('chws__province', [self.province()] if self.kw.get('province') else [], {}),
      'district'  : lambda _: ('chws__district', [self.district()] if self.kw.get('district') else [], {'province = %s': self.province()['indexcol']}),
      'hc'        : lambda _: ('chws__healthcentre', [], {'province = %s':self.province()['indexcol'], 'district = %s':self.district()['indexcol']})
    }[level or self.subarea](None)
    prvq      = orm.ORM.query(tbl, etc,
      cols  = ['*'] + ['indexcol = %d AS selected' % (s['indexcol'], ) for s in sel],
      sort  = ('name', 'DESC')
    )
    return prvq.list()

  def conditions(self, tn = 'created_at'):
    ans = {
      (tn + ' >= %s')  : self.start,
      (tn + ' <= %s')  : self.finish
    }
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
    if not self.kw:
      return url
    pcs, qrs  = self.pre_link(url)
    qrs.update(kw)
    return urlparse.urlunsplit((pcs[0], pcs[1], pcs[2], '&'.join(['%s=%s' % (k, urllib2.quote(str(qrs[k]))) for k in qrs if qrs[k]]), pcs[4]))

class Application:
  def __init__(self, templates, statics, static_path, app_data, **kw):
    self.templates    = templates
    self.statics      = statics
    self.static_path  = static_path
    self.kw           = kw
    self.app_data     = app_data
    self.jinja        = Environment(loader = FileSystemLoader(templates))
    self.jinja.filters.update({
      'neat_numbers'  : neat_numbers
    })

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
      'nav'           : ThousandNavigation(*args, **kw),
      'static_path'   : self.static_path
    })
    info.update(self.app_data)
    info.update(kw)
    mapping.pop('self', None)
    info.update({'display': mapping})
    return self.jinja.get_template('%s.html' % (chart, )).render(*args, **info)

  @cherrypy.expose
  def index(self, *args, **kw):
    return self.dynamised('index', *args, **kw)

  @cherrypy.expose
  def charts(self, *args, **kw):
    return ':-\\'

  @cherrypy.expose
  def dashboards_death(self, *args, **kw):
    return self.dynamised('death', *args, **kw)

  @cherrypy.expose
  def dashboards_redalert(self, *args, **kw):
    return self.dynamised('redalert', *args, **kw)

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
    navb    = ThousandNavigation(*args, **kw)
    cnds    = navb.conditions('report_date')
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
    navb    = ThousandNavigation(*args, **kw)
    cnds    = navb.conditions('report_date')
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

  @cherrypy.expose
  def tables_delivery(self, *args, **kw):
    navb    = ThousandNavigation(*args, **kw)
    cols    = self.tables_in_general(*args, **kw)
    cnds    = navb.conditions('report_date')
    # TODO: optimise
    nat     = orm.ORM.query('bir_table', cnds,
      cols  = [x[0] for x in cols if x[0][0] != '_'],
    )
    return self.dynamised('delivery_table', mapping = locals(), *args, **kw)

  @cherrypy.expose
  def tables_pregnancy(self, *args, **kw):
    navb    = ThousandNavigation(*args, **kw)
    cols    = self.tables_in_general(*args, **kw)
    # TODO: optimise
    cnds    = navb.conditions('report_date')
    nat     = orm.ORM.query('pre_table', cnds,
      cols  = [x[0] for x in cols if x[0][0] != '_'],
    )
    return self.dynamised('pregnancy_table', mapping = locals(), *args, **kw)

  def tables_in_general(self, *args, **kw):
    navb    = ThousandNavigation(*args, **kw)
    cnds    = navb.conditions('report_date')
    cols    = (([
      ('indexcol',          'Report ID'),
      ('report_date',       'Date'),
      ('reporter_phone',    'Reporter'),
      ('reporter_pk',       'Reporter ID')
    ]) +

    (([] if 'province' in kw else [('province_pk',       'Province')]) +
     ([] if 'district' in kw else [('district_pk',       'District')]) +
     ([] if 'hc' in kw else [('health_center_pk',  'Health Centre')])) +

    ([('patient_id',        'Mother ID'),
      ('lmp',               'LMP'),
    ]))
    return cols

  @cherrypy.expose
  def dashboards_pregnancy(self, *args, **kw):
    navb    = ThousandNavigation(*args, **kw)
    cnds    = navb.conditions('report_date')
    nat     = orm.ORM.query('pre_table', cnds,
      cols      = ['COUNT(*) AS allpregs'],
      extended  = {
        'coughing':('COUNT(*)', 'ch_bool IS NOT NULL'),
        'diarrhoea':('COUNT(*)',  'di_bool IS NOT NULL'),
        'fever':('COUNT(*)',  'fe_bool IS NOT NULL'),
        'oedema':('COUNT(*)',  'oe_bool IS NOT NULL'),
        'pneumo':('COUNT(*)',  'pc_bool IS NOT NULL'),
        'disab':('COUNT(*)',  'db_bool IS NOT NULL'),
        'cordi':('COUNT(*)',  'ci_bool IS NOT NULL'),
        'necks':('COUNT(*)',  'ns_bool IS NOT NULL'),
        'malaria':('COUNT(*)',  'ma_bool IS NOT NULL'),
        'vomiting':('COUNT(*)',  'vo_bool IS NOT NULL'),
        'stillb':('COUNT(*)',  'sb_bool IS NOT NULL'),
        'jaun':('COUNT(*)',  'ja_bool IS NOT NULL'),
        'hypoth':('COUNT(*)',  'hy_bool IS NOT NULL'),
        'ibibari':('COUNT(*)',  'ib_bool IS NOT NULL')
      },
      migrations  = [
        ('db_bool', False),
        ('fe_bool', False),
        ('ma_bool', False),
        ('to_bool', False),
        ('ch_bool', False),
        ('vo_bool', False),
        ('ja_bool', False),
        ('ns_bool', False),
        ('pc_bool', False),
        ('ci_bool', False),
        ('oe_bool', False),
        ('di_bool', False),
        ('sb_bool', False),
        ('hy_bool', False),
        ('hw_bool', False),
        ('gs_bool', False),
        ('mu_bool', False),
        ('rm_bool', False),
        ('ol_bool', False),
        ('yg_bool', False),
        ('kx_bool', False),
        ('yj_bool', False),
        ('lz_bool', False),
        ('ib_bool', False)
      ]
    )
    toi     = nat.specialise({'to_bool IS NOT NULL':''})
    hnd     = nat.specialise({'hw_bool IS NOT NULL':''})
    weighed = nat.specialise({'mother_height_float > 100.0 AND mother_weight_float > 15.0':''})
    thinq   = weighed.specialise({'(mother_weight_float / ((mother_height_float * mother_height_float) / 10000.0)) < %s': settings.BMI_MIN})
    fatq    = weighed.specialise({'(mother_weight_float / ((mother_height_float * mother_height_float) / 10000.0)) > %s': settings.BMI_MAX})
    riskhsh = {'(gs_bool IS NOT NULL OR mu_bool IS NOT NULL OR rm_bool IS NOT NULL OR ol_bool IS NOT NULL OR yg_bool IS NOT NULL OR kx_bool IS NOT NULL OR yj_bool IS NOT NULL OR lz_bool IS NOT NULL)':''}
    riskys  = nat.specialise(riskhsh)
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


