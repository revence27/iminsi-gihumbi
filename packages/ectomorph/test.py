#!  /usr/bin/env python

from orm import *
from os import getenv

ORM.connect(dbname = 'revence', user = 'revence')
for run in range(int(getenv('ORMTIMES', '5'))):
  print 'Item ID:', ORM.store('them', {'title':'In the Silence', 'artist':'Hillsong United', 'album':'People Just Like Us'})

them  = ORM.query('them',
  hooks = {'describe': lambda x, _: '"%s", from \'%s\' by %s' % (x['title'], x['album'], x['artist'])}
)
print them.query
for it in them.list():
  print ('%2d' % (it['indexcol'], )), it['describe']
