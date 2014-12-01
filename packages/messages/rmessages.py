# encoding: utf-8
# vim: expandtab ts=2

from abc import ABCMeta, abstractmethod
import copy
from datetime import datetime
import re
from parser import *

def first_cap(s):
  '''Capitalises the first letter (without assaulting the others like Ruby's #capitalize does).'''
  if len(s) < 1: return s
  return s[0].upper() + s[1:]

class IDField(ThouField):
  'The commonly-used ID field.'

  column_name = 'indangamuntu'
  @classmethod
  def is_legal(self, ans, dt):
    'For now, checks are limited to length assurance.'
    return [] if len(ans) == 16 else 'bad_indangamuntu'

class DateField(ThouField):
  'The descriptor for valid message fields.'

  column_name = 'daymonthyear'
  @classmethod
  def check_gap(self, sdate, adate):
    return True

  @classmethod
  def is_legal(self, fld, dt):
    ans = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', fld)
    if not ans: return 'bad_date'
    gps   = ans.groups()
    sdate = None
    try:
      sdate = datetime(year = int(gps[2]), month = int(gps[1]), day = int(gps[0]))
    except ValueError:
      return 'impossible_date'
    return ([] if self.check_gap(sdate, dt) else 'incoherent_date_periods')

  @classmethod
  def convert(self, fld):
    ans = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', fld)
    gps = ans.groups()
    return datetime(year = int(gps[2]), month = int(gps[1]), day = int(gps[0]))

class LMPDateField(DateField):
  'Date field, strictly for LMP.'
  # Mostly a disambiguation trick.
  column_name = 'lmp'

  @classmethod
  def check_gap(self, sdate, adate):
    'For now, only checking that the active date (normally today) is after the LMP date supplied.'
    return sdate < adate

class NumberField(ThouField):
  'The descriptor for number fields.'

  column_name = 'number'
  @classmethod
  def is_legal(self, fld, dt):
    'Basically a regex.'
    return [] if re.match(r'\d+', fld) else 'bad_number'

  @classmethod
  def convert(self, fld):
    return int(fld)

class CodeField(ThouField):
  'This should match basically any simple code, plain and numbered.'

  column_name = 'code'
  @classmethod
  def is_legal(self, fld, dt):
    'Basically a simple regex.'
    return [] if re.match(r'\w+', fld) else 'what_code'

class GravidityField(NumberField):
  'Gravidity is a number.'

  column_name = 'gravidity'
  pass

class ParityField(NumberField):
  'Parity is a number.'

  column_name = 'parity'
  pass

class PregCodeField(CodeField):
  'Field for Pregnancy codes.'

  column_name = 'pregnancy'
  @classmethod
  def expectations(self):
    'These are all the codes related to pregnancy.'
    return ['GS', 'MU', 'HD', 'RM', 'OL', 'YG', 'NR', 'TO', 'HW', 'NT', 'NT', 'NH', 'KX', 'YJ', 'LZ']

class PrevPregField(PregCodeField):
  'Field for Previous pregnancy codes.'

  column_name = 'prev_pregnancy'
  @classmethod
  def expectations(self):
    'Codes associated with previous pregnancy.'
    return ['GS', 'MU', 'HD', 'RM']

class SymptomCodeField(CodeField):
  'Field for codes associated with symptoms.'

  column_name = 'symptom'
  @classmethod
  def expectations(self):
    'These are the codes associated with symptoms.'
    return ['AF', 'CH', 'CI', 'CM', 'IB', 'DB', 'DI', 'DS', 'FE', 'FP', 'HY', 'JA', 'MA', 'NP', 'NS',
            'OE', 'PC', 'RB', 'SA', 'SB', 'VO']

class RedSymptomCodeField(SymptomCodeField):
  'Field for codes associated with symptoms.'

  column_name = 'red_symptom'
  @classmethod
  def expectations(self):
    'These are the codes in red alerts.'
    return ['AP', 'CO', 'HE', 'LA', 'MC', 'PA', 'PS', 'SC', 'SL', 'UN']

class LocationField(CodeField):
  'Field for codes that communicate locations.'

  column_name = 'location'
  @classmethod
  def expectations(self):
    'The codes for RED alerts.'
    return ['CL', 'HO', 'HP', 'OR']

class FloatedField(CodeField):
  'Field for codes that carry fractional numbers with decimal points.'

  column_name = 'float_value'
  @classmethod
  def is_legal(self, fld, dt):
    'Basically a regex.'
    return [] if re.match(r'\w+\d+(\.\d+)?', fld) else 'bad_floated_field'

  @classmethod
  def convert(self, fld):
    ans = re.sub(r'[A-Z]', '', fld, 0, re.IGNORECASE)
    return float(ans)

