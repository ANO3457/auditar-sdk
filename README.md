# auditar-sdk

[![PyPI version](https://img.shields.io/pypi/v/auditar-sdk)](https://pypi.org/project/auditar-sdk/)
[![PyPI downloads](https://img.shields.io/pypi/dm/auditar-sdk)](https://pypistats.org/packages/auditar-sdk)
[![Python Version](https://img.shields.io/pypi/pyversions/auditar-sdk)](https://pypi.org/project/auditar-sdk/)

Zero-knowledge inference instrumentation for AI decision audit.

`pip install auditar-sdk`

- Captures inputs/outputs only — never touches model weights
- Works with scikit-learn, XGBoost, LightGBM, and custom APIs
- Decorator API or batch context manager
- Local SQLite queue for air-gapped deployments
- Sub-ms overhead

Built for regulated AI in Indian financial services. [RBI FREE-AI 7-Sutras ready](https://github.com/Pulvan/auditar-sdk/blob/sdk/RBI_7SUTRAS_COMPLIANCE_MAPPING.md).

## Quick install

```bash
pip install auditar-sdk
```

## Quickstart

```python
from auditar_sdk import AuditarClient, trace_inference, InferenceSession

client = AuditarClient(
    workspace="retail-lend-prod",
    endpoint="https://core.auditar.io",
    default_use_case="loan",
)

@trace_inference(client, model_name="Credit-Scout-V2", use_case="loan")
def predict(income, credit_score, age, existing_debt):
    return model.predict_proba([[income, credit_score, age, existing_debt]])[0][1]

prob = predict(income=75000, credit_score=680, age=35, existing_debt=12000)
```

## What you get in open source

- Inference observation without model access
- Decorator + async decorator + batch context manager
- Local queue for air-gapped environments
- Deterministic decision records: inputs, outputs, model name, version, workspace, timestamp
- No mandatory telemetry or outbound connectivity

## What you will need for production

The open-source SDK is the instrumentation layer. For production governance in regulated financial services, you also need:

- Governance dashboard with workspace-level tenant isolation
- RBI FREE-AI 7-Sutras compliance report export
- Alerting, anomaly detection, and SLA reporting
- Role-based access control and SSO
- Centralized audit store with encryption at rest and append-only trail
- Managed gateway and attribution pipeline
- On-prem or private VPC deployment option

Those capabilities are delivered through the Auditar platform after the free pilot.

If you are an ML Platform Lead at an Indian fintech, NBFC, or neo-bank, this is the fastest path from observability to compliance:

1. `pip install auditar-sdk`
2. Instrument your models locally
3. 15-minute pilot kickoff with Auditar engineers
4. Live production governance dashboard + RBI mapping

**From pip install to pilot: https://auditar.in/?utm_source=github&utm_medium=sdk&utm_campaign=launch#pilot**

## Local queue overflow notifications

`LocalTransport` accepts an optional synchronous `on_queue_full` callback:

```python
import logging
from auditar_sdk.transport import LocalTransport

transport = LocalTransport(
    "auditar_queue.db",
    on_queue_full=lambda error: logging.warning("Audit queue capacity reached: %s", error),
)
```

The callback receives the same `QueueFullError` that `enqueue()` raises, after
the SQLite connection is closed. It runs once for each rejected enqueue; successful
enqueues do not call it. No decision payload is passed to the callback. Keep the
callback fast: it runs synchronously on the enqueue caller's thread (which may be
the client's flush timer). Do not call back into the same `AuditarClient` from this
hook: a flush can hold the client's lock. Callback exceptions are logged and do not replace the
original `QueueFullError`. The existing queue and overflow exception are preserved;
this hook does not retry, drop old records, or increase capacity. Pass this transport
to `AuditarClient(transport=transport, ...)` to observe client fallback overflows.

## Docs

- RBI mapping: `RBI_7SUTRAS_COMPLIANCE_MAPPING.md`
- Production data sheet: `PILOT_PRODUCTION_DATA_SHEET.md`
- Contributing: `CONTRIBUTING.md`
- Issues: https://github.com/Pulvan/auditar-sdk/issues

## Contact

foundersoffice@auditar.in
