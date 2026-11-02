import os
import shutil
import pandas as pd
import logging
from datetime import datetime
from google.cloud import storage
import boto3
from botocore.exceptions import ClientError
from google.cloud import bigquery


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


def process_gcloud_storage(bucket_name, source_file_name,  action=None, destination_blob_name=None):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    if action == "create":
        blob = bucket.blob(destination_blob_name)
        try:
            blob.upload_from_filename(source_file_name)
        except Exception as e:
            logging.error(e)
            return False
        return True

    else:
        blobs = storage_client.list_blobs(bucket.name)
        for blob in blobs:
            blob = bucket.blob(blob.name)
            logging.info(f"File {blob.name} will be deleted.") if blob.name.lower().startswith(source_file_name.lower()) else None
            blob.delete() if blob.name.lower().startswith(source_file_name.lower()) else None


def upload_file_s3(file_name, bucket, object_name=None):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def delete_file_s3(bucket_name, source_file_name):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    for object_summary in bucket.objects.all():
        # Los "directorios" en S3 son objetos vacíos cuya clave termina en "/"
        if object_summary.key.endswith('/'):
            continue
        logging.info(f"File {object_summary.key} will be deleted") if object_summary.key.lower().startswith(source_file_name.lower()) else None
        object_summary.delete() if object_summary.key.lower().startswith(source_file_name.lower()) else None

def read_query(file):
    with open(file, mode="r", encoding="utf-8") as cf:
        QUERY = cf.read()
    return QUERY

