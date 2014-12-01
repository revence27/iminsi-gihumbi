ADMIN_MIGRATIONS  = [
  ('address',           'user@example.com'),
  ('province_pk',       0),
  ('district_pk',       0),
  ('health_center_pk',  0)
]

PREGNANCY_MIGRATIONS = [
  ('db_bool', False),
  ('fe_bool', False),
  ('ma_bool', False),
  ('to_bool', False),
  ('ch_bool', False),
  ('vo_bool', False),
  ('ja_bool', False),
  ('ns_bool', False),
  ('pc_bool', False),
  ('ci_bool', False),
  ('oe_bool', False),
  ('di_bool', False),
  ('sb_bool', False),
  ('hy_bool', False),
  ('hw_bool', False),
  ('gs_bool', False),
  ('mu_bool', False),
  ('rm_bool', False),
  ('ol_bool', False),
  ('yg_bool', False),
  ('kx_bool', False),
  ('yj_bool', False),
  ('lz_bool', False),
  ('ib_bool', False)
]

RISK_MOD = {'(gs_bool IS NOT NULL OR mu_bool IS NOT NULL OR rm_bool IS NOT NULL OR ol_bool IS NOT NULL OR yg_bool IS NOT NULL OR kx_bool IS NOT NULL OR yj_bool IS NOT NULL OR lz_bool IS NOT NULL)':''}

TREATED = [
  ('oldid',   0),
  ('success', True),
  ('deleted', True),
  ('province_pk', 0),
  ('district_pk', 0),
  ('health_center_pk', 0)
]

FAILED = [
  ('oldid',     0),
  ('message',   u''),
  ('failcode',  u''),
  ('failpos',   0),
  ('province_pk', 0),
  ('district_pk', 0),
  ('health_center_pk', 0)
]