class NumberedField(CodeField):
  'Field for codes that carry whole numbers.'

  column_name = 'numbered_value'
  @classmethod
  def is_legal(self, fld, dt):
    'Basically a regex.'
    return [] if re.match(r'\w+\d+', fld) else 'bad_numbered_field'

  @classmethod
  def convert(self, fld):
    ans = re.sub(r'[A-Z]', '', fld, 0, re.IGNORECASE)
    return int(ans)

class HeightField(NumberedField):
  'Field for height codes.'

  column_name = 'height'
  pass

class WeightField(FloatedField):
  'Field for weight codes.'

  column_name = 'weight'
  pass

class ToiletField(CodeField):
  'Field for codes concerning toilets.'

  column_name = 'toilet'
  @classmethod
  def expectations(self):
    'Toilet or no toilet?'
    return ['TO', 'NT']

class HandwashField(CodeField):
  'Field for codes concerning handwwashing basic.'

  column_name = 'handwash'
  @classmethod
  def expectations(self):
    'Hand-wash or no hand-wash?'
    return ['HW', 'NH']

class PhoneBasedIDField(IDField):
  'The alternative ID field, incorporating phone number.'
  @classmethod
  def is_legal(self, fld, dt):
    'Basic regex.'
    return [] if re.match(r'0\d{15}', fld) else 'bad_phone_id'

class ANCField(NumberedField):
  'Ante-Natal Care visit number is a ... number.'

  column_name = 'anc_visit'
  @classmethod
  def is_legal(self, fld, dt):
    'Matches the code, not insisting on the string that precedes the number.'
    return [] if re.match(r'\w+\d', fld) else 'anc_code'

class PNCField(NumberedField):
  'Post-Natal Care visit number is a ... number.'

  column_name = 'pnc_visit'
  @classmethod
  def is_legal(self, fld, dt):
    'Matches the code, not insisting on the string that precedes the number.'
    return [] if re.match(r'\w+\d', fld) else 'pnc_code'

class NBCField(NumberedField):
  'New-Born Care visit number is a ... number.'

  column_name = 'nbc_visit'
  @classmethod
  def is_legal(self, fld, dt):
    'Matches the code, not insisting on the string that precedes the number.'
    return [] if re.match(r'\w+\d', fld) else 'nbc_code'

  @classmethod
  def expectations(self):
    'Pre-enforcing the discipline that `is_legal` does not enforce.'
    return ['EBF', 'NB', 'PH', 'NBC1', 'NBC2', 'NBC3', 'NBC4', 'NBC5']

class GenderField(CodeField):
  'Gender is a a code.'

  column_name = 'gender'
  @classmethod
  def expectations(self):
    'Boy or girl?'
    return ['BO', 'GI']

class BreastFeedField(NBCField):
  'Breast-feeding code has new-born care fields.'

  column_name = 'breastfeeding'
  @classmethod
  def expectations(self):
    'The accepted codes. May be booleanisable.'
    return ['CBF', 'EBF', 'NB']

class InterventionField(CodeField):
  'Field for general interventions.'
  column_name = 'intervention_field'

  @classmethod
  def expectations(self):
    'Intervention codes.'
    return ['PR', 'AA', 'AL', 'AT', 'NA', 'PT', 'TR']

class NBCInterventionField(InterventionField):
  'New-born care intervention field.'
  pass

class HealthStatusField(CodeField):
  'General health status field.'

  column_name = 'health_status'
  @classmethod
  def expectations(self):
    return ['MW', 'MS', 'CW', 'CS']

class NewbornHealthStatusField(HealthStatusField):
  'New born health status is a ... health status.'
  @classmethod
  def expectations(self):
    'New born health status codes.'
    return ['CW', 'CS']

class MotherHealthStatusField(HealthStatusField):
  'Mother health status fields.'
  @classmethod
  def expectations(self):
    'Mother health codes.'
    return ['MW', 'MS']

class VaccinationField(NumberedField):
  'Vaccination Completion is apparently a number.'

  column_name = 'vacc_completion'
  @classmethod
  def expectations(self):
    'The vaccination completion codes.'
    # return ['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'VC', 'VI', 'NV']
    return ['V1', 'V2', 'V3', 'V4', 'V5', 'V6']

# class VaccinationCompletionField(VaccinationField):
class VaccinationCompletionField(CodeField):
  'Vaccination Completion fields.'
  @classmethod
  def expectations(self):
    'Levels of vaccination checkpoints.'
    return ['VC', 'VI', 'NV']

