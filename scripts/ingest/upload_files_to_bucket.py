import os
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
from tqdm import tqdm
import sys

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
ENDPOINT_URL = os.getenv("SUPABASE_STORAGE_ENDPOINT") 
BUCKET_NAME = os.getenv("SUPABASE_BUCKET")
REGION = os.getenv("AWS_REGION")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    endpoint_url=ENDPOINT_URL,
    region_name=REGION
)

def upload_pdfs(folder_path: str):

    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    file_list = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.pdf')]

    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        print("❌ Invalid folder path.")
        return

    pdf_files = list(folder.glob("*.pdf"))

    if not pdf_files:
        print("Folder exists, but no PDF files were found.")
        return

    for file_path in tqdm(pdf_files):
        key = file_path.name
        print(f"📄 Uploading: {key}")

        if key in file_list:
            print(f"✅ {key} already exists in the bucket, skipping.")
            continue
        else:
            try:
                s3.upload_file(
                    Filename=str(file_path),
                    Bucket=BUCKET_NAME,
                    Key=key,
                    ExtraArgs={"ContentType": "application/pdf"},
                )
            except ClientError as e:
                print(f"❌ Error uploading {key}: {e}")

    print("✅ Upload complete. Run `make sync-bucket` to process the files.")



def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        print("No folder path provided. Using default: backend/data/rag_articles")
        folder = input("📂 Enter path to folder with PDFs (normally backend/data/rag_articles)): ").strip()

    print(f"Using folder: {folder}")
    upload_pdfs(folder)
    # Your existing logic here, using `folder`

if __name__ == "__main__":
    main()
