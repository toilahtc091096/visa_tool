# utils/r2_util.py
import os
import boto3
from botocore.config import Config
from env_loader import load_dotenv


def _get_r2_client_and_bucket():
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
            "R2_BUCKET_NAME",
        ]
        if not os.getenv(k)
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    return s3, bucket_name


def delete_r2_folder(folder_name: str) -> int:
    """
    Xoá "thư mục" trên R2 theo folder_name (thực chất là xoá toàn bộ objects có prefix đó).
    Return: số object đã xoá.

    Ví dụ:
      delete_r2_folder("data/abc/")
      delete_r2_folder("/data/abc")  # vẫn ok, sẽ normalize
    """
    s3, bucket_name = _get_r2_client_and_bucket()

    # normalize folder_name -> prefix
    prefix = (folder_name or "").lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    paginator = s3.get_paginator("list_objects_v2")
    deleted_count = 0

    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        contents = page.get("Contents", [])
        if not contents:
            continue

        # S3/R2 delete_objects tối đa 1000 keys/lần
        keys = [{"Key": obj["Key"]} for obj in contents]
        resp = s3.delete_objects(Bucket=bucket_name, Delete={"Objects": keys, "Quiet": True})

        deleted_count += len(resp.get("Deleted", []))

        # nếu có lỗi xoá, raise để dễ debug
        errors = resp.get("Errors", [])
        if errors:
            raise RuntimeError(f"Delete errors: {errors}")
    if deleted_count != 0:
        print(f"Deleted {deleted_count} objects under r2://{bucket_name}/{prefix}")
    return deleted_count 