import argparse
import os
import boto3
import sys
import json

def upload_files_to_s3(bucket_name, local_files, s3_folder="input/"):
    s3 = boto3.client("s3")
    s3_keys = []

    for file in local_files:
        s3_key = f"{s3_folder}{os.path.basename(file)}"
        s3.upload_file(file, bucket_name, s3_key)
        print(f"Uploaded {file} to s3://{bucket_name}/{s3_key}")
        s3_keys.append(s3_key)

    return s3_keys

def upload_file_to_s3(bucket_name, file_path, s3_key):
    s3 = boto3.client("s3")
    s3.upload_file(file_path, bucket_name, s3_key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")

def download_file_from_s3(bucket_name, s3_key, local_path):
    s3 = boto3.client("s3")
    s3.download_file(bucket_name, s3_key, local_path)
    print(f"Downloaded s3://{bucket_name}/{s3_key} to {local_path}")

def invoke_lambda(function_name, payload):
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode("utf-8")
    )
    return json.loads(response['Payload'].read().decode("utf-8"))

def handle_merge(args):
    bucket = "tirth-pdf-service"
    lambda_function = "cloudpdf"

    if len(args.files) < 2:
        print("You must provide at least two PDF files to merge.")
        sys.exit(1)

    # Upload input files
    s3_keys = upload_files_to_s3(bucket, args.files)

    output_key = f"output/{args.output}"

    payload = {
        "action": "merge",
        "bucket": bucket,
        "input_files": s3_keys,
        "output_file": output_key
    }

    response = invoke_lambda(lambda_function, payload)
    print("Lambda response:", response)

    if response.get("status") == "success":
        local_output = os.path.basename(output_key)
        download_file_from_s3(bucket, response["output_file"], local_output)
        print(f"Downloaded merged file to {local_output}")
    else:
        print("Merge failed:", response.get("message", "Unknown error"))

def handle_split(args):
    bucket = "tirth-pdf-service"
    lambda_function = "cloudpdf"

    # Upload input file
    s3_keys = upload_files_to_s3(bucket, [args.file])
    s3_input_key = s3_keys[0]

    # Convert flat range list to list of tuples (e.g., 1 3 5 6 => [[1,3],[5,6]])
    if len(args.ranges) % 2 != 0:
        print("Split ranges must be in pairs (e.g., 1 3 5 6 means 1-3 and 5-6).")
        sys.exit(1)

    ranges = [[int(args.ranges[i]), int(args.ranges[i+1])] for i in range(0, len(args.ranges), 2)]

    payload = {
        "action": "split",
        "bucket": bucket,
        "input_file": s3_input_key,
        "ranges": ranges
    }

    response = invoke_lambda(lambda_function, payload)
    print("Lambda response:", response)

    if response.get("status") == "success":
        for output_key in response["output_files"]:
            local_output = os.path.basename(output_key)
            download_file_from_s3(bucket, output_key, local_output)
        print("Downloaded all split files.")
    else:
        print("Split failed:", response.get("message", "Unknown error"))

def main():
    parser = argparse.ArgumentParser(description="PDF Tool CLI for AWS Lambda + S3")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge PDF files")
    merge_parser.add_argument("files", nargs="+", help="PDF files to merge")
    merge_parser.add_argument("--output", "-o", required=True, help="Output merged file name (e.g., merged.pdf)")
    merge_parser.set_defaults(func=handle_merge)

    # Split command
    split_parser = subparsers.add_parser("split", help="Split a PDF file")
    split_parser.add_argument("file", help="PDF file to split")
    split_parser.add_argument("ranges", nargs="+", help="Page ranges to split (e.g., 1 3 5 6 means 1-3 and 5-6)")
    split_parser.set_defaults(func=handle_split)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
