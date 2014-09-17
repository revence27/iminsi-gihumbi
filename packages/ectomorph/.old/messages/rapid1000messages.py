# encoding: utf-8
# vim: expandtab ts=2

#This is a comment. Push it, push it. Harder now!
from abc import ABCMeta, abstractmethod
import re
from ..messages.parser import *
from rapidsmsrw1000.settings import THE_DATABASE as db
# from .reports.reports import THE_DATABASE as db

def first_cap(s):
  '''Capitalises the first letter (without assaulting the others like Ruby's #capitalize does).'''
  if len(s) < 1: return s
  return s[0].upper() + s[1:]

class IDField(ThouField):
  'The commonly-used ID field.'

  column_name = 'patient_id'
  @classmethod
  def is_legal(self, ans):
    'For now, checks are limited to length assurance.'
    return [] if len(ans) == 16 else 'pre_2'

class DateField(ThouField):
  'The descriptor for valid message fields.'

  column_name = 'lmp'
  @classmethod
  def is_legal(self, fld):
    ans = re.match(r'(\d{2})\.(\d{2})\.(\d{4})')
    if not ans: return 'pre_4'
    gps = ans.groups()
    return [] # Check that it is a valid date. TODO. Move to semantics part?

class NumberField(ThouField):
  'The descriptor for number fields.'

  column_name = 'number'
  @classmethod
  def is_legal(self, fld):
    'Basically a regex.'
    return [] if re.match(r'\d+', fld) else 'bad_number'

class CodeField(ThouField):
  'This should match basically any simple code, plain and numbered.'

  column_name = 'code'
  @classmethod
  def is_legal(self, fld):
    'Basically a simple regex.'
    return [] if re.match(r'\w+', fld) else 'what_code'

class GravidityField(NumberField):
  'Gravidity is a number.'

  column_name = 'gravity_float' # (sic.)
  pass

class ParityField(NumberField):
  'Parity is a number.'

  column_name = 'parity_float'
  pass

class PregCodeField(CodeField):
  'Field for Pregnancy codes.'
  @classmethod
  def expectations(self):
    'These are all the codes related to pregnancy.'
    return ['GS', 'MU', 'HD', 'RM', 'OL', 'YG', 'NR', 'TO', 'HW', 'NT', 'NT', 'NH', 'KX', 'YJ', 'LZ']

class PrevPregField(PregCodeField):
  'Field for Previous pregnancy codes.'
  @classmethod
  def expectations(self):
    'Codes associated with previous pregnancy.'
    return ['GS', 'MU', 'HD', 'RM']

class SymptomCodeField(CodeField):
  'Field for codes associated with symptoms.'
  @classmethod
  def expectations(self):
    'These are the codes associated with symptoms.'
    return ['AF', 'CH', 'CI', 'CM', 'IB', 'DB', 'DI', 'DS', 'FE', 'FP', 'HY', 'JA', 'MA', 'NP', 'NS',
            'OE', 'PC', 'RB', 'SA', 'SB', 'VO']

class RedSymptomCodeField(SymptomCodeField):
  'Field for codes associated with symptoms.'
  @classmethod
  def expectations(self):
    'These are the codes in red alerts.'
    return ['AP', 'CO', 'HE', 'LA', 'MC', 'PA', 'PS', 'SC', 'SL', 'UN']

class LocationField(CodeField):
  'Field for codes that communicate locations.'
  @classmethod
  def expectations(self):
    'The codes for RED alerts.'
    return ['CL', 'HO', 'HP', 'OR']

class FloatedField(CodeField):
  'Field for codes that carry fractional numbers with decimal points.'
  @classmethod
  def is_legal(self, fld):
    'Basically a regex.'
    return [] if re.match(r'\w+\d+(\.\d+)?', fld) else 'bad_floated_field'

class NumberedField(CodeField):
  'Field for codes that carry whole numbers.'
  @classmethod
  def is_legal(self, fld):
    'Basically a regex.'
    return [] if re.match(r'\w+\d+', fld) else 'bad_numbered_field'

class HeightField(NumberedField):
  'Field for height codes.'
  pass

class WeightField(FloatedField):
  'Field for weight codes.'
  pass

