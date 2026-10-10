#!/usr/bin/env bash
# API entrypoint: ensure a governed model + policy store exist, then serve.
# No manual steps required for `docker-compose up` (Definition of Done).
set -euo pipefail

echo "[entrypoint] waiting for MLflow at ${CS_MLFLOW_TRACKING_URI:-<unset>} ..."
python - <<'PY'
import os, time, urllib.request
uri = os.environ.get("CS_MLFLOW_TRACKING_URI", "")
if uri.startswith("http"):
    for _ in range(90):
        try:
            urllib.request.urlopen(uri + "/health", timeout=2)
            print("[entrypoint] MLflow is up.")
            break
        except Exception:
            time.sleep(2)
    else:
        print("[entrypoint] WARNING: MLflow not reachable; continuing.")
PY

echo "[entrypoint] ensuring a governed model is registered ..."
python - <<'PY'
from creditsentinel.config import get_settings
from creditsentinel.models.registry import MlflowRegistry
s = get_settings()
reg = MlflowRegistry(s.mlflow_tracking_uri, s.model_name, s.mlflow_artifact_root or None)
try:
    reg.load_latest()
    print("[entrypoint] model already registered.")
except Exception as e:
    print(f"[entrypoint] no model found ({e}); training now ...")
    from creditsentinel.models.train import train_and_register
    print("[entrypoint] trained:", train_and_register())
PY

echo "[entrypoint] recording an initial drift evaluation if none exists ..."
python - <<'PY'
# Populate the drift view on first boot so a stranger sees a real recorded run,
# not an empty state (FR-016b). Skips silently if one already exists.
from pathlib import Path

from creditsentinel.config import get_settings

s = get_settings()
if Path(s.drift_runs_path).exists():
    print("[entrypoint] drift evaluation already recorded.")
else:
    try:
        import sys

        from creditsentinel.monitoring import drift as d

        sys.argv = ["creditsentinel-drift", "--scenario", "stable"]
        d.main()
    except SystemExit:
        pass  # the job exits non-zero only on breach; recording still happened
    except Exception as e:  # noqa: BLE001 - drift seeding is best-effort
        print(f"[entrypoint] WARNING: could not record initial drift ({e}).")
PY

# Bind the port the platform injects (Railway/Render/Fly set $PORT); the
# 8000 default keeps docker-compose and local runs unchanged.
PORT="${PORT:-8000}"
echo "[entrypoint] starting API on :${PORT}"
exec uvicorn creditsentinel.api.app:app --host 0.0.0.0 --port "${PORT}"
