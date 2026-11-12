# PASO 1: Subida de datos a Google Cloud y AWS


El propósito de este Repositorio es subir datos a Google Cloud y AWS que luego serán utilizados en los siguientes repositorios de DataCloud:
https://github.com/fatimafer/DC_connections.git
https://github.com/fatimafer/DC_objects.git



## Preparación de los entornos cloud
Es necesario disponer de credenciales de acceso a los servicios de Google Cloud y AWS. 
También es necesario tener activadas instancias de BigQuery y Redshift en los servicios de Google Cloud y AWS respectivamente.

Además, es necesario crear, dentro de los Buckets predeterminados los directorios con los siguientes nombres:
* Vip-Next-season_VIP-Customers dentro del bucket escogido para trabajar con s3.
* INPUT_Data_360_segments dentro del Bucket escogido para trabajar con GCS.

## Preparación de las credenciales
* Es necesario incluir los nombres de los buckets de S3 y de los datasets de BigQuery en el json [parameters.json](parameters.json).

Se preparan las credenciales de acceso a los servicios de Google Cloud y AWS en los directios [.aws](.aws) y [.gcloud](.gcloud) respectivamente.
Las credenciales que hay en esos archivos son ejemplos **En ningún caso, se trata de credenciales reales**

## Preparación de los datos de ejemplo
Se incluyen datos de ejemplo en formato .csv en la carpeta Sample_Data. Para que el script funcione con esos datos de prueba,
* Copiamos [CLOUD_Coral_Clouds_Hotel_Reservations.csv](Sample_data/CLOUD_Coral_Clouds_Hotel_Reservations.csv) en los directorios [conversion_dat_parquet](conversion_dat_parquet) y [conversion_dat_csv](conversion_dat_csv).
* Copiamos [CLOUD_Coral_Clouds_Guests.csv](Sample_data/CLOUD_Coral_Clouds_Guests.csv) en el directorio [conversion_dat_csv](conversion_dat_csv).

## Ejemplos de lanzadores.
También se incluyen dos archivos .bat que sirven como ejemplo de lanzadores del script.

1. Para subir incluir la id de proyecto en gcloud en los lanzadores de ejemplo:
   * [win_create_launcher.bat](win_create_launcher.bat) Modificar la id de proyecto en gcloud y lanzar en la carpeta donde hayamos descargado el repositorio y con el entorno env correcto
   * [create_launcher.sh](create_launcher.sh) Modificar el el entorno de Conda y la id de proyecto en gcloud y lanzar en la carpeta donde hayamos descargado el repositorio y con el entorno env correcto
   
2. Para borrar ejecutar los lanzadores de ejemplo también con la id de proyecto en gcloud:
   * [win_delete_launcher.bat](win_delete_launcher.bat) Modificar la id de proyecto en gcloud y lanzar en la carpeta donde hayamos descargado el repositorio y con el entorno env correcto
   * [delete_launcher.sh](delete_launcher.sh) Modificar el el entorno de Conda y la id de proyecto en gcloud y lanzar en la carpeta donde hayamos descargado el repositorio y con el entorno env correcto