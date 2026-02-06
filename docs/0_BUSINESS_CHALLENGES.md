# 0. Business Challenges & Value

## Business Challenge

Every declined legitimate transaction is lost revenue. Key pain points: **false declines**, **static rules**, **suboptimal routing**, **manual analysis**.

## Solution

Databricks-powered platform: (1) real-time ML on every transaction, (2) smart routing, (3) intelligent retry, (4) 7 AI agents, (5) Genie for natural-language analytics.

## Payment Services Context

| Service | Description | Status |
|---------|-------------|--------|
| Antifraud | Risk scoring; ~40–50% of declines | Active |
| 3DS | SCA; 60% auth success, 80% authenticated approved | Active |
| Vault, Data Only, Recurrence, Network Token, Click to Pay | Tokenization, enrichment, subscriptions, etc. | Active |
| IdPay, Passkey | Biometric, FIDO2 | Pre-prod / Dev |

All tracked in simulator → bronze → silver → gold.

## Data Foundation

**Smart Checkout**, **Reason Codes**, **Smart Retry** depend on: canonical data model, dedup (`canonical_transaction_key`), reason-code mapping, service-path tracking.

## Geography & Channels

Brazil >70% volume. Entry channels (Brazil): PD ~62%, WS ~34%, SEP ~3%, Checkout ~1%. Flows: Checkout BR → PD → WS → Base24 → Issuer; recurring/legacy variants.

## Initiatives

| Initiative | Scope | Platform deliverables |
|------------|--------|------------------------|
| **Smart Checkout** | Payment links, Brazil | Service-path breakdown, 3DS funnel, antifraud attribution, decision logging |
| **Reason Codes** | Full e-commerce, Brazil | Consolidated declines (4 entry systems), unified taxonomy, actionable insights, feedback loop, False Insights counter-metric |
| **Smart Retry** | Brazil | Recurrence vs reattempt (`retry_scenario`), features, success rate, effectiveness (Effective/Moderate/Low) |

## Key Objectives & Impact

| Goal | Target | Initiative lift (approval) |
|------|--------|---------------------------|
| Approval rates | 90%+ | Smart routing +2–5%, retry +1–2%, false positive reduction +1–2%, network token +1–3%, 3DS +0.5–1% → **+6–13% total** |
| Operational | ~80% faster insights | Genie 100+ MAU; ~20 h/week reporting saved; ~40% fewer manual reviews |

## Why Databricks

Unified data + ML + apps; real-time; scalable; Unity Catalog; serverless.

## Success Metrics

**Primary:** Approval 90%+; revenue recovery; false positive <2%. **Secondary:** Genie adoption, query success >85%, model latency <50ms p95. **Counter:** False Insights rate. **Monitoring:** Real-time (serving); daily (approval/retry); weekly (Genie/drift); monthly (ROI).

---

**Next:** [1_DEPLOYMENTS](1_DEPLOYMENTS.md) · [2_DATA_FLOW](2_DATA_FLOW.md) · [3_AGENTS_VALUE](3_AGENTS_VALUE.md) · [4_TECHNICAL](4_TECHNICAL.md) · [5_DEMO_SETUP](5_DEMO_SETUP.md)
