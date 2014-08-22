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

class ThousandDays:
  def __init__(self, pth, bst, stp, **kw):
    self.path   = pth
    self.jinja  = Environment(loader = FileSystemLoader(pth))
    self.base   = bst
    self.static = stp
    self.jinja.filters.update(kw.get('filters', {}))

  @cherrypy.expose
  def index(self, *args, **kw):
    return self.dynamised('index', *args, **kw)

  def app_data(self):
    try:
      return settings.APP_DATA
    except:
      pass
    return {}

  @cherrypy.expose
  def dynamised(self, chart, mapping = {}, *args, **kw):
    info  = {}
    info.update({
      'base_template' : self.base,
      'ref'           : chart,
      'locations'     : ['TODO'],
      'args'          : kw,
      'nav'           : ThousandNavigation(*args, **kw),
      'static_path'   : self.static
    })
    info.update(self.app_data())
    info.update(kw)
    mapping.pop('self', None)
    info.update({'display': mapping})
    return self.jinja.get_template('%s.html' % (chart, )).render(*args, **info)

class ThousandNavigation:
  def __init__(self, *args, **kw):
    self.args   = args
    self.kw     = kw
    td          = datetime.today()
    self.fin    = datetime(year = td.year, month = td.month, day = td.day)
    self.gap    = timedelta(days = 1000)

  def conditions(self, tn = 'created_at'):
    ans = {
      (tn + ' >= %s')  : self.start,
      (tn + ' <= %s')  : self.finish
    }
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
    try:
      return datetime(year = pcs[2], month = pcs[1], day = pcs[0])
    except ValueError:
      return datetime(year = pcs[2], month = pcs[0], day = pcs[1])

class ThousandCharts(ThousandDays):
  @cherrypy.expose
  def charts(self, *args, **kw):
    return ':-\\'

  @cherrypy.expose
  def anc(self, *args, **kw):
    return self.dynamised('anc', *args, **kw)

  @cherrypy.expose
  def ccm(self, *args, **kw):
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
  def birthreport(self, *args, **kw):
    return self.dynamised('birthreport', mapping = self.locals_for_births(*args, **kw), *args, **kw)

  @cherrypy.expose
  def childhealth(self, *args, **kw):
    return self.dynamised('childhealth', mapping = self.locals_for_births(*args, **kw), *args, **kw)

  @cherrypy.expose
  def nbc(self, *args, **kw):
    return self.dynamised('nbc', mapping = self.locals_for_births(*args, **kw), *args, **kw)

  @cherrypy.expose
  def delivery(self, *args, **kw):
    return self.dynamised('delivery', mapping = self.locals_for_births(*args, **kw), *args, **kw)

  @cherrypy.expose
  def vaccination(self, *args, **kw):
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
  def nutrition(self, *args, **kw):
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
  def pregnancy(self, *args, **kw):
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

def neat_numbers(num):
  pcs = divided_num(str(num), 3)
  return ','.join(pcs)

def divided_num(num, mx = 3):
  if len(num) < (mx + 1):
    return [num]
  lft = num[0:-3]
  rgt = num[-3:]
  return divided_num(lft) + [rgt]

class URLMapping(cherrypy.dispatch.Dispatcher):
  def __init__(self, mapper, *args, **kw):
    self.mapper = mapper
    super(URLMapping, self).__init__(*args, **kw)

  def __call__(self, path):
    gat = re.search(r'/static/(.*)', path)
    if gat:
      return super(URLMapping, self).__call__(path)
    return super(URLMapping, self).__call__(self.mapper.match(path))

def rwabugiri_main(argv):
  larg  = len(argv)
  if larg < 4:
    sys.stderr.write('%s templatedir staticdir staticpath [port] [host]\r\n' % (argv[0], ))
    return 1
  pth       = os.path.abspath(argv[1])
  stt       = argv[2]
  stp       = argv[3]
  handler   = __import__(settings.WEBAPP).Application(pth, stt, stp, settings.APP_DATA)
  def launch(hst, prt, *args):
    cherrypy.server.socket_host = hst
    cherrypy.server.socket_port = prt
    cherrypy.quickstart(handler, '/', {
      '/':  {
        'request.dispatch':   URLMapping(handler),
        'tools.sessions.on':  True
      },
      # '/static':{
      stp:{
        'tools.staticdir.on':   True,
        'tools.staticdir.root': os.path.abspath(stt),
        # 'tools.staticdir.root': pth,
        'tools.staticdir.dir':  ''
      }
    })
  # thd       = thread.start_new_thread(launch, (None, ))
  hst = '0.0.0.0'
  prt = '8081'
  if larg == 5:
    prt = argv[4]
  if larg == 6:
    hst = argv[5]
  return launch(hst, int(prt))

if __name__ == '__main__':
  bottom  = sys.exit(rwabugiri_main(sys.argv))
