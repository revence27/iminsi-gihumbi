import os

WEBAPP          = 'miisigihumbi'
GESTATION       = 270
BMI_MIN         = 19
BMI_MAX         = 25
MIN_WEIGHT      = 45
MAX_WEIGHT      = 65

APP_DATA  = {
  'indicators'  : [
    {'name':'Ante-Natal',
      'ref':'anc'},
    {'name':'Pregnancies',
      'ref':'pregnancy'},
    {'name':'Deliveries',
      'ref':'delivery'},
    {'name':'New-Borns',
      'ref':'nbc'},
    {'name':'Vaccinations',
      'ref':'vaccination'},
    {'name':'Nutrition',
      'ref':'nutrition'},
    {'name':'Child Health',
      'ref':'childhealth'},
    {'name':'CCM',
      'title' : 'Community Case Management',
      'ref'   : 'ccm'}
  ]
}


