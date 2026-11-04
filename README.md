Este repositorio contiene unos archivos de credenciales que muestran ejemplos de como preparar las credenciales en un entorno Cloud.
**En ningún caso, se trata de credenciales reales**



1. Abrimos desde la terminal donde descarguemos este repositorio

2. Para subir ejecutar el lanzador [create_launcher.bat](create_launcher.bat) o ejecutar el siguiente comando:
   set "AWS_CONFIG_FILE=.aws\config" && set "AWS_SHARED_CREDENTIALS_FILE=.aws\credentials" && set "AWS_PROFILE=default" && set "GCLOUD_PROJECT=[aquí introducimos el id de proyecto]" && set "GOOGLE_APPLICATION_CREDENTIALS=.gcloud\adc.json" && python upload_delete_all.py --action create 

3. Para borrar ejecutar el lanzador [delete_launcher.bat](delete_launcher.bat) o ejecutar el siguiente comando:
   set "AWS_CONFIG_FILE=.aws\config" && set "AWS_SHARED_CREDENTIALS_FILE=.aws\credentials" && set "AWS_PROFILE=default" && set "GCLOUD_PROJECT=[aquí introducimos el id de proyecto]" && set "GOOGLE_APPLICATION_CREDENTIALS=.gcloud\adc.json" && python upload_delete_all.py
