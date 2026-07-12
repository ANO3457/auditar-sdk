AUDITAR-SDK — RBI FREE-AI 7-SUTRAS COMPLIANCE MAPPING
One-page reference for compliance teams evaluating auditar-sdk in Indian financial services.

================================================================================
BACKGROUND
================================================================================
RBI FREE-AI 7-Sutras is the regulatory framework for AI in banking, NBFC, and
fintech. auditar-sdk provides observation-only instrumentation; it does not alter
model behavior. This mapping shows which SDK artifacts satisfy each Sutra.

================================================================================
SUTRA 1 — FAIRNESS / NON-DISCRIMINATION
================================================================================
Requirement: Models must not produce biased or discriminatory outcomes.

SDK evidence:
- DecisionRecord stores exact input feature values and resulting score/probability
  per inference, enabling group-level fairness audits (age, gender, location,
  income, credit_score, etc.) without touching model internals.
- Trace-level replay via InferenceSession allows historical fairness regression
  testing against protected attributes.

Field mapping:
  auditar_sdk.models.DecisionRecord.inputs -> protected feature snapshot
  auditar_sdk.models.BatchRequest.batch_id -> fairness run identifier

================================================================================
SUTRA 2 — TRANSPARENCY / EXPLAINABILITY
================================================================================
Requirement: Decisions must be explainable to customers and regulators.

SDK evidence:
- Decorator captures feature-level input/output pairs deterministically.
- Model name, version, use_case, workspace, and endpoint are recorded per call.
- Outputs can be exported from local SQLite queue for downstream explanation
  frameworks (SHAP/LIME) without exporting raw model artifacts.

Field mapping:
  auditar_sdk.models.DecisionRecord.model_name -> model identifier
  auditar_sdk.models.DecisionRecord.model_version -> explainability lineage
  auditar_sdk.models.DecisionRecord.outputs -> model judgment snapshot
  auditar_sdk.models.BatchResponse.accepted/failed -> decision delivery audit

================================================================================
SUTRA 3 — ACCOUNTABILITY / OWNERSHIP
================================================================================
Requirement: Clear ownership of model performance, errors, and review cycles.

SDK evidence:
- workspace field assigns all traces to a business unit / portfolio.
- Inference timestamp and referrer / user_agent provide invocation lineage.
- manual_flush() exposes operational control to platform engineers.

Field mapping:
  auditar_sdk.models.DecisionRecord.workspace -> ownership namespace
  auditar_sdk.models.DecisionRecord.recorded_at -> audit timestamp
  client.register_model(use_case=...) -> policy owner linkage

================================================================================
SUTRA 4 — DATA PRIVACY / ZERO-KNOWLEDGE OBSERVATION
================================================================================
Requirement: Customer data must be protected; vendors/service providers must not
leverage production inference payloads.

SDK evidence:
- Zero-knowledge posture: auditar-sdk observes inputs/outputs only. It never
  collects model weights, gradients, embeddings, training data, or raw PII beyond
  what the calling application passes to the model.
- Local SQLite queue by default; no outbound connectivity required.

Field mapping:
  auditar_sdk.transport.LocalTransport -> air-gapped deployment path
  auditar_sdk.models.DecisionRecord.inputs -> business-layer fields only
  httpx transport -> optional encrypted egress to auditar core (DOT TLS 1.3)

================================================================================
SUTRA 5 — RISK MANAGEMENT / GOVERNANCE
================================================================================
Requirement: AI risk must be measured, monitored, and escalated.

SDK evidence:
- BatchRequest + BatchResponse allow platform teams to measure throughput, failure
  rate, and partial flush behavior.
- InferenceSession context manager batches traces for regulated windows.
- Timestamped records enable drift detection and SLA breach correlation.

Field mapping:
  auditar_sdk.models.BatchResponse.failed/errors -> risk event evidence
  auditar_sdk.client.AuditarClient.pending_count() -> operational buffer health
  auditar_sdk.models.BatchRequest.batch_id -> risk event grouping key

================================================================================
SUTRA 6 — CYBERSECURITY / MODEL INTEGRITY
================================================================================
Requirement: Models and inference pipelines must be protected from tampering.

SDK evidence:
- auditar-sdk is observation-only. It does not mutate model state.
- model_name + model_version binding per trace prevents silent model swaps
  going unrecorded.
- Optional transport encryption via auditar core endpoint with token auth.

Field mapping:
  auditar_sdk.models.DecisionRecord.model_version -> integrity baseline
  client.token -> authenticated telemetry path
  auditar_sdk.http_client.HttpClient -> TLS + auth controls

================================================================================
SUTRA 7 — AUDIT TRAIL / REGULATORY INSPECTION READINESS
================================================================================
Requirement: Complete, immutable audit trail available for supervisory review.

SDK evidence:
- Local SQLite queue persists decision records with timestamps.
- Batch export via InferenceSession produces reviewable artifacts.
- Gateway logging exposes campaign attribution without embedding telemetry in SDK.

Field mapping:
  auditar_sdk.models.DecisionRecord -> individual auditable event
  auditar_sdk.models.BatchRequest -> audit batch
  gateway/attribution.db -> deployment/operational lineage
  GitHub Release tag + PyPI version -> packaged artifact provenance

================================================================================
PRODUCTION READINESS SUMMARY
================================================================================
This SDK provides observation and local queueing at launch. The following
production capabilities are provided through the Auditar platform / pilot:

- Governance dashboard and RBI FREE-AI 7-Sutras compliance report export
- Centralized multi-tenant audit store with role-based access control
- Alerting, anomaly detection, and SLA reporting
- Managed gateway and attribution pipeline
- On-prem or regulated-cloud deployment options

Auditar-sdk is the client-side instrumentation layer.
The Auditar platform is the compliance enforcement layer.

================================================================================
CONTACT
================================================================================
For pilots, RBI mapping reviews, or enterprise deployment:
foundersoffice@auditar.in / https://auditar.in
