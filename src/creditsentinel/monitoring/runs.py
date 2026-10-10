"""Drift-run store port + JSONL adapter (FR-016, AD-6).

Slice 4's job computed a report, printed it and exited — nothing survived the
process. The console must show an evaluation that actually ran, so each run is
appended here with its identity and provenance. Append-only: history is the
point of a monitoring artifact, and the newest run is the last line.

Mirrors the shape of the audit sink deliberately — one persistence pattern in
this codebase, not two.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol


class DriftRunStorePort(Protocol):
    def record(self, report: dict, scenario: str) -> str: ...
    def latest(self) -> dict: ...


class JsonlDriftRunStore:
    """One JSON object per line; `latest()` is the last parseable line."""

    def __init__(self, path: str | Path):
        self._path = Path(path)

    def record(self, report: dict, scenario: str) -> str:
        run_id = str(uuid.uuid4())
        record = {
            "run_id": run_id,
            "ts": datetime.now(UTC).isoformat(),
            "scenario": scenario,
            **report,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return run_id

    def latest(self) -> dict:
        if not self._path.exists():
            raise FileNotFoundError(
                f"no drift evaluation recorded at {self._path}; "
                "run the drift job first (creditsentinel-drift)"
            )
        latest: dict | None = None
        with self._path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    latest = json.loads(line)
                except json.JSONDecodeError:
                    # A half-written trailing line must not take the drift view down.
                    continue
        if latest is None:
            raise FileNotFoundError(f"no readable drift evaluation in {self._path}")
        return latest
