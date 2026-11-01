from google.cloud import storage
storage_client = storage.Client()
buckets = storage_client.list_buckets()
for bucket in buckets:
        print(bucket.name)
        blobs = storage_client.list_blobs(bucket.name)
        for blob in blobs:
                print(blob.name)



