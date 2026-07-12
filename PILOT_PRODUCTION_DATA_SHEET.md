AUDITAR-SDK — PILOT PRODUCTION DATA SHEET
One-page brief for ML Platform Leads, CISOs, and compliance heads.

================================================================================
PRODUCT
================================================================================
auditar-sdk is an open-source Python instrumentation layer for AI decision audit.
It captures inputs and outputs only — never model weights, gradients, or training
data — and emits structured decision records through a local SQLite queue.

This data sheet covers the **production tier** delivered through the Auditar
platform after the free 8-week pilot.

================================================================================
PILOT SCOPE
================================================================================
- Up to 5 production models instrumented
- Workspace + model registration in auditar core
- Batch inference trace capture with sub-ms SDK overhead
- Local SQLite queue for air-gapped infra
- Weekly sync with Auditar engineers

What you get in the pilot:
- Live inference observability within 15 minutes
- RBI FREE-AI 7-Sutras mapping dashboard
- Raw trace export for internal compliance review

================================================================================
PRODUCTION TIER CAPABILITIES
================================================================================
1. Governance Dashboard
   - Model-level oversight for every lending / fraud / credit decision
   - Time-range drill-down, drill-in to individual decisions
   - Workspace-level tenant isolation

2. Audit Report Export
   - Schedule or ad-hoc PDF/JSON exports for supervisory review
   - Field-level lineage: model name, version, use case, workspace, timestamp

3. Alerting & Anomaly Detection
   - Threshold alerts on drift, latency spikes, batch failure rate
   - Escalation via email / webhook / Slack

4. Access Control
   - SSO / OIDC support
   - Role-based access: viewer, analyst, admin
   - Audit logs for admin actions

5. Deployment Options
   - Managed SaaS on India-region cloud
   - Private VPC / on-prem option with data residency controls
   - No model weights ever leave your network

6. Support
   - L1/L2 support during business hours IST
   - 24x7 for production incidents
   - 30-day notice for breaking schema changes

================================================================================
SECURITY & PRIVACY
================================================================================
- Zero-knowledge observation: inputs/outputs only
- No model weights, gradients, or training data accessed
- Transport encryption in transit
- Encryption at rest for centralized audit store
- No mandatory telemetry inside auditar-sdk package
- Audit trail is append-only in production tier

================================================================================
SLAs
================================================================================
- SDK availability: client-side; no SLA applicable
- Platform availability: 99.9% monthly for managed SaaS
- Incident response:
    P1 - 1 hour initial response, 4 hour resolution target
    P2 - 4 hour initial response, 1 business day resolution target
- Data retention: configurable per workspace; default 24 months
- Schema change policy: 30-day deprecation notice

================================================================================
PRICING INDICATIVE
================================================================================
Model A: Per-workflow managed instrumentation
  INR 75,000 / workflow / month

Model B: Managed decisions endpoint
  $49 per 1M decisions

Data sheet covers framework only; final pricing depends on model count, volume,
and deployment region. Pilot is free. Proposal follows kickoff.

================================================================================
TERMS
================================================================================
Pilot: 8 weeks, no credit card, no auto-renewal.
Production: monthly or annual contract; annual prepay preferred.
Buyout / on-prem: quote on request.

================================================================================
NEXT STEP
================================================================================
- Pilot: foundersoffice@auditar.in
- Docs: https://github.com/Pulvan/auditar-sdk
- Package: pip install auditar-sdk
