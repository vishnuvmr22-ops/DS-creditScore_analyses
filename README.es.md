# CreditSentinel

[English](README.md) · 📖 **Español**

**Un servicio de decisión de riesgo crediticio en tiempo real, con un modelo de ML gobernado y una capa de explicabilidad LLM fundamentada, envuelto en un pipeline de MLOps completo.**

CreditSentinel puntúa la probabilidad de incumplimiento (PD) de un solicitante, convierte ese puntaje en una decisión de **aprobar / rechazar / revisar** y — el objetivo de todo el proyecto — explica cada decisión con **códigos de razón de acción adversa al estilo regulatorio, fundamentados en los propios drivers SHAP del modelo más la política de riesgo recuperada** (nunca alucinados libremente). Alrededor de eso está la maquinaria de producción que de verdad importa en préstamos regulados: un registro de modelos versionado, una ficha de modelo autogenerada, métricas de calibración y equidad, y monitoreo de deriva por PSI.

> ⚠️ **Procedencia de los datos (léelo primero).** Todos los datos son **sintéticos**, generados a partir de una semilla fija, **sin personas reales y sin PII real**. Los valores de las métricas reflejan el generador sintético, no el rendimiento en el mundo real. Se **inyecta deliberadamente** una pequeña disparidad de grupo en los datos sintéticos únicamente para que la verificación de equidad no sea trivial. Nada de esto debe usarse para decisiones crediticias reales. Esta honestidad es un principio de diseño, no un descargo de responsabilidad — ver `constitution.md`.

---

## Arquitectura

```
Cliente ──POST /score──►  Servicio FastAPI
                          1. Validar (Pydantic v2)                → 422 si la entrada es inválida
                          2. Pipeline de features (determinista, versionado)
                          3. Inferencia de PD  ◄──── versión de modelo fijada desde el Registro (MLflow)
                          4. Política de decisión (umbrales → aprobar/rechazar/revisar)
                          5. Explicación:  drivers SHAP principales ─┐
                                           código de razón LLM ◄─────┘  fundamentado en los drivers
                                           + política recuperada (Chroma RAG)
                          6. Respuesta estructurada + log de auditoría sin PII

Pipeline offline:  datos sintéticos → features → entrenar modelo PD → evaluar
                   → registrar en MLflow (métricas, calibración, equidad, ficha de modelo)
                   → puerta de registro gobernado (lo no gobernado no puede registrarse)
                   → línea base PSI escrita para el monitoreo de deriva
```

La base de código es **hexagonal (puertos y adaptadores)**: un núcleo de decisión puro (features, política de decisión, SHAP, fundamentación) con MLflow / Chroma / Anthropic / FastAPI como adaptadores intercambiables. Diseño completo en [`architecture.md`](architecture.md); requisitos en [`PRD.md`](PRD.md); principios de gobierno en [`constitution.md`](constitution.md).

**Stack:** Python 3.12 · FastAPI + Pydantic v2 · scikit-learn / XGBoost + SHAP · MLflow · Chroma · Anthropic (con fallback determinista) · Docker Compose · Pytest · Ruff · GitHub Actions.

---

## Ejecútalo en menos de 10 minutos

### Opción A — Docker Compose (API + Chroma + MLflow, cero pasos manuales)

```bash
docker compose up --build
```

En el primer arranque, el contenedor de la API entrena un modelo gobernado, lo registra en MLflow e ingesta el almacén de políticas — y luego sirve. Cuando imprima `Uvicorn running`, en otra terminal:

```bash
# Salud
curl http://localhost:8080/health

# Puntuar un solicitante de alto riesgo → rechazo con código de razón fundamentado
curl -X POST http://localhost:8080/score -H "Content-Type: application/json" -d '{
  "applicant_id":"APP-1","age":24,"annual_income":21000,"employment_length":0.5,
  "debt_to_income":0.95,"credit_utilization":1.4,"num_delinquencies":6,
  "num_open_accounts":14,"loan_amount":42000,"interest_rate":28.0,
  "home_ownership":"RENT","purpose":"debt_consolidation"}'
```

