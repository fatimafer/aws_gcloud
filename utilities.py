import os
import shutil
import pandas as pd
import logging
from datetime import datetime
from google.cloud import storage
import boto3
from botocore.exceptions import ClientError


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




def procesar_archivos_en_carpeta(input_folder, archivo, delimiter=",", encoding="utf-8",bucket_name="default",parquet_format=True, extension=".dat"):

    ruta_entrada = os.path.join(input_folder, archivo)
    fecha = datetime.now().strftime("%Y%m%d")

    local_output_dir = os.path.join(input_folder, "parquet", fecha)
    procesados_dir = os.path.join(input_folder, "procesados", fecha)
    fallos_dir = os.path.join(input_folder, "fallos", fecha)

    os.makedirs(local_output_dir, exist_ok=True)
    os.makedirs(procesados_dir, exist_ok=True)
    os.makedirs(fallos_dir, exist_ok=True)

    nombre_base = os.path.splitext(archivo)[0]
    ruta_salida = os.path.join(local_output_dir, f"{nombre_base}.parquet")

    try:
        df = pd.read_csv(
            ruta_entrada,
            delimiter=delimiter,
            encoding=encoding,
            dtype=str,
            engine="python"
        )

        df = df[df['Room Type'] == bucket_name]

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
        mover_archivo(ruta_entrada, os.path.join(procesados_dir, archivo))
    except Exception as e:
        logging.error(f"ERROR en {archivo}: {str(e)}")
        mover_archivo(ruta_entrada, os.path.join(fallos_dir, archivo))

    return local_output_dir, ruta_salida


def upload_file_gcloud_storage(bucket_name, source_file_name, destination_blob_name):

    # Upload the file
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    try:
        blob.upload_from_filename(source_file_name)
    except Exception as e:
        logging.error(e)
        return False
    return True

def upload_file_s3(file_name, bucket, object_name=None):

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def search_files_in_folder(bucket_folder, source_folder, file_date):
    folder = bucket_folder + "_hotelbookings/"

    archivos_csv = [f for f in os.listdir(source_folder) if f.lower().endswith(".csv")]

    if not archivos_csv:
        logging.warning("No se encontraron archivos .csv en %s", source_folder)
        exit(0)

    log_file = configurar_logger(source_folder, file_date)
    logging.info("Log de conversión guardado en: %s", log_file)

    return folder, archivos_csv

def read_query(file):
    with open(file, mode="r", encoding="utf-8") as cf:
        QUERY = cf.read()
    return QUERY