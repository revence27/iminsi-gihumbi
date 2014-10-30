from ectomorph import orm
import json
import sys

GENDERS = ['boy', 'girl']
PROBS   = ['stunting', 'wasting', 'underweight']
HINFO_MIGRATIONS = [
  ('month', 1),
  ('sd2neg', 1.0),
  ('boy', True),
  ('problem', '|'.join(PROBS))
]

orm.ORM.connect(dbname  = 'thousanddays', user = 'thousanddays', host = 'localhost', password = 'thousanddays')

def handle_file(gdr, prob, f):
  with open(f) as fch:
    gat = json.load(fch)
    for mth in gat:
      dat = {
        'month'   : int(mth['Month']),
        'sd2neg'  : float(mth['SD2neg']),
        'boy'     : gdr == 'boy',
        'problem' : prob
      }
      print orm.ORM.store('ig_deviations', dat, migrations = HINFO_MIGRATIONS)

def rwabugiri_main(argv):
  if len(argv) < 4:
    sys.stderr.write('%s %s %s datafile.json\n' % (argv[0], '|'.join(GENDERS), '|'.join(PROBS)))
    return 1
  _, gdr, attr, fch = argv
  if not (gdr in GENDERS):
    sys.stderr.write('%s\n' % ('|'.join(GENDERS), ))
    return 2
  if not (attr in PROBS):
    sys.stderr.write('%s\n' % ('|'.join(PROBS), ))
    return 3
  ans = handle_file(gdr, attr, fch)
  return ans

if __name__ == '__main__':
  bottom  = sys.exit(rwabugiri_main(sys.argv))

