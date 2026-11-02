import os
import shutil
import pandas as pd
import logging
import json

from datetime import datetime
from google.cloud import storage
from google.cloud import bigquery
import boto3


def open_json_file(parameters):
    with open(parameters, mode="r", encoding="utf-8") as js:
        params = json.load(js)
    js.close()
    return params

def configurar_logger(base_path, fecha):
    log_dir = os.path.join(base_path, "log", fecha)
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"log_{fecha}.log")

    # Crear logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.getLogger('botocore.credentials').setLevel(logging.WARNING)

    # Evitar duplicados si se llama varias veces
    if not logger.handlers:
        # Handler para archivo
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        # Handler para consola
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(stream_handler)

    return log_path


def mover_archivo(origen, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    shutil.move(origen, destino)

def search_files_in_folder(bucket_folder, source_folder):
    folder = bucket_folder + "_hotelbookings/"

    sufijo = "guests.csv" if bucket_folder == "Guests" else "reservations.csv"
    archivos_csv = [f for f in os.listdir(source_folder) if f.lower().endswith(sufijo)]

    if not archivos_csv:
        logging.warning("No se encontraron archivos .csv en %s", source_folder)
        exit(0)

    return folder, archivos_csv


def procesar_archivos_en_carpeta(input_folder, archivo, delimiter=",", encoding="utf-8"
                                 , cloud_folder="default", parquet_format=False, move_processed=True):

    ruta_entrada = os.path.join(input_folder, archivo)
    fecha = datetime.now().strftime("%Y%m%d")

    formato = "parquet" if parquet_format else "csv"

    local_output_dir = os.path.join(input_folder, formato, fecha)
    procesados_dir = os.path.join(input_folder, "procesados", fecha)
    fallos_dir = os.path.join(input_folder, "fallos", fecha)

    os.makedirs(local_output_dir, exist_ok=True)
    os.makedirs(procesados_dir, exist_ok=True)
    os.makedirs(fallos_dir, exist_ok=True)

    nombre_base = os.path.splitext(archivo)[0]
    ruta_salida = os.path.join(local_output_dir, f"{nombre_base}.{formato}")

    try:
        df = pd.read_csv(
            ruta_entrada,
            delimiter=delimiter,
            encoding=encoding,
            dtype=str,
            engine="python"
        )

        if cloud_folder != "Guests":
            df = df[df['Room Type'] == cloud_folder]

        if parquet_format==True:
            df.to_parquet(
                ruta_salida,
                engine="pyarrow",
                compression="snappy",
                index=False
            )

        else:
            df.to_csv(
                ruta_salida,
                sep=delimiter,
                encoding=encoding,
                index=False
            )


        logging.info(f"CONVERTIDO: {archivo} -> {ruta_salida}")
        mover_archivo(ruta_entrada, os.path.join(procesados_dir, archivo)) if move_processed == True else None

    except Exception as e:
        logging.error(f"ERROR en {archivo}: {str(e)}")
        mover_archivo(ruta_entrada, os.path.join(fallos_dir, archivo)) if move_processed == True else None

    return local_output_dir, ruta_salida


def upload_file_s3(file_name, bucket, object_name=None):
    # If S3 object_name was not specified, use file_name
    try:
        if object_name is None:
            object_name = os.path.basename(file_name)
        # Upload the file
        s3_client = boto3.client('s3')
        logging.info("S3 client created successfully for bucket: %s", bucket)
    except Exception  as e:
        logging.error("Failed to create S3 client: %s", str(e))
        return

    try:
        s3_client.upload_file(file_name, bucket, object_name)
        logging.info("Files uploaded to s3: %s/%s", bucket, object_name)
    except Exception as e:
        logging.error("Failed to upload files to s3: %s", str(e))


def delete_file_s3(bucket_name, source_file_name):
    try:
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)

        for object_summary in bucket.objects.all():
            # Se omiten los objetos que son directorios
            if object_summary.key.endswith('/'):
                continue
            if object_summary.key.lower().startswith(source_file_name.lower()):
                logging.info(f"File {object_summary.key} will be deleted")
                object_summary.delete()
                logging.info("Files successfully deleted in s3: %s", bucket)
    except Exception as e:
        logging.error("Failed to delete files in s3: %s", str(e))


class GCS(object):

    def __init__(self, bucket):
        self.bucket = bucket

        try:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket)
            logging.info("Google Cloud Storage client created successfully for bucket: %s", bucket)
        except Exception as e:
            logging.error("Failed to create Google Cloud Storage client: %s", str(e))
        return

    def upload_file(self, destination_blob_name, source_file_name):
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name)
            logging.info("Files uploaded to Google Cloud Storage: %s/%s", self.bucket.name, source_file_name)
        except Exception as e:
            logging.error("Failed to upload files to Google Cloud Storage: %s", str(e))

    def delete_file(self, bucket_folder):
        try:
            blobs = self.storage_client.list_blobs(self.bucket.name)
            for blob in blobs:
                blob = self.bucket.blob(blob.name)
                if blob.name.lower().startswith(bucket_folder.lower()):
                    logging.info(f"File {blob.name} will be deleted.")
                    blob.delete()
                    logging.info("Files successfully deleted in Google Cloud Storage: %s", self.bucket.name)
        except Exception as e:
            logging.error("Failed to delete files in Cloud Storage: %s", str(e))


def read_query(action, data_warehouse, folder):
    with open(f"{folder}/{action}_{data_warehouse}.sql", mode="r", encoding="utf-8") as qy:
        QUERY = qy.read()
        qy.close()
    return QUERY


def execute_bq(QUERY, action):
    try:
        client = bigquery.Client()
    except Exception as e:
        logging.error(f"Error occurred while creating BigQuery client: {e}")

    try:
        client.query(QUERY)
        logging.info("Query executed in BigQuery successfully for action: %s", action)
    except Exception as e:
        logging.error(f"Error occurred while executing query: {e}")


def execute_redshift(workgroup, database, secret, QUERY, action):
    try:
        client = boto3.client("redshift-data")
    except Exception as e:
        logging.error(f"Error occurred while creating Redshift client: {e}")

    try:
        client.execute_statement(
            WorkgroupName=workgroup,
            Database=database,
            SecretArn=secret,
            Sql=QUERY,
        )
        logging.info("Query executed in Redshift successfully for action: %s", action)
    except Exception as e:
        logging.error(f"Error occurred while executing query in Redshift: {e}")