class MUACField(FloatedField):
  'MUAC is a decimal float.'

  column_name = 'muac'
  @classmethod
  def is_legal(self, fld, dt):
    'Regex alert.'
    return [] if re.match(r'MUAC\d+(\.\d+)', fld) else 'bad_muac_code'

class DeathField(CodeField):
  'Field for describing death codes.'

  column_name = 'death'
  @classmethod
  def expectations(self):
    'Expected death codes.'
    return ['ND', 'CD', 'MD']

class ThouMsgError:
  'Small exception class.'
  def __init__(self, msg, errors):
    self.errors     = errors
    self.message    = msg

class ThouMessage:
  '''Base class describing the standard RapidSMS 1000 Days message.'''
  fields      = []
  created     = False

  # @staticmethod
  @classmethod
  def creation_sql(self, repc):
    cols  = [('created_at', 'TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()', 'No field class.', 'Created'),
             #  ('modified_at', 'TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()', 'No field class.', 'Modified')
             ]
    col   = None
    for fld in self.fields:
      if type(fld) == type((1, 2)):
        fldc  = fld[0]
        col   = str(fldc).split('.')[-1].lower()
        for exp in fldc.expectations():
          subans  = ('%s_%s' % (col, exp.lower()), '%s DEFAULT %s' % (fldc.dbtype(), fldc.default_dbvalue()), fldc, exp)
          cols.append(subans)
      else:
        col = str(fld).split('.')[-1].lower()
        cols.append((col, '%s DEFAULT %s' % (fld.dbtype(), fld.default_dbvalue()), fld, first_cap(fld.display())))
    return (str(repc).split('.')[-1].lower() + 's', cols)

  @classmethod
  def create_in_db(self, repc):
    try:
      tbl, cols = stuff = self.creation_sql(repc)
      if self.created: return stuff
      curz  = db.cursor()
      curz.execute('SELECT TRUE FROM information_schema.tables WHERE table_name = %s', (tbl,))
      if not curz.fetchone():
        curz.execute('CREATE TABLE %s (indexcol SERIAL NOT NULL);' % (tbl,))
        curz.close()
        return self.create_in_db(repc)
      for col in cols:
        curz.execute('SELECT TRUE FROM information_schema.columns WHERE table_name = %s AND column_name = %s', (tbl, col[0]))
        if not curz.fetchone():
          curz.execute('ALTER TABLE %s ADD COLUMN %s %s;' % (tbl, col[0], col[1]))
      curz.close()
      db.commit()
      self.created  = True
      return stuff
    except Exception, e:
      raise Exception, ('Table creation: ' + str(e))

  @staticmethod
  def pull_code(msg):
    return ((re.split(r'\s+', msg, 1)) + [''])[0:2]

  @staticmethod
  def caseless_hash(hsh):
    ans = {}
    for k in hsh:
      ans[k.lower()] = hsh[k]
    return ans

  @staticmethod
  def parse_report(msg, fh, hsh, **kwargs):
    pz  = ThouMessage.parse(msg)
    nch = ThouMessage.caseless_hash(hsh)
    if pz.__class__ == UnknownMessage:
      ukh = lambda x: x
      try:
        ukh = kwargs['unknown_handler']
      except KeyError:
        pass
      return ukh(pz)
    if not pz.errors:
      return fh(pz, nch[pz.code.lower()](pz))
    erh = lambda x: x
    try:
      erh = kwargs['error_handler']
    except KeyError:
      pass
    return erh(pz)

  @staticmethod
  def parse(msg, assoc = {}, activedate = None):
    code, rem = ThouMessage.pull_code(msg.strip())
    response  = None
    assocs    = ThouMessage.caseless_hash(assoc)
    try:
      response = assocs[code.lower()]
    except KeyError:
      raise ThouMsgError("Unknown code '%s'" % (code, ), [('unknown_code', None)])
    if type(response) == type({}):
      return ThouMessage.parse(rem, response, activedate)
    klass = response[0]
    msg   = klass.process(klass, code, rem, activedate or datetime.today())
    return (msg, response[1])

  # “Private”
  @staticmethod
  def process(klass, cod, msg, dt):
    errors  = []
    fobs    = []
    etc     = msg
    for fld in klass.fields:
      try:
        if type(fld) == type((1, 2)):
          cur, err, etc  = fld[0].pull(fld[0], cod, etc, dt, fld[1])
          errors.extend([(e, fld) for e in err])
        else:
          cur, err, etc  = fld.pull(fld, cod, etc, dt)
          errors.extend([(e, fld) for e in err])
        fobs.append(cur)
      except Exception, err:
        errors.append((str(err), fld))
    if etc.strip():
      errors.append(('bad_text', 'Superfluous text: "%s"' % (etc.strip(),)))
    return klass(cod, msg, fobs, errors, dt)

  def __init__(self, cod, txt, fobs, errs, dt):
    self.code     = cod
    self.errors   = errs
    self.text     = txt
    self.fields   = fobs
    if self.errors: raise ThouMsgError(self, self.errors)
    semerrors     = self.semantics_check(dt)
    if semerrors: raise ThouMsgError(self, semerrors)
    def as_hash(p, n):
      p[n.__class__.subname()] = n
      return p
    self.entries  = reduce(as_hash, fobs, {})
    self.extra    = {}

  def add_extra(self, hsh = {}):
    self.extra.update(hsh)
    return self.extra

  def data(self):
    ans = {}
    for x in self.entries:
      ans[x] = self.entries[x].data()
    ans.update(self.extra)
    return ans

  @abstractmethod
  def semantics_check(self, adate):
    return ['Extend semantics_check.']  # Hey, why doesn’t 'abstract' scream out? TODO.

