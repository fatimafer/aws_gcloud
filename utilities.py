import os
import shutil
import pandas as pd
import logging
import json

from datetime import datetime
from google.cloud import storage
from google.cloud import bigquery
import boto3


# Cargar parámetros desde un archivo JSON
def open_json_file(parameters):
    with open(parameters, mode="r", encoding="utf-8") as js:
        params = json.load(js)
    js.close()
    return params

# Configurar el logger para registrar eventos en un archivo de log y en la consola
def configure_logger(base_path, date):
    log_dir = os.path.join(base_path, "log", date)
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"log_{date}.log")

    # Configurar el logger para registrar eventos en un archivo de log y en la consola
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.getLogger('botocore.credentials').setLevel(logging.WARNING)

    # Evitar agregar múltiples handlers si el logger ya tiene handlers configurados
    if not logger.handlers:
        # Handler para registrar eventos en un archivo de log
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        # Handler para registrar eventos en la consola
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(stream_handler)

    return log_path


def move_file(source, target):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.move(source, target)

def search_files_in_folder(bucket_folder, source_folder):

    # Generar la ruta de la carpeta en el bucket de destino
    folder = bucket_folder + "_hotelbookings/"

    # Buscar archivos .csv en la carpeta de origen que coincidan con el tipo de registro correspondiente
    sufijo = "guests.csv" if bucket_folder == "Guests" else "reservations.csv"
    archivos_csv = [f for f in os.listdir(source_folder) if f.lower().endswith(sufijo)]

    if not archivos_csv:
        logging.warning("No se encontraron archivos .csv en %s", source_folder)
        exit(0)

    return folder, archivos_csv


