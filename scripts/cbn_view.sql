
DROP VIEW cbn_view;

CREATE VIEW cbn_view AS
  SELECT
    *,
    ((child_height_float < (SELECT sd2neg FROM ig_deviations WHERE problem = 'stunting' AND month = ((EXTRACT(DAYS FROM (report_date - lmp)) / 30)) :: INTEGER LIMIT 1))) AS stunting_bool,
    ((child_weight_float < (SELECT sd2neg FROM ig_deviations WHERE problem = 'underweight' AND month = ((EXTRACT(DAYS FROM (report_date - lmp)) / 30)) :: INTEGER LIMIT 1))) AS underweight_bool,
    ((child_weight_float < (RANDOM() * 10.0))) AS wasting_bool
  FROM
    cbn_table
