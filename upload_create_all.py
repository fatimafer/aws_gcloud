# Guardar requisitos
# pip freeze > requirements.txt
# pip list --format=freeze > requirements.txt

# Instalar requisitos
# pip install -r requirements.txt

#Ejecutar con
# set GCLOUD_PROJECT=coral-cloud
# set GOOGLE_APPLICATION_CREDENTIALS=.gcloud/adc.json
# set AWS_PROFILE=mi-perfil o export AWS_PROFILE=mi-perfil
# set AWS_CONFIG_FILE=.aws\config
# set AWS_SHARED_CREDENTIALS_FILE=.aws\credentials


import os
import argparse
import logging
import json
from datetime import datetime

from utilities import procesar_archivos_en_carpeta, process_s3, process_gcloud_storage, search_files_in_folder, configurar_logger

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Procesar archivos .csv y subirlos a las platafrormas cloud")
    parser.add_argument("--action", default="delete", help="create para crear y delete para borrar")

    args = parser.parse_args()

    fecha =datetime.now().strftime("%Y%m%d")
    encoding = "utf-8"
    delimiter = ","

    with open("parameters.json", mode="r", encoding="utf-8") as cf:
        params = json.load(cf)
        targets = params["TARGETS"]
        del params
    cf.close()


    for target in targets.keys():

        bucket = targets[target]["bucket"]
        formats = targets[target]["output_formats"]

        for format in formats.keys():
            carpeta = formats[format]["carpeta"]
            bucket_folder = formats[format]["folder"]
            is_parquet = carpeta.endswith("parquet")

            log_file = configurar_logger(carpeta, fecha)
            logging.info("Log de conversión será guardado en: %s", log_file)

            if args.action != "create":
                if target == "GCS":
                    try:
                        process_gcloud_storage(bucket, bucket_folder, args.action)
                        logging.info("Archivos borrados en Google Cloud Storage: %s", bucket)
                    except Exception  as e:
                        logging.error("Error al borrar en Cloud Storage: %s", str(e))

            elif args.action == "create":
                folder, archivos_csv = search_files_in_folder(bucket_folder, carpeta)

                for archivo_csv in archivos_csv:
                    parquet_dir, ruta_salida = procesar_archivos_en_carpeta(carpeta, archivo_csv, delimiter, encoding
                                                                            , bucket_folder, is_parquet, move_processed=False)
                    logging.info("Archivo .parquet guardado en: %s", parquet_dir)

                    nombre_objeto = os.path.join(folder, os.path.basename(ruta_salida))

                    if target == "s3":
                        try:
                            process_s3(ruta_salida, bucket, nombre_objeto)
                            logging.info("Archivo subido a s3: %s/%s", bucket, nombre_objeto)
                        except Exception as e:
                            logging.error("Error al subir el archivo a s3: %s", str(e))

                    if target == "GCS":
                        try:
                            if process_gcloud_storage(bucket, ruta_salida, args.action, nombre_objeto):
                                logging.info("Archivo subido a Google Cloud Storage: %s/%s", bucket, nombre_objeto)
                        except Exception as e:
                            logging.error("Error al subir el archivo a Cloud Storage: %s", str(e))



