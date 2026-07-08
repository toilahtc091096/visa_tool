from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from api.api_login import login
from utils import build_upload_headers, log_event
from utils.token_store import load_login_payload, save_login_data


def _extract_candidate_link(data: Any) -> str:
    if isinstance(data, str):
        return data.strip()

    if isinstance(data, dict):
        for key in ("url", "downloadUrl", "fileUrl", "path", "data", "Data"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for key in ("Response", "response"):
            nested = data.get(key)
            candidate = _extract_candidate_link(nested)
            if candidate:
                return candidate

        for value in data.values():
            candidate = _extract_candidate_link(value)
            if candidate:
                return candidate

    if isinstance(data, list):
        for item in data:
            candidate = _extract_candidate_link(item)
            if candidate:
                return candidate

    return ""


async def api_download_application_form(
    client: httpx.AsyncClient,
    applyid: str,
    credential_key: str = "",
    authorization: str = "",
    output_dir: str | Path | None = None,
) -> tuple[bool, dict[str, Any]]:
    applyid = str(applyid).strip()
    if not applyid:
        log_event(
            {
                "level": "warn",
                "component": "api_download_application_form",
                "state": "missing_applyid",
            }
        )
        return False, {
            "status_code": -1,
            "error": "missing_applyid",
        }

    payload = load_login_payload()
    token = str(payload.get("token", "") or "").strip()
    tmp_secret = str(payload.get("tmpSecret", "") or "").strip()
    email = str(payload.get("userEmail", "") or "").strip()
    guid = str(payload.get("guid", "") or "").strip()
    uid = str(payload.get("uid", "") or "").strip()
    if not token or not tmp_secret:
        log_event(
            {
                "level": "warn",
                "component": "api_download_application_form",
                "state": "missing_login_payload",
                "applyid": applyid,
            }
        )
        return False, {
            "status_code": -1,
            "error": "missing_token_or_tmpSecret",
        }

    url = (
        "https://consular.mfa.gov.cn/VISA/api/cova-service/Visa/Apply/V2/"
        "DownloadApplicationForm"
    )
    log_event(
        {
            "level": "info",
            "component": "api_download_application_form",
            "state": "request_start",
            "applyid": applyid,
            "url": url,
        }
    )
    headers = build_upload_headers(
        token=token,
        tmp_secret=tmp_secret,
        email=email,
        guid=guid or "",
    )
    # headers.update(
    #     {
    #         "access_token": token,
    #         "content-type": "application/x-www-form-urlencoded",
    #         "form-token": applyid,
    #         "uid": uid or headers.get("uid", ""),
    #     }
    # )
    # if credential_key:
    #     headers["x-credential-key"] = credential_key

    async def _post_once() -> tuple[httpx.Response, dict[str, Any], str, str]:
        resp = await client.post(
            url,
            headers=headers,
            data={
                "applyid": applyid,
                "_t": str(int(time.time() * 1000)),
            },
        )
        is_json = resp.headers.get("content-type", "").lower().startswith("application/json")
        log_event(
            {
                "level": "info",
                "component": "api_download_application_form",
                "state": "response_received",
                "applyid": applyid,
                "status_code": resp.status_code,
                "content_type": resp.headers.get("content-type", ""),
            }
        )
        content_type_inner = resp.headers.get("content-type", "").lower()
        content_disposition_inner = resp.headers.get("content-disposition", "")
        if is_json:
            try:
                data_inner = resp.json()
            except ValueError:
                data_inner = {"raw": ""}
        else:
            data_inner = {}
        return resp, data_inner, content_type_inner, content_disposition_inner

    resp, data, content_type, content_disposition = await _post_once()
    ok = resp.status_code in (200, 201)

    if not ok and authorization.strip():
        log_event(
            {
                "level": "warn",
                "component": "api_download_application_form",
                "state": "request_failed_retry_login",
                "applyid": applyid,
                "status_code": resp.status_code,
            }
        )
        try:
            login_response = await asyncio.to_thread(login, authorization.strip())
            if login_response.data is None:
                raise RuntimeError("login_returned_empty_data")
            save_login_data(login_response.data)
            payload_after_login = load_login_payload()
            token = str(payload_after_login.get("token", "") or "").strip()
            tmp_secret = str(payload_after_login.get("tmpSecret", "") or "").strip()
            email = str(payload_after_login.get("userEmail", "") or "").strip()
            guid = str(payload_after_login.get("guid", "") or "").strip()
            headers = build_upload_headers(
                token=token,
                tmp_secret=tmp_secret,
                email=email,
                guid=guid or "",
            )
            resp, data, content_type, content_disposition = await _post_once()
            ok = resp.status_code in (200, 201)
        except Exception as exc:
            log_event(
                {
                    "level": "error",
                    "component": "api_download_application_form",
                    "state": "request_failed_retry_login_error",
                    "applyid": applyid,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    result: dict[str, Any] = {
        "status_code": resp.status_code,
        "response": data,
        "request": {
            "url": url,
            "headers": {
                "access_token": "***",
                "token": "***",
                "tmp_secret": "***",
                "form-token": applyid,
            },
            "data": {
                "applyid": applyid,
                "_t": "<generated>",
            },
        },
    }

    if not ok:
        log_event(
            {
                "level": "warn",
                "component": "api_download_application_form",
                "state": "request_failed",
                "applyid": applyid,
                "status_code": resp.status_code,
            }
        )
        result["error"] = "failedDownloadApplicationForm"
        return False, result

    if content_type.startswith("application/pdf") or resp.content.startswith(b"%PDF"):
        result["content_type"] = content_type or "application/pdf"
        result["content_disposition"] = content_disposition
        if output_dir is not None:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            filename = f"{applyid}_application_form.pdf"
            if content_disposition:
                import re

                filename_match = re.search(r'filename="?([^"]+)"?', content_disposition, re.I)
                if filename_match:
                    filename = filename_match.group(1)
            filename = Path(filename).name
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            file_path = output_path / filename
            file_path.write_bytes(resp.content)
            result["file_path"] = str(file_path)
            log_event(
                {
                    "level": "info",
                    "component": "api_download_application_form",
                    "state": "pdf_saved",
                    "applyid": applyid,
                    "file_path": str(file_path),
                    "byte_size": len(resp.content),
                }
            )
        return True, result

    if "application/json" in content_type:
        candidate_url = _extract_candidate_link(data)
        candidate_file = ""
        if isinstance(data, dict):
            for key in ("file", "content", "pdfBase64", "base64"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    candidate_file = value.strip()
                    break

        if candidate_url:
            if not candidate_url.lower().startswith("http"):
                candidate_url = urljoin(url, candidate_url)
            log_event(
                {
                    "level": "info",
                    "component": "api_download_application_form",
                    "state": "follow_download_url",
                    "applyid": applyid,
                    "source_url": candidate_url,
                }
            )
            file_resp = await client.get(candidate_url, follow_redirects=True)
            if file_resp.status_code in (200, 201) and (
                file_resp.content.startswith(b"%PDF")
                or "application/pdf" in file_resp.headers.get("content-type", "").lower()
            ):
                result["content_type"] = file_resp.headers.get("content-type", "")
                result["source_url"] = candidate_url
                if output_dir is not None:
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)
                    file_path = output_path / f"{applyid}.pdf"
                    file_path.write_bytes(file_resp.content)
                    result["file_path"] = str(file_path)
                    log_event(
                        {
                            "level": "info",
                            "component": "api_download_application_form",
                            "state": "pdf_saved_from_url",
                            "applyid": applyid,
                            "file_path": str(file_path),
                            "byte_size": len(file_resp.content),
                        }
                    )
                return True, result

        if candidate_file:
            if output_dir is not None:
                try:
                    import base64

                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)
                    decoded = base64.b64decode(candidate_file, validate=False)
                    file_path = output_path / f"{applyid}.pdf"
                    file_path.write_bytes(decoded)
                    result["file_path"] = str(file_path)
                    log_event(
                        {
                            "level": "info",
                            "component": "api_download_application_form",
                            "state": "pdf_saved_from_base64",
                            "applyid": applyid,
                            "file_path": str(file_path),
                            "byte_size": len(decoded),
                        }
                    )
                except Exception:
                    pass
            return True, result

    log_event(
        {
            "level": "warn",
            "component": "api_download_application_form",
            "state": "unexpected_response",
            "applyid": applyid,
            "status_code": resp.status_code,
            "content_type": content_type,
        }
    )
    return True, result
