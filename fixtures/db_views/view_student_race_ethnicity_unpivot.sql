SELECT
    sr.student_id,
    sum(
        CASE
            WHEN (r.id = 1) THEN 1
            ELSE 0
        END
    ) AS eth_american_indian,
    sum(
        CASE
            WHEN (r.id = 2) THEN 1
            ELSE 0
        END
    ) AS eth_asian,
    sum(
        CASE
            WHEN (r.id = 3) THEN 1
            ELSE 0
        END
    ) AS eth_arab,
    sum(
        CASE
            WHEN (r.id = 4) THEN 1
            ELSE 0
        END
    ) AS eth_black_african_american,
    sum(
        CASE
            WHEN (r.id = 5) THEN 1
            ELSE 0
        END
    ) AS eth_hispanic_latino,
    sum(
        CASE
            WHEN (r.id = 6) THEN 1
            ELSE 0
        END
    ) AS eth_pacific_islander,
    sum(
        CASE
            WHEN (r.id = 7) THEN 1
            ELSE 0
        END
    ) AS eth_white,
    sum(
        CASE
            WHEN (r.id = 8) THEN 1
            ELSE 0
        END
    ) AS eth_not_list
FROM
    (
        coderdojochi_student_race_ethnicity sr
        LEFT JOIN coderdojochi_raceethnicity r ON ((sr.raceethnicity_id = r.id))
    )
GROUP BY
    sr.student_id;
