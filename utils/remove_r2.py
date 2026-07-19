# utils/r2_util.py
import boto3
from botocore.config import Config
from utils.r2_env import get_active_r2_config


def _get_r2_client_and_bucket():
    config = get_active_r2_config(log=True)

    s3 = boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    return s3, config.bucket_name


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
        print(f"Deleted {deleted_count} objects under r2://{bucket_name}/{prefix}", flush=True)
    return deleted_count 
