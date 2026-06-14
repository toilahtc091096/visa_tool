import os
from pathlib import Path

import boto3
from botocore.config import Config
from env_loader import load_dotenv


def upload_pdf_to_r2(file_path: str, prefix: str = "data/") -> str:
    """
    Upload 1 file PDF lên Cloudflare R2 theo prefix.
    Trả về key của file trên R2.
    """
    load_dotenv()

    endpoint_url = os.getenv("R2_ENDPOINT_URL")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("R2_BUCKET_NAME")

    missing = [
        k for k in [
            "R2_ENDPOINT_URL",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_BUCKET_NAME"
        ]
        if not os.getenv(k)
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    # normalize prefix
    prefix = prefix.lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    # init client
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # tạo key file trên R2
    key = f"{prefix}{file_path.name}"

    # upload
    s3.upload_file(
        str(file_path),
        bucket_name,
        key,
        ExtraArgs={"ContentType": "application/pdf"}
    )

    print(f"Uploaded: {file_path} -> r2://{bucket_name}/{key}")

    # cleanup local file
    file_path.unlink(missing_ok=True)

    return key
