import os
import argparse
import logging
import json
from datetime import datetime

from utilities import procesar_archivos_en_carpeta, upload_file_s3, upload_file_gcloud_storage, search_files_in_folder

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

        logging.info("Preparando la subida de archivos a: %s, bucket: %s", target, bucket)

        formats = targets[target]["output_formats"]

        for format in formats.keys():
            carpeta = formats[format]["carpeta"]
            bucket_folder = formats[format]["folder"]
            is_parquet = carpeta.endswith("parquet")

            logging.info("Procesando formato: %s, carpeta: %s, bucket_folder: %s", format, carpeta, bucket_folder)

            folder, archivos_csv = search_files_in_folder(bucket_folder, carpeta, fecha)

            for archivo_csv in archivos_csv:
                parquet_dir, ruta_salida = procesar_archivos_en_carpeta(carpeta, archivo_csv, delimiter, encoding
                                                                        , bucket_folder, is_parquet, move_processed=False)
                logging.info("Archivo .parquet guardado en: %s", parquet_dir)

                nombre_objeto = os.path.join(folder, os.path.basename(ruta_salida))

                if target == "s3":
                    try:
                        upload_file_s3(ruta_salida, bucket, nombre_objeto)
                        logging.info("Archivo subido a s3: %s/%s", bucket, nombre_objeto)
                    except Exception as e:
                        logging.error("Error al subir el archivo a s3: %s", str(e))

                if target == "GCS":
                    try:
                        if upload_file_gcloud_storage(bucket, ruta_salida, nombre_objeto):
                            logging.info("Archivo subido a Google Cloud Storage: %s/%s", bucket, nombre_objeto)
                    except Exception as e:
                        logging.error("Error al subir el archivo a Cloud Storage: %s", str(e))