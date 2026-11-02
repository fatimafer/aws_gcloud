import boto3


s3 = boto3.resource('s3')
bucket = s3.Bucket("coral-cloud-demo-reservations")

for object_summary in bucket.objects.all():
    # Los "directorios" en S3 son objetos vacíos cuya clave termina en "/"
    if object_summary.key.endswith('/'):
        continue
    print(object_summary.key)
    object_summary.delete()

