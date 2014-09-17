# encoding: utf-8
# vim: expandtab ts=2

from abc import ABCMeta, abstractmethod
import re
import psycopg2

class ThouField:
  '''Class defining the field of a "RapidSMS 1000 Days" message field.
Has the ability to parse itself from a message string, conditionally pulling several of itself before giving up.
It also supplies contextual information about its unsuccessful parsing.'''
  # __metaclass__   = ABCMeta

  column_name = None

  @staticmethod
  def pull(self, cod, txt, many = False):
    '''A field will process thestring `txt` to parse of a valid object of its class (passed in as `self` and linked to the SMS code passed in as `cod`).
Error cases are communicated as single-token error codes, strings that should be short, and unique for every error case.
Returns a triple: the resulting Message object, the array of error codes, and the part of `txt` that has not been consumed to produce the Message object.'''
    got = []
    etc = txt
    err = []
    while True:
      if not etc:
        if not got:
          err.append(('%s_missing_fields' % (cod,)).lower())
        break
      prv   = etc
      stuff = re.split(r'\s+', etc, 1)
      if len(stuff) < 2:
        stuff.append('')
      p1, etc = stuff
      ans     = p1.strip()
      etc     = etc.strip()
      if self.expected(ans):
        errs  = self.is_legal(ans)
        if errs:
          if type(errs) == type([]):
            err.extend(errs)
          else:
            err.append(errs)
        else:
          got.append(ans)
      else:
        if many and got:
          etc = prv
        else:
          err.append(('%s_invalid_code_field_%s' % (cod, self.subname())).lower())
        break
        # err.append("Invalid code (expected %s; not %s)" % (', '.join(self.expectations() or ['nothing']), ans))
      if not many: break
    return (self(got, many), err, etc)

  @classmethod
  @abstractmethod
  def is_legal(self, fld):
    'This method is to be extended to restrict fields, in the event that the `expectations` mechanism is insufficient.'
    pass

  @classmethod
  @abstractmethod
  def expectations(self):
    'This method is to be extended to restrict fields to certain pre-determined codes.'
    return []

  @classmethod
  def expected(self, fld):
    '''This method is to be extended if the `expectations` mechanism is almost sufficient, but requires some elaborate validation.
This default one works best on the simple codes that we have, not every possible thing.'''
    exps  = self.expectations()
    if not exps: return True
    for exp in exps:
      if exp.lower() == fld.lower():
        return True
    return False

  @classmethod
  def fixed_for_db(self, val):
    '''Field-level specification of the necessary escapes for sanitising the data for SQL.
TODO: This only passes because we are using simple, plain codes in testing.'''
    if type(val) == type(None):
      return 'NULL'
    if type(val) in [type(x) for x in [1, 1.0]]:
      return str(val)
    if val in self.expectations():
      return self.fixed_for_db(self.expectations().index(val))
    if type(val) == type(''):
      return str("'%s'" % (val,)) # TODO: Proper SQL escapes, valid for current engine.

  @classmethod
  def dbtype(self, it = None):
    '''Field-level specificiation of the SQL data type to give to the database column that will hold the data held by this field.
TODO: At present, every field is supposed to be a TEXT. This is clearly false in the case of dates, for instance.'''
    return 'TEXT'    # TODO. Force them to adapt this per ThouField?

  @classmethod
  def dbvalue(self, it, kasa):
    'Returns the value if `it` escaped with the database cursor `kasa`.'
    return kasa.mogrify('%s', (it,))

  @classmethod
  def default_dbvalue(self):
    '''Returns the string that represents the default DB value.
TODO: Currently gives no heed to the opinions of the field itself.'''
    # TODO: Find the callers and re-educate them.
    # return self.fixed_for_db(self.default_value)
    return self.fixed_for_db(None)

  @classmethod
  def subname(self):
    'Returns the name of this field as it would be used in composing a column name.'
    return self.column_name or str(self).split('.')[-1].lower()

  @classmethod
  def display(self):
    'Returns the descriptive name of this field (useful for displaying database columns without listing the unsigtly column name).'
    return re.sub(r'field$', '', str(self).split('.')[-1].lower())

  def __init__(self, val, many):
    'Initialise the field and its associated value `val`, specifying whether it is one of `many` associated as a group with the message.'
    self.working_value  = val
    self.several_fields = many
