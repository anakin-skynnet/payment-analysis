# 0. Business Challenges & Value

## Business Challenge

Every declined legitimate transaction is lost revenue and a frustrated customer. Organizations face:

- **False Declines** -- Good transactions blocked by overly cautious fraud rules
- **Static Rules** -- Systems that don't adapt to changing patterns
- **Suboptimal Routing** -- Not using the best payment solution per transaction
- **Manual Analysis** -- Slow, manual decline investigation

## Solution

A **Databricks-powered platform** that maximizes payment approval rates through:

1. **Real-time intelligence** -- ML models analyze every transaction in milliseconds
2. **Smart routing** -- Route to the best payment solution per transaction
3. **Intelligent retry** -- Recover declined transactions with high success probability
4. **AI-powered insights** -- 7 specialized AI agents for continuous optimization
5. **Natural language analytics** -- Business users query data without SQL (Genie)

---

## Payment Services Context

In the e-commerce context, a payment transaction can leverage several complementary services, which may be provided by the acquirer or by third parties. These services aim to increase security, improve user experience, and/or positively impact approval rates:

| Service | Description | Status |
|---------|-------------|--------|
| **Antifraud** | Risk scoring and fraud detection before authorization | Active -- accounts for ~40-50% of declines |
| **Vault** | Secure card-on-file tokenization | Active |
| **3DS** | Strong Customer Authentication (mandatory for debit in Brazil) | Active -- 60% auth success, 80% of authenticated approved |
| **Data Only** | Enriched data for issuer decisioning (no consumer friction) | Active -- uplift measurement in progress |
| **Recurrence** | Scheduled / subscription-based payment management | Active -- 1M+ transactions/month in Brazil |
| **Network Token** | Card-network-level tokenization (mandatory for Visa) | Active -- Visa + Mastercard |
| **IdPay (Unico)** | Biometric recognition for identity verification | Pre-production -- 60-80% expected success |
| **Passkey** | FIDO2 passwordless authentication | In development |
| **Click to Pay** | One-click checkout using stored credentials | Active |

All 9 services are tracked end-to-end in the platform's data pipeline (simulator -> bronze -> silver -> gold).

---

## Data Foundation for the Initiatives

The three core initiatives -- **Smart Checkout**, **Reason Codes**, and **Smart Retry** -- all rely on a significant effort around **data mapping**, **data treatment**, and **data quality** in order to generate relevant and actionable insights. Without a strong and well-aligned data foundation, the value extracted from these use cases will be limited.

### Canonical data model

- **Provenance fields**: `geo_country`, `entry_system`, `flow_type`, `transaction_stage`, `merchant_response_code`
- **Deduplication**: Deterministic `canonical_transaction_key` (SHA-256 over merchant, amount, card token, timestamp bucket) ensures one row per merchant-visible attempt
- **Mapping tables**: Reason code taxonomy (raw -> standard + group + actionability) and service routing context

---

## Geographic Distribution

From a geographic perspective, **Brazil accounts for more than 70%** of total transaction volume, which is why most of the concrete data points and early initiatives are currently Brazil-focused.

### Transaction distribution by entry channel (Brazil -- monthly view)

| Entry System | Share | Description |
|-------------|-------|-------------|
| **PD** (Digital Platform) | ~62% | Primary digital channel |
| **WS** (WebService) | ~34% | Legacy API integration |
| **SEP** (Single Entry Point) | ~3% | Unified entry point |
| **Checkout** | ~1% | Payment link / hosted checkout |

### Intermediation complexity

Transactions flow through multiple intermediate systems depending on the type:

| Transaction Type | Flow |
|-----------------|------|
| Payment Link | Checkout BR -> PD -> WS -> Base24 -> Issuer |
| Recurring | PD -> WS -> Base24 -> Issuer |
| Legacy merchant | WS -> Base24 -> Issuer |
| Payment Link via SEP | Checkout Global -> SEP -> Payments Core -> Base24 -> Issuer |

The platform consolidates data from all four entry systems with strict dedup controls to prevent double-counting.

---

## Initiative 1: Smart Checkout (Brazil -- Payment Links)

**Phase 1 scope**: Payment link transactions, Brazil-focused.

| Metric | Value |
|--------|-------|
| Annual volume | ~5 million transactions |
| Overall approval rate | ~73% |
| Variance | Significant by seller profile |

### Service breakdown (Payment Link -- Brazil)

| Service | Key Insight |
|---------|-------------|
| **Antifraud** | Accounts for ~40-50% of all declined transactions |
| **3DS** | Mandatory for debit; ~80% friction rate; 60% auth success; 80% of authenticated approved by issuer |
| **IdPay** | Not yet live; provider claims 60-80% biometric success |
| **Data Only** | No concrete approval-rate uplift data yet |
| **Network Token** | Mandatory for Visa; available for Visa + Mastercard |
| **Passkey** | Still under development; no production data |

### Platform implementation

