import entities
from messages import rmessages

ASSOCIATIONS = {
  'PRE':  (rmessages.PregMessage,
    {'initialises': [entities.Mother, entities.Pregnancy]}
  ),
  'REF':  (rmessages.RefMessage,
    {'initialises': []}
  ),
  'ANC':  (rmessages.ANCMessage,
    {'initialises': [entities.Mother, entities.ANCVisit]}
  ),
  'DEP':  (rmessages.DepMessage,
    {'initialises': [entities.Mother]}
  ),
  'RISK': (rmessages.RiskMessage,
    {'initialises': [entities.Mother]}
  ),
  'RED':  (rmessages.RedMessage,
    {'initialises': []}
  ),
  'BIR':  (rmessages.BirMessage,
    {'initialises': [entities.Mother, entities.Pregnancy, entities.Child]}
  ),
  'CHI':  (rmessages.ChildMessage,
    {'initialises': [entities.Mother, entities.Child]}
  ),
  'DTH':  (rmessages.DeathMessage,
    {'initialises': [entities.Mother, entities.Child, entities.Death]}
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
    {'initialises': [entities.PNCVisit]}
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
