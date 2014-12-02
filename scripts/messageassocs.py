from entities import rentities
from messages import rmessages

ASSOCIATIONS = {
  'PRE':  (rmessages.PregMessage,
    {'initialises': [rentities.Mother, rentities.Pregnancy]}
  ),
  'REF':  (rmessages.RefMessage,
    {'initialises': []}
  ),
  'ANC':  (rmessages.ANCMessage,
    {'initialises': [rentities.Mother, rentities.ANCVisit]}
  ),
  'DEP':  (rmessages.DepMessage,
    {'initialises': [rentities.Mother]}
  ),
  'RISK': (rmessages.RiskMessage,
    {'initialises': [rentities.Mother]}
  ),
  'RED':  (rmessages.RedMessage,
    {'initialises': []}
  ),
  'BIR':  (rmessages.BirMessage,
    {'initialises': [rentities.Mother, rentities.Pregnancy, rentities.Child]}
  ),
  'CHI':  (rmessages.ChildMessage,
    {'initialises': [rentities.Mother, rentities.Child]}
  ),
  'DTH':  (rmessages.DeathMessage,
    {'initialises': [rentities.Mother, rentities.Child, rentities.Death]}
  ),
  'RES':  (rmessages.ResultMessage,
    {'initialises': []}
  ),
  'RAR':  (rmessages.RedResultMessage,
    {'initialises': []}
  ),
  'NBC':  (rmessages.NBCMessage,
    {'initialises': []}
  ),
  'PNC':  (rmessages.PNCMessage,
    {'initialises': [rentities.PNCVisit]}
  ),
  'CCM':  (rmessages.CCMMessage,
    {'initialises': []}
  ),
  'CMR':  (rmessages.CMRMessage,
    {'initialises': []}
  ),
  'CBN':  (rmessages.CBNMessage,
    {'initialises': []}
  )
}
