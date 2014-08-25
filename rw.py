#!  /usr/bin/env python
# encoding: utf-8
# vim: ts=2 expandtab

import os, sys

def rmain(argv):
  if len(argv) < 2:
    sys.stderr.write('%s operation [args]\n' % (argv[0], ))
    return 1
  elmod = __import__(argv[1])
  yes   = True
  try:
    yes = elmod.rwabugiri_init(argv[1:])
  except AttributeError:
    # sys.stderr.write('The Rwabugiri component “%s” lacks rwabugiri_init\n' % (argv[1], ))
    pass
  if yes:
    try:
      ans = elmod.rwabugiri_main(argv[1:])
      try:
        elmod.rwabugiri_clean()
      except AttributeError:
        pass
      return ans
    except AttributeError, e:
      sys.stderr.write('The Rwabugiri component “%s” lacks rwabugiri_main\n' % (argv[1], ))
      raise e
  return 2

if __name__ == '__main__':
  for sp in ['scripts', 'packages'] + [x for x in os.getenv('RWABUGIRI_PATHS', '').split(':') if x]:
    sys.path.insert(0, os.path.join(os.getcwd(), sp))
  sys.exit(rmain(sys.argv))
