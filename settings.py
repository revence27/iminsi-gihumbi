import os

DBHOST = 'localhost'
DBPORT = 5432
DBNAME = 'thousanddays'
DBUSER = 'thousanddays'
DBPASSWORD = 'thousanddays'

WEBAPP          = 'iminsigihumbi'
GESTATION       = 270
BMI_MIN         = 19
BMI_MAX         = 25
MIN_WEIGHT      = 45
MAX_WEIGHT      = 65
SALT_STRENGTH   = 2


LOCATION_INFO = [
			('sector_pk',            'Sector'),
			('cell_pk',            'Cell'),
			('village_pk',            'Village'),
		]

PATIENT_DETAILS = [
			('patient_id','Patient/Mother ID'),	
			('reporter_phone','Reporter Phone'),
		  ] + LOCATION_INFO

INDEXED_VALS = {'location': [('province_pk', 'indexcol', 'chws__province', 'Province'),
					('district_pk', 'indexcol',  'chws__district', 'District'),
					('health_center_pk', 'indexcol', 'chws__healthcentre', 'HealthCentre'),
					('sector_pk',  'indexcol',   'chws__sector',        'Sector'),
					('cell_pk',     'indexcol',  'chws__cell' ,     'Cell'),
					('village_pk',  'indexcol',  'chws__village'  ,       'Village'),
			     ]
		}

NO_RISK = {'attrs': 
			[('gs_bool IS NOT NULL', 'Previous Obstetric Surgery'), 
			 ('mu_bool IS NOT NULL', 'Multiples'),
			 ('hd_bool IS NOT NULL', 'Previous Home Delivery'), 
			 ('rm_bool IS NOT NULL', 'Repetiive Miscarriage'),
			 ('ol_bool IS NOT NULL', 'Old Age (Over 35)'),
			 ('yg_bool IS NOT NULL', 'Young Age (Under 18)'),
			 ('kx_bool IS NOT NULL', 'Previous Convulsion'),
			 ('yj_bool IS NOT NULL', 'Previous Serious Conditions'),
			 ('lz_bool IS NOT NULL', 'Previous Hemorrhaging/Bleeding'),
			], 
	'query_str': 
		'gs_bool IS NULL AND mu_bool IS NULL AND hd_bool IS NULL AND rm_bool IS NULL AND ol_bool IS NULL AND yg_bool IS NULL AND kx_bool IS NULL AND yj_bool IS NULL AND lz_bool IS NULL AND vo_bool IS NULL AND pc_bool IS NULL AND oe_bool IS NULL AND ns_bool IS NULL AND ma_bool IS NULL AND ja_bool IS NULL AND fp_bool IS NULL AND fe_bool IS NULL AND ds_bool IS NULL AND di_bool IS NULL AND sa_bool IS NULL AND rb_bool IS NULL AND hy_bool IS NULL AND ch_bool IS NULL AND af_bool IS NULL'}

RISK = { 'attrs': 
			[('vo_bool IS NOT NULL', 'Vomiting'),
			 ('pc_bool IS NOT NULL', 'Pneumonia'),
			 ('oe_bool IS NOT NULL', 'Oedema'),
			 ('ns_bool IS NOT NULL', 'Neck Stiffness'),
			 ('ma_bool IS NOT NULL', 'Malaria'),
			 ('ja_bool IS NOT NULL', 'Jaundice'),
			 ('fp_bool IS NOT NULL', 'Fraccid Paralysis'),
			 ('fe_bool IS NOT NULL', 'Fever'),
			 ('ds_bool IS NOT NULL', 'Chronic Disease'),
			 ('di_bool IS NOT NULL', 'Diarrhea'),
			 ('sa_bool IS NOT NULL', 'Severe Anemia'),
			 ('rb_bool IS NOT NULL', 'Rapid Breathing'),
			 ('hy_bool IS NOT NULL', 'Hypothermia'),
			 ('ch_bool IS NOT NULL', 'Coughing'),
			 ('af_bool IS NOT NULL', 'Abnormal Fontinel'),
			], 
	'query_str': 
		'(vo_bool IS NOT NULL OR pc_bool IS NOT NULL OR oe_bool IS NOT NULL OR ns_bool IS NOT NULL OR ma_bool IS NOT NULL OR ja_bool IS NOT NULL OR fp_bool IS NOT NULL OR fe_bool IS NOT NULL OR ds_bool IS NOT NULL OR di_bool IS NOT NULL OR sa_bool IS NOT NULL OR rb_bool IS NOT NULL OR hy_bool IS NOT NULL OR ch_bool IS NOT NULL OR af_bool IS NOT NULL) AND NOT (gs_bool IS NOT NULL OR mu_bool IS NOT NULL OR hd_bool IS NOT NULL OR rm_bool IS NOT NULL OR ol_bool IS NOT NULL OR yg_bool IS NOT NULL OR kx_bool IS NOT NULL OR yj_bool IS NOT NULL OR lz_bool IS NOT NULL)'}

HIGH_RISK = { 'attrs': 
			[('gs_bool IS NOT NULL', 'Previous Obstetric Surgery'), 
			 ('mu_bool IS NOT NULL', 'Multiples'),
			 ('hd_bool IS NOT NULL', 'Previous Home Delivery'), 
			 ('rm_bool IS NOT NULL', 'Repetitive Miscarriage'),
			 ('ol_bool IS NOT NULL', 'Old Age (Over 35)'),
			 ('yg_bool IS NOT NULL', 'Young Age (Under 18)'),
			 ('kx_bool IS NOT NULL', 'Previous Convulsion'),
			 ('yj_bool IS NOT NULL', 'Previous Serious Conditions'),
			 ('lz_bool IS NOT NULL', 'Previous Hemorrhaging/Bleeding'),
			], 
		'query_str': 
		'gs_bool IS NOT NULL OR mu_bool IS NOT NULL OR hd_bool IS NOT NULL OR rm_bool IS NOT NULL OR ol_bool IS NOT NULL OR yg_bool IS NOT NULL OR kx_bool IS NOT NULL OR yj_bool IS NOT NULL OR lz_bool IS NOT NULL'

	}

PREGNANCY_DATA = [
      ('lmp', 'LMP'),
      ('gravity_float', 'Gravidity'),
      ('parity_float', 'Parity'),
      ('mother_weight_float', 'Weight'),
      ('mother_height_float', 'Height'),
      ('report_date', 'Submission Date'),
    ]


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


