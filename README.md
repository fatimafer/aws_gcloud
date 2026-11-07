El propósito de este Repositorio es subir datos a Google Cloud y AWS que luego serán utilizados en los siguientes repositorios de DataCloud:
https://github.com/fatimafer/DC_connections.git
https://github.com/fatimafer/DC_objects.git

Para ello, es necesario disponer de credenciales de acceso a los servicios de Google Cloud y AWS. 
También es necesario tener activadas instancias de BigQuery y Redshift en los servicios de Google Cloud y AWS respectivamente.

Es necesario incluir los nombres de los buckets de S3 y de los datasets de BigQuery en el json [parameters.json](parameters.json).

Este repositorio contiene unos archivos de credenciales que muestran ejemplos de como preparar las credenciales en un entorno Cloud.
**En ningún caso, se trata de credenciales reales**

Se incluyen datos de ejemplo en formato .csv en la carpeta Sample_Data.

También se incluyen dos archivos .bat que sirven como ejemplo de lanzadores del script.

1. Para subir incluir la id de proyecto en gcloud en los lanzadores de ejemplo:
   * [win_create_launcher.bat](win_create_launcher.bat) Modificar la id de proyecto en gcloud y lanzar en la carpeta donde hayamos descargado el repositorio y con el entorno env correcto
   * [create_launcher.sh](create_launcher.sh) Modificar el el entorno de Conda y la id de proyecto en gcloud y lanzar en la carpeta donde hayamos descargado el repositorio y con el entorno env correcto
   
2. Para borrar ejecutar los lanzadores de ejemplo también con la id de proyecto en gcloud:
   * [win_delete_launcher.bat](win_delete_launcher.bat) Modificar la id de proyecto en gcloud y lanzar en la carpeta donde hayamos descargado el repositorio y con el entorno env correcto
   * [delete_launcher.sh](delete_launcher.sh) Modificar el el entorno de Conda y la id de proyecto en gcloud y lanzar en la carpeta donde hayamos descargado el repositorio y con el entorno env correcto