SELECT
   o.id,
   o.session_id,
   o.student_id,
   o.is_active,
   o.check_in,
   o.created_at,
   s.first_name,
   s.last_name,
   s.guardian_zip,
   s.age,
   s.gender,
   s.school_name,
   s.school_type,
   s.eth_american_indian,
   s.eth_asian,
   s.eth_arab,
   s.eth_black_african_american,
   s.eth_hispanic_latino,
   s.eth_pacific_islander,
   s.eth_white,
   s.eth_not_list,
   ses.code,
   ses.title,
   ses.start_date,
   ses.end_date,
   ses.name
FROM
   (
      (
         coderdojochi_order o
         LEFT JOIN view_coderdojochi_session ses ON ((o.session_id = ses.id))
      )
      LEFT JOIN view_coderdojochi_student_w_eth s ON ((o.student_id = s.id))
   )
WHERE
   (o.is_active = true);