class UnknownMessage(ThouMessage):
  '''To the Unknown Message.
Since every message has to be successfully parsed as a Message object, this is the one in the event that none other matches.'''
  pass

class PregMessage(ThouMessage):
  'Pregnancy message.'
  fields  = [IDField, LMPDateField, DateField, GravidityField, ParityField,
              (PregCodeField, True),
              (SymptomCodeField, True),
             LocationField, WeightField, ToiletField, HandwashField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class RefMessage(ThouMessage):
  'Referral message.'
  fields  = [PhoneBasedIDField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class ANCMessage(ThouMessage):
  'Ante-natal care visit message.'
  fields  = [IDField, DateField, ANCField,
             (SymptomCodeField, True),
             LocationField, WeightField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class DepMessage(ThouMessage):
  'Departure message.'
  fields  = [IDField, NumberField, DateField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class RiskMessage(ThouMessage):
  'Risk report message.'
  fields  = [IDField,
             (SymptomCodeField, True),
             LocationField, WeightField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class RedMessage(ThouMessage):
  'Red alert message.'
  fields  = [(RedSymptomCodeField, True), LocationField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class BirMessage(ThouMessage):
  'Birth message.'
  fields  = [IDField, NumberField, DateField, GenderField,
             (SymptomCodeField, True),
             LocationField, BreastFeedField, WeightField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class ChildMessage(ThouMessage):
  'Child message.'
  fields  = [IDField, NumberField, DateField, VaccinationField, VaccinationCompletionField,
             (SymptomCodeField, True),
             LocationField, WeightField, MUACField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class DeathMessage(ThouMessage):
  'Death message.'
  fields  = [IDField, NumberField, DateField, LocationField, DeathField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class ResultMessage(ThouMessage):
  'Result message.'
  fields  = [IDField,
             (SymptomCodeField, True),
             LocationField, InterventionField, MotherHealthStatusField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class RedResultMessage(ThouMessage):
  'Red alert result message.'
  fields  = [IDField, DateField,
             (SymptomCodeField, True),
             LocationField, InterventionField, MotherHealthStatusField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class NBCMessage(ThouMessage):
  'New-born care message.'
  fields  = [IDField, NumberField, NBCField, DateField,
             (SymptomCodeField, True),
             BreastFeedField, NBCInterventionField, NewbornHealthStatusField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class PNCMessage(ThouMessage):
  'Post-natal care message.'
  fields  = [IDField, PNCField, DateField,
             (SymptomCodeField, True),
             InterventionField, MotherHealthStatusField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class CCMMessage(ThouMessage):
  'Commmunity Case Management message.'
  fields  = [IDField, NumberField, DateField,
             (SymptomCodeField, True),
             InterventionField, MUACField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class CMRMessage(ThouMessage):
  'Commmunity Management Response message.'
  fields  = [IDField, NumberField, DateField,
             (SymptomCodeField, True),
             InterventionField, NewbornHealthStatusField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class CBNMessage(ThouMessage):
  'Commmunity-Based Nutrition message.'
  fields  = [IDField, NumberField, DateField, BreastFeedField, HeightField, WeightField, MUACField]

  def semantics_check(self, adate):
    'TODO.'
    return []

class ChildHealthMessage(ThouMessage):
  # Slightly different from other CHI. Systemic inconsistency.
  'Child Health message.'
  fields  = [IDField, NumberField, DateField, VaccinationField,
             (SymptomCodeField, True),
             LocationField, WeightField, MUACField]

  def semantics_check(self, adate):
    'TODO.'
    return []
