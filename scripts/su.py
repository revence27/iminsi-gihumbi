from ectomorph import orm
import getpass
import settings
import sha
import sys
import random

orm.ORM.connect(dbname  = 'thousanddays', user = 'thousanddays', host = 'localhost', password = 'thousanddays')

MIGS  = [
  ('address',           'you@example.com'),
  ('province_pk',       0),
  ('district_pk',       0),
  ('health_center_pk',  0)
]

def record_su(email, pwd):
  gat = orm.ORM.query('ig_admins', {'address = %s': email}, migrations = MIGS)
  if gat.count() > 0:
    for it in gat.list():
      orm.ORM.delete('ig_admins', it['indexcol'])
    return record_su(email, pwd)
  salt  = ''.join([str(random.random()) for _ in range(settings.SALT_STRENGTH)])
  sha1  = sha.sha('%s%s' % (salt, pwd)).hexdigest()
  orm.ORM.store('ig_admins', {'address': email, 'salt': salt, 'sha1_pass': sha1}, migrations = MIGS)
  return 0

def rwabugiri_main(argv):
  if len(argv) < 2:
    sys.stderr.write('%s superuseremail\n' % (argv[0], ))
    return 1
  ans = record_su(argv[1], getpass.getpass("%s's Password: " % (argv[1], )))
  return ans

if __name__ == '__main__':
  bottom  = sys.exit(rwabugiri_main(sys.argv))