#TODO:  DB value for 2-long expectations() should be Bool.
class ToiletField(CodeField):
  'Field for codes concerning toilets.'
  @classmethod
  def expectations(self):
    'Toilet or no toilet?'
    return ['TO', 'NT']

class HandwashField(CodeField):
  'Field for codes concerning handwwashing basic.'
  @classmethod
  def expectations(self):
    'Hand-wash or no hand-wash?'
    return ['HW', 'NH']

class PhoneBasedIDField(IDField):
  'The alternative ID field, incorporating phone number.'
  @classmethod
  def is_legal(self, fld):
    'Basic regex.'
    return [] if re.match(r'0\d{15}', fld) else 'bad_phone_id'

class ANCField(NumberedField):
  'Ante-Natal Care visit number is a ... number.'
  @classmethod
  def is_legal(self, fld):
    'Matches the code, not insisting on the string that precedes the number.'
    return [] if re.match(r'\w+\d', fld) else 'anc_code'

class PNCField(NumberedField):
  'Post-Natal Care visit number is a ... number.'
  @classmethod
  def is_legal(self, fld):
    'Matches the code, not insisting on the string that precedes the number.'
    return [] if re.match(r'\w+\d', fld) else 'pnc_code'

class NBCField(NumberedField):
  'New-Born Care visit number is a ... number.'
  @classmethod
  def is_legal(self, fld):
    'Matches the code, not insisting on the string that precedes the number.'
    return [] if re.match(r'\w+\d', fld) else 'nbc_code'

  @classmethod
  def expectations(self):
    'Pre-enforcing the discipline that `is_legal` does not enforce.'
    return ['EBF', 'NB', 'PH', 'NBC1', 'NBC2', 'NBC3', 'NBC4', 'NBC5']

class GenderField(CodeField):
  'Gender is a a code.'
  @classmethod
  def expectations(self):
    'Boy or girl?'
    return ['BO', 'GI']

class BreastFeedField(NBCField):
  'Breast-feeding code has new-born care fields.'
  @classmethod
  def expectations(self):
    'The accepted codes. May be booleanisable.'
    return ['EBF', 'NB']

class InterventionField(CodeField):
  'Field for general interventions.'
  @classmethod
  def expectations(self):
    'Intervention codes.'
    return ['PR', 'AA', 'AL', 'AT', 'NA']

class NBCInterventionField(InterventionField):
  'New-born care intervention field.'
  pass

