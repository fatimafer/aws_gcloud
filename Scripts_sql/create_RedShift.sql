-- 1. Esquema de la demo
CREATE SCHEMA IF NOT EXISTS coral_cloud_demo;

-- 2. Tabla intermedia, igual que el Parquet: 18 columnas de texto en el mismo orden.
--    COPY desde Parquet asigna las columnas por posición y el número de columnas debe coincidir.
DROP TABLE IF EXISTS coral_cloud_demo.reservations_suite;

CREATE TABLE coral_cloud_demo.reservations_suite (
    reservation_id      VARCHAR(256),   -- Reservation ID
    contact_id          VARCHAR(256),   -- Contact ID
    check_in_date       VARCHAR(256),   -- Check-in Date (MM/DD/YYYY)
    check_out_date      VARCHAR(256),   -- Check-out Date (MM/DD/YYYY)
    room_type           VARCHAR(256),   -- Room Type
    room_number         VARCHAR(256),   -- Room Number
    rate_plan           VARCHAR(256),   -- Rate Plan
    total_price         VARCHAR(256),   -- Total Price
    taxes_and_fees      VARCHAR(256),   -- Taxes and Fees
    payment_status      VARCHAR(256),   -- Payment Status
    reservation_status  VARCHAR(256),   -- Reservation Status
    special_requests    VARCHAR(256),   -- Special Requests
    number_of_adults    VARCHAR(256),   -- Number of Adults
    number_of_children  VARCHAR(256),   -- Number of Children
    booking_channel     VARCHAR(256),   -- Booking Channel
    creation_date       VARCHAR(256),   -- Creation Date (MM/DD/YYYY)
    last_modified_date  VARCHAR(256)    -- Last Modified Date (MM/DD/YYYY)
);

-- 3. Carga desde S3 con el rol IAM por defecto del namespace.
--    Carga todos los objetos que haya bajo la carpeta (la ruta distingue mayúsculas).
COPY coral_cloud_demo.reservations_suite
FROM 's3://coral-cloud-demo-reservations/Suite_hotelbookings/'
IAM_ROLE default
FORMAT AS PARQUET;

-- 4. Tabla final con tipos: la que leerá Data 360 (mismo esquema que en BigQuery)
CREATE TABLE IF NOT EXISTS coral_cloud_demo.reservations_premium (
    reservation_id      VARCHAR(64) NOT NULL,
    contact_id          VARCHAR(64) NOT NULL,
    check_in_date       DATE,
    check_out_date      DATE,
    room_type           VARCHAR(64),
    room_number         VARCHAR(64),
    rate_plan           VARCHAR(64),
    total_price         DECIMAL(12,2),
    taxes_and_fees      DECIMAL(12,2),
    payment_status      VARCHAR(64),
    reservation_status  VARCHAR(64),
    special_requests    VARCHAR(64),
    number_of_adults    INTEGER,
    number_of_children  INTEGER,
    booking_channel     VARCHAR(64),
    creation_date       DATE,
    last_modified_date  DATE,
    source_system       VARCHAR(64),
    PRIMARY KEY (reservation_id)
);

-- 5. Vaciar y cargar convirtiendo los tipos
TRUNCATE coral_cloud_demo.reservations_premium;

INSERT INTO coral_cloud_demo.reservations_premium
SELECT
    reservation_id,
    contact_id,
    TO_DATE(check_in_date, 'MM/DD/YYYY'),
    TO_DATE(check_out_date, 'MM/DD/YYYY'),
    room_type,
    room_number,
    rate_plan,
    CAST(total_price AS DECIMAL(12,2)),
    CAST(taxes_and_fees AS DECIMAL(12,2)),
    payment_status,
    reservation_status,
    special_requests,
    CAST(number_of_adults AS INTEGER),
    CAST(number_of_children AS INTEGER),
    booking_channel,
    TO_DATE(creation_date, 'MM/DD/YYYY'),
    TO_DATE(last_modified_date, 'MM/DD/YYYY')
FROM coral_cloud_demo.reservations_suite;

-- 6. Quitar la tabla intermedia
DROP TABLE coral_cloud_demo.reservations_suite;