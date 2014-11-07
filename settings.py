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
AUTH_HOME       = '/dashboards/home'

# ref : (table, sort column)
# Default sort column (None) is: report_date
EXPORT_KEYS     = {
  '_'       : ('thousanddays_reports', None),
  'predash' : ('pre_table', None),
  'mothers' : ('ig_mothers', 'indexcol')
}

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
			[('gs_bool IS NULL', 'Previous Obstetric Surgery'), 
			 ('mu_bool IS NULL', 'Multiples'),
			 ('hd_bool IS NULL', 'Previous Home Delivery'), 
			 ('rm_bool IS NULL', 'Repetiive Miscarriage'),
			 ('ol_bool IS NULL', 'Old Age (Over 35)'),
			 ('yg_bool IS NULL', 'Young Age (Under 18)'),
			 ('kx_bool IS NULL', 'Previous Convulsion'),
			 ('yj_bool IS NULL', 'Previous Serious Conditions'),
			 ('lz_bool IS NULL', 'Previous Hemorrhaging/Bleeding'),
			 ('vo_bool IS NULL', 'Vomiting'),
			 ('pc_bool IS NULL', 'Pneumonia'),
			 ('oe_bool IS NULL', 'Oedema'),
			 ('ns_bool IS NULL', 'Neck Stiffness'),
			 ('ma_bool IS NULL', 'Malaria'),
			 ('ja_bool IS NULL', 'Jaundice'),
			 ('fp_bool IS NULL', 'Fraccid Paralysis'),
			 ('fe_bool IS NULL', 'Fever'),
			 ('ds_bool IS NULL', 'Chronic Disease'),
			 ('di_bool IS NULL', 'Diarrhea'),
			 ('sa_bool IS NULL', 'Severe Anemia'),
			 ('rb_bool IS NULL', 'Rapid Breathing'),
			 ('hy_bool IS NULL', 'Hypothermia'),
			 ('ch_bool IS NULL', 'Coughing'),
			 ('af_bool IS NULL', 'Abnormal Fontinel'),
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

ANC = { 
	'attrs': [
			('anc2_bool IS NOT NULL', 'ANC2'),
			('anc3_bool IS NOT NULL', 'ANC3'),
			('anc4_bool IS NOT NULL', 'ANC4'),
		],

	'query_str':[]

	}


CBN_DATA = {
		'attrs': [
        (u'nb_bool IS NOT NULL', u'Not Breast-feeding'),
        (u'ebf_bool IS NOT NULL', u'Exclusive Breast-feeding'),
        (u'cbf_bool IS NOT NULL', u'Complementary Breast-feeding'),
        (u'cbf_bool IS NULL AND ebf_bool IS NULL AND nb_bool IS NULL', u'Unknown Breast-feeding Status'),
        (u'stunting_bool IS NOT NULL', u'Stunting'),
        (u'underweight_bool IS NOT NULL', u'Underweight'),
        (u'wasting_bool IS NOT NULL', u'Wasting')
					],

		'query_str': '((cbf_bool IS NOT NULL) OR (ebf_bool IS NOT NULL) OR (nb_bool IS NOT NULL))'
		}


NBC_DATA = {
		'cols' : [
				      ('lmp AS dob', 'LMP'),
				      ('report_date', 'Submission Date'),
				    ],

		'NO_RISK': { 	'attrs': [
						('sb_bool IS NULL', 'Stillborn'),
						('af_bool IS NULL', 'Abnormal Fontinel'),
						('ci_bool IS NULL', 'Cord Infection'),
						('cm_bool IS NULL', 'Congenital Malformation'),
						('nb_bool IS NULL', 'Not Breastfeeding'),
						('ja_bool IS NULL', 'Jaundice'),
						('rb_bool IS NULL', 'Rapid Breathing'),
						('ns_bool IS NULL', 'Neck Stiffness'),
						('hy_bool IS NULL', 'Hypothermia'),
						('fe_bool IS NULL', 'Fever'),
						('pm_bool IS NULL', 'Premature'),
					],
				'query_str': '((sb_bool IS NULL) AND (af_bool IS NULL) AND (ci_bool IS NULL) AND (cm_bool IS NULL) AND (nb_bool IS NULL) AND (ja_bool IS NULL) AND (rb_bool IS NULL) AND (ns_bool IS NULL) AND (hy_bool IS NULL) AND (fe_bool IS NULL) AND (pm_bool IS NULL) )'
				},

		'RISK':	{
					'attrs': [
							('sb_bool IS NOT NULL', 'Stillborn'),
							('af_bool IS NOT NULL', 'Abnormal Fontinel'),
							('ci_bool IS NOT NULL', 'Cord Infection'),
							('cm_bool IS NOT NULL', 'Congenital Malformation'),
							('nb_bool IS NOT NULL', 'Not Breastfeeding'),
							('ja_bool IS NOT NULL', 'Jaundice'),
							],
					'query_str': '((sb_bool IS NOT NULL) OR (af_bool IS NOT NULL) OR (ci_bool IS NOT NULL) OR (cm_bool IS NOT NULL) OR (nb_bool IS NOT NULL) OR (ja_bool IS NOT NULL)) AND NOT ((rb_bool IS NOT NULL) OR (ns_bool IS NOT NULL) OR (hy_bool IS NOT NULL) OR (fe_bool IS NOT NULL) OR (pm_bool IS NOT NULL))'
	
				},
		'HIGH_RISK':	{
					'attrs': [ 
							('rb_bool IS NOT NULL', 'Rapid Breathing'),
							('ns_bool IS NOT NULL', 'Neck Stiffness'),
							('hy_bool IS NOT NULL', 'Hypothermia'),
							('fe_bool IS NOT NULL', 'Fever'),
							('pm_bool IS NOT NULL', 'Premature'),							

							],
					'query_str': '((rb_bool IS NOT NULL) OR (ns_bool IS NOT NULL) OR (hy_bool IS NOT NULL) OR (fe_bool IS NOT NULL) OR (pm_bool IS NOT NULL))'
				}
		
		}

PNC_DATA = {
	
		'NO_RISK': {
			   'attrs':	[
						(u'af_bool IS NULL', u'Abnormal Fontinel'), 
						(u'ch_bool IS NULL', u'Coughing'), 
						(u'hy_bool IS NULL', u'Hypothermia'), 
						(u'rb_bool IS NULL', u'Rapid Breathing'), 
						(u'sa_bool IS NULL', u'Severe Anemia'),
						(u'ds_bool IS NULL', u'Chronic Disease'),
						(u'fe_bool IS NULL', u'Fever'), 
						(u'fp_bool IS NULL', u'Fraccid Paralysis'),
						(u'ja_bool IS NULL', u'Jaundice'),
						(u'ns_bool IS NULL', u'Neck Stiffness'),
						(u'oe_bool IS NULL', u'Edema'),
						(u'pc_bool IS NULL', u'Pneumonia'),
						(u'vo_bool IS NULL', u'Vomiting'),
						(u'di_bool IS NULL', u'Diarhea'),
						(u'ma_bool IS NULL', u'Malaria'),
					],

			   'query_str': '((af_bool IS NULL) AND (ch_bool IS NULL) AND (hy_bool IS NULL) AND (rb_bool IS NULL) AND (sa_bool IS NULL) AND (ds_bool IS NULL) AND (fe_bool IS NULL) AND (fp_bool IS NULL) AND (ja_bool IS NULL) AND (ns_bool IS NULL) AND (oe_bool IS NULL) AND (pc_bool IS NULL) AND (vo_bool IS NULL) AND (di_bool IS NULL) AND (ma_bool IS NULL))'
			},

		'RISK': {
			   'attrs':	[
						(u'af_bool IS NOT NULL', u'Abnormal Fontinel'), 
						(u'ch_bool IS NOT NULL', u'Coughing'), 
						(u'hy_bool IS NOT NULL', u'Hypothermia'), 
						(u'rb_bool IS NOT NULL', u'Rapid Breathing'), 
						(u'sa_bool IS NOT NULL', u'Severe Anemia'),
						(u'ds_bool IS NOT NULL', u'Chronic Disease'),
						(u'fe_bool IS NOT NULL', u'Fever'), 
						(u'fp_bool IS NOT NULL', u'Fraccid Paralysis'),
						(u'ja_bool IS NOT NULL', u'Jaundice'),
						(u'ns_bool IS NOT NULL', u'Neck Stiffness'),
						(u'oe_bool IS NOT NULL', u'Edema'),
						(u'pc_bool IS NOT NULL', u'Pneumonia'),
						(u'vo_bool IS NOT NULL', u'Vomiting'),
						(u'di_bool IS NOT NULL', u'Diarhea'),
						(u'ma_bool IS NOT NULL', u'Malaria'),
					],

			   'query_str': '( (af_bool IS NOT NULL) OR (ch_bool IS NOT NULL) OR (hy_bool IS NOT NULL) OR (rb_bool IS NOT NULL) OR (sa_bool IS NOT NULL) OR (ds_bool IS NOT NULL) OR (fe_bool IS NOT NULL) OR (fp_bool IS NOT NULL) OR (ja_bool IS NOT NULL) OR (ns_bool IS NOT NULL) OR (oe_bool IS NOT NULL) OR (pc_bool IS NOT NULL) OR (vo_bool IS NOT NULL) OR (di_bool IS NOT NULL) OR (ma_bool IS NOT NULL) )'

		}
	}


VAC_DATA = {
		'VAC_SERIES': {

				'attrs': [
						(u'v1_bool IS NOT NULL', u'BCG, PO'),
						(u'v2_bool IS NOT NULL', u'P1, Penta1, PCV1, Rota1'),
						(u'v3_bool IS NOT NULL', u'P2, Penta2, PCV2, Rota2'),
						(u'v4_bool IS NOT NULL', u'P3, Penta3, PCV3, Rota3'),
						(u'v5_bool IS NOT NULL', u'Measles1, Rubella'),
						(u'v6_bool IS NOT NULL', u'Measles2'),					
					],
		
				'query_str': '((v1_bool IS NOT NULL) OR (v2_bool IS NOT NULL) OR (v3_bool IS NOT NULL) OR (v4_bool IS NOT NULL) OR (v5_bool IS NOT NULL) OR (v6_bool IS NOT NULL))'
			},

		'VAC_COMPLETION': {

					'attrs': [
							(u'vc_bool IS NOT NULL', u'Vaccine Complete'),
							(u'vi_bool IS NOT NULL', u'Vaccine Incomplete'),
							(u'nv_bool IS NOT NULL', u'Unimmunized Child'),				
						],
			
					'query_str': '((vc_bool IS NOT NULL) OR (vi_bool IS NOT NULL) OR (nv_bool IS NOT NULL))'
			},



		}

DEATH_DATA = {
		'attrs': [
						(u'md_bool IS NOT NULL', u'Maternal Death'),
						(u'nd_bool IS NOT NULL', u'Newborn Death'),
						(u'cd_bool IS NOT NULL', u'Child Death'),
											
					],

		'query_str': '((md_bool IS NOT NULL) OR (nd_bool IS NOT NULL) OR (cd_bool IS NOT NULL))',

                'bylocs': {
				'attrs': [
						(u'hp_bool IS NOT NULL', u'At Hospital'),
						(u'cl_bool IS NOT NULL', u'At Clinic'),
						(u'or_bool IS NOT NULL', u'On Route'),
						(u'ho_bool IS NOT NULL', u'At home'),
											
					],

				'query_str': '((md_bool IS NOT NULL) OR (nd_bool IS NOT NULL) OR (cd_bool IS NOT NULL)) AND ((hp_bool IS NOT NULL) OR (cl_bool IS NOT NULL) OR (or_bool IS NOT NULL) OR (ho_bool IS NOT NULL))',

				}

		}

CCM_DATA = {
		'attrs': [
						(u'di_bool IS NOT NULL', u'Diarrhea'),
						(u'ma_bool IS NOT NULL', u'Malaria'),
						(u'pc_bool IS NOT NULL', u'Pneumonia'),
											
					],

		'query_str': '((di_bool IS NOT NULL) OR (ma_bool IS NOT NULL) OR (pc_bool IS NOT NULL))'
		
		}

CMR_DATA = {
		'attrs': [
						(u'pt_bool IS NOT NULL', u'Patient Treated'),
						(u'pr_bool IS NOT NULL', u'Patient Directly Referred'),
						(u'tr_bool IS NOT NULL', u'Patient Referred After Treatment'),
						(u'aa_bool IS NOT NULL', u'Binome Advice'),
											
					],

		'query_str': '((pt_bool IS NOT NULL) OR (pr_bool IS NOT NULL) OR (tr_bool IS NOT NULL) OR (aa_bool IS NOT NULL))'
		
		}

RED_DATA = {

		'attrs': [
				(u'ap_bool IS NOT NULL', u'Acute Abd Pain Early Pregnancy') ,
				(u'co_bool IS NOT NULL', u'Convulsions') ,
				(u'he_bool IS NOT NULL', u'Hemorrhaging/Bleeding') ,
				(u'la_bool IS NOT NULL', u'Mother in Labor at Home') ,
				(u'mc_bool IS NOT NULL', u'Miscarriage') ,
				(u'pa_bool IS NOT NULL', u'Premature Contraction') ,
				(u'ps_bool IS NOT NULL', u'Labour with Previous C-Section') ,
				(u'sc_bool IS NOT NULL', u'Serious Condition but Unknown') ,
				#(u'sl_bool IS NOT NULL', u'Stroke during Labor') ,
				(u'un_bool IS NOT NULL', u'Unconscious'), 
			],

		'query_str': '((ap_bool IS NOT NULL) OR  (co_bool IS NOT NULL) OR  (he_bool IS NOT NULL) OR  (la_bool IS NOT NULL) OR  (mc_bool IS NOT NULL) OR  (pa_bool IS NOT NULL) OR  (ps_bool IS NOT NULL) OR  (sc_bool IS NOT NULL) OR  (un_bool IS NOT NULL) OR  (ho_bool IS NOT NULL) OR  (or_bool IS NOT NULL))'

		#'query_str': '((ap_bool IS NOT NULL) OR  (co_bool IS NOT NULL) OR  (he_bool IS NOT NULL) OR  (la_bool IS NOT NULL) OR  (mc_bool IS NOT NULL) OR  (pa_bool IS NOT NULL) OR  (ps_bool IS NOT NULL) OR  (sc_bool IS NOT NULL) OR  (sl_bool IS NOT NULL) OR  (un_bool IS NOT NULL) OR  (ho_bool IS NOT NULL) OR  (or_bool IS NOT NULL))'

		}

RAR_DATA = {

		'attrs': [
				(u'al_bool IS NOT NULL', u'Ambulance Late') ,
				(u'at_bool IS NOT NULL', u'Ambulance on Time') ,
				(u'na_bool IS NOT NULL', u'No Ambulance Response') ,
				(u'mw_bool IS NOT NULL', u'Mother Well(OK)') ,
				(u'ms_bool IS NOT NULL', u'Mother Sick') ,
			],

		'query_str': '((al_bool IS NOT NULL) OR  (at_bool IS NOT NULL) OR  (na_bool IS NOT NULL) OR  (mw_bool IS NOT NULL) OR  (ms_bool IS NOT NULL))'

		}

DELIVERY_DATA = {
		'attrs': [
				(u'hp_bool IS NOT NULL', u'At Hospital'),
				(u'cl_bool IS NOT NULL', u'At Clinic'),
				(u'or_bool IS NOT NULL', u'On Route'),
				(u'ho_bool IS NOT NULL', u'At home'),
									
			],

		'query_str':'((hp_bool IS NOT NULL) OR (cl_bool IS NOT NULL) OR (or_bool IS NOT NULL) OR (ho_bool IS NOT NULL))',
		
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

RED_ALERT_FIELDS    =   [
    ('Patient ID', 'patient_id'),
    ('Reporter', 'reporter_phone')
]
