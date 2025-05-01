import json
import os
from pdf_service import merge_pdfs, split_pdf
from utils import download_files_from_s3, upload_file_to_s3

def lambda_handler(event, context):
    action = event.get("action")
    bucket = event.get("bucket")
    
    if action == "merge":
        s3_input_keys = event["s3_input_keys"]
        s3_output_key = event["s3_output_key"]

        local_files = download_files_from_s3(bucket, s3_input_keys)
        output_path = "/tmp/merged_file.pdf"
        merge_pdfs(local_files, output_path)
        upload_file_to_s3(bucket, output_path, s3_output_key)

        return {"status": "success", "output_file": s3_output_key}

    elif action == "split":
        s3_input_key = event["s3_input_key"]
        ranges = event["ranges"]
        output_dir = "/tmp/splits"

        os.makedirs(output_dir, exist_ok=True)
        input_file = download_files_from_s3(bucket, [s3_input_key])[0]
        split_pdf(input_file, ranges, output_dir)

        output_files = []
        for f in os.listdir(output_dir):
            local_path = os.path.join(output_dir, f)
            s3_key = f"output/{f}"
            upload_file_to_s3(bucket, local_path, s3_key)
            output_files.append(s3_key)

        return {"status": "success", "output_files": output_files}

    else:
        return {"status": "error", "message": "Unsupported action"}
