SELECT
   DISTINCT coderdojochi_student.school_name,
   count(*) AS count
FROM
   coderdojochi_student
WHERE
   (coderdojochi_student.is_active = true)
GROUP BY
   coderdojochi_student.school_name;
