from typing import Any

import httpx

from utils import build_upload_headers


from constants import CHECK_OLD_LIST_BASE_URL


async def api_list_online_applications(
    client: httpx.AsyncClient,
    token: str,
    tmp_secret:str,
    passportNo: str,
    pageNum: int = 1,
    pageSize: int = 10,
    authorization: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    """POST to ``{base_url}/application/online/list?pageNum=&pageSize=``.

    Returns ``(True, {status_code, response})`` on HTTP 200/201, else
    ``(False, {status_code, error})``. Network/parsing errors return
    ``status_code`` -1 and the exception message as ``error``.
    """
    try:
        url = f"{CHECK_OLD_LIST_BASE_URL}/application/online/list"
        # url = "https://bio.visaforchina.cn/onlineWeb/personalCenter/visa/historyForms?centerId=HAN3&site=HAN3_VI&language=vi_VN&userType=02&token=eyJhbGciOiJIUzUxMiJ9.eyJ3ZWJzaXRlX2xvZ2luX3VzZXJfa2V5IjoiMDFlYjhhYzctYTYzMC00MWE4LTk0MGEtODBhZWVmMzZmNTZkIn0.1vbVdFaIC7lmLT3StJOMDlhju_ahqS1kMCX-K545DfAgjVVa3lF809bdN3SZKdRM5mr6oSZefsE11j--XntV8A&username=wmtravelvn@gmail.com&time=1779780433442&routerPath=/HAN3_VI/qianzhengyewu"
        params = {"pageNum": pageNum, "pageSize": pageSize}
        headers = build_upload_headers(token, tmp_secret, authorization=authorization)
        payload = {"passportNo": passportNo}
        # eyJhbGciOiJIUzUxMiJ9.eyJ3ZWJzaXRlX2xvZ2luX3VzZXJfa2V5IjoiMDFlYjhhYzctYTYzMC00MWE4LTk0MGEtODBhZWVmMzZmNTZkIn0.1vbVdFaIC7lmLT3StJOMDlhju_ahqS1kMCX-K545DfAgjVVa3lF809bdN3SZKdRM5mr6oSZefsE11j--XntV8A
        resp = await client.post(url, params=params, headers=headers, json=payload)
        data = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {"raw": resp.text}
        )
        ok = resp.status_code in (200, 201)
        if not ok:
            return False, {
                "status_code": resp.status_code,
                "error": "failedListOnlineApplications",
                "response": data,
            }
        return True, {
            "status_code": resp.status_code,
            "response": data,
        }

    except Exception as e:
        return False, {
            "status_code": -1,
            "error": str(e),
        }


api_get_online_application_list_by_passport = api_list_online_applications