- **Consola de operador: http://localhost:3000** — la puerta de entrada visual (ver abajo)
- API: http://localhost:8080  (Swagger UI en `/docs`)
- UI de seguimiento de MLflow: http://localhost:5000
- Define `ANTHROPIC_API_KEY` en tu entorno antes de `up` para habilitar códigos de razón redactados por el LLM; sin ella, el servicio devuelve la razón por **plantilla determinista** (igualmente fundamentada).

### Opción B — Local (uv)

```bash
uv sync --extra dev              # Python 3.12
uv run creditsentinel-train      # entrena + gobierna + registra en ./mlflow, escribe la línea base PSI
uv run creditsentinel-ingest-policy   # construye el almacén de políticas Chroma desde ./policies
uv run uvicorn creditsentinel.api.app:app --reload   # sirve en :8000
```

### Usar la API

`POST /score` recibe un cuerpo JSON con los atributos del solicitante (ver el ejemplo con `curl` arriba) y devuelve la determinación completa en una sola petición. La documentación interactiva está en `http://localhost:8080/docs` (Swagger UI), donde puedes probar cada endpoint desde el navegador. Endpoints principales:

- `GET /health` — estado del servicio y versión del modelo que está sirviendo.
- `POST /score` — puntúa un solicitante y devuelve PD, decisión, umbrales, drivers SHAP, código de razón fundamentado y `audit_id`.

La consola también expone una superficie de **solo lectura** que consume el mismo servicio (`/decision-policy`, `/governance`, `/governance/model-card`, `/drift`, `/audit`) — todos GET, sin verbos de mutación.

### Consola de operador (la web)

Una consola web de cuatro vistas — **Decisiones, Gobernanza del modelo, Deriva, Auditoría** — servida como su propia app en **http://localhost:3000**. Compose la levanta junto al resto; no hay que hacer nada más. Para ejecutarla por su cuenta contra una API local:

```bash
cd web
npm install
CS_API_BASE_URL=http://localhost:8080 npm run dev   # http://localhost:3000
```

Puntúa un solicitante y lee la determinación — la probabilidad frente a los umbrales de la política, los drivers SHAP detrás de ella y la razón de acción adversa fundamentada con sus pasajes de política — y luego inspecciona la gobernanza del modelo que está sirviendo (AUC/KS/Brier, curva de calibración, equidad), la última evaluación de deriva registrada y el rastro de auditoría de decisiones seudonimizado. Es **solo lectura y puntuación**: la consola no tiene ninguna vía para mutar modelos, políticas, umbrales ni registros de auditoría (constitución v1.1.0).

- **Apariencia:** oscura por defecto, con un toggle `claro` / `oscuro` en el header (se recuerda por navegador).
- **Idioma:** la interfaz viene en **inglés y español**, conmutable con el toggle `EN` / `ES` junto al de apariencia (se recuerda por navegador). El *chrome* está completamente traducido; el contenido que genera el servicio — el texto de la razón, la ficha del modelo, los pasajes de política recuperados — se muestra tal cual lo devolvió la API.

La consola alcanza el servicio desde el navegador, así que la API permite su origen explícitamente vía `CS_CORS_ALLOW_ORIGINS`. Detalles en [`specs/006-web-console/`](specs/006-web-console/).

### Trabajo de deriva

```bash
uv run creditsentinel-drift --scenario stable   # PSI vs línea base; exit 0, registra la corrida
uv run creditsentinel-drift --scenario drift    # desplazamiento de covariables inyectado → marcado, exit 1
```

Cada corrida ahora también se registra en `data/drift_runs.jsonl`; la vista Deriva de la consola muestra la más reciente.

### Tests y lint

```bash
# Servicio (Python)
uv run ruff check src tests
uv run pytest --cov=creditsentinel

# Consola (TypeScript)
cd web && npm run lint && npm test && npm run build
```

---

## Qué contiene cada respuesta

`POST /score` devuelve, en una sola petición: la `pd`, la `decision`, los `thresholds` usados, la `model_version` + `feature_pipeline_version` (determinismo), los principales **drivers SHAP** con contribuciones firmadas, un **código de razón fundamentado** (`text`, las features `grounded_in`, `policy_refs` y qué `generator` lo produjo) y un `audit_id`. El id del solicitante se seudonimiza; no se registra ni se envía al LLM ninguna PII cruda.

