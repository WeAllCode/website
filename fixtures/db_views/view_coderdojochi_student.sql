SELECT
   max(s.id) AS id,
   s.guardian_id,
   g.zip AS guardian_zip,
   s.first_name,
   s.last_name,
   s.birthday,
   (
      date_part(
         'day' :: text,
         (
            (CURRENT_DATE) :: timestamp with time zone - s.birthday
         )
      ) / (365) :: double precision
   ) AS age,
   COALESCE(dq.mapping, 'unknown' :: character varying) AS gender,
   max(s.created_at) AS created_at,
   max(s.updated_at) AS updated_at,
   s.is_active,
   s.school_name,
   s.school_type
FROM
   (
      (
         coderdojochi_student s
         LEFT JOIN (
            SELECT
               coderdojochi_guardian.id,
               coderdojochi_guardian.user_id,
               coderdojochi_guardian.is_active,
               coderdojochi_guardian.phone,
               coderdojochi_guardian.created_at,
               coderdojochi_guardian.updated_at,
               coderdojochi_guardian.zip
            FROM
               coderdojochi_guardian
            WHERE
               (coderdojochi_guardian.is_active = true)
         ) g ON ((s.guardian_id = g.id))
      )
      LEFT JOIN dq_lookup_gender dq ON (((dq.value) :: text = (s.gender) :: text))
   )
WHERE
   (s.is_active = true)
GROUP BY
   s.guardian_id,
   g.zip,
   s.first_name,
   s.last_name,
   s.birthday,
   s.gender,
   s.is_active,
   s.school_name,
   s.school_type,
   dq.mapping;
