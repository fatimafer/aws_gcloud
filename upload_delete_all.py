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
from google.cloud import bigquery
import boto3

from utilities import (get_json_parameters,
                       procesar_archivos_en_carpeta, upload_file_s3, process_gcloud_storage, search_files_in_folder
                        , configurar_logger, delete_file_s3, read_query)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Procesar archivos .csv y subirlos a las platafrormas cloud")
    parser.add_argument("--action", default="delete", help="create para crear y delete para borrar")

    args = parser.parse_args()

    fecha =datetime.now().strftime("%Y%m%d")
    encoding = "utf-8"
    delimiter = ","

    params = get_json_parameters(parameters= "parameters.json")

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
                if target == "s3":
                    try:
                        delete_file_s3(bucket, bucket_folder)
                        logging.info("Files successfully deleted in s3: %s", bucket)
                    except Exception  as e:
                        logging.error("Failed to delete files in s3: %s", str(e))

                if target == "GCS":
                    try:
                        process_gcloud_storage(bucket, bucket_folder, args.action)
                        logging.info("Files successfully deleted in Google Cloud Storage: %s", bucket)
                    except Exception  as e:
                        logging.error("Failed to delete files in Cloud Storage: %s", str(e))

            elif args.action == "create":
                folder, archivos_csv = search_files_in_folder(bucket_folder, carpeta)

                for archivo_csv in archivos_csv:
                    parquet_dir, ruta_salida = procesar_archivos_en_carpeta(carpeta, archivo_csv, delimiter, encoding
                                                                            , bucket_folder, is_parquet, move_processed=False)
                    logging.info("Files saved in: %s", parquet_dir)

                    nombre_objeto = os.path.join(folder, os.path.basename(ruta_salida))

                    if target == "s3":
                        try:
                            upload_file_s3(ruta_salida, bucket, nombre_objeto)
                            logging.info("Files uploaded to s3: %s/%s", bucket, nombre_objeto)
                        except Exception as e:
                            logging.error("Failed to upload files to s3: %s", str(e))

                    if target == "GCS":
                        try:
                            if process_gcloud_storage(bucket, ruta_salida, args.action, nombre_objeto):
                                logging.info("Files uploaded to Google Cloud Storage: %s/%s", bucket, nombre_objeto)
                        except Exception as e:
                            logging.error("Failed to upload files to Google Cloud Storage: %s", str(e))


    #Ejecutar la acción en BigQuery
    QUERY = read_query(f"Scripts_sql/{args.action}_bigquery.sql")

    carpeta = 'Scripts_sql'
    log_file = configurar_logger(carpeta, fecha)
    logging.info("Conversion log will be saved in: %s", log_file)

    try:
        client = bigquery.Client()
    except Exception as e:
        logging.error(f"Error occurred while creating BigQuery client: {e}")

    try:
        query_job = client.query(QUERY)
        logging.info("Query executed in BigQuery successfully for action: %s", args.action)
    except Exception as e:
        logging.error(f"Error occurred while executing query: {e}")

    # Ejecutar la acción en Redshift
    QUERY = read_query(f"Scripts_sql/{args.action}_RedShift.sql")

    params = get_json_parameters(parameters=".aws/redshift.json")

    try:
        client = boto3.client("redshift-data")
    except Exception as e:
        logging.error(f"Error occurred while creating Redshift client: {e}")


    try:
        statement = client.execute_statement(
            WorkgroupName=params["REDSHIFT_CONNECTION"]["workgroup"],
            Database=params["REDSHIFT_CONNECTION"]["database"],
            SecretArn=params["REDSHIFT_CONNECTION"]["secret"],
            Sql=QUERY,
        )
        logging.info("Query executed in Redshift successfully for action: %s", args.action)
    except Exception as e:
        logging.error(f"Error occurred while executing query in Redshift: {e}")

    logging.info("Script finished successfully.")