- **Service-path breakdown**: every transaction's service path (antifraud + 3DS + token + ...) is tracked and aggregated
- **3DS funnel**: routed -> friction -> authenticated -> approved metrics
- **Antifraud attribution**: percentage of declines caused by antifraud decisions
- **Decision logging**: checkout path decisions recorded for analysis

---

## Initiative 2: Reason Codes Intelligence Layer (Brazil -- Full E-Commerce)

Unlike Smart Checkout, this initiative requires visibility over the **full set of e-commerce transactions** to correctly identify decline reasons across the entire approval chain.

### What the platform delivers

1. **Consolidated declines** across all 4 entry systems (Checkout, PD, WS, SEP) with dedup
2. **Unified taxonomy**: raw decline codes mapped to standardized reason groups with actionability classification
3. **Actionable insights**: recommended actions per decline pattern with estimated recoverable volume and value
4. **Feedback loop**: expert reviews recorded in `insight_feedback_silver` to continuously improve model accuracy
5. **Counter-metric (False Insights)**: percentage of insights marked invalid/non-actionable by domain specialists -- balances speed vs. accuracy and embeds expert validation in the learning loop

### Expected outcome

A data- and AI-driven intelligence layer that:

- Consolidates declines across different transaction flows and systems
- Standardizes decline reasons into a single, unified taxonomy
- Identifies approval rate degradation patterns and their most likely root causes
- Translates patterns into actionable insights with estimated approval or revenue uplift
- Enables a feedback loop, capturing executed actions and observed results to continuously improve

This layer supports not only descriptive/diagnostic analytics, but also **prescriptive and learning-based decision making** over time.

---

## Initiative 3: Smart Retry (Brazil)

Two distinct recurrence-related scenarios:

| Scenario | Description | Volume |
|----------|-------------|--------|
| **Payment Recurrence** | Scheduled / subscription-based payments (e.g., monthly charges) | Combined: 1M+ txn/month in Brazil |
| **Payment Retry** (Reattempts) | Cardholder retries after decline under same conditions (same card, amount, merchant) | |

### Platform implementation

- **Scenario separation**: `retry_scenario` field distinguishes recurrence vs reattempt
- **Feature engineering**: time since last attempt, attempt sequence, prior success history
- **Performance metrics**: success rate, recovered value, incremental lift vs baseline approval rate
- **Effectiveness classification**: Effective (>40%), Moderate (20-40%), Low (<20%)

---

## Key Objectives

| Goal | Target | Impact |
|------|--------|--------|
| **Approval rates** | 90%+ | +5-10 percentage points |
| **Revenue recovery** | Substantial | Capture declined legitimate transactions |
| **Customer experience** | Excellent | Fewer false declines |
| **Operational efficiency** | +80% | Automate manual review |
| **Self-service analytics** | 100+ users | Genie-based data access |

---

## Why Databricks

| Capability | Benefit |
|------------|---------|
| Unified platform | One environment for data, ML, and apps |
| Real-time processing | Sub-second decisions on live transactions |
| Scalability | Handle millions of transactions without redesign |
| AI/ML native | Production ML and LLMs |
| Governance | Unity Catalog for security and audit |
| Serverless | Auto-scaling, pay-per-use compute |

---

## Business Impact

### Approval rate improvement

| Initiative | Expected lift | Impact |
|-----------|----------------|--------|
| Smart routing | +2-5% | High |
| Smart retry | +1-2% | Medium-high |
| False positive reduction | +1-2% | Medium |
| Network tokenization | +1-3% | Medium-high |
| 3DS optimization | +0.5-1% | Medium |
| **Total potential** | **+6-13%** | **Significant** |

### Operational impact

- **Analyst productivity:** ~80% faster (e.g. 10h -> 2h per analysis)
- **Self-service:** 100+ business users via Genie
- **Reporting:** ~20 hours/week saved
- **Manual review:** ~40% fewer transactions needing human review
- **Root cause:** ~90% faster (minutes vs. days)

---

## Success Metrics

- **Primary:** Approval rate 90%+; revenue recovery; false positive rate <2%; customer satisfaction
- **Secondary:** Genie adoption (100+ MAU); query success >85%; model latency <50ms p95; fewer analyst requests
- **Counter-metrics:** False Insights rate (% invalid/non-actionable insights) tracked daily
- **Monitoring:** Real-time (serving, flow); daily (approval/retry); weekly (Genie, drift); monthly (impact, ROI)

---

## Next Steps

1. **Review** -- [1_DEPLOYMENTS](1_DEPLOYMENTS.md) for deployment steps
2. **Architecture** -- [4_TECHNICAL](4_TECHNICAL.md) for technical details
3. **Agents** -- [3_AGENTS_VALUE](3_AGENTS_VALUE.md) for the 7 AI agents
4. **Run demo** -- [5_DEMO_SETUP](5_DEMO_SETUP.md) for one-click run links

**Platform:** Databricks (Azure/AWS) | **Users:** Enterprise payments, fintechs, PSPs | **Deployment:** Databricks Asset Bundles
