SELECT
    s.id,
    s.guardian_id,
    s.guardian_zip,
    s.first_name,
    s.last_name,
    s.birthday,
    s.age,
    s.gender,
    s.created_at,
    s.updated_at,
    s.is_active,
    s.school_name,
    s.school_type,
    CASE
        WHEN (sr.student_id IS NULL) THEN 'false' :: text
        ELSE 'true' :: text
    END AS ethnicity_entered,
    COALESCE(sr.eth_american_indian, (0) :: bigint) AS eth_american_indian,
    COALESCE(sr.eth_asian, (0) :: bigint) AS eth_asian,
    COALESCE(sr.eth_arab, (0) :: bigint) AS eth_arab,
    COALESCE(sr.eth_black_african_american, (0) :: bigint) AS eth_black_african_american,
    COALESCE(sr.eth_hispanic_latino, (0) :: bigint) AS eth_hispanic_latino,
    COALESCE(sr.eth_pacific_islander, (0) :: bigint) AS eth_pacific_islander,
    COALESCE(sr.eth_white, (0) :: bigint) AS eth_white,
    COALESCE(sr.eth_not_list, (0) :: bigint) AS eth_not_list
FROM
    (
        view_coderdojochi_student s
        LEFT JOIN view_student_race_ethnicity_unpivot sr ON ((s.id = sr.student_id))
    )
ORDER BY
    s.id;