class HealthStatusField(CodeField):
  'General health status field.'
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
  @classmethod
  def expectations(self):
    'The vaccination completion codes.'
    return ['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'VC', 'VI', 'NV']

class VaccinationCompletionField(VaccinationField):
  'Vaccination Completion fields.'
  @classmethod
  def expectations(self):
    'Levels of vaccination checkpoints.'
    return ['VC', 'VI', 'NV']

class MUACField(FloatedField):
  'MUAC is a decimal float.'
  @classmethod
  def is_legal(self, fld):
    'Regex alert.'
    return [] if re.match(r'MUAC\d+(\.\d+)', fld) else 'bad_muac_code'

class DeathField(CodeField):
  'Field for describing death codes.'
  @classmethod
  def expectations(self):
    'Expected death codes.'
    return ['ND', 'CD', 'MD']

class ThouMsgError:
  'Small exception class.'
  def __init__(self, errors):
    self.errors     = errors

class ThouMessage:
  '''Base class describing the standard RapidSMS 1000 Days message.'''
  fields  = []
  created = False

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
  def parse(msg):
    code, rem = ThouMessage.pull_code(msg.strip())
    klass     = UnknownMessage
    try:
      klass     = MSG_ASSOC[code.upper()]
    except KeyError:
      pass
    return klass.process(klass, code, rem)

  # “Private”
  @staticmethod
  def process(klass, cod, msg):
    errors  = []
    fobs    = []
    etc     = msg
    for fld in klass.fields:
      try:
        if type(fld) == type((1, 2)):
          cur, err, etc  = fld[0].pull(fld[0], cod, etc, fld[1])
          errors.extend([(e, fld) for e in err])
        else:
          cur, err, etc  = fld.pull(fld, cod, etc)
          errors.extend([(e, fld) for e in err])
        fobs.append(cur)
      except Exception, err:
        errors.append((str(err), fld))
    if etc.strip():
      errors.append('Superfluous text: "%s"' % (etc.strip(),))
    return klass(cod, fobs, errors)

  def __init__(self, cod, fobs, errs):
    self.code     = cod
    self.errors   = errs
    if self.errors: raise ThouMsgError(self.errors)
    semerrors     = self.semantics_check()
    if semerrors: raise ThouMsgError(semerrors)
    def as_hash(p, n):
      p[n.__class__.subname()] = n
      return p
    self.entries  = reduce(as_hash, fobs, {})

  @abstractmethod
  def semantics_check(self):
    return ['Ariko Didier! I told you ThouMessage#semantics_check is abstract.']  # Hey, why doesn’t 'abstract' scream out? TODO.

class UnknownMessage(ThouMessage):
  '''To the Unknown Message.
Since every message has to be successfully parsed as a Message object, this is the one in the event that none other matches.'''
  pass

class PregMessage(ThouMessage):
  'Pregnancy message.'
  fields  = [IDField, DateField, DateField, GravidityField, ParityField,
              (PregCodeField, True),
              (SymptomCodeField, True),
             LocationField, WeightField, ToiletField, HandwashField]

class RefMessage(ThouMessage):
  'Referral message.'
  fields  = [PhoneBasedIDField]

class ANCMessage(ThouMessage):
  'Ante-natal care visit message.'
  fields  = [IDField, DateField, ANCField,
             (SymptomCodeField, True),
             LocationField, WeightField]

class DepMessage(ThouMessage):
  'Departure message.'
  fields  = [IDField, NumberField, DateField]

class RiskMessage(ThouMessage):
  'Risk report message.'
  fields  = [IDField,
             (SymptomCodeField, True),
             LocationField, WeightField]

class RedMessage(ThouMessage):
  'Red alert message.'
  fields  = [(RedSymptomCodeField, True), LocationField]

class BirMessage(ThouMessage):
  'Birth message.'
  fields  = [IDField, NumberField, DateField, GenderField,
             (SymptomCodeField, True),
             LocationField, BreastFeedField, WeightField]

class ChildMessage(ThouMessage):
  'Child message.'
  fields  = [IDField, NumberField, DateField, VaccinationField, VaccinationCompletionField,
             (SymptomCodeField, True),
             LocationField, WeightField, MUACField]

class DeathMessage(ThouMessage):
  'Death message.'
  fields  = [IDField, NumberField, DateField, LocationField, DeathField]

class ResultMessage(ThouMessage):
  'Result message.'
  fields  = [IDField,
             (SymptomCodeField, True),
             LocationField, InterventionField, MotherHealthStatusField]

class RedResultMessage(ThouMessage):
  'Red alert result message.'
  fields  = [IDField, DateField,
             (SymptomCodeField, True),
             LocationField, InterventionField, MotherHealthStatusField]

class NBCMessage(ThouMessage):
  'New-born care message.'
  fields  = [IDField, NumberField, NBCField, DateField,
             (SymptomCodeField, True),
             BreastFeedField, NBCInterventionField, NewbornHealthStatusField]

class PNCMessage(ThouMessage):
  'Post-natal care message.'
  fields  = [IDField, PNCField, DateField,
             (SymptomCodeField, True),
             InterventionField, MotherHealthStatusField]

# Testing field. Takes any of my names.
class TextField(ThouField):
  'What I call TextField is really a RevNameField.'
  @classmethod
  def expectations(self):
    'Only my names are legal here.'
    return ['Revence', 'Kato', 'Kalibwani']

# Testing message.
class RevMessage(ThouMessage):
  'Testing message. Takes any number of legal fields.'
  fields  = [(TextField, True)]

MSG_ASSOC = {
  'PRE':  PregMessage,
  'REF':  RefMessage,
  'ANC':  ANCMessage,
  'DEP':  DepMessage,
  'RISK': RiskMessage,
  'RED':  RedMessage,
  'BIR':  BirMessage,
  'CHI':  ChildMessage,
  'DTH':  DeathMessage,
  'RES':  ResultMessage,
  'RAR':  RedResultMessage,
  'NBC':  NBCMessage,
  'PNC':  PNCMessage,

  'REV':  RevMessage,
}
