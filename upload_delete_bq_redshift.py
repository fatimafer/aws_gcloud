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

import argparse
import json
from google.cloud import bigquery
import boto3
from utilities import read_query

parser = argparse.ArgumentParser(description="Borrar/Crear BIGQUERY/REDSHIFT")
parser.add_argument("--action", default="delete", help="create para crear y delete para borrar")
args = parser.parse_args()

#Ejecutar la acción en BigQuery
QUERY = read_query(f"Scripts_sql/{args.action}_bigquery.sql")

try:
    client = bigquery.Client()
except Exception as e:
    print(f"Error occurred while creating BigQuery client: {e}")

try:
    query_job = client.query(QUERY)
    print("Query executed in BigQuery successfully for action:", args.action)
except Exception as e:
    print(f"Error occurred while executing query: {e}")

# Ejecutar la acción en Redshift
QUERY = read_query(f"Scripts_sql/{args.action}_RedShift.sql")

with open(".aws/redshift.json", mode="r", encoding="utf-8") as cf:
    params = json.load(cf)

workgroup_json = params["REDSHIFT_CONNECTION"]["workgroup"]
database_json = params["REDSHIFT_CONNECTION"]["database"]
secret_json = params["REDSHIFT_CONNECTION"]["secret"]


try:
    client = boto3.client("redshift-data")
except Exception as e:
    print(f"Error occurred while creating Redshift client: {e}")

try:
    statement = client.execute_statement(
        WorkgroupName=workgroup_json,
        Database=database_json,
        SecretArn=secret_json,
        Sql=QUERY,
    )
    print("Query executed in Redshift successfully for action:", args.action)
except Exception as e:
    print(f"Error occurred while executing query in Redshift: {e}")


print('fin')