---

## Puntos de conversación para entrevista (cada uno respaldado por código real aquí)

1. **"Explícame cómo se sirve un modelo de riesgo crediticio en tiempo real."** → `src/creditsentinel/api/` — validar → pipeline de features versionado → inferencia de PD en una versión de modelo fijada del registro → política de decisión → SHAP → razón fundamentada → auditoría, todo en una sola llamada `/score`.
2. **"¿Cómo mantienes gobernado un modelo en producción?"** → `governance/` + `models/registry.py`: registro MLflow, ficha de modelo automática, AUC-ROC / KS / Brier + calibración, una métrica de paridad de tasa de aprobación, y una **puerta de registro gobernado** que rechaza versiones no gobernadas (`test_governance.py`, `test_registry.py`).
3. **"¿Dónde aporta valor real el LLM — no es puro bombo?"** → `explain/` + `rag/`: produce códigos de razón de acción adversa fundamentados en los propios drivers SHAP del modelo + la política recuperada, no chat libre.
4. **"¿Cómo evitas que el LLM alucine una razón?"** → `explain/reason.py::assert_grounded` obliga a que la razón referencie los drivers principales *reales*; la salida LLM no fundamentada se descarta en favor de la plantilla (`test_llm_reason.py`, `test_api.py::test_high_risk_declines_with_grounded_reason`).
5. **"¿Cómo manejas la PII al llamar a un LLM externo?"** → `api/redact.py` seudonimiza el id del solicitante antes de registrar, y el prompt del LLM (`explain/llm_reason.py`) contiene solo *etiquetas* de drivers y texto de política — nunca el id ni los valores crudos de las features (`test_llm_reason.py::test_prompt_has_no_pii`).
6. **"¿Cómo detectas la deriva del modelo?"** → `monitoring/drift.py`: PSI sobre las distribuciones de features/puntaje entrantes vs. la línea base de entrenamiento, con un escenario de deriva sintética demostrable (`test_drift.py`).
7. **"¿Estrategia de pruebas para un sistema ML + LLM?"** → tests del núcleo determinista (features, decisión, drivers) + una aserción de fidelidad/referencia de drivers + un test de la puerta de gobernanza + un test de deriva, todos exigidos en CI con ≥80% de cobertura del núcleo.

---

## Encuadre de negocio

Las decisiones se calibran sobre una visión de **pérdida esperada**, no de exactitud cruda: los umbrales de aprobar / rechazar / revisar intercambian tasa de aprobación por tasa de incumplimiento. En la cartera sintética (tasa base de incumplimiento ≈ 23%) la política por defecto aprueba el ~34% de menor PD, rechaza el ~10% de mayor PD y enruta el resto a revisión manual — la banda donde un analista humano aporta más valor. Los umbrales son configuración (`CS_APPROVE_BELOW`, `CS_DECLINE_AT_OR_ABOVE`), así que el equilibrio de pérdida es ajustable sin cambios de código.

---

## Cómo se construyó (Desarrollo dirigido por especificación)

Planificado con **BMAD** (planificación agéntica multipersona → `PRD.md`, `architecture.md`, `project-context.md`) e implementado bajo la gobernanza de **GitHub Spec Kit** (`constitution.md` + specs por slice en `specs/`), una slice gobernada a la vez: entrenamiento/gobernanza → API de puntuación → RAG + códigos de razón → deriva → empaquetado/CI.

## Estructura del repositorio

```
src/creditsentinel/  features/ models/ governance/ explain/ rag/ monitoring/ api/  config.py
policies/            política de riesgo + docs de ficha de modelo (corpus RAG)
tests/               suite pytest (lógica del núcleo, fundamentación, puerta de gobernanza, deriva)
specs/               specs de features de Spec Kit (una por slice)
Dockerfile · docker-compose.yml · .github/workflows/ci.yml
PRD.md · architecture.md · constitution.md · project-context.md
```
