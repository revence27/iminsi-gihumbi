import os

WEBAPP          = 'iminsigihumbi'
GESTATION       = 270
BMI_MIN         = 19
BMI_MAX         = 25
MIN_WEIGHT      = 45
MAX_WEIGHT      = 65
SALT_STRENGTH   = 2

APP_DATA  = {
  'indicators'  : [
    {'name':'Reporting',
      'title' : 'Reports and Reporters',
      'ref'   : 'reporting'},
    {'name':'Pregnant Women',
      'ref':'mothers'},
    {'name':'Pregnancies',
      'ref':'pregnancies'},
    {'name':'Babies',
      'ref':'babies'},
    {'name':'Expected Deliveries',
      'ref':'delivs'},
    # {'name':'Red Alerts',
    #   'ref':'alerts'},
    {'name':'Admins',
      'ref':'admins'},
    # {'name':'Sanitation',
    #   'title' : 'Toilets and Water',
    #   'ref'   : 'sanitation'}
  ],
  'rindicators'  : [
    {'name':'Ante-Natal',
      'ref':'anc'},
    {'name':'Birth Reports',
      'ref':'birthreport'},
    {'name':'Pregnancies',
      'ref':'pregnancy'},
    {'name':'Deliveries',
      'ref':'delivery'},
    {'name':'New-Born Care',
      'ref':'nbc'},
    {'name':'Vaccinations',
      'ref':'vaccination'},
    {'name':'Nutrition',
      'ref':'nutrition'},
    {'name':'Child Health',
      'ref':'childhealth'},
    {'name':'CCM',
      'title' : 'Community Case Management',
      'ref'   : 'ccm'},
    {'name':'PNC',
      'title' : 'Post-Natal Care',
      'ref'   : 'pnc'},
    {'name':'Red Alerts',
      'title' : 'Red Alerts',
      'ref'   : 'redalert'},
    {'name':'Death',
      'title' : 'Death Reports',
      'ref'   : 'death'}
  ]
}


