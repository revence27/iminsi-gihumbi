import os, sys

def rwabugiri_main(argv):
  pcks  = os.path.join(os.getcwd(), 'packages')
  env   = os.environ
  env.update({'PYTHONPATH': pcks})
  argl  = argv
  argl.append(env)
  return os.execlpe('python', *argl)

if __name__ == '__main__':
  bottom  = sys.exit(rwabugiri_main(sys.argv))

