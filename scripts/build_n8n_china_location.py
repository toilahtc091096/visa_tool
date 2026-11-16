"""Build the n8n sub-workflow "WF-COMMON Resolve China Division".

One place for every flow that needs a Chinese province / city / district
(WF-04D Special Documents, WF-04D School, WF-04I Visit Relatives):

  Prepare -> AI Extract Divisions (one shared prompt)
          -> Match Locations (filter on resources/china_locations.json)
          -> Need Nearest? -> AI Nearest (pick from candidates) -> Apply Nearest
          -> Restore Order

Output fields (added to the caller's item): provinceNamePinyin / cityNamePinyin /
districtNamePinyin (exactly the `name` in china_locations.json, so /run always
resolves them), provinceNameCn / cityNameCn / districtNameCn, province_code /
city_code / district_code (COVA codes) and china_location (match details).

Sources: scripts/n8n_china_location/*.js|*.txt and resources/china_locations.json.
The workflow id, name and credentials are kept from the existing file.

Usage:
  python scripts/build_n8n_china_location.py [path/to/WF-COMMON Resolve China Division.json]
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "n8n_china_location"
LOCATIONS = ROOT / "resources" / "china_locations.json"
DEFAULT_OUT = ROOT / "n8n-flow" / "WF-COMMON Resolve China Division.json"
DATA_MARK = "/*__CHINA_LOCATIONS__*/ null"
AI_MODEL = "gpt-4.1"

# Used when the existing file has no OpenAI credential to copy.
DEFAULT_OPENAI_CREDENTIALS = {"openAiApi": {"id": "1M9yXBtGqqfHCDhA", "name": "OpenAI account"}}


def _read(name: str) -> str:
    return (SRC / name).read_text(encoding="utf-8")


def _compact_locations() -> str:
    data = json.loads(LOCATIONS.read_text(encoding="utf-8"))
    compact = {
        "p": [[r["id"], r["code"], r["name"], r.get("cn", "")] for r in data["provinces"]],
        "c": [
            [r["id"], r["code"], r["parent_id"], r["name"], r.get("cn", "")]
            for r in data["cities"]
        ],
        "k": [
            [r["id"], r["code"], r["parent_id"], r["name"], r.get("cn", ""), r.get("postcode", "")]
            for r in data["counties"]
        ],
    }
    return json.dumps(compact, ensure_ascii=False, separators=(",", ":"))


def _node_id(name: str) -> str:
    # Stable ids: rebuilding does not change node ids.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "wf-common-china-division/" + name))


def _code(name: str, js: str, x: int, y: int) -> dict:
    return {
        "parameters": {"jsCode": js},
        "id": _node_id(name),
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [x, y],
    }


def _openai(name: str, system: str, user: str, max_tokens: int, x: int, y: int, creds: dict) -> dict:
    return {
        "parameters": {
            "modelId": {
                "__rl": True,
                "value": AI_MODEL,
                "mode": "list",
                "cachedResultName": AI_MODEL,
            },
            "responses": {
                "values": [
                    {"role": "system", "content": system},
                    {"content": user},
                ]
            },
            "builtInTools": {},
            "options": {
                "maxTokens": max_tokens,
                "textFormat": {"textOptions": {"type": "json_object"}},
                "temperature": 0,
            },
        },
        "id": _node_id(name),
        "name": name,
        "type": "@n8n/n8n-nodes-langchain.openAi",
        "typeVersion": 2.3,
        "position": [x, y],
        "credentials": creds,
        "retryOnFail": True,
        "maxTries": 3,
        "waitBetweenTries": 2000,
    }


def build(out_path: Path) -> None:
    old = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    creds = next(
        (
            n["credentials"]
            for n in old.get("nodes", [])
            if n.get("type") == "@n8n/n8n-nodes-langchain.openAi" and n.get("credentials")
        ),
        DEFAULT_OPENAI_CREDENTIALS,
    )

    common = _read("common.js")
    match_js = _read("match.js")
    if DATA_MARK not in match_js:
        raise SystemExit(f"{DATA_MARK!r} not found in match.js")
    match_js = match_js.replace(DATA_MARK, _compact_locations())

    extract_user = (
        "=address: {{ $json._loc_address }}\n"
        "hint (may be wrong or empty): {{ $json._loc_hint }}"
    )
    nearest_user = (
        "=address: {{ $json._loc_address }}\n"
        "extracted: {{ $json._loc_nearest.extracted }}\n"
        "already matched: {{ $json._loc_nearest.matched }}\n"
        "choose: {{ $json._loc_nearest.choose }}\n"
        "candidates:\n"
        "{{ $json._loc_nearest.candidatesText }}"
    )

    nodes = [
        {
            "parameters": {"inputSource": "passthrough"},
            "id": _node_id("Input Divisions"),
            "name": "Input Divisions",
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1.2,
            "position": [-880, 80],
        },
        _code("Prepare", _read("prepare.js"), -656, 80),
        _openai(
            "AI Extract Divisions", _read("extract_prompt.txt"), extract_user, 300, -432, 80, creds
        ),
        _code("Match Locations", common + "\n" + match_js, -208, 80),
        {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "loose",
                        "version": 3,
                    },
                    "conditions": [
                        {
                            "id": _node_id("Need Nearest/cond"),
                            "leftValue": "={{ $json._loc_need_nearest === true }}",
                            "rightValue": "",
                            "operator": {
                                "type": "boolean",
                                "operation": "true",
                                "singleValue": True,
                            },
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
            "id": _node_id("Need Nearest"),
            "name": "Need Nearest",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.3,
            "position": [16, 80],
        },
        _openai("AI Nearest", _read("nearest_prompt.txt"), nearest_user, 200, 240, 0, creds),
        _code("Apply Nearest", common + "\n" + _read("apply_nearest.js"), 464, 0),
        {
            "parameters": {},
            "id": _node_id("Merge Results"),
            "name": "Merge Results",
            "type": "n8n-nodes-base.merge",
            "typeVersion": 3.2,
            "position": [688, 80],
        },
        _code("Restore Order", _read("restore.js"), 912, 80),
    ]

    def link(*targets: tuple[str, int]) -> list[dict]:
        return [{"node": node, "type": "main", "index": index} for node, index in targets]

    connections = {
        "Input Divisions": {"main": [link(("Prepare", 0))]},
        "Prepare": {"main": [link(("AI Extract Divisions", 0))]},
        "AI Extract Divisions": {"main": [link(("Match Locations", 0))]},
        "Match Locations": {"main": [link(("Need Nearest", 0))]},
        "Need Nearest": {"main": [link(("AI Nearest", 0)), link(("Merge Results", 1))]},
        "AI Nearest": {"main": [link(("Apply Nearest", 0))]},
        "Apply Nearest": {"main": [link(("Merge Results", 0))]},
        "Merge Results": {"main": [link(("Restore Order", 0))]},
    }

    workflow = {
        "name": old.get("name", "WF-COMMON Resolve China Division"),
        "nodes": nodes,
        "pinData": {},
        "connections": connections,
        "active": old.get("active", False),
        "settings": old.get("settings", {"executionOrder": "v1"}),
        "versionId": str(uuid.uuid4()),
        "meta": old.get("meta", {}),
        "nodeGroups": old.get("nodeGroups", []),
        "id": old.get("id", "BTd8dN5tfmJrcGRS"),
        "tags": old.get("tags", []),
    }
    out_path.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    size = out_path.stat().st_size
    print(f"{out_path}: {len(nodes)} nodes, {size // 1024} KB")


if __name__ == "__main__":
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT)
