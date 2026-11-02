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
from datetime import datetime
import boto3

from utilities import (open_json_file,
                       procesar_archivos_en_carpeta, upload_file_s3, process_gcloud_storage, search_files_in_folder
                        , configurar_logger, delete_file_s3, read_query, execute_bq,execute_redshift)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Procesar archivos .csv y subirlos a las platafrormas cloud")
    parser.add_argument("--action", default="delete", help="create para crear y delete para borrar")

    args = parser.parse_args()

    fecha =datetime.now().strftime("%Y%m%d")
    encoding = "utf-8"
    delimiter = ","

    params = open_json_file(parameters="parameters.json")

    targets = params["TARGETS"]

    for target in targets.keys():

        bucket = targets[target]["bucket"]
        formats = targets[target]["output_formats"]

        for format in formats.keys():
            carpeta = formats[format]["carpeta"]
            bucket_folder = formats[format]["folder"]
            is_parquet = carpeta.endswith("parquet")

            log_file = configurar_logger(carpeta, fecha)
            logging.info("Conversion log will be saved in: %s", log_file)

            if args.action != "create":
                delete_file_s3(bucket, bucket_folder) if target == "s3" else None
                process_gcloud_storage(bucket, bucket_folder, args.action) if target == "GCS" else None

            else:
                folder, archivos_csv = search_files_in_folder(bucket_folder, carpeta)

                for archivo_csv in archivos_csv:
                    parquet_dir, ruta_salida = procesar_archivos_en_carpeta(carpeta, archivo_csv, delimiter, encoding
                                                                            , bucket_folder, is_parquet, move_processed=False)
                    logging.info("Files saved in: %s", parquet_dir)

                    nombre_objeto = os.path.join(folder, os.path.basename(ruta_salida))

                    upload_file_s3(ruta_salida, bucket, nombre_objeto) if target == "s3" else None
                    process_gcloud_storage(bucket, ruta_salida, args.action, nombre_objeto) if target == "GCS" else None


    carpeta = 'Scripts_sql'
    log_file = configurar_logger(carpeta, fecha)
    logging.info("Conversion log will be saved in: %s", log_file)

    #Ejecutar la acción en BigQuery

    QUERY = read_query(args.action, "bigquery")
    execute_bq(QUERY, args.action)


    # Ejecutar la acción en Redshift
    QUERY = read_query(args.action, "RedShift")
    params = open_json_file(parameters=".aws/redshift.json")

    execute_redshift(params["REDSHIFT_CONNECTION"]["workgroup"], params["REDSHIFT_CONNECTION"]["database"]
                     , params["REDSHIFT_CONNECTION"]["secret"], QUERY, args.action)

    logging.info("Script finished successfully.")


