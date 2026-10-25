Este repositorio contiene unos archivos de credenciales que muestran ejemplos de como preparar las credenciales en un entorno Cloud.

En ningún caso, se trata de credenciales reales


EJEMPLOS PARÁMETROS DE EJECUCION:
PARQUET A S3: conversion_dat_parquet --delimiter "," --encoding "utf-8" --bucket "coral-cloud-demo-reservations" --folder "Suite"
PARQUET GOOGLE CLOUD STORAGE: conversion_dat_parquet --delimiter "," --encoding "utf-8" --bucket "coral-cloud-demo" --folder "Deluxe"
CSV A S3: conversion_dat_csv --delimiter "," --encoding "utf-8" --bucket "coral-cloud-demo-reservations" --folder "Standard"
CSV A GOOGLE CLOUD STORAGE: conversion_dat_csv --delimiter "," --encoding "utf-8" --bucket "coral-cloud-demo" --folder "Guests"

SUBIR A BIGQUERY Y REDSHIFT: --action create
BORRAR CSV Y REDSHIFT: NO ES NECESARIO NINGÚN PARÁMETRO

