#!/usr/bin/env python3
"""Backfill per-add ingest latency fields in existing ingest.json reports."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.config import PROJECT_ROOT
from utils.ingest_add_metrics import aggregate_add_metrics


def migrate_system_block(block: dict[str, Any]) -> dict[str, Any]:
    details = block.get("details") or []
    metrics = aggregate_add_metrics(details, estimated=True)
    out = dict(block)
    out["details"] = metrics["details"]
    out["session_count"] = metrics["session_count"]
    out["success_count"] = metrics["success_count"]
    out["failure_count"] = metrics["failure_count"]
    out["latency"] = metrics["latency"]
    out["add_count"] = metrics["add_count"]
    out["add_success_count"] = metrics["add_success_count"]
    out["add_latency"] = metrics["add_latency"]
    out["session_latency"] = metrics["session_latency"]
    out["latency_granularity"] = metrics["latency_granularity"]
    out["add_latency_estimated"] = True
    out["sum_latency_ms"] = metrics["sum_latency_ms"]
    return out


def migrate_ingest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {system: migrate_system_block(block) for system, block in payload.items()}


def migrate_run(run_id: str, *, dry_run: bool = False) -> Path:
    path = PROJECT_ROOT / "reports" / run_id / "ingest.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing ingest report: {path}")

    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    migrated = migrate_ingest_payload(payload)
    if dry_run:
        print(json.dumps({k: {
            "add_count": v.get("add_count"),
            "add_latency_p50": (v.get("add_latency") or {}).get("p50"),
            "session_latency_p50": (v.get("session_latency") or {}).get("p50"),
            "estimated": v.get("add_latency_estimated"),
        } for k, v in migrated.items()}, indent=2))
        return path

    backup = path.with_suffix(".json.bak")
    shutil.copy2(path, backup)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(migrated, f, indent=2, ensure_ascii=False)
    print(f"Migrated {path} (backup: {backup})")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill add-level ingest latency in ingest.json")
    parser.add_argument("--run-id", default="LJY_NEW", help="Run id under reports/")
    parser.add_argument("--dry-run", action="store_true", help="Print summary only, do not write")
    args = parser.parse_args()
    migrate_run(args.run_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
