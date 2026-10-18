# pip freeze > requirements.txt
# pip list --format=freeze > requirements.txt

from google.cloud import bigquery

client = bigquery.Client()

QUERY = (
f"""SELECT DISTINCT room_type FROM coral_cloud_demo.reservations_premium;
""")
query_job = client.query(QUERY)  # API request

try:
    rows = query_job.result()
    for row in rows:
        print(row.room_type)    # Waits for query to finish
except Exception as e:
    print(f"Error occurred while executing query: {e}")


