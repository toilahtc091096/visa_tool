from pathlib import Path

from utils.r2_env import build_r2_client


def download_r2_folder(
    prefix: str = "data/", local_dir: str = "./resources/data"
) -> int:
    """
    Download tất cả object có prefix (vd: 'data/') từ Cloudflare R2 về local_dir.
    Trả về số file đã tải.
    """
    s3, config = build_r2_client(log=True)

    # chuẩn hoá prefix: bỏ / đầu và đảm bảo kết thúc bằng /
    prefix = prefix.lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=config.bucket_name, Prefix=prefix)

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

            s3.download_file(config.bucket_name, key, str(out_path))
            total += 1
            print(
                f"Downloaded: r2://{config.bucket_name}/{key} -> {out_path}", flush=True
            )

    print(
        f"Done. Downloaded {total} files from '{prefix}' into '{local_dir}'.",
        flush=True,
    )
    return total


# if __name__ == "__main__":
# download folder "data/" về thư mục local "./data"
# download_r2_folder(prefix=ctx.passportNumber, local_dir="./data")
