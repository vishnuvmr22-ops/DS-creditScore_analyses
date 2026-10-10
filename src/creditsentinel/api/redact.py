"""PII redaction port + adapter (FR-15, AD-4).

Runs before any audit-log write and before any external LLM call. The applicant
id is pseudonymized via a salted one-way hash; no raw id ever reaches logs or
prompts. Numeric/categorical features are not identifiers but are still excluded
from LLM prompts by the reason-code layer (which only ever sees driver labels).
"""

from __future__ import annotations

import hashlib
from typing import Protocol


class RedactorPort(Protocol):
    def pseudonymize(self, applicant_id: str) -> str: ...


class HashRedactor:
    def __init__(self, salt: str = "creditsentinel"):
        self._salt = salt.encode()

    def pseudonymize(self, applicant_id: str) -> str:
        digest = hashlib.sha256(self._salt + applicant_id.encode()).hexdigest()
        return f"pseudo_{digest[:12]}"
