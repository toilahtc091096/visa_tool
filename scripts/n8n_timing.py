"""Where does a case spend its time? Read-only report from the n8n API.

Reads the executions of the last N hours (every workflow), links each
sub-workflow run to the case (WF01-GENERAL run) that started it, and prints:
  1. each case: total time and time per sub-workflow
  2. the nodes with the most total time (own work: Execute Workflow nodes
     are left out, their time is the child's)
  3. AI nodes: calls, average, slowest, tries

Env: N8N_API_KEY (n8n -> Settings -> n8n API), N8N_BASE_URL (default: the
Railway instance). Nothing is written to n8n.

    .venv\\Scripts\\python.exe scripts\\n8n_timing.py --hours 24
    .venv\\Scripts\\python.exe scripts\\n8n_timing.py --hours 48 --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import httpx

DEFAULT_BASE = "https://n8n-production-d4d9.up.railway.app"
ROOT_WORKFLOW = "WF01-GENERAL"
AI_TYPES = ("openAi", "lmChatOpenAi", "chainLlm", "informationExtractor", "anthropic")
AI_URLS = ("api.openai.com", "api.anthropic.com")


def _ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch(base: str, key: str, since: datetime, page: int = 25) -> list[dict]:
    out: list[dict] = []
    cursor = None
    with httpx.Client(base_url=base, headers={"X-N8N-API-KEY": key}, timeout=120) as client:
        while True:
            params = {"includeData": "true", "limit": page}
            if cursor:
                params["cursor"] = cursor
            r = client.get("/api/v1/executions", params=params)
            r.raise_for_status()
            body = r.json()
            rows = body.get("data") or []
            stop = False
            for row in rows:
                started = _ts(row.get("startedAt"))
                if started and started < since:
                    stop = True
                    break
                out.append(row)
            print(f"  fetched {len(out)} executions", file=sys.stderr)
            cursor = body.get("nextCursor")
            if stop or not cursor or not rows:
                return out


def workflow_names(base: str, key: str) -> dict[str, dict]:
    out = {}
    cursor = None
    with httpx.Client(base_url=base, headers={"X-N8N-API-KEY": key}, timeout=60) as client:
        while True:
            params = {"limit": 100, **({"cursor": cursor} if cursor else {})}
            r = client.get("/api/v1/workflows", params=params)
            r.raise_for_status()
            body = r.json()
            for wf in body.get("data") or []:
                out[str(wf["id"])] = {
                    "name": wf.get("name", wf["id"]),
                    "nodes": {n["name"]: n for n in wf.get("nodes", [])},
                }
            cursor = body.get("nextCursor")
            if not cursor:
                return out


def _parent_id(ex: dict) -> str:
    data = ex.get("data") or {}
    parent = data.get("parentExecution") or {}
    return str(parent.get("executionId") or "")


def _duration(ex: dict) -> float:
    a, b = _ts(ex.get("startedAt")), _ts(ex.get("stoppedAt"))
    return (b - a).total_seconds() if a and b else 0.0


def _is_ai(node: dict | None) -> bool:
    if not node:
        return False
    t = node.get("type", "")
    if any(t.endswith(x) or f".{x}" in t for x in AI_TYPES):
        return True
    url = str((node.get("parameters") or {}).get("url", ""))
    return any(u in url for u in AI_URLS)


def _is_call(node: dict | None) -> bool:
    return bool(node) and node.get("type", "").endswith("executeWorkflow")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--json", help="also write the raw per-case table here")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    key = os.getenv("N8N_API_KEY", "").strip()
    if not key:
        sys.exit("N8N_API_KEY is not set")
    base = os.getenv("N8N_BASE_URL", DEFAULT_BASE).rstrip("/")
    since = datetime.now(timezone.utc) - timedelta(hours=args.hours)

    wfs = workflow_names(base, key)
    execs = fetch(base, key, since)
    by_id = {str(e["id"]): e for e in execs}
    name = lambda e: wfs.get(str(e.get("workflowId")), {}).get("name", str(e.get("workflowId")))

    def root_of(e: dict) -> dict:
        seen = set()
        while True:
            pid = _parent_id(e)
            if not pid or pid not in by_id or pid in seen:
                return e
            seen.add(pid)
            e = by_id[pid]

    # 1. cases
    cases: dict[str, dict] = {}
    for e in execs:
        r = root_of(e)
        if name(r) != ROOT_WORKFLOW:
            continue
        c = cases.setdefault(str(r["id"]), {"id": r["id"], "started": r.get("startedAt"), "status": r.get("status"),
                                            "total": _duration(r), "by_wf": defaultdict(float), "runs": defaultdict(int)})
        if e is not r:
            c["by_wf"][name(e)] += _duration(e)
            c["runs"][name(e)] += 1

    print(f"\n== {len(cases)} hồ sơ ({ROOT_WORKFLOW}) trong {args.hours:g} giờ, {len(execs)} execution")
    totals = [c["total"] for c in cases.values() if c["total"]]
    if totals:
        print(f"   tổng thời gian: trung bình {statistics.mean(totals):.0f}s, "
              f"trung vị {statistics.median(totals):.0f}s, lâu nhất {max(totals):.0f}s")
    for c in sorted(cases.values(), key=lambda c: -c["total"]):
        top = sorted(c["by_wf"].items(), key=lambda kv: -kv[1])[:6]
        parts = ", ".join(f"{k} {v:.0f}s" + (f" x{c['runs'][k]}" if c["runs"][k] > 1 else "") for k, v in top)
        print(f"   #{c['id']} {c['started'][:16]} {c['status']:<8} {c['total']:>5.0f}s | {parts}")

    # 2/3. nodes
    node_t: dict[tuple, list] = defaultdict(list)
    tries: dict[tuple, int] = defaultdict(int)
    for e in execs:
        wf = wfs.get(str(e.get("workflowId")), {})
        run_data = (((e.get("data") or {}).get("resultData") or {}).get("runData")) or {}
        for node_name, runs in run_data.items():
            node = wf.get("nodes", {}).get(node_name)
            if _is_call(node):
                continue
            k = (wf.get("name", e.get("workflowId")), node_name, _is_ai(node))
            for run in runs:
                node_t[k].append((run.get("executionTime") or 0) / 1000)
                if run.get("error"):
                    tries[k] += 1

    rows = sorted(node_t.items(), key=lambda kv: -sum(kv[1]))
    print(f"\n== {args.top} node tốn nhiều thời gian nhất (tổng các lần chạy, không tính node gọi workflow con)")
    print(f"   {'tổng':>7} {'lần':>5} {'tb':>6} {'max':>6}  workflow / node")
    for (wf, node, ai), ts in rows[: args.top]:
        print(f"   {sum(ts):>6.0f}s {len(ts):>5} {statistics.mean(ts):>5.1f}s {max(ts):>5.1f}s  "
              f"{'[AI] ' if ai else ''}{wf} / {node}")

    print("\n== Node AI")
    ai_rows = [r for r in rows if r[0][2]]
    all_ai = sum(sum(ts) for _, ts in ai_rows)
    all_nodes = sum(sum(ts) for _, ts in rows)
    if all_nodes:
        print(f"   AI chiếm {all_ai:.0f}s / {all_nodes:.0f}s thời gian node ({100 * all_ai / all_nodes:.0f}%)")
    for (wf, node, _), ts in ai_rows:
        p90 = sorted(ts)[int(0.9 * (len(ts) - 1))]
        err = f" lỗi {tries[(wf, node, True)]}" if tries[(wf, node, True)] else ""
        print(f"   {sum(ts):>6.0f}s {len(ts):>4} lần tb {statistics.mean(ts):>5.1f}s p90 {p90:>5.1f}s max {max(ts):>5.1f}s{err}  {wf} / {node}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump([{**c, "by_wf": dict(c["by_wf"]), "runs": dict(c["runs"])} for c in cases.values()],
                      fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
