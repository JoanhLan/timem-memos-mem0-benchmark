"""One-off probe: MemOS add/message POST time vs task completion (get/status)."""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

BASE = os.environ["MEMOS_BASE_URL"].rstrip("/")
KEY = os.environ["MEMOS_API_KEY"]
HEADERS = {"Authorization": f"Token {KEY}", "Content-Type": "application/json"}


async def poll_status(client: httpx.AsyncClient, task_id: str, *, timeout: float = 300) -> tuple[float, int, dict]:
    started = time.perf_counter()
    interval = 1.0
    checks = 0
    last: dict = {}
    while (time.perf_counter() - started) < timeout:
        checks += 1
        resp = await client.post(f"{BASE}/get/status", headers=HEADERS, json={"task_id": task_id})
        resp.raise_for_status()
        body = resp.json()
        data = body.get("data") if isinstance(body, dict) else {}
        if isinstance(data, list):
            statuses = [
                str((item or {}).get("status") or "").lower()
                for item in data
                if isinstance(item, dict)
            ]
            if statuses and all(s in ("completed", "complete", "success", "succeeded") for s in statuses):
                return (time.perf_counter() - started) * 1000, checks, body
            if any(s in ("failed", "error") for s in statuses):
                raise RuntimeError(f"task failed: {body}")
            status = statuses[0] if statuses else ""
        elif isinstance(data, dict):
            status = str(data.get("status") or "").lower()
        else:
            status = ""
        last = body if isinstance(body, dict) else {"body": body}
        if status in ("completed", "complete", "success", "succeeded"):
            return (time.perf_counter() - started) * 1000, checks, last
        if status in ("failed", "error"):
            raise RuntimeError(f"task failed: {last}")
        await asyncio.sleep(interval)
    raise TimeoutError(f"timeout after {timeout}s, last={last}")


async def search_counts(client: httpx.AsyncClient, user_id: str, conversation_id: str) -> tuple[int, int]:
    resp = await client.post(
        f"{BASE}/search/memory",
        headers=HEADERS,
        json={
            "user_id": user_id,
            "query": "Guangzhou hotel 7 Days Inn travel preference",
            "conversation_id": conversation_id,
        },
    )
    resp.raise_for_status()
    body = resp.json()
    payload = body.get("data") if isinstance(body.get("data"), dict) else body
    factual = payload.get("memory_detail_list") or payload.get("memories") or []
    pref = payload.get("preference_detail_list") or []
    return len(factual), len(pref)


async def main() -> None:
    fixture = json.loads(
        (PROJECT_ROOT / "benchmark_data" / "fixtures" / "sample_persona.json").read_text(encoding="utf-8")
    )
    session = fixture[0]["sessions"][0]
    user_id = f"memos_probe_{uuid.uuid4().hex[:8]}"
    conv_id = f"{session['session_id']}_{uuid.uuid4().hex[:6]}"

    payload = {
        "user_id": user_id,
        "conversation_id": conv_id,
        "messages": session["messages"],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        t0 = time.perf_counter()
        resp = await client.post(f"{BASE}/add/message", headers=HEADERS, json=payload)
        post_ms = (time.perf_counter() - t0) * 1000
        resp.raise_for_status()
        add_body = resp.json()

        task_id = None
        if isinstance(add_body, dict):
            data = add_body.get("data") if isinstance(add_body.get("data"), dict) else add_body
            if isinstance(data, dict):
                task_id = data.get("task_id")
            task_id = task_id or add_body.get("task_id")

        result: dict = {
            "user_id": user_id,
            "conversation_id": conv_id,
            "message_count": len(session["messages"]),
            "post_ms": round(post_ms, 1),
            "task_id": task_id,
        }
        if isinstance(add_body, dict):
            data = add_body.get("data")
            if isinstance(data, dict):
                result["add_status"] = data.get("status")
            elif isinstance(data, list) and data:
                result["add_status"] = [d.get("status") for d in data if isinstance(d, dict)]

        if task_id:
            ready_ms, checks, status_body = await poll_status(client, task_id)
            result["status_poll_ms"] = round(ready_ms, 1)
            result["status_poll_checks"] = checks
            data = status_body.get("data")
            if isinstance(data, dict):
                result["final_status"] = data.get("status")
            elif isinstance(data, list):
                result["final_status"] = [d.get("status") for d in data if isinstance(d, dict)]
            result["total_ready_ms"] = round(post_ms + ready_ms, 1)
        else:
            started = time.perf_counter()
            checks = 0
            while (time.perf_counter() - started) < 180:
                checks += 1
                n_f, n_p = await search_counts(client, user_id, conv_id)
                if n_f + n_p > 0:
                    search_ms = (time.perf_counter() - started) * 1000
                    result["search_ready_ms"] = round(search_ms, 1)
                    result["search_poll_checks"] = checks
                    result["factual_count"] = n_f
                    result["preference_count"] = n_p
                    result["total_ready_ms"] = round(post_ms + search_ms, 1)
                    break
                await asyncio.sleep(2)
            else:
                result["search_ready_ms"] = None
                result["note"] = "no task_id and search never returned memories within 180s"

        n_f, n_p = await search_counts(client, user_id, conv_id)
        result["factual_count_final"] = n_f
        result["preference_count_final"] = n_p

        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
