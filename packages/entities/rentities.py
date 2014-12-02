from processor import *

class IndangamuntuEntity(UniqueEntity):
  unique  = ['indangamuntu']

class IndangamuntuRelativeEntity(IndangamuntuEntity):
  unique  = ['indangamuntu', 'number']

class ANCVisit(UniqueEntity):
  table       = 'rw_ancvisits'
  unique      = ['indangamuntu', 'anc_visit']
  belongs_to  = lambda _: Pregnancy

class PNCVisit(UniqueEntity):
  table       = 'rw_pncvisits'
  unique      = ['indangamuntu', 'pnc_visit']
  belongs_to  = lambda _: Pregnancy

class Pregnancy(IndangamuntuEntity):
  table       = 'rw_pregnancies'
  unique      = ['indangamuntu', 'lmp']
  belongs_to  = lambda _: Mother
  has_some    = lambda _: [ANCVisit, Child, PNCVisit]

class Mother(IndangamuntuEntity):
  table       = 'rw_mothers'
  has_some    = lambda _: [Pregnancy]

class Child(IndangamuntuRelativeEntity):
  table       = 'rw_children'
  belongs_to  = lambda _: Pregnancy

class Death(IndangamuntuRelativeEntity):
  table       = 'rw_deaths'
  # belongs_to  = lambda _: [Mother, Child]
