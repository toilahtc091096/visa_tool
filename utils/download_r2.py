import os
from pathlib import Path

import boto3
from botocore.config import Config
from env_loader import load_dotenv


def download_r2_folder(
    prefix: str = "data/", local_dir: str = "./resources/data"
) -> int:
    """
    Download tất cả object có prefix (vd: 'data/') từ Cloudflare R2 về local_dir.
    Trả về số file đã tải.
    """
    load_dotenv()

    endpoint_url = os.getenv("R2_ENDPOINT_URL")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("R2_BUCKET_NAME")

    missing = [
        k
        for k in [
            "R2_ENDPOINT_URL",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_BUCKET_NAME",
        ]
        if not os.getenv(k)
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    # chuẩn hoá prefix: bỏ / đầu và đảm bảo kết thúc bằng /
    prefix = prefix.lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    local_base = Path(local_dir)
    total = 0

    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue  # bỏ qua folder marker

            # path local = local_dir + phần sau prefix
            rel = key[len(prefix) :] if key.startswith(prefix) else key
            out_path = local_base / rel
            out_path.parent.mkdir(parents=True, exist_ok=True)

            s3.download_file(bucket_name, key, str(out_path))
            total += 1
            print(f"Downloaded: r2://{bucket_name}/{key} -> {out_path}")

    print(f"Done. Downloaded {total} files from '{prefix}' into '{local_dir}'.")
    return total


# if __name__ == "__main__":
    # download folder "data/" về thư mục local "./data"
    # download_r2_folder(prefix=ctx.passportNumber, local_dir="./data")
