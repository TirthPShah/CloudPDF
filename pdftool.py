import argparse
import os
import boto3
import sys
from PyPDF2 import PdfReader, PdfWriter

def upload_files_to_s3(bucket_name, local_files, s3_folder="input/"):
    s3 = boto3.client("s3")
    s3_keys = []

    for file in local_files:
        s3_key = f"{s3_folder}{os.path.basename(file)}"
        s3.upload_file(file, bucket_name, s3_key)
        print(f"Uploaded {file} to s3://{bucket_name}/{s3_key}")
        s3_keys.append(s3_key)

    return s3_keys

def invoke_lambda(function_name, payload):
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=bytes(str(payload).replace("'", '"'), encoding='utf-8')
    )
    return response['Payload'].read().decode("utf-8")

def split_pdf(input_pdf_path, ranges):
    reader = PdfReader(input_pdf_path)
    output_files = []
    
    base_filename = os.path.basename(input_pdf_path).split('.')[0]  # Get the file name without extension
    
    for r in ranges:
        start, end = r
        writer = PdfWriter()
        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])
        output_pdf_path = f"{base_filename}_{start}_{end}.pdf"
        with open(output_pdf_path, "wb") as output_pdf:
            writer.write(output_pdf)
        output_files.append(output_pdf_path)
    
    return output_files

def main():
    parser = argparse.ArgumentParser(description="PDF Tool CLI for splitting PDFs via AWS Lambda + S3")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Split command
    split_parser = subparsers.add_parser("split", help="Split PDF files")
    split_parser.add_argument("file", help="PDF file to split")
    split_parser.add_argument("--ranges", "-r", required=True, nargs="+", help="Ranges to split the PDF (e.g., 1-3 5-6)")

    args = parser.parse_args()

    if args.command == "split":
        bucket = "tirth-pdf-service"
        lambda_function = "cloudpdf"  # replace this with your actual lambda function name

        ranges = []
        for r in args.ranges:
            start, end = map(int, r.split('-'))
            ranges.append((start, end))

        # Split PDF locally first
        output_files = split_pdf(args.file, ranges)

        # Upload the split files to S3
        s3_keys = upload_files_to_s3(bucket, output_files)

        # Invoke Lambda
        payload = {
            "action": "split",
            "bucket": bucket,
            "input_file": args.file,
            "output_files": s3_keys
        }

        response = invoke_lambda(lambda_function, payload)
        print("Lambda response:", response)

if __name__ == "__main__":
    main()
