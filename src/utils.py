import boto3
import os

s3 = boto3.client('s3')

def download_files_from_s3(bucket, keys, local_dir="/tmp"):
    local_paths = []
    for key in keys:
        local_path = os.path.join(local_dir, os.path.basename(key))
        s3.download_file(bucket, key, local_path)
        local_paths.append(local_path)
    return local_paths

def upload_file_to_s3(bucket, local_path, s3_key):
    s3.upload_file(local_path, bucket, s3_key)
