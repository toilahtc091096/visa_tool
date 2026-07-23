import os
from pathlib import Path

from utils.r2_env import build_r2_client


def upload_pdf_to_r2(file_path: str, prefix: str = "data/") -> str:
    """
    Upload 1 file PDF lên Cloudflare R2 theo prefix.
    Trả về key của file trên R2.
    """
    s3, config = build_r2_client(log=True)

    # normalize prefix
    prefix = prefix.lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # tạo key file trên R2
    key = f"{prefix}{file_path.name}"

    # upload
    s3.upload_file(
        str(file_path),
        config.bucket_name,
        key,
        ExtraArgs={"ContentType": "application/pdf"}
    )

    print(f"Uploaded: {file_path} -> r2://{config.bucket_name}/{key}", flush=True)

    # cleanup local file
    file_path.unlink(missing_ok=True)

    return key


def upload_pdf_to_r2_keep_local(file_path: str, prefix: str = "data/") -> str:
    """
    Upload 1 file PDF lên Cloudflare R2 theo prefix nhưng không xoá file local.
    Trả về key của file trên R2.
    """
    s3, config = build_r2_client(log=True)

    prefix = prefix.lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    key = f"{prefix}{file_path.name}"
    s3.upload_file(
        str(file_path),
        config.bucket_name,
        key,
        ExtraArgs={"ContentType": "application/pdf"},
    )
    print(f"Uploaded: {file_path} -> r2://{config.bucket_name}/{key}", flush=True)
    return key
