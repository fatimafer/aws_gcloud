SET @@location = 'europe-southwest1';
-- 1. Dataset.
--    Tiene que estar en la misma región que el bucket, y no se puede cambiar después.
CREATE SCHEMA IF NOT EXISTS coral_cloud_demo
OPTIONS (location = 'europe-southwest1');


-- 2. Carga del Parquet en una tabla intermedia. 
--    El esquema sale del propio fichero: 17 columnas de texto con los nombres originales.
LOAD DATA OVERWRITE coral_cloud_demo.stg_reservations_deluxe
FROM FILES (
  format = 'PARQUET',
  uris = ['gs://coral-cloud-demo/Deluxe_hotelbookings/CLOUD_Coral_Clouds_Hotel_Reservations.parquet']
);

-- 3. Tabla final con tipos.
CREATE OR REPLACE TABLE coral_cloud_demo.reservations_premium AS
SELECT
  `Reservation ID`                              AS reservation_id,
  `Contact ID`                                  AS contact_id,
  PARSE_DATE('%m/%d/%Y', `Check-in Date`)       AS check_in_date,
  PARSE_DATE('%m/%d/%Y', `Check-out Date`)      AS check_out_date,
  `Room Type`                                   AS room_type,
  `Room Number`                                 AS room_number,
  `Rate Plan`                                   AS rate_plan,
  CAST(`Total Price` AS NUMERIC)                AS total_price,
  CAST(`Taxes and Fees` AS NUMERIC)             AS taxes_and_fees,
  `Payment Status`                              AS payment_status,
  `Reservation Status`                          AS reservation_status,
  `Special Requests`                            AS special_requests,   
  CAST(`Number of Adults` AS INT64)             AS number_of_adults,
  CAST(`Number of Children` AS INT64)           AS number_of_children,
  `Booking Channel`                             AS booking_channel,
  PARSE_DATE('%m/%d/%Y', `Creation Date`)       AS creation_date,
  PARSE_DATE('%m/%d/%Y', `Last Modified Date`)  AS last_modified_date
FROM coral_cloud_demo.stg_reservations_deluxe;

-- 4. Quitar la tabla intermedia, para que Data 360 solo vea la tabla final
DROP TABLE coral_cloud_demo.stg_reservations_deluxe;