SELECT
    m.id AS mentor_id,
    u.id AS user_id,
    (
        ((u.first_name) :: text || ' ' :: text) || (u.last_name) :: text
    ) AS mentor_name,
    m.is_active,
    m.created_at,
    date_trunc('month' :: text, m.created_at) AS created_month,
    m.updated_at,
    CASE
        WHEN (m.background_check IS TRUE) THEN 1
        ELSE 0
    END AS background_check,
    max(s.start_date) AS last_class_date,
    min(s.start_date) AS first_class_date,
    sum(
        CASE
            WHEN (s.start_date IS NOT NULL) THEN 1
            ELSE 0
        END
    ) AS num_classes,
    COALESCE(
        sum(
            date_part('hour' :: text, (s.end_date - s.start_date))
        ),
        (0) :: double precision
    ) AS hours_volunteered,
    date_part(
        'days' :: text,
        (
            (CURRENT_DATE) :: timestamp with time zone - max(s.start_date)
        )
    ) AS days_since_last_class,
    CASE
        WHEN (
            date_part(
                'days' :: text,
                (
                    (CURRENT_DATE) :: timestamp with time zone - max(s.start_date)
                )
            ) <= (365) :: double precision
        ) THEN 1
        ELSE 0
    END AS active_mentor,
    CASE
        WHEN (
            sum(
                CASE
                    WHEN (s.start_date IS NOT NULL) THEN 1
                    ELSE 0
                END
            ) > 0
        ) THEN 1
        ELSE 0
    END AS mentored
FROM
    (
        (
            (
                coderdojochi_mentor m
                LEFT JOIN coderdojochi_cdcuser u ON ((m.user_id = u.id))
            )
            LEFT JOIN coderdojochi_mentororder mo ON (
                (
                    (mo.mentor_id = m.id)
                    AND (mo.is_active = true)
                )
            )
        )
        LEFT JOIN view_coderdojochi_session s ON (
            (
                (mo.session_id = s.id)
                AND (s.is_active = true)
            )
        )
    )
WHERE
    (m.is_active = true)
GROUP BY
    m.id,
    m.user_id,
    u.id,
    (
        ((u.first_name) :: text || ' ' :: text) || (u.last_name) :: text
    ),
    m.is_active,
    m.created_at,
    m.updated_at,
    m.background_check
ORDER BY
    m.id;
