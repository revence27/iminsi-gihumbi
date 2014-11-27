#!  /usr/bin/env python
# encoding: utf-8
# vim: ts=2 expandtab


def fans( sms_report = [] ):
 ans = {}
 for sms in sms_report: ans.update({sms.keyword: (sms.title_en, sms.title_rw)})
 return ans

def fields(fs = [], ans = {}):
 fans = {}
 for an in ans.keys(): fans.update({an: []})
 for ff in fs:
  d = fans.get(ff.sms_report.keyword)#; print d
  key = ff.key
  ## muac, date_of_birth, date_of_emergency, af_bool, db_bool
  if key in ['mother_weight', 'mother_height', 'child_weight', 'child_height', 'child_number', 'gravidity', 'parity']: key = '%s_float' % key
  else:	key = '%s_bool' % key 
  if key == 'gravidity_float': key = 'gravity_float' 
  if key == 'nid_bool':
   dd = ('patient_id', ff.title_en, ff.title_rw)
   d.append(dd)
   d.append(('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama"))
   d.append(('report_date', 'Submission Date', "Itariki yatanzweho"))   
  else:
    dd = (key, ff.title_en, ff.title_rw)
    d.append(dd)
  fans.update({ff.sms_report.keyword: d })
 
 return fans
 
#FIELDS = fields(fs = sms_report_fields, fans = fans(sms_reports))

REPORTS = {
            'PRE' : (u'Pregnancy', u'Ugusama') ,
            'DTH' : (u'Death', u'Urupfu') ,
            'RISK' : (u'Risk', u'Ibibazo mpuruza') ,
            'ANC' : (u'AntenatalConsultation', u'Ukwipimisha') ,
            'DEP' : (u'Departure', u'Ukwimuka') ,
            'RES' : (u'RiskResult', u'Igisubizo ku bibazo mpuruza') ,
            'CBN' : (u'CommunityBasedNutrition', u'Imirire') ,
            'CCM' : (u'CommunityCaseManagement', u'Ukuvura abana') ,
            'RAR' : (u'RedAlertResult', u'Igisubizo ku bibazo simusiga') ,
            'REF' : (u'Refusal', u'Ukwanga') ,
            'CHI' : (u'ChildHealth', u'Ugukingira') ,
            'NBC' : (u'NewbornCare', u"Isurwa ry'uruhinja") ,
            'PNC' : (u'PostnatalCare', u"Isurwa ry'umubyeyi") ,
            'BIR' : (u'Birth', u'Ukuvuka') ,
            'CMR' : (u'CaseManagementResponse', u"Iherezo ry'uburwayi") ,
            'RED' : (u'RedAlert', u'Ibibazo simusiga') 
        }


FIELDS = {
          'PRE' : [
	                   ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                      ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama"),
                      ('report_date', 'Submission Date', "Itariki yatanzweho"), 
                      #(u'mother_phone_bool', u"Mother's Telephone", u"Telephoni y'umubyeyi") ,
                      (u'lmp', u'Last Menstrual Period', u"Itariki ya nyuma y'imihango"),
                      (u'parity_float', u'Parity', u"Umubare w'imbyaro") ,
                      ('gravity_float', u'Gravidity', u'Inshuro yasamye') ,
                      #(u'anc2_date_bool', u'Second ANC Appointment Date', u'Itariki yo gusubira kwipimisha') ,
                      (u'mother_height_float', u'Mother Height', u"Uburebure bw'umubyeyi") ,
                      (u'mother_weight_float', u'Mother Weight', u"Ibiro by'umubyeyi") , 
                      (u'nh_bool', u'Has no Handwashing', u'Ntafite Kandagira Ukarabe') ,
                      (u'nt_bool', u'Has no Toilet', u'Ntafite ubwiherero') ,
                      (u'hw_bool', u'Has Handwashing', u'Afite Kandagira Ukarabe') ,
                      (u'to_bool', u'Has Toilet', u'Afite ubwiherero') ,
                      (u'cl_bool', u'At Clinic Facility', u'Ku Kigo nderabuzima/Ivuriri') ,
                      (u'hp_bool', u'At hospital facility', u'Ku bitaro') ,
                      (u'af_bool', u'Abnormal Fontinel', u'Igihorihori kibyimbye/gitebeye') ,
                      (u'ch_bool', u'Coughing', u'Inkorora') ,
                      (u'hy_bool', u'Hypothermia', u'Ubukonje bukabije') ,
                      (u'rb_bool', u'Rapid Breathing', u'Guhumeka vuba') ,
                      (u'sa_bool', u'Severe Anemia', u'Kubura amaraso') ,
                      (u'ds_bool', u'Chronic disease', u'indwara idakira') ,
                      (u'fe_bool', u'Fever', u'umuriro ukabije') ,
                      (u'fp_bool', u'Fraccid paralysis', u'Uburema bushya') ,
                      (u'ja_bool', u'Jaundice', u'Umubiri wabaye umuhondo') ,
                      (u'ns_bool', u'Neck Stiffness', u'Yagagaye iosi') ,
                      (u'oe_bool', u'Edema', u'Kubyimbagana') ,
                      (u'pc_bool', u'Pneumonia', u'Umusonga') ,
                      (u'vo_bool', u'Vomiting', u'Kuruka') ,
                      (u'di_bool', u'Diarhea', u'Impiswi') ,
                      (u'ma_bool', u'Malaria', u'Malariya') ,
                      (u'np_bool', u'No Problem', u'Ntakibazo') ,
                      (u'lz_bool', u'Previous Hemorrhaging/Bleeding', u'Yigeze kuva amaraso') ,
                      (u'yj_bool', u'Previous Serious Conditions', u'Yigeze agira ikibazo gikomeye kidasobanutse') ,
                      (u'kx_bool', u'Previous Convulsion', u'Yigeze kugagara') ,
                      (u'yg_bool', u'Young Age(Under 18)', u'Yasamye atarageza ku myaka 18') ,
                      (u'ol_bool', u'Old Age(Over 35)', u'Yasamye arengeje imyaka 35') ,
                      (u'rm_bool', u'Repetitive Miscarriage', u'Yakuyemo inda') ,
                      (u'hd_bool', u'Previous Home Delivery', u'Yigeze kubyarira mu rugo') ,
                      (u'mu_bool', u'Multiples', u'Atwite abana barenze umwe') ,
                      (u'gs_bool', u'Previous Obstetric Surgery', u'Yigeze kubagwa abyara') ,
                      (u'nr_bool', u'No Previous Risk', u'Ntakibazo yagize ku nda yabanje') ,
                      
                ],
          'DTH' : [ 
	          
                    ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                    ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                    ('report_date', 'Submission Date', "Itariki yatanzweho"),
                    (u'child_number_float', u'Child number', u"Nimero y'umwana") ,
                    (u'lmp', u'Date of Birth', u"Itariki y'amavuko") ,
                    (u'ho_bool', u'At Home', u'Mu rugo') ,
                    (u'or_bool', u'On Route', u'Mu nzira') ,
                    (u'cl_bool', u'At Clinic Facility', u'Ku Kigo nderabuzima/Ivuriri') ,
                    (u'hp_bool', u'At hospital facility', u'Ku bitaro') ,
                    (u'md_bool', u'Maternal death', u"Urupfu rw'umubyeyi") ,
                    (u'nd_bool', u'Newborn death', u"Urupfu rw'uruhinja") ,
                    (u'cd_bool', u'Child death', u"Urupfu rw'umwana") 
                ],
            'RISK' : [

                      ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                      ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                      ('report_date', 'Submission Date', "Itariki yatanzweho"),
                      #(u'af_bool', u'Abnormal Fontinel', u'Igihorihori kibyimbye/gitebeye') ,
                      (u'ch_bool', u'Coughing', u'Inkorora') ,
                      (u'hy_bool', u'Hypothermia', u'Ubukonje bukabije') ,
                      (u'rb_bool', u'Rapid Breathing', u'Guhumeka vuba') ,
                      (u'sa_bool', u'Severe Anemia', u'Kubura amaraso') ,
                      (u'ds_bool', u'Chronic disease', u'indwara idakira') ,
                      (u'fe_bool', u'Fever', u'umuriro ukabije') ,
                      (u'fp_bool', u'Fraccid paralysis', u'Uburema bushya') ,
                      (u'ja_bool', u'Jaundice', u'Umubiri wabaye umuhondo') ,
                      (u'ns_bool', u'Neck Stiffness', u'Yagagaye iosi') ,
                      (u'oe_bool', u'Edema', u'Kubyimbagana') ,
                      (u'pc_bool', u'Pneumonia', u'Umusonga') ,
                      (u'vo_bool', u'Vomiting', u'Kuruka') ,
                      (u'di_bool', u'Diarhea', u'Impiswi') ,
                      (u'ma_bool', u'Malaria', u'Malariya') ,
                      (u'ho_bool', u'At Home', u'Mu rugo') ,
                      (u'or_bool', u'On Route', u'Mu nzira') ,
                      (u'cl_bool', u'At Clinic Facility', u'Ku Kigo nderabuzima/Ivuriri') ,
                      (u'hp_bool', u'At hospital facility', u'Ku bitaro') ,
                      (u'mother_weight_float', u'Mother Weight', u"Ibiro by'umubyeyi")
                  ],
              'ANC' :[ 
	              
                      ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                      ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                      ('report_date', 'Submission Date', "Itariki yatanzweho"),
                      (u'lmp', u'Date of ANC', u'Itariki yisuzumirishejeho') ,
                      (u'anc2_bool', u'Second ANC', u'Yipimishije inshuro ya 2') ,
                      (u'anc3_bool', u'Third ANC', u'Yipimishije inshuro ya 3') ,
                      (u'anc4_bool', u'Fourth ANC', u'Yipimishije inshuro ya 4') ,
                      #(u'af_bool', u'Abnormal Fontinel', u'Igihorihori kibyimbye/gitebeye') ,
                      (u'ch_bool', u'Coughing', u'Inkorora') ,
                      (u'hy_bool', u'Hypothermia', u'Ubukonje bukabije') ,
                      (u'rb_bool', u'Rapid Breathing', u'Guhumeka vuba') ,
                      (u'sa_bool', u'Severe Anemia', u'Kubura amaraso') ,
                      (u'ds_bool', u'Chronic disease', u'indwara idakira') ,
                      (u'fe_bool', u'Fever', u'umuriro ukabije') ,
                      (u'fp_bool', u'Fraccid paralysis', u'Uburema bushya') ,
                      (u'ja_bool', u'Jaundice', u'Umubiri wabaye umuhondo') ,
                      (u'ns_bool', u'Neck Stiffness', u'Yagagaye iosi') ,
                      (u'oe_bool', u'Edema', u'Kubyimbagana') ,
                      (u'pc_bool', u'Pneumonia', u'Umusonga') ,
                      (u'vo_bool', u'Vomiting', u'Kuruka') ,
                      (u'di_bool', u'Diarhea', u'Impiswi') ,
                      (u'ma_bool', u'Malaria', u'Malariya') ,
                      (u'np_bool', u'No Problem', u'Ntakibazo') ,
                      (u'cl_bool', u'At Clinic Facility', u'Ku Kigo nderabuzima/Ivuriri') ,
                      (u'hp_bool', u'At hospital facility', u'Ku bitaro') ,
                      (u'mother_weight_float', u'Mother Weight', u"Ibiro by'umubyeyi")
                   ],
              'DEP' : [
	              
                      ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                      ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                      ('report_date', 'Submission Date', "Itariki yatanzweho"),
                      (u'child_number_float', u'Child number', u"Nimero y'umwana") ,
                      (u'lmp', u'Date of Birth', u"Itariki y'amavuko")
                   ],
              'RES' : [
	              
                      ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                      ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                      ('report_date', 'Submission Date', "Itariki yatanzweho"),
                      #(u'af_bool', u'Abnormal Fontinel', u'Igihorihori kibyimbye/gitebeye') ,
                      (u'ch_bool', u'Coughing', u'Inkorora') ,
                      (u'hy_bool', u'Hypothermia', u'Ubukonje bukabije') ,
                      (u'rb_bool', u'Rapid Breathing', u'Guhumeka vuba') ,
                      (u'sa_bool', u'Severe Anemia', u'Kubura amaraso') ,
                      (u'ds_bool', u'Chronic disease', u'indwara idakira') ,
                      (u'fe_bool', u'Fever', u'umuriro ukabije') ,
                      (u'fp_bool', u'Fraccid paralysis', u'Uburema bushya') ,
                      (u'ja_bool', u'Jaundice', u'Umubiri wabaye umuhondo') ,
                      #(u'ns_bool', u'Neck Stiffness', u'Yagagaye iosi') ,
                      (u'oe_bool', u'Edema', u'Kubyimbagana') ,
                      (u'pc_bool', u'Pneumonia', u'Umusonga') ,
                      (u'vo_bool', u'Vomiting', u'Kuruka') ,
                      (u'di_bool', u'Diarhea', u'Impiswi') ,
                      (u'ma_bool', u'Malaria', u'Malariya') ,
                      (u'ho_bool', u'At Home', u'Mu rugo') ,
                      (u'or_bool', u'On Route', u'Mu nzira') ,
                      (u'cl_bool', u'At Clinic Facility', u'Ku Kigo nderabuzima/Ivuriri') ,
                      (u'hp_bool', u'At hospital facility', u'Ku bitaro') ,
                      (u'aa_bool', u'ASM Advice', u"Inama y'umujyanama") ,
                      (u'pr_bool', u'Patient Directly Referred', u'Yahise yoherezwa kwa muganga ako kanya') ,
                      (u'mw_bool', u'Mother Well', u'Umubyeyi ameze neza') ,
                      (u'ms_bool', u'Mother Sick', u'Umubyeyi ararwaye')
                    ],
              'BIR' :  [

                        ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                        ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                        ('report_date', 'Submission Date', "Itariki yatanzweho"),
                        (u'child_number_float', u'Child number', u"Nimero y'umwana") ,
                        (u'lmp', u'Date of Birth', u"Itariki y'amavuko") ,
                        (u'bo_bool', u'Male', u'Umuhungu') ,
                        (u'gi_bool', u'Female', u'Umukobwa') ,
                        (u'sb_bool', u'Stillborn', u'Umwana avutse apfuye') ,
                        (u'rb_bool', u'Rapid Breathing', u'Guhumeka vuba') ,
                        (u'af_bool', u'Abnormal Fontinel', u'Igihorihori kibyimbye/gitebeye') ,
                        (u'ci_bool', u'Cord Infection', u"Ukwandura k'urureri") ,
                        (u'cm_bool', u'Congenital Malformation', u'Kuvukana ubumuga') ,
                        (u'ib_bool', u'Cleft Palate/Lip', u'Ibibari') ,
                        #(u'db_bool', u'Children Living With Disability', u"Abana n'ubumuga") ,
                        (u'pm_bool', u'Premature', u'Umwana yavutse adashyitse') ,
                        (u'np_bool', u'No Problem', u'Ntakibazo') ,
                        (u'ho_bool', u'At Home', u'Mu rugo') ,
                        (u'or_bool', u'On Route', u'Mu nzira') ,
                        (u'cl_bool', u'At Clinic Facility', u'Ku Kigo nderabuzima/Ivuriri') ,
                        (u'hp_bool', u'At hospital facility', u'Ku bitaro') ,
                        (u'bf1_bool', u'Breastfeeding within 1 Hour of Birth', u'Konsa mu isaha ya mbere akivuka') ,
                        (u'nb_bool', u'Not Breastfeeding', u'Ntiyonka') ,
                        (u'child_weight_float', u'Child Weight', u"Ibiro by'umwana")
                    ],
              'CBN' :  [
	              
                        ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                        ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                        ('report_date', 'Submission Date', "Itariki yatanzweho"),
                        (u'child_number_float', u'Child number', u"Nimero y'umwana") ,
                        (u'lmp', u'Date of Birth', u"Itariki y'amavuko") ,
                        (u'ebf_bool', u'Exclusive Breastfeeding', u'Aronka gusa') ,
                        (u'nb_bool', u'Not Breastfeeding', u'Ntiyonka') ,
                        (u'cbf_bool', u'Complementary Breastfeeding', u'Inyunganirabere') ,
                        (u'child_height_float', u'Child Height', u"Uburebure bw'umwana") ,
                        (u'child_weight_float', u'Child Weight', u"Ibiro by'umwana") ,
                        (u'muac_float', u'MUAC', u'Ibipimo bya MUAC')
                      ],
                'CCM' :  [
	                
                          ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                          ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                          ('report_date', 'Submission Date', "Itariki yatanzweho"),
                          (u'child_number_float', u'Child number', u"Nimero y'umwana") ,
                          (u'lmp', u'Date of Birth', u"Itariki y'amavuko") ,
                          (u'pc_bool', u'Pneumonia', u'Umusonga') ,
                          (u'di_bool', u'Diarhea', u'Impiswi') ,
                          (u'ma_bool', u'Malaria', u'Malariya') ,
                          #(u'ib_bool', u'Cleft Palate/Lip', u'Ibibari') ,
                          #(u'db_bool', u'Children Living With Disability', u"Abana n'ubumuga") ,
                          #(u'nv_bool', u'Unimmunized Child', u'Ntiyigeze akingirwa') ,
                          (u'oi_bool', u'Other Infection', u'Indi ndwara') ,
                          #(u'np_bool', u'No Problem', u'Ntakibazo') ,
                          (u'aa_bool', u'ASM Advice', u"Inama y'umujyanama") ,
                          (u'pr_bool', u'Patient Directly Referred', u'Yahise yoherezwa kwa muganga ako kanya') ,
                          (u'pt_bool', u'Patient Treated', u'Yavuwe') ,
                          (u'tr_bool', u'Patient Referred After Treatment', u'Yoherejwe ku ivuriro nyuma yo kuvurwa') ,
                          (u'muac_float', u'MUAC', u'Ibipimo bya MUAC')
                        ],
                'RAR' :   [
	                
                          ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                          ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                          ('report_date', 'Submission Date', "Itariki yatanzweho"),
                          #(u'lmp', u'Date of Emergency', u'Itariki yagiriye ibibazo') ,
                          (u'ap_bool', u'Acute Abd Pain Early Pregnancy', u'Ububare butunguranye bukabije') ,
                          (u'co_bool', u'Convulsions', u'Kugagara') ,
                          (u'he_bool', u'Hemorrhaging/Bleeding', u'Kuva amaraso') ,
                          (u'la_bool', u'Mother in labor at home', u'atangiye ibise ari mu rugo') ,
                          (u'mc_bool', u'Miscarriage', u'Gukuramo inda') ,
                          (u'pa_bool', u'Premature Contraction', u'Kujya ku bise inda itarageza igihe') ,
                          (u'ps_bool', u'Labour with Previous C-Section', u'Kujya ku nda yarabazwe abyara') ,
                          (u'sc_bool', u'Serious Condition but Unknown', u'Ikibazo gikomeye kidasobanutse') ,
                          #(u'sl_bool', u'Stroke during Labor', u'Paralize') ,
                          #(u'un_bool', u'Unconscious', u'Guta ubwenge') ,
                          (u'ho_bool', u'At Home', u'Mu rugo') ,
                          (u'or_bool', u'On Route', u'Mu nzira') ,
                          #(u'cl_bool', u'At Clinic Facility', u'Ku Kigo nderabuzima/Ivuriri') ,
                          #(u'hp_bool', u'At hospital facility', u'Ku bitaro') ,
                          (u'al_bool', u'Ambulance Late', u'Ambilansi yatinze') ,
                          (u'at_bool', u'Ambulance on Time', u'Ambilansi yahageze ku gihe') ,
                          (u'na_bool', u'No Ambulance Response', u'Ambilansi ntiyaje') ,
                          (u'mw_bool', u'Mother Well', u'Umubyeyi ameze neza') ,
                          (u'ms_bool', u'Mother Sick', u'Umubyeyi ararwaye')
                      ],
                'CHI' :   [
	                
                          ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                          ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                          ('report_date', 'Submission Date', "Itariki yatanzweho"),
                          (u'child_number_float', u'Child number', u"Nimero y'umwana") ,
                          (u'lmp', u'Date of Birth', u"Itariki y'amavuko") ,
                          (u'v1_bool', u'BCG, PO', u'BCG, PO') ,
                          (u'v2_bool', u'P1, Penta1, PCV1, Rota1', u'P1, Penta1, PCV1, Rota1') ,
                          (u'v3_bool', u'P2, Penta2, PCV2, Rota2', u'P2, Penta2, PCV2, Rota2') ,
                          (u'v4_bool', u'P3, Penta3, PCV3, Rota3', u'P3, Penta3, PCV3, Rota3') ,
                          (u'v5_bool', u'Measles1, Rubella', u'Iseru1, Rubewole') ,
                          (u'v6_bool', u'Measles2', u'Iseru2') ,
                          (u'vc_bool', u'Vaccine Complete', u'Yarangije inkingo zose ziteganijwe') ,
                          (u'vi_bool', u'Vaccine Incomplete', u'Ntiyarangije inkingo zose ziteganijwe') ,
                          (u'nv_bool', u'Unimmunized Child', u'Ntiyigeze akingirwa') ,
                          #(u'sb_bool', u'Stillborn', u'Umwana avutse apfuye') ,
                          (u'rb_bool', u'Rapid Breathing', u'Guhumeka vuba') ,
                          (u'af_bool', u'Abnormal Fontinel', u'Igihorihori kibyimbye/gitebeye') ,
                          (u'ci_bool', u'Cord Infection', u"Ukwandura k'urureri") ,
                          (u'cm_bool', u'Congenital Malformation', u'Kuvukana ubumuga') ,
                          (u'ib_bool', u'Cleft Palate/Lip', u'Ibibari') ,
                          #(u'db_bool', u'Children Living With Disability', u"Abana n'ubumuga") ,
                          (u'pm_bool', u'Premature', u'Umwana yavutse adashyitse') ,
                          (u'np_bool', u'No Problem', u'Ntakibazo') ,
                          (u'ho_bool', u'At Home', u'Mu rugo') ,
                          (u'or_bool', u'On Route', u'Mu nzira') ,
                          (u'cl_bool', u'At Clinic Facility', u'Ku Kigo nderabuzima/Ivuriri') ,
                          (u'hp_bool', u'At hospital facility', u'Ku bitaro') ,
                          (u'child_weight_float', u'Child Weight', u"Ibiro by'umwana") ,
                          (u'muac_float', u'MUAC', u'Ibipimo bya MUAC')
                        ],
                  'NBC' :  [
	                  
                            ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                            ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                            ('report_date', 'Submission Date', "Itariki yatanzweho"),
                            (u'child_number_float', u'Child number', u"Nimero y'umwana") ,
                            (u'nbc1_bool', u'First NBC', u'Gusura uruhinja bwa mbere mu rugo') ,
                            (u'nbc2_bool', u'Second NBC', u'Gusura uruhinja bwa kabiri mu rugo') ,
                            (u'nbc3_bool', u'Third NBC', u'Gusura uruhinja bwa gatatu mu rugo') ,
                            #(u'nbc4_bool', u'Fourth NBC', u'Gusura uruhinja bwa kane mu rugo') ,
                            #(u'nbc5_bool', u'Fifth NBC', u'Gusura uruhinja bwa gatanu mu rugo') ,
                            (u'lmp', u'Date of Birth', u"Itariki y'amavuko") ,
                            (u'sb_bool', u'Stillborn', u'Umwana avutse apfuye') ,
                            (u'rb_bool', u'Rapid Breathing', u'Guhumeka vuba') ,
                            (u'af_bool', u'Abnormal Fontinel', u'Igihorihori kibyimbye/gitebeye') ,
                            (u'ci_bool', u'Cord Infection', u"Ukwandura k'urureri") ,
                            (u'cm_bool', u'Congenital Malformation', u'Kuvukana ubumuga') ,
                            (u'ib_bool', u'Cleft Palate/Lip', u'Ibibari') ,
                            #(u'db_bool', u'Children Living With Disability', u"Abana n'ubumuga") ,
                            (u'pm_bool', u'Premature', u'Umwana yavutse adashyitse') ,
                            (u'np_bool', u'No Problem', u'Ntakibazo') ,
                            (u'ebf_bool', u'Exclusive Breastfeeding', u'Aronka gusa') ,
                            (u'nb_bool', u'Not Breastfeeding', u'Ntiyonka') ,
                            (u'cbf_bool', u'Complementary Breastfeeding', u'Inyunganirabere') ,
                            (u'aa_bool', u'ASM Advice', u"Inama y'umujyanama") ,
                            (u'pr_bool', u'Patient Directly Referred', u'Yahise yoherezwa kwa muganga ako kanya') ,
                            (u'cw_bool', u'Child well(OK)', u'umwana ameze neza') ,
                            (u'cs_bool', u'Child sick', u'Umwana ararwaye')
                          ],
                    'PNC' :   [
	                    
                                ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                                ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                                ('report_date', 'Submission Date', "Itariki yatanzweho"),
                                (u'pnc1_bool', u'First PNC', u'Gusura umubyeyi wabyaye bwa mbere mu rugo') ,
                                (u'pnc2_bool', u'Second PNC', u'Gusura umubyeyi wabyaye bwa kabiri mu rugo') ,
                                (u'pnc3_bool', u'Third PNC', u'Gusura umubyeyi wabyaye bwa gatatu mu rugo') ,
                                (u'lmp', u'Date of Birth', u"Itariki y'amavuko") ,
                                (u'af_bool', u'Abnormal Fontinel', u'Igihorihori kibyimbye/gitebeye') ,
                                (u'ch_bool', u'Coughing', u'Inkorora') ,
                                (u'hy_bool', u'Hypothermia', u'Ubukonje bukabije') ,
                                (u'rb_bool', u'Rapid Breathing', u'Guhumeka vuba') ,
                                (u'sa_bool', u'Severe Anemia', u'Kubura amaraso') ,
                                (u'ds_bool', u'Chronic disease', u'indwara idakira') ,
                                (u'fe_bool', u'Fever', u'umuriro ukabije') ,
                                (u'fp_bool', u'Fraccid paralysis', u'Uburema bushya') ,
                                (u'ja_bool', u'Jaundice', u'Umubiri wabaye umuhondo') ,
                                (u'ns_bool', u'Neck Stiffness', u'Yagagaye iosi') ,
                                (u'oe_bool', u'Edema', u'Kubyimbagana') ,
                                (u'pc_bool', u'Pneumonia', u'Umusonga') ,
                                (u'vo_bool', u'Vomiting', u'Kuruka') ,
                                (u'di_bool', u'Diarhea', u'Impiswi') ,
                                (u'ma_bool', u'Malaria', u'Malariya') ,
                                (u'np_bool', u'No Problem', u'Ntakibazo') ,
                                (u'aa_bool', u'ASM Advice', u"Inama y'umujyanama") ,
                                (u'pr_bool', u'Patient Directly Referred', u'Yahise yoherezwa kwa muganga ako kanya') ,
                                (u'mw_bool', u'Mother Well', u'Umubyeyi ameze neza') ,
                                (u'ms_bool', u'Mother Sick', u'Umubyeyi ararwaye')
                                ],
                        'REF' :   [
	                        
                                    ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                                    ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama"),
                                    ('report_date', 'Submission Date', "Itariki yatanzweho"),
                                  ],
                          'CMR' :   [
	                          
                                      ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                                      ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                                      ('report_date', 'Submission Date', "Itariki yatanzweho"),
                                      (u'child_number_float', u'Child number', u"Nimero y'umwana") ,
                                      (u'lmp', u'Date of Birth', u"Itariki y'amavuko") ,
                                      (u'pc_bool', u'Pneumonia', u'Umusonga') ,
                                      (u'di_bool', u'Diarhea', u'Impiswi') ,
                                      (u'ma_bool', u'Malaria', u'Malariya') ,
                                      (u'ib_bool', u'Cleft Palate/Lip', u'Ibibari') ,
                                      #(u'db_bool', u'Children Living With Disability', u"Abana n'ubumuga") ,
                                      (u'nv_bool', u'Unimmunized Child', u'Ntiyigeze akingirwa') ,
                                      (u'oi_bool', u'Other Infection', u'Indi ndwara') ,
                                      (u'np_bool', u'No Problem', u'Ntakibazo') ,
                                      (u'aa_bool', u'ASM Advice', u"Inama y'umujyanama") ,
                                      (u'pr_bool', u'Patient Directly Referred', u'Yahise yoherezwa kwa muganga ako kanya') ,
                                      (u'pt_bool', u'Patient Treated', u'Yavuwe') ,
                                      (u'tr_bool', u'Patient Referred After Treatment', u'Yoherejwe ku ivuriro nyuma yo kuvurwa') ,
                                      (u'cw_bool', u'Child well(OK)', u'umwana ameze neza') ,
                                      (u'cs_bool', u'Child sick', u'Umwana ararwaye')
                                    ],
                            'RED' :  [
	                                    ('patient_id', u'National Identifier', u"Numero y'irangamuntu y'umubyeyi") ,
                                      ('reporter_phone', 'Reporter Telephone', "Telefoni y'Umujyanama") ,
                                      ('report_date', 'Submission Date', "Itariki yatanzweho"),
                                      (u'ap_bool', u'Acute Abd Pain Early Pregnancy', u'Ububare butunguranye bukabije') ,
                                      (u'co_bool', u'Convulsions', u'Kugagara') ,
                                      (u'he_bool', u'Hemorrhaging/Bleeding', u'Kuva amaraso') ,
                                      (u'la_bool', u'Mother in labor at home', u'atangiye ibise ari mu rugo') ,
                                      (u'mc_bool', u'Miscarriage', u'Gukuramo inda') ,
                                      (u'pa_bool', u'Premature Contraction', u'Kujya ku bise inda itarageza igihe') ,
                                      (u'ps_bool', u'Labour with Previous C-Section', u'Kujya ku nda yarabazwe abyara') ,
                                      (u'sc_bool', u'Serious Condition but Unknown', u'Ikibazo gikomeye kidasobanutse') ,
                                      #(u'sl_bool', u'Stroke during Labor', u'Paralize') ,
                                      (u'un_bool', u'Unconscious', u'Guta ubwenge') ,
                                      (u'ho_bool', u'At Home', u'Mu rugo') ,
                                      (u'or_bool', u'On Route', u'Mu nzira')
                                      ]
                  }



