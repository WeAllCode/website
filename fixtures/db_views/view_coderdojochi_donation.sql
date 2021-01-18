SELECT
   a.source,
   a.id,
   a.address_country,
   a.address_city,
   a.address_name,
   a.address_state,
   a.address_zip,
   a.first_name,
   a.last_name,
   a.payer_business_name,
   a.mc_fee,
   a.mc_gross,
   a.payment_date
FROM
   (
      SELECT
         'paypal' :: text AS source,
         paypal_ipn.id,
         paypal_ipn.address_country,
         paypal_ipn.address_city,
         paypal_ipn.address_name,
         paypal_ipn.address_state,
         paypal_ipn.address_zip,
         paypal_ipn.first_name,
         paypal_ipn.last_name,
         paypal_ipn.payer_business_name,
         paypal_ipn.mc_fee,
         paypal_ipn.mc_gross,
         paypal_ipn.payment_date
      FROM
         paypal_ipn
      UNION
      ALL
      SELECT
         'cdc' :: text AS source,
         coderdojochi_donation.id,
         NULL :: character varying AS "varchar",
         NULL :: character varying AS "varchar",
         NULL :: character varying AS "varchar",
         NULL :: character varying AS "varchar",
         NULL :: character varying AS "varchar",
         coderdojochi_donation.first_name,
         coderdojochi_donation.last_name,
         NULL :: character varying AS "varchar",
         NULL :: numeric AS "numeric",
         coderdojochi_donation.amount,
         coderdojochi_donation.created_at
      FROM
         coderdojochi_donation
   ) a
ORDER BY
   a.payment_date;
