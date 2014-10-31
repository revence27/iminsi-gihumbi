DROP VIEW ig_babies_adata;

CREATE VIEW ig_babies_adata AS
  SELECT
    Babies.*,
    (SELECT exc_breast FROM ig_adata WHERE baby = Babies.indexcol ORDER BY report_date DESC LIMIT 1) AS exc_breast,
    (SELECT no_breast FROM ig_adata WHERE baby = Babies.indexcol ORDER BY report_date DESC LIMIT 1) AS no_breast,
    (SELECT comp_breast FROM ig_adata WHERE baby = Babies.indexcol ORDER BY report_date DESC LIMIT 1) AS comp_breast,
    (SELECT weight FROM ig_adata WHERE baby = Babies.indexcol ORDER BY report_date DESC LIMIT 1) AS aweight,
    (SELECT height FROM ig_adata WHERE baby = Babies.indexcol ORDER BY report_date DESC LIMIT 1) AS aheight,
    indexcol AS baby,
/*
    (
      Babies.height < (
        SELECT
          sd2neg
        FROM
          ig_deviations
        WHERE
          problem = 'stunting'
        AND
          month = ((EXTRACT(DAYS FROM
            (
              (
                SELECT
                  report_date
                FROM
                  ig_adata
                WHERE
                  baby = Babies.indexcol
                ORDER BY report_date DESC LIMIT 1
              ) - Babies.birth_date)) / 30)) :: INTEGER
      )
    ) AS stunting,
    (
      Babies.height < (
        SELECT
          sd2neg
        FROM
          ig_deviations
        WHERE
          problem = 'wasting'
        AND
          month = ((EXTRACT(DAYS FROM
            (
              (
                SELECT
                  report_date
                FROM
                  ig_adata
                WHERE
                  baby = Babies.indexcol
                ORDER BY
                  report_date DESC LIMIT 1
              ) - Babies.birth_date)) / 30)) :: INTEGER
      )
    ) AS wasting,
    (
      Babies.weight < (
        SELECT
          sd2neg
        FROM
          ig_deviations
        WHERE
          problem = 'underweight'
        AND
          month = (EXTRACT(DAYS FROM
            (
              (
                SELECT
                  report_date
                FROM
                  ig_adata
                WHERE
                  baby = Babies.indexcol
                ORDER BY report_date DESC LIMIT 1
              ) - Babies.birth_date
            )) / 30) :: INTEGER
      )
    ) AS underweight
*/
/*
*/
    (RANDOM() > 0.95) AS wasting,
    (RANDOM() > 0.85) AS underweight,
    (RANDOM() > 0.75) AS stunting
/*
*/
  FROM
    ig_babies Babies  --  , ig_adata Anthropometric
  WHERE
        --  TODO: Restore.
        --  Babies.birth_date IS NOT NULL
        TRUE
    AND
        --  TODO: Restore.
        TRUE
        /*
        (
          SELECT
            (BabiesSub.boy IS NOT NULL OR BabiesSub.girl IS NOT NULL)
          FROM
            ig_babies BabiesSub
          WHERE
            BabiesSub.indexcol = Babies.indexcol
        )
        */
    AND
        --  TODO: Restore.
        TRUE
        /*
      (
        SELECT
          TouAnthropou.report_date IS NOT NULL
        FROM
          ig_adata TouAnthropou
        WHERE
          TouAnthropou.baby = Babies.indexcol
        ORDER BY TouAnthropou.report_date LIMIT 1
      )
      */
;
