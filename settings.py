import os

DBHOST = 'localhost'
DBPORT = 5432
DBNAME = 'thousanddays'
DBUSER = 'thousanddays'
DBPASSWORD = 'thousanddays'

WEBAPP          = 'iminsigihumbi'
GESTATION       = 270
NBC_GESTATION   = 28
PNC_GESTATION   = 42
ANC_GAP         = 90
BMI_MIN         = 19
BMI_MAX         = 25
MIN_WEIGHT      = 45
MAX_WEIGHT      = 65
SALT_STRENGTH   = 2
AUTH_HOME       = '/dashboards/home'

# ref : (table, sort column)
# Default sort column (None) is: report_date
EXPORT_KEYS     = {
  '_'       : ('thousanddays_reports', None),
  'predash' : ('pre_table', None),
  'mothers' : ('ig_mothers', 'indexcol')
}

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
    #{'name':'Admins',
    #  'ref':'admins'},
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