def process_files_in_folder(input_folder, file, delimiter=",", encoding="utf-8"
                            , record_type="default", parquet_format=False, date=None, move_processed=True, ):

    # Determinar la ruta de origen de los archivos
    source_dir = os.path.join(input_folder, file)

    # Establecer la fecha actual si no se proporciona una fecha específica
    if date is None:
        date = datetime.now().strftime("%Y%m%d")

    # Determinar el formato de salida
    output_format = "parquet" if parquet_format else "csv"

    # Definir las rutas de salida para los archivos procesados, fallidos y convertidos
    local_output_dir = os.path.join(input_folder, output_format, date)
    processed_dir = os.path.join(input_folder, "procesados", date)
    errors_dir = os.path.join(input_folder, "fallos", date)

    # Crear las carpetas de salida si no existen
    os.makedirs(local_output_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(errors_dir, exist_ok=True)

    #Eliminamos la extensión de origen del archivo para quedarnos solo con el nombre
    base_name = os.path.splitext(file)[0]

    #Generar el nombre del archivo de salida con la extensión correspondiente al formato de salida
    output_file_name = os.path.join(local_output_dir, f"{base_name}.{output_format}")

    # Creamos un DataFrame a partir del archivo de origen
    try:
        df = pd.read_csv(
            source_dir,
            delimiter=delimiter,
            encoding=encoding,
            dtype=str,
            engine="python"
        )

        # Filtramos el DataFrame para eliminar tipos de registros que no proceden
        if record_type != "Guests":
            df = df[df['Room Type'] == record_type]

        # Convertimos el DataFrame a Parquet o CSV según el formato de salida especificado
        if parquet_format==True:
            df.to_parquet(
                output_file_name,
                engine="pyarrow",
                compression="snappy",
                index=False
            )

        else:
            df.to_csv(
                output_file_name,
                sep=delimiter,
                encoding=encoding,
                index=False
            )


        logging.info(f"CONVERTIDO: {file} -> {output_file_name}")

        # Movemos el archivo procesado a la carpeta de procesados si se especifica move_processed=True
        move_file(source_dir, os.path.join(processed_dir, file)) if move_processed == True else None

    except Exception as e:
        logging.error(f"ERROR en {file}: {str(e)}")

        # Movemos el archivo procesado a la carpeta de procesados si se especifica move_processed=True
        move_file(source_dir, os.path.join(errors_dir, file)) if move_processed == True else None

    return local_output_dir, output_file_name


def upload_file_s3(file_name, bucket, object_name=None):
    # Si no se proporciona un nombre de objeto, se utiliza el nombre del archivo como nombre de objeto
    try:
        if object_name is None:
            object_name = os.path.basename(file_name)

        # Subimos el archivo al bucket de S3 utilizando el cliente de boto3
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

    # Inicializamos el recurso de S3 utilizando boto3
    try:
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        logging.info("S3 resource created successfully for bucket: %s", bucket_name)
    except Exception  as e:
        logging.error("Failed to create S3 resource: %s", str(e))
        return

    try:
        for object_summary in bucket.objects.all():
            # Listamos los objetos en el bucket que no sean "directorios" (objetos vacíos cuya clave termina en "/")
            if object_summary.key.endswith('/'):
                continue
            # Verificamos si el nombre del objeto en S3 coincide con el nombre del archivo que queremos eliminar
            if object_summary.key.lower().startswith(source_file_name.lower()):
                logging.info(f"File {object_summary.key} will be deleted")
                object_summary.delete()
                logging.info("Files successfully deleted in s3: %s", bucket)
    except Exception as e:
        logging.error("Failed to delete files in s3: %s", str(e))


class GCS(object):

    # Inicializamos la clase GCS con el nombre del bucket de Google Cloud Storage
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

            # Subimos el archivo al bucket de Google Cloud Storage utilizando el cliente de storage
            blob.upload_from_filename(source_file_name)
            logging.info("Files uploaded to Google Cloud Storage: %s/%s", self.bucket.name, source_file_name)
        except Exception as e:
            logging.error("Failed to upload files to Google Cloud Storage: %s", str(e))

    def delete_file(self, bucket_folder):
        try:

            # Obtenemos la lista de blobs (archivos) en el bucket de Google Cloud Storage
            blobs = self.storage_client.list_blobs(self.bucket.name)

            # Iteramos sobre los archivos del bucket
            for blob in blobs:
                blob = self.bucket.blob(blob.name)

                # Verificamos si el nombre del blob coincide con el nombre del archivo que queremos eliminar
                if blob.name.lower().startswith(bucket_folder.lower()):
                    logging.info(f"File {blob.name} will be deleted.")
                    blob.delete()
                    logging.info("Files successfully deleted in Google Cloud Storage: %s", self.bucket.name)
        except Exception as e:
            logging.error("Failed to delete files in Cloud Storage: %s", str(e))


def read_query(action, data_warehouse, folder):
    # Leer la consulta SQL desde un archivo
    with open(f"{folder}/{action}_{data_warehouse}.sql", mode="r", encoding="utf-8") as qy:
        QUERY = qy.read()
        qy.close()
    return QUERY


def execute_bq(QUERY, action):
    # Inicializamos el cliente de BigQuery
    try:
        client = bigquery.Client()
    except Exception as e:
        logging.error(f"Error occurred while creating BigQuery client: {e}")

    # Ejecutamos la consulta SQL en BigQuery
    try:
        client.query(QUERY)
        logging.info("Query executed in BigQuery successfully for action: %s", action)
    except Exception as e:
        logging.error(f"Error occurred while executing query: {e}")



def execute_redshift(prm_file, QUERY, action):

    # Inicializamos el cliente de Redshift Data API utilizando boto3
    try:
        client = boto3.client("redshift-data")
    except Exception as e:
        logging.error(f"Error occurred while creating Redshift client: {e}")

    # Inicializamos los parámetros de conexión
    params = open_json_file(prm_file)

    # Ejecutamos la consulta SQL en Redshift utilizando el cliente de Redshift
    try:
        client.execute_statement(
            WorkgroupName=params["REDSHIFT_CONNECTION"]["workgroup"],
            Database=params["REDSHIFT_CONNECTION"]["database"],
            SecretArn=params["REDSHIFT_CONNECTION"]["secret"],
            Sql=QUERY,
        )
        logging.info("Query executed in Redshift successfully for action: %s", action)
    except Exception as e:
        logging.error(f"Error occurred while executing query in Redshift: {e}")
