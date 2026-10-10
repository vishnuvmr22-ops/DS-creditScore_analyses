"""Audit-sink port + JSONL adapter (FR-12, AD-4).

Each scored decision writes one PII-safe entry (id already pseudonymized). Entries
capture decision provenance: pseudo id, PD, decision, model + pipeline versions,
drivers, and reason code.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol


class AuditSinkPort(Protocol):
    def append(self, entry: dict) -> str: ...


class AuditReaderPort(Protocol):
    def recent(self, limit: int, decision: str | None = None) -> list[dict]: ...


class JsonlAuditSink:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: dict) -> str:
        audit_id = str(uuid.uuid4())
        record = {"audit_id": audit_id, "ts": datetime.now(UTC).isoformat(), **entry}
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return audit_id


class JsonlAuditReader:
    """Bounded, newest-first reads over the audit log (FR-009, FR-017).

    Read-only: never writes, rotates or truncates. Entries were written already
    pseudonymized and without applicant attribute values, so no redaction is
    needed on the way out — the guarantee comes from what the writer omits.
    """

    def __init__(self, path: str | Path):
        self._path = Path(path)

    def recent(self, limit: int, decision: str | None = None) -> list[dict]:
        if not self._path.exists():
            raise FileNotFoundError(
                f"no audit log at {self._path}; score an applicant to create one"
            )
        entries: list[dict] = []
        with self._path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a partially written line must not fail the whole read
                if decision is None or entry.get("decision") == decision:
                    entries.append(entry)
        # Filter first, then truncate: "the N most recent declines" means that.
        entries.reverse()
        return entries[:limit]
