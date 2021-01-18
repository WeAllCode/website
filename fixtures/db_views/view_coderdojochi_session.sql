SELECT
   ses.id,
   ses.course_id,
   c.code,
   c.title,
   ses.start_date,
   ses.old_end_date AS end_date,
   l.name,
   l.address,
   l.zip,
   ses.capacity,
   ses.instructor_id AS teacher_id,
   ses.is_active,
   ses.created_at,
   ses.mentor_capacity,
   ses.gender_limitation
FROM
   (
      (
         coderdojochi_session ses
         LEFT JOIN coderdojochi_course c ON ((ses.course_id = c.id))
      )
      LEFT JOIN coderdojochi_location l ON ((ses.location_id = l.id))
   )
WHERE
   (ses.is_active = true);
