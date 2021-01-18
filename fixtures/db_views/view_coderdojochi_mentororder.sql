SELECT
   m.mentor_id,
   m.user_id,
   m.mentor_name,
   m.background_check,
   mo.check_in,
   mo.created_at AS sign_up_time,
   mo.session_id,
   s.code,
   s.title,
   s.start_date,
   s.end_date,
   date_part('hour' :: text, (s.end_date - s.start_date)) AS class_hours
FROM
   (
      (
         coderdojochi_mentororder mo
         JOIN view_weallcode_mentor m ON ((mo.mentor_id = m.mentor_id))
      )
      JOIN view_coderdojochi_session s ON ((mo.session_id = s.id))
   )
WHERE
   (mo.is_active = true);
