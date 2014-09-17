# vim: expandtab ts=2
from django.contrib import messages as flashes
from django.shortcuts import render, redirect
# from .messages.rapid1000messages import *
# from .reports.rapid1000reports import *
# from .reports.reports import THE_DATABASE as db
from rapidsmsrw1000.settings import *
from rapidsmsrw1000.apps.thoureport.reports.rapid1000reports import *
from rapidsmsrw1000.apps.thoureport.reports.reports import *
from .models import *

REPORT_SET = {
  # 'PRE':  PregReport,
  # 'REF':  RefReport,
  # 'ANC':  ANCReport,
  # 'DEP':  DepReport,
  # 'RISK': RiskReport,
  'RED':  RedReport,
  # 'BIR':  BirReport,
  # 'CHI':  ChildReport,
  # 'DTH':  DeathReport,
  # 'RES':  ResultReport,
  # 'RAR':  RedResultReport,
  # 'NBC':  NBCReport,
  # 'CCM':  CCMReport,
  # 'CMR':  CMRReport,
  # 'CBN':  CBNReport,
  # 'PNC':  PNCReport,

  # 'TIM':  TimothyReport,
  'REV': RevenceReport,
}

TRANSFORMATIONS = {
  '[!!!]' : (
    'Expected codes',
    lambda x: and_join(x.expectations())
  )
}

class TraversibleTX:
  def __init__(self):
    self.them = TRANSFORMATIONS.keys()
    self.them.sort()

  def fetch(self):
    ans = []
    for it in self.them:
      ans.append({'code': it, 'descr': TRANSFORMATIONS[it][0]})
    return ans

def and_join(dem):
  if len(dem) < 2: dem[0]
  return ', and '.join([', '.join(dem[0:-1]), dem[-1]])

class TraversibleReport:
  def __init__(self, repc, msgc):
    self.repc                 = repc
    self.msgc                 = msgc
    self.tablename, self.cols = msgc.creation_sql(repc)

  def columns(self):
    self.msgc.create_in_db(self.repc)
    return [x[3] for x in self.cols]

  def rows(self):
    curz  = db.cursor()
    qry   = 'SELECT %s FROM %s' % (', '.join([x[0] for x in self.cols]), self.tablename)
    curz.execute(qry)
    rs  = curz.fetchall()
    curz.close()
    db.commit()
    return rs

def error_messenger(dat, msgobj, fld):
  def applicant(p, n):
    return p.replace(n, TRANSFORMATIONS[n][1](dat))
  return reduce(applicant, TRANSFORMATIONS.keys(), fld)

def smser(req):
  msgs  = StoredSMS.objects.all().order_by('-when')
  return render(req, 'smser.html', {'msgs': msgs})

def reports(req, rcode = None):
  reps  = []
  if rcode:
    try:
      reqc      = rcode[1:]
      fst, snd  = metup = REPORT_SET[reqc], MSG_ASSOC[reqc]
      reps      = [TraversibleReport(fst, snd)]
    except Exception, e:
      raise e
      pass
  return render(req, 'reports.html', {'reps': reps, 'repset': REPORT_SET})

def messages(req):
  msgs  = StoredSMS.objects.all().order_by('-when')
  return render(req, 'messages.html', {'msgs': msgs})

def resp_mod(req, cod):
  try:
    msg       = StoredResponse.objects.get(code = cod)
    msg.text  = req.POST['msg']
    msg.save()
  except Exception, e:
    StoredResponse.objects.create(code = req.POST['code'], text = req.POST['msg'])
  return redirect('/responses')

def docs(req):
  msgs  = StoredResponse.objects.all()
  return render(req, 'rapid1000.html', {})

def responses(req):
  msgs  = StoredResponse.objects.all()
  return render(req, 'responses.html', {'msgs': msgs, 'txes':TraversibleTX().fetch()})

def sender(req):
  message               = req.POST['msg']
  req.session['phone']  = req.POST['phone']
  req.session['msg']    = message
  sm                    = StoredSMS(message = message, sender = req.POST['phone'])
  sm.save()
  def unknown(uk):
    flashes.add_message(req, flashes.ERROR, StoredResponse.fetch('unknown_message'))
    return redirect('/')

  def has_errors(msgobj):
    for er in msgobj.errors:
      toproc  = None
      if type(er) == type((1, 2)):
        kls     = er[1]
        if type(kls) == type((1, 2)):
          kls = kls[0]
        toproc  = error_messenger(kls, msgobj, StoredResponse.fetch(er[0]))
      else:
        toproc  = StoredResponse.fetch(er)
      flashes.add_message(req, flashes.ERROR, toproc)
    return redirect('/')

  def is_fine(msg, rept):
    got = rept.save()
    return redirect('/')

  return ThouMessage.parse_report(req.POST['msg'], is_fine, REPORT_SET, error_handler   = has_errors, unknown_handler = unknown)
