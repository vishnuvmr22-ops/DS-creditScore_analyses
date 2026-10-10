"""Policy retriever port (FR-13, AD-3). Null adapter here; Chroma adapter in Slice 3."""

from __future__ import annotations

from typing import Protocol

from ..explain.reason import PolicyPassage


class PolicyRetrieverPort(Protocol):
    def retrieve(self, query: str, k: int = 3) -> list[PolicyPassage]: ...


class NullPolicyRetriever:
    """No-op retriever — reason codes are still grounded in SHAP drivers."""

    def retrieve(self, query: str, k: int = 3) -> list[PolicyPassage]:
        return []
