import json
import time
import boto3

with open("./.aws/redshift.json", mode="r", encoding="utf-8") as cf:
    params = json.load(cf)

workgroup_json = params["REDSHIFT_CONNECTION"]["workgroup"]
database_json = params["REDSHIFT_CONNECTION"]["database"]
secret_json = params["REDSHIFT_CONNECTION"]["secret"]

client = boto3.client("redshift-data")

statement = client.execute_statement(
    WorkgroupName=workgroup_json,
    Database=database_json,
    SecretArn=secret_json,
    Sql="select distinct room_type from coral_cloud_demo.reservations_premium;",
)

# Devuelve un Id y hay que esperar a que la consulta termine
description = client.describe_statement(Id=statement["Id"])

while description["Status"] not in ("FINISHED", "FAILED", "ABORTED"):
    time.sleep(1)
    description = client.describe_statement(Id=statement["Id"])


# Cada campo llega como un dict de una sola clave: {"stringValue": "Suite"}, {"longValue": 3}, {"isNull": True}...
try:
    records = client.get_statement_result(Id=statement["Id"])["Records"]
except Exception as e:
    print(f"Error occurred while fetching statement result: {e}")
    records = []

for record in records:
    for field in record:
        print(None if field.get("isNull") else next(iter(field.values())))
