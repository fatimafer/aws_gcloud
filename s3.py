import os
import argparse
import logging
from datetime import datetime
from utilities import procesar_archivos_en_carpeta, upload_file_s3, search_files_in_folder

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Procesar archivos .csv y convertirlos a Parquet con clasificación por fecha.")
    parser.add_argument("carpeta", help="Ruta a la carpeta que contiene los archivos .dat")
    parser.add_argument("--delimiter", default="|", help="Delimitador de los archivos")
    parser.add_argument("--encoding", default="utf-8", help="Codificación de los archivos")
    parser.add_argument("--fecha", default=datetime.now().strftime("%Y%m%d"), help="fecha de los archivos")
    parser.add_argument("--bucket", help="Nombre del bucket de destino en S3")
    parser.add_argument("--folder", help="carpeta dentro del bucket")

    args = parser.parse_args()

    is_parquet = args.carpeta.endswith("parquet")

    folder, archivos_csv = search_files_in_folder(args.folder, args.carpeta, args.fecha)

    for archivo_csv in archivos_csv:
        parquet_dir, ruta_salida = procesar_archivos_en_carpeta(args.carpeta, archivo_csv, args.delimiter, args.encoding
                                                                , args.folder, is_parquet)
        logging.info("Archivo .parquet guardado en: %s", parquet_dir)

        nombre_objeto = os.path.join(folder, os.path.basename(ruta_salida))

        try:
            upload_file_s3(ruta_salida, args.bucket, nombre_objeto)
            logging.info("Archivo subido a S3: %s/%s", args.bucket, nombre_objeto)
        except Exception as e:
            logging.error("Error al subir el archivo a S3: %s", str(e))