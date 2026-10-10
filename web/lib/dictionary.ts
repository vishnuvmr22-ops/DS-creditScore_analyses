/**
 * The console's interface language, as data.
 *
 * One flat table per locale, resolved by a tiny `translate`. There is no i18n
 * dependency here for the same reason there is no charting or data-fetching one:
 * the surface is small, the behaviour must be legible, and a hand-built lookup
 * is easier to audit than a framework. English is the source of truth and the
 * fallback — any key missing from `es` falls back to `en`, never to a blank.
 *
 * Scope is the console's own chrome. Content the service authors — the reason
 * text, the driver labels, the model card, retrieved policy passages — is shown
 * verbatim in whatever language the API returned, never re-translated here.
 */

export type Locale = "en" | "es";

export const LOCALES: readonly Locale[] = ["en", "es"] as const;
export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_KEY = "creditsentinel.locale";

export function isLocale(value: unknown): value is Locale {
  return value === "en" || value === "es";
}

type Dict = Record<string, string>;

const EN: Dict = {
  // Navigation
  "nav.decisioning": "Decisioning",
  "nav.governance": "Governance",
  "nav.drift": "Drift",
  "nav.audit": "Audit",

  // Shell
  "shell.tagline": "Credit-risk decisioning console",
  "shell.synthetic.badge": "Synthetic data",
  "shell.synthetic.body":
    "Every applicant, metric and decision here is generated from a pinned seed. No real people, no real PII, and nothing shown is a real lending decision.",
  "shell.status.checking": "Checking service",
  "shell.status.unreachable": "● Service unreachable",
  "shell.status.degraded": "◆ Degraded — no governed model",
  "shell.status.serving": "● Serving",
  "shell.views": "Views",
  "shell.serving": "Serving",
  "shell.service": "Service",
  "shell.model": "model {v}",
  "shell.pipeline": "pipeline {v}",

  // Appearance toggle
  "theme.group": "Appearance",
  "theme.light": "light",
  "theme.dark": "dark",

  // Language toggle
  "lang.group": "Language",

  // Decisioning page
  "decisioning.title": "Decisioning",
  "decisioning.intro":
    "Score an applicant and read the determination: where the probability fell against the policy, which drivers moved it, and the reason those drivers support.",
  "decisioning.blocked.unreachable": "Scoring is unavailable while the service is unreachable.",
  "decisioning.blocked.noModel":
    "Scoring is unavailable until a governed model is trained and registered.",
  "decisioning.rejected.title": "Application rejected",
  "decisioning.rejected.body":
    "The service rejected this application. The fields that caused it are marked on the form.",
  "decisioning.empty.title": "No determination yet",
  "decisioning.empty.body":
    "Load a profile or fill the application, then score it. The determination, its drivers and its reason appear here.",
  "decisioning.clearDetermination": "Clear determination",
  "decisioning.clearApplication": "Clear application",
  "decisioning.loadingLabel": "determination",

  // Shared states
  "states.loading": "Loading {label}",
  "states.notProduced.title": "Nothing recorded yet",
  "states.notProduced.body":
    "No {artifact} exists for this deployment. The service is running normally — this artifact simply has not been produced.",
  "states.notProduced.toProduce": "To produce it",
  "states.failed.unreachable": "Service unreachable",
  "states.failed.requestFailed": "Request failed",
  "states.tryAgain": "Try again",

  // Applicant form
  "form.application": "Application",
  "form.heldHere": "Held in this page only",
  "form.loadProfile": "Load a profile",
  "form.submit": "Score applicant",
  "form.submitting": "Scoring…",

  // Validation
  "validation.reference": "Enter a reference.",
  "validation.chooseOption": "Choose an option.",
  "validation.enterValue": "Enter a value.",
  "validation.enterNumber": "Enter a number.",
  "validation.min": "Must be {min} or more.",
  "validation.max": "Must be {max} or less.",
  "validation.exclusiveMin": "Must be more than {min}.",

  // Sections
  "section.applicant": "Applicant",
  "section.credit": "Credit profile",
  "section.loan": "Requested loan",

  // Units
  "unit.yr": "yr",

  // Fields
  "field.applicant_id.label": "Reference",
  "field.applicant_id.help": "Pseudonymized before anything is logged.",
  "field.age.label": "Age",
  "field.age.help": "18–120.",
  "field.annual_income.label": "Annual income",
  "field.annual_income.help": "Gross, before tax.",
  "field.employment_length.label": "Employment length",
  "field.employment_length.help": "Years in current employment, 0–60.",
  "field.home_ownership.label": "Home ownership",
  "field.home_ownership.help": "Housing status.",
  "field.debt_to_income.label": "Debt-to-income",
  "field.debt_to_income.help": "Ratio, 0–2. 0.35 means debt service is 35% of income.",
  "field.credit_utilization.label": "Credit utilization",
  "field.credit_utilization.help": "Ratio of balances to limits, 0–3.",
  "field.num_delinquencies.label": "Delinquencies",
  "field.num_delinquencies.help": "Count of recent delinquencies.",
  "field.num_open_accounts.label": "Open accounts",
  "field.num_open_accounts.help": "Count of open trade lines.",
  "field.loan_amount.label": "Loan amount",
  "field.loan_amount.help": "Must be greater than zero.",
  "field.interest_rate.label": "Interest rate",
  "field.interest_rate.help": "Annual rate, 0–100.",
  "field.purpose.label": "Purpose",
  "field.purpose.help": "What the loan is for.",

  // Enum options
  "option.home_ownership.RENT": "Rent",
  "option.home_ownership.OWN": "Own",
  "option.home_ownership.MORTGAGE": "Mortgage",
  "option.purpose.debt_consolidation": "Debt consolidation",
  "option.purpose.credit_card": "Credit card",
  "option.purpose.home_improvement": "Home improvement",
  "option.purpose.major_purchase": "Major purchase",
  "option.purpose.other": "Other",

  // Presets
  "preset.strong.label": "Strong file",
  "preset.strong.expectation": "Expect approve",
  "preset.borderline.label": "Borderline file",
  "preset.borderline.expectation": "Expect referral",
  "preset.impaired.label": "Impaired file",
  "preset.impaired.expectation": "Expect decline",

  // Determination result
  "result.determination": "Determination",
  "result.pd": "Probability of default",
  "result.topDrivers": "Top drivers",
  "result.shapContribution": "SHAP contribution",
  "result.reason": "Reason for determination",
  "result.generator.template": "Deterministic template",
  "result.generator.anthropic": "Model-authored, grounded",
  "result.generatorNote.template":
    "No language-model key is configured, so the reason was composed from the drivers by a fixed template. It is bound by the same grounding rule.",
  "result.generatorNote.anthropic":
    "Composed by a language model and checked against the drivers above before it was returned.",
  "result.groundedIn": "Grounded in",
  "result.policyRefs": "Policy references",
  "result.policyRefs.none":
    "None retrieved. The policy store is empty or unreachable, so the reason rests on the drivers alone.",
  "result.provenance": "Provenance",
  "result.modelVersion": "Model version",
  "result.pipelineVersion": "Pipeline version",
  "result.auditId": "Audit id",
  "result.applicantRef": "Applicant reference",

  // Decision labels
  "decision.approve": "Approve",
  "decision.review": "Refer to review",
  "decision.decline": "Decline",

  // Driver direction
  "direction.increases_risk": "increases risk",
  "direction.reduces_risk": "reduces risk",
  "drivers.none": "No drivers recorded.",

  // Determination scale
  "scale.aria":
    "Probability of default {pd} on a scale from 0 to 1. Approve below {approve}, decline at or above {decline}. Outcome: {outcome}.",
  "scale.tick.aria": "Probability {pd} on the decision scale",
  "scale.approveBelow": "approve below",
  "scale.declineAt": "decline at",

  // Governance page
  "governance.title": "Model governance",
  "governance.intro":
    "Discrimination, calibration and fairness for the model version currently serving decisions, read back from the registry exactly as registration logged them.",
  "governance.serving": "Serving",
  "governance.servingMeta": "model {model} · pipeline {pipeline}",
  "governance.metric.auc.name": "AUC-ROC",
  "governance.metric.auc.gloss":
    "Ranking power — chance a defaulter is scored above a non-defaulter.",
  "governance.metric.ks.name": "KS statistic",
  "governance.metric.ks.gloss": "Widest separation between the two outcome distributions.",
  "governance.metric.brier.name": "Brier score",
  "governance.metric.brier.gloss": "Mean squared error of the probabilities. Lower is better.",
  "governance.calibration": "Calibration",
  "governance.bins": "{n} bins",
  "governance.fairness": "Fairness",
  "governance.approvalParity": "Approval-rate parity",
  "governance.modelCard": "Model card",
  "governance.version": "version {v}",
  "governance.label.record": "governance record",
  "governance.label.modelCard": "model card",

  // Calibration plot
  "calibration.aria":
    "Calibration plot of {n} bins comparing mean predicted probability with observed default rate. Expected calibration error {ece}.",
  "calibration.xAxis": "MEAN PREDICTED PD",
  "calibration.yAxis": "OBSERVED DEFAULT RATE",
  "calibration.ece": "Expected calibration error",
  "calibration.eceNote":
    "Mean gap between predicted and observed rates across {n} bins. Dashed line is perfect calibration; marker size is bin population.",

  // Fairness panel
  "fairness.group": "Group {group}",
  "fairness.parityGap": "Parity gap (max − min)",
  "fairness.disparateImpact": "Disparate impact (min ÷ max)",
  "fairness.note":
    "A small association between the protected attribute and default was injected into the synthetic data deliberately, so this check is not trivially clean. Read it as evidence the check works — not as a finding about any real population. The attribute is never a model feature.",

  // Drift page
  "drift.title": "Population drift",
  "drift.intro":
    "How far the scored population has moved from the training baseline, from the most recent recorded evaluation. Opening this view never runs a new one.",
  "drift.refresh": "Refresh",
  "drift.label.evaluation": "drift evaluation",
  "drift.verdict": "Verdict",
  "drift.run": "run {id}",
  "drift.drifted": "Drifted",
  "drift.stable": "Stable",
  "drift.breachedSummary.one": "{count} feature at or above the alert threshold: {list}.",
  "drift.breachedSummary.other": "{count} features at or above the alert threshold: {list}.",
  "drift.withinThreshold": "Every monitored feature is within the alert threshold.",
  "drift.evaluated": "Evaluated",
  "drift.scenario": "Scenario",
  "drift.scoreDrift": "Score drift",
  "drift.notComputed": "not computed",
  "drift.injectedNote":
    "This evaluation ran against a batch with a covariate shift injected on purpose. The breach below is the monitor working, not a live incident.",
  "drift.perFeature": "Per-feature stability",
  "drift.worstFirst": "Worst first",

  // PSI bars
  "psi.none": "No features monitored.",
  "psi.alertThreshold": "Alert threshold",
  "psi.breach": "Breach",
  "psi.stable": "Stable",
  "psi.aria.breach": "{feature} PSI {psi}, breaching the threshold",
  "psi.aria.within": "{feature} PSI {psi}, within threshold",

  // Audit page
  "audit.title": "Decision audit trail",
  "audit.intro":
    "The {n} most recent decisions, newest first, with the drivers recorded at the time each was made. References are pseudonymized — no applicant data was ever written.",
  "audit.refresh": "Refresh",
  "audit.outcome": "Outcome",
  "audit.filter.all": "All",
  "audit.filter.approve": "Approved",
  "audit.filter.review": "Referred",
  "audit.filter.decline": "Declined",
  "audit.recorded": "Recorded decisions",
  "audit.shown": "{count} shown",
  "audit.label.trail": "audit trail",
  "audit.empty.title": "No decisions match",
  "audit.empty.filtered":
    "No recorded decision has this outcome yet. Clear the filter to see the rest.",
  "audit.empty.none":
    "Nothing has been scored yet. Score an applicant on the Decisioning view and it will appear here.",

  // Audit table column heads
  "auditTable.recorded": "Recorded",
  "auditTable.reference": "Reference",
  "auditTable.pd": "PD",
  "auditTable.position": "Position",
  "auditTable.outcome": "Outcome",
  "auditTable.drivers": "Drivers",
  "auditTable.versions": "Versions",
  "auditTable.reasonBy": "Reason by",

  // Feature names (for grounded-in and PSI rows)
  "feature.age": "age",
  "feature.annual_income": "annual income",
  "feature.employment_length": "employment length",
  "feature.debt_to_income": "debt to income",
  "feature.credit_utilization": "credit utilization",
  "feature.num_delinquencies": "num delinquencies",
  "feature.num_open_accounts": "num open accounts",
  "feature.loan_amount": "loan amount",
  "feature.interest_rate": "interest rate",
  "feature.income_to_loan": "income to loan",
  "feature.delinquency_flag": "delinquency flag",
};

const ES: Dict = {
  // Navigation
  "nav.decisioning": "Decisiones",
  "nav.governance": "Gobernanza",
  "nav.drift": "Deriva",
  "nav.audit": "Auditoría",

  // Shell
  "shell.tagline": "Consola de decisión de riesgo crediticio",
  "shell.synthetic.badge": "Datos sintéticos",
  "shell.synthetic.body":
    "Cada solicitante, métrica y decisión aquí se genera a partir de una semilla fija. No hay personas reales, ni PII real, y nada de lo mostrado es una decisión crediticia real.",
  "shell.status.checking": "Verificando servicio",
  "shell.status.unreachable": "● Servicio inaccesible",
  "shell.status.degraded": "◆ Degradado — sin modelo gobernado",
  "shell.status.serving": "● Sirviendo",
  "shell.views": "Vistas",
  "shell.serving": "Sirviendo",
  "shell.service": "Servicio",
  "shell.model": "modelo {v}",
  "shell.pipeline": "pipeline {v}",

  // Appearance toggle
  "theme.group": "Apariencia",
  "theme.light": "claro",
  "theme.dark": "oscuro",

  // Language toggle
  "lang.group": "Idioma",

  // Decisioning page
  "decisioning.title": "Decisiones",
  "decisioning.intro":
    "Evalúa a un solicitante y lee la determinación: dónde cayó la probabilidad frente a la política, qué factores la movieron y la razón que esos factores sustentan.",
  "decisioning.blocked.unreachable":
    "La evaluación no está disponible mientras el servicio esté inaccesible.",
  "decisioning.blocked.noModel":
    "La evaluación no está disponible hasta que se entrene y registre un modelo gobernado.",
  "decisioning.rejected.title": "Solicitud rechazada",
  "decisioning.rejected.body":
    "El servicio rechazó esta solicitud. Los campos que la causaron están marcados en el formulario.",
  "decisioning.empty.title": "Aún no hay determinación",
  "decisioning.empty.body":
    "Carga un perfil o completa la solicitud, luego evalúala. La determinación, sus factores y su razón aparecen aquí.",
  "decisioning.clearDetermination": "Limpiar determinación",
  "decisioning.clearApplication": "Limpiar solicitud",
  "decisioning.loadingLabel": "determinación",

  // Shared states
  "states.loading": "Cargando {label}",
  "states.notProduced.title": "Aún no hay registro",
  "states.notProduced.body":
    "No existe {artifact} para este despliegue. El servicio funciona con normalidad — este artefacto simplemente no se ha producido.",
  "states.notProduced.toProduce": "Para producirlo",
  "states.failed.unreachable": "Servicio inaccesible",
  "states.failed.requestFailed": "La solicitud falló",
  "states.tryAgain": "Reintentar",

  // Applicant form
  "form.application": "Solicitud",
  "form.heldHere": "Retenida solo en esta página",
  "form.loadProfile": "Cargar un perfil",
  "form.submit": "Evaluar solicitante",
  "form.submitting": "Evaluando…",

  // Validation
  "validation.reference": "Ingresa una referencia.",
  "validation.chooseOption": "Elige una opción.",
  "validation.enterValue": "Ingresa un valor.",
  "validation.enterNumber": "Ingresa un número.",
  "validation.min": "Debe ser {min} o más.",
  "validation.max": "Debe ser {max} o menos.",
  "validation.exclusiveMin": "Debe ser mayor que {min}.",

  // Sections
  "section.applicant": "Solicitante",
  "section.credit": "Perfil crediticio",
  "section.loan": "Préstamo solicitado",

  // Units
  "unit.yr": "años",

  // Fields
  "field.applicant_id.label": "Referencia",
  "field.applicant_id.help": "Seudonimizada antes de registrar nada.",
  "field.age.label": "Edad",
  "field.age.help": "18–120.",
  "field.annual_income.label": "Ingreso anual",
  "field.annual_income.help": "Bruto, antes de impuestos.",
  "field.employment_length.label": "Antigüedad laboral",
  "field.employment_length.help": "Años en el empleo actual, 0–60.",
  "field.home_ownership.label": "Vivienda",
  "field.home_ownership.help": "Situación de vivienda.",
  "field.debt_to_income.label": "Deuda-ingreso",
  "field.debt_to_income.help":
    "Razón, 0–2. 0.35 significa que el servicio de deuda es 35% del ingreso.",
  "field.credit_utilization.label": "Utilización de crédito",
  "field.credit_utilization.help": "Razón de saldos a límites, 0–3.",
  "field.num_delinquencies.label": "Morosidades",
  "field.num_delinquencies.help": "Cantidad de morosidades recientes.",
  "field.num_open_accounts.label": "Cuentas abiertas",
  "field.num_open_accounts.help": "Cantidad de líneas de crédito abiertas.",
  "field.loan_amount.label": "Monto del préstamo",
  "field.loan_amount.help": "Debe ser mayor que cero.",
  "field.interest_rate.label": "Tasa de interés",
  "field.interest_rate.help": "Tasa anual, 0–100.",
  "field.purpose.label": "Propósito",
  "field.purpose.help": "Para qué es el préstamo.",

  // Enum options
  "option.home_ownership.RENT": "Alquiler",
  "option.home_ownership.OWN": "Propia",
  "option.home_ownership.MORTGAGE": "Hipoteca",
  "option.purpose.debt_consolidation": "Consolidación de deuda",
  "option.purpose.credit_card": "Tarjeta de crédito",
  "option.purpose.home_improvement": "Mejoras del hogar",
  "option.purpose.major_purchase": "Compra mayor",
  "option.purpose.other": "Otro",

  // Presets
  "preset.strong.label": "Perfil sólido",
  "preset.strong.expectation": "Se espera aprobar",
  "preset.borderline.label": "Perfil límite",
  "preset.borderline.expectation": "Se espera derivación",
  "preset.impaired.label": "Perfil deteriorado",
  "preset.impaired.expectation": "Se espera rechazar",

  // Determination result
  "result.determination": "Determinación",
  "result.pd": "Probabilidad de incumplimiento",
  "result.topDrivers": "Factores principales",
  "result.shapContribution": "Contribución SHAP",
  "result.reason": "Razón de la determinación",
  "result.generator.template": "Plantilla determinista",
  "result.generator.anthropic": "Redactada por el modelo, fundamentada",
  "result.generatorNote.template":
    "No hay clave de modelo de lenguaje configurada, así que la razón se compuso a partir de los factores mediante una plantilla fija. Está sujeta a la misma regla de fundamentación.",
  "result.generatorNote.anthropic":
    "Compuesta por un modelo de lenguaje y verificada contra los factores anteriores antes de devolverse.",
  "result.groundedIn": "Fundamentada en",
  "result.policyRefs": "Referencias de política",
  "result.policyRefs.none":
    "Ninguna recuperada. El almacén de políticas está vacío o inaccesible, así que la razón se apoya solo en los factores.",
  "result.provenance": "Procedencia",
  "result.modelVersion": "Versión del modelo",
  "result.pipelineVersion": "Versión del pipeline",
  "result.auditId": "ID de auditoría",
  "result.applicantRef": "Referencia del solicitante",

  // Decision labels
  "decision.approve": "Aprobar",
  "decision.review": "Derivar a revisión",
  "decision.decline": "Rechazar",

  // Driver direction
  "direction.increases_risk": "aumenta el riesgo",
  "direction.reduces_risk": "reduce el riesgo",
  "drivers.none": "No hay factores registrados.",

  // Determination scale
  "scale.aria":
    "Probabilidad de incumplimiento {pd} en una escala de 0 a 1. Aprobar por debajo de {approve}, rechazar en o por encima de {decline}. Resultado: {outcome}.",
  "scale.tick.aria": "Probabilidad {pd} en la escala de decisión",
  "scale.approveBelow": "aprobar por debajo",
  "scale.declineAt": "rechazar en",

  // Governance page
  "governance.title": "Gobernanza del modelo",
  "governance.intro":
    "Discriminación, calibración y equidad de la versión del modelo que actualmente sirve decisiones, leídas del registro tal como el registro las guardó.",
  "governance.serving": "Sirviendo",
  "governance.servingMeta": "modelo {model} · pipeline {pipeline}",
  "governance.metric.auc.name": "AUC-ROC",
  "governance.metric.auc.gloss":
    "Poder de ordenamiento — probabilidad de que un incumplidor reciba mayor puntaje que un no incumplidor.",
  "governance.metric.ks.name": "Estadístico KS",
  "governance.metric.ks.gloss": "Máxima separación entre las dos distribuciones de resultado.",
  "governance.metric.brier.name": "Puntaje de Brier",
  "governance.metric.brier.gloss":
    "Error cuadrático medio de las probabilidades. Menor es mejor.",
  "governance.calibration": "Calibración",
  "governance.bins": "{n} tramos",
  "governance.fairness": "Equidad",
  "governance.approvalParity": "Paridad de tasa de aprobación",
  "governance.modelCard": "Ficha del modelo",
  "governance.version": "versión {v}",
  "governance.label.record": "registro de gobernanza",
  "governance.label.modelCard": "ficha del modelo",

  // Calibration plot
  "calibration.aria":
    "Gráfico de calibración de {n} tramos que compara la probabilidad media predicha con la tasa de incumplimiento observada. Error de calibración esperado {ece}.",
  "calibration.xAxis": "PD MEDIA PREDICHA",
  "calibration.yAxis": "TASA DE INCUMPLIMIENTO OBSERVADA",
  "calibration.ece": "Error de calibración esperado",
  "calibration.eceNote":
    "Diferencia media entre las tasas predichas y observadas a lo largo de {n} tramos. La línea discontinua es la calibración perfecta; el tamaño del marcador es la población del tramo.",

  // Fairness panel
  "fairness.group": "Grupo {group}",
  "fairness.parityGap": "Brecha de paridad (máx − mín)",
  "fairness.disparateImpact": "Impacto dispar (mín ÷ máx)",
  "fairness.note":
    "Se inyectó deliberadamente una pequeña asociación entre el atributo protegido y el incumplimiento en los datos sintéticos, para que esta verificación no sea trivialmente limpia. Léelo como evidencia de que la verificación funciona — no como un hallazgo sobre una población real. El atributo nunca es una variable del modelo.",

  // Drift page
  "drift.title": "Deriva de población",
  "drift.intro":
    "Cuánto se ha alejado la población evaluada de la línea base de entrenamiento, según la evaluación registrada más reciente. Abrir esta vista nunca ejecuta una nueva.",
  "drift.refresh": "Actualizar",
  "drift.label.evaluation": "evaluación de deriva",
  "drift.verdict": "Veredicto",
  "drift.run": "corrida {id}",
  "drift.drifted": "Con deriva",
  "drift.stable": "Estable",
  "drift.breachedSummary.one": "{count} variable en o por encima del umbral de alerta: {list}.",
  "drift.breachedSummary.other": "{count} variables en o por encima del umbral de alerta: {list}.",
  "drift.withinThreshold": "Cada variable monitoreada está dentro del umbral de alerta.",
  "drift.evaluated": "Evaluado",
  "drift.scenario": "Escenario",
  "drift.scoreDrift": "Deriva de puntaje",
  "drift.notComputed": "no calculado",
  "drift.injectedNote":
    "Esta evaluación se corrió contra un lote con un desplazamiento de covariables inyectado a propósito. El incumplimiento de abajo es el monitor funcionando, no un incidente real.",
  "drift.perFeature": "Estabilidad por variable",
  "drift.worstFirst": "Peores primero",

  // PSI bars
  "psi.none": "No hay variables monitoreadas.",
  "psi.alertThreshold": "Umbral de alerta",
  "psi.breach": "Incumple",
  "psi.stable": "Estable",
  "psi.aria.breach": "{feature} PSI {psi}, incumpliendo el umbral",
  "psi.aria.within": "{feature} PSI {psi}, dentro del umbral",

  // Audit page
  "audit.title": "Rastro de auditoría de decisiones",
  "audit.intro":
    "Las {n} decisiones más recientes, la más nueva primero, con los factores registrados en el momento en que se tomó cada una. Las referencias están seudonimizadas — nunca se escribió ningún dato del solicitante.",
  "audit.refresh": "Actualizar",
  "audit.outcome": "Resultado",
  "audit.filter.all": "Todos",
  "audit.filter.approve": "Aprobados",
  "audit.filter.review": "Derivados",
  "audit.filter.decline": "Rechazados",
  "audit.recorded": "Decisiones registradas",
  "audit.shown": "{count} mostradas",
  "audit.label.trail": "rastro de auditoría",
  "audit.empty.title": "Ninguna decisión coincide",
  "audit.empty.filtered":
    "Ninguna decisión registrada tiene este resultado todavía. Quita el filtro para ver el resto.",
  "audit.empty.none":
    "Aún no se ha evaluado nada. Evalúa a un solicitante en la vista Decisiones y aparecerá aquí.",

  // Audit table column heads
  "auditTable.recorded": "Registrado",
  "auditTable.reference": "Referencia",
  "auditTable.pd": "PD",
  "auditTable.position": "Posición",
  "auditTable.outcome": "Resultado",
  "auditTable.drivers": "Factores",
  "auditTable.versions": "Versiones",
  "auditTable.reasonBy": "Razón por",

  // Feature names (for grounded-in and PSI rows)
  "feature.age": "edad",
  "feature.annual_income": "ingreso anual",
  "feature.employment_length": "antigüedad laboral",
  "feature.debt_to_income": "deuda-ingreso",
  "feature.credit_utilization": "utilización de crédito",
  "feature.num_delinquencies": "morosidades",
  "feature.num_open_accounts": "cuentas abiertas",
  "feature.loan_amount": "monto del préstamo",
  "feature.interest_rate": "tasa de interés",
  "feature.income_to_loan": "ingreso-préstamo",
  "feature.delinquency_flag": "indicador de morosidad",
};

const DICT: Record<Locale, Dict> = { en: EN, es: ES };

export type Vars = Record<string, string | number>;

/** Resolve a key in `locale`, falling back to English, then to the key itself. */
export function translate(locale: Locale, key: string, vars?: Vars): string {
  const template = DICT[locale][key] ?? DICT.en[key] ?? key;
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_match, name: string) =>
    name in vars ? String(vars[name]) : `{${name}}`,
  );
}

/**
 * A monitored feature's name, in words. Known features are translated; anything
 * else (one-hot columns like `home_ownership=RENT`) falls back to the raw name
 * with underscores relaxed, never a blank.
 */
export function featureLabel(locale: Locale, name: string): string {
  const key = `feature.${name}`;
  return DICT[locale][key] ?? DICT.en[key] ?? name.replace(/_/g, " ");
}
