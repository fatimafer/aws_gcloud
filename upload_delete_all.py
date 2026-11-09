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

from utilities import (open_json_file, GCS, s3,
                       process_files_in_folder, search_files_in_folder
                        , configure_logger, read_query, execute_bq, execute_redshift)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Procesar archivos .csv y subirlos a las platafrormas cloud")
    parser.add_argument("--action", default="delete", help="create para crear y delete para borrar")

    args = parser.parse_args()


    date =datetime.now().strftime("%Y%m%d")
    
    # Subimos o borramos archivos en las plataformas cloud
    encoding = "utf-8"
    delimiter = ","

    params = open_json_file(parameters="parameters.json")

    # Definir la carpeta de origen de scripts SQL
    qy_folder = 'Scripts_sql'

    # Definir las plataformas cloud de destino
    targets = params["TARGETS"]

    log_file = configure_logger(".", date)
    logging.info("Conversion log will be saved in: %s", log_file)

    for target in targets.keys():

        # Obtener el bucket y los formatos de salida para la plataforma actual
        bucket = targets[target]["bucket"]
        formats = targets[target]["output_formats"]

        # Inicializar el cliente del bucket según la plataforma cloud
        s3 = s3(bucket) if target == "s3" else None
        gcs = GCS(bucket) if target == "GCS" else None

        for format in formats.keys():

            # Obtener la carpeta de origen y la carpeta destino en el bucket para el formato actual
            origin_dir = formats[format]["origin_dir"]
            record_type = formats[format]["record_type"]

            # Determinar si los archivos se convertirán a Parquet o CSV
            is_parquet = origin_dir.endswith("parquet")

            # Configurar el logger para la carpeta de origen y la fecha actual
            # log_file = configure_logger(origin_dir, date)
            # logging.info("Conversion log will be saved in: %s", log_file)

            if args.action == "delete":
                s3.delete_file_s3(record_type) if target == "s3" else None
                gcs.delete_file(record_type) if target == "GCS" else None

            else:

                # Buscar archivos en la carpeta de origen
                bucket_folder, raw_files = search_files_in_folder(record_type, origin_dir)

                # Realizamos las transformaciones
                for raw_file in raw_files:
                    conversion_dir, converted_file = process_files_in_folder(origin_dir, raw_file, delimiter, encoding
                                                                             , record_type, is_parquet, date, move_processed=False)
                    logging.info("Files saved in: %s", conversion_dir)

                    object_name_in_bucket = os.path.join(bucket_folder, os.path.basename(converted_file))

                    # Subir el archivo convertido a la plataforma cloud correspondiente
                    s3.upload_file_s3(converted_file, object_name_in_bucket) if target == "s3" else None
                    gcs.upload_file(object_name_in_bucket, converted_file) if target == "GCS" else None


            # Subimos o borramos a las Data Warehouses Redshift o BigQuery según el destino.
            # Solo se sube si el archivo está en formato .parquet
            if is_parquet is True:

                # Cargar la consulta SQL correspondente
                QUERY = read_query(args.action, ("RedShift" if target == "s3" else "bigquery"), qy_folder)

                # Ejecutar la consulta SQL en Redshift o BigQuery según el destino
                execute_redshift(".aws/redshift.json", QUERY, args.action) if target == "s3" else None
                execute_bq(QUERY, args.action) if target == "GCS" else None


logging.info("Script finished successfully.")

