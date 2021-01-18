SELECT
    s.id,
    s.course_id,
    s.code,
    s.title,
    s.start_date,
    s.end_date,
    s.name,
    s.address,
    s.zip,
    s.capacity,
    s.teacher_id,
    s.is_active,
    s.created_at,
    s.mentor_capacity,
    s.gender_limitation,
    COALESCE(so.student_signup, (0) :: bigint) AS student_signup,
    COALESCE(so.student_attend, (0) :: bigint) AS student_attend,
    COALESCE(mo.mentor_signup, (0) :: bigint) AS mentor_signup,
    COALESCE(mo.mentor_attend, (0) :: bigint) AS mentor_attend
FROM
    (
        (
            view_coderdojochi_session s
            LEFT JOIN (
                SELECT
                    coderdojochi_order.session_id,
                    count(coderdojochi_order.student_id) AS student_signup,
                    sum(
                        CASE
                            WHEN (coderdojochi_order.check_in IS NOT NULL) THEN 1
                            ELSE 0
                        END
                    ) AS student_attend
                FROM
                    coderdojochi_order
                GROUP BY
                    coderdojochi_order.session_id
                ORDER BY
                    coderdojochi_order.session_id
            ) so ON ((s.id = so.session_id))
        )
        LEFT JOIN (
            SELECT
                coderdojochi_mentororder.session_id,
                count(coderdojochi_mentororder.mentor_id) AS mentor_signup,
                sum(
                    CASE
                        WHEN (coderdojochi_mentororder.check_in IS NOT NULL) THEN 1
                        ELSE 0
                    END
                ) AS mentor_attend
            FROM
                coderdojochi_mentororder
            GROUP BY
                coderdojochi_mentororder.session_id
            ORDER BY
                coderdojochi_mentororder.session_id
        ) mo ON ((s.id = mo.session_id))
    )
ORDER BY
    s.start_date;
