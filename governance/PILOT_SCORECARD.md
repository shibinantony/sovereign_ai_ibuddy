# Pilot scorecard

## Instructions

Copy this file for each pilot. Replace every bracketed field. Use `?` where evidence is unknown; do not manufacture a score. A pilot cannot start while the accountable owner, permitted data, human decision, incident route, or stop rule is unknown.

## Decision record

| Field | Entry |
|---|---|
| Pilot name | [Name] |
| Business problem | [Workflow pain and consequence, without leading with technology] |
| Beneficiary | [User/customer/organization] |
| Executive sponsor | [Named person] |
| Business outcome owner | [Named person] |
| Product/technology owner | [Named person] |
| Data owner | [Named person] |
| Security owner | [Named person] |
| Privacy owner | [Named person] |
| Model-risk/responsible-AI owner | [Named person] |
| Risk acceptance owner | [Named person and delegated authority] |
| Adoption owner | [Named person] |
| Finance partner | [Named person] |
| Pilot start/end | [Dates] |
| Decision review | [Date and forum] |
| Current decision | [Start / revise / stop / scale] |

## Context and boundary

| Field | Entry |
|---|---|
| Intended use | [One narrow, testable use] |
| Prohibited use | [Consequential and other excluded tasks] |
| Users and affected people | [Population and material impact] |
| Human decision | [Who checks what, with what authority and evidence] |
| Reversibility | [How an error is detected, corrected, and contained] |
| Input data class and authority | [Classification, purpose, owner approval] |
| Output data class | [Classification and downstream restrictions] |
| Runtime profile | [Strict local / approved search / hosted] |
| External endpoints | [Every provider/domain, or none] |
| Storage and retention | [Location, duration, deletion, hold, backups] |
| Model/runtime version | [Exact IDs/hashes] |
| Support and incident route | [Owner and contact process] |

## Entry gate

| Requirement | Evidence | Owner | Status |
|---|---|---|---|
| Measurable business outcome and baseline plan | | | ? |
| Approved intended and prohibited use | | | ? |
| Permitted data and device/network boundary | | | ? |
| Representative, locked evaluation set | | | ? |
| Qualified human review and escalation | | | ? |
| Security, privacy, model-risk, and legal/compliance review as applicable | | | ? |
| Installation/model/dependency source and license review | | | ? |
| Incident, rollback, deletion, end date, and stop rule | | | ? |

**Gate 0 decision:** [Start / revise / stop]

## Outcome and adoption

Set targets only after the baseline is measured.

| Measure | Baseline | Proposed target | Actual | Evidence source | Owner | Confidence |
|---|---:|---:|---:|---|---|---|
| Workflow cycle time | ? | ? | ? | | | ? |
| Accepted output/task rate | ? | ? | ? | | | ? |
| Human review/rework time | ? | ? | ? | | | ? |
| Throughput or service quality | ? | ? | ? | | | ? |
| Eligible-user active adoption | ? | ? | ? | | | ? |
| Correct-workflow use | ? | ? | ? | | | ? |
| User correction/rejection | ? | ? | ? | | | ? |
| Unapproved alternative use | ? | ? | ? | | | ? |

## Quality and model risk

| Test | Threshold | Result | Evidence | Owner | Status |
|---|---:|---:|---|---|---|
| Factual/task correctness | ? | ? | | | ? |
| Unsupported claim or citation | ? | ? | | | ? |
| Completeness and relevance | ? | ? | | | ? |
| Safe uncertainty/abstention | ? | ? | | | ? |
| Prompt-injection and hostile-source behavior | ? | ? | | | ? |
| Sensitive-data leakage | ? | ? | | | ? |
| Prohibited-use attempts | ? | ? | | | ? |
| Language/subgroup/accessibility performance where applicable | ? | ? | | | ? |
| Reviewer agreement and escalation | ? | ? | | | ? |

Record evaluation-set version, sampling method, adjudication, exclusions, and confidence interval where meaningful. An average score cannot hide a material failure mode.

## Control effectiveness

| Control | Test | Pass condition | Result/evidence | Owner | Status |
|---|---|---|---|---|---|
| Offline/external-egress policy | Observe expected and blocked traffic | No unapproved endpoint or payload | | | ? |
| Identity/device boundary | Attempt unauthorized access | Access denied and event handled | | | ? |
| Data classification/minimization | Sample inputs and derived stores | Only approved necessary data | | | ? |
| Retention/deletion | Delete a test case and inspect all stores | Meets approved disposition rule | | | ? |
| Human approval | Sample material tasks | Qualified review is substantive and traceable | | | ? |
| Failure/rollback | Remove model/search/storage dependency | Approved failure policy and recovery | | | ? |
| Model/runtime change | Attempt unapproved version | Prevented or detected; approved rollout can roll back | | | ? |
| Incident response | Run tabletop or simulation | Ownership, evidence, containment, communication, learning | | | ? |

## Operations and scalability

| Measure/test | Target | Result | Evidence | Owner | Status |
|---|---:|---:|---|---|---|
| Time to first token and completion percentiles | ? | ? | | | ? |
| Queue, concurrency, cancellation, and backpressure | ? | ? | | | ? |
| Availability/error behavior | ? | ? | | | ? |
| Support effort and incident volume | ? | ? | | | ? |
| Backup restore and data consistency | ? | ? | | | ? |
| Approved RTO/RPO recovery exercise | ? | ? | | | ? |
| Capacity headroom and failure reserve | ? | ? | | | ? |

The current workstation profile is not eligible for shared-service scale. Complete only the measures relevant to the approved profile; do not reinterpret missing enterprise controls as “not applicable” without risk-owner approval.

## Economics

| Item | Assumption | Actual | Confidence/source |
|---|---:|---:|---|
| Eligible tasks per period | ? | ? | |
| Adoption and accepted-task rate | ? | ? | |
| Verified time/quality value per accepted task | ? | ? | |
| Hardware, facilities, and energy | ? | ? | |
| Engineering and integration | ? | ? | |
| Security, privacy, validation, and compliance | ? | ? | |
| External services and licenses | ? | ? | |
| Operations, support, monitoring, and training | ? | ? | |
| Resilience, incident, change, and exit | ? | ? | |
| Confidence-adjusted net benefit | ? | ? | |

Classify each benefit as hard saving, cost avoidance, capacity, revenue enablement, service quality, or risk avoidance. Do not double count.

## Exceptions and incidents

| ID | Type | Description | Owner | Severity | Treatment | Due/review | Status |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

No exception can silently redefine the intended use, data boundary, or human decision. Material exceptions require the delegated risk authority and an expiry/review date.

## Final decision

### Scale rule

[List the value, quality, adoption, risk, economic, and operational conditions that all must be true.]

### Stop rule

[List material-harm thresholds, failed controls, lack of value/adoption, cost limits, and the stop date/owner.]

### Decision

- **Outcome:** [Scale / revise / stop]
- **Evidence summary:** [Observed facts, not aspirations]
- **Residual risks accepted by:** [Name, authority, date, scope, expiry]
- **Funded remediation:** [Owner, due date, acceptance test]
- **Next review or retirement date:** [Date]
- **What would reverse this decision:** [Trigger]
