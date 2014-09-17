Ectomorph: The Lanky ORM
============

A thin translator between your Python and your SQL.

Philosophy: SomeSQL
----------
First the data, then the schema. (Storage similar to NoSQL.)
Code is not data. (Object names do not determine table names by default.)
There is nothing wrong with SQL. (All ORM abstractions can be replaced by SQL.)
There is something wrong with too much SQL. (It is “liturgical”; its use should signal solemnity.)

Examples
--------

    from orm import *
    from os import getenv
    
    ORM.connect(dbname = 'postgres', user = 'postgres')
    for run in range(int(getenv('ORMTIMES', '5'))):
      print 'Stored Item ID:', ORM.store('them', {'title':'In the Silence', 'artist':'Hillsong United', 'album':'People Just Like Us'})
  
    them  = ORM.query('them',
      hooks = {'describe': lambda x, _: '"%s", from \'%s\' by %s' % (x['title'], x['album'], x['artist'])}
    )
    print them.query
    for it in them.list():
      print ('%2d' % (it['indexcol'], )), it['describe']

The above can be executed thus:

    $ env ORMTIMES=1 python test.py

It prints this:

    Item ID: 1
    SELECT * FROM them
     1 "In the Silence", from 'People Just Like Us' by Hillsong United

Features
--------
- SomeSQL approach: language abstractions and data structures over a transparent and accessible SQL database.
- Storing Python dictionary objects into a relational table structure.
- Auto-adjusting of schema when stored object extends table structure.
- Stored values optionally carry extra information to facilitate table alteration, even migration (presumed idempotent).
- Index column (`indexcol SERIAL NOT NULL`) for each table; returned from every successful store.
- Default PostgreSQL adapter.
- Support for Python data types (`int`, `float`, `Decimal`, `str`, `unicode`, `datetime.datetime`, `datetime.time`, `datetime.timedelta`).
- Support for idempotent migrations, as part of code. A code-independent schema is not always desirable, manageable, superior, or even realistic.
- Lazy queries.
- Purely-functional query interface. (Not very Pythonic; but then, neither is civilised DB access.)
- Data access hooks enable simple templates (and correspondingly more-complex views—as it should be).
- Independence between code structure and database structure (unlike Django and ActiveRecord, for example).
- Support for Django ORM’s data access protocol (`__getitem__`).
- Support for named (“server-side”) cursors and query-optimisation hooks.
- Batch inserts (`COPY FROM`, `COPY TO`) with extensible interface.

TODO:
----
- Ensure that ORM implements full relational algebra (5 primitives).
- Ensure that ORM implements full monoid algebra.
- Ensure that ORM implements co-extensive functor algebra.
- Ensure that ORM implements traditional functional morphisms.
- Deep object storage.
- datetime.timedelta
- grep -r TODO .
