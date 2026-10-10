"""FastAPI application (FR-8, FR-9). Driving adapter — translates HTTP <-> core."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from .reads import router as reads_router
from .schemas import HealthResponse, ScoreRequest, ScoreResponse
from .service import ScoringService

_state: dict[str, ScoringService | None] = {"service": None}


def get_service() -> ScoringService:
    if _state["service"] is None:
        # Lazy build so import doesn't require a trained model (tests inject their own).
        _state["service"] = ScoringService.from_settings(get_settings())
    return _state["service"]


def set_service(service: ScoringService | None) -> None:
    """Test/composition seam to inject a preconfigured service."""
    _state["service"] = service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast if no governed model is registered (constitution III / AD-1).
    try:
        get_service()
    except Exception as exc:  # noqa: BLE001 - surfaced via /health
        app.state.startup_error = str(exc)
    yield


app = FastAPI(title="CreditSentinel", version="0.1.0", lifespan=lifespan)

# The operator console runs on its own origin and calls this service from the
# browser. Consent is granted to an explicit list, never a wildcard (FR-021);
# credentials stay off because no authentication exists to carry.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

# Read-only projections for the console. No write verb enters here (FR-022).
app.include_router(reads_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        svc = get_service()
    except Exception:  # noqa: BLE001
        return HealthResponse(status="degraded", model_loaded=False)
    return HealthResponse(
        status="ok",
        model_loaded=True,
        model_version=svc.model.model_version,
        feature_pipeline_version=svc.model.feature_pipeline_version,
    )


@app.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest) -> ScoreResponse:
    return get_service().score(request)
