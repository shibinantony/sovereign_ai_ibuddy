---
title: "Sovereign AI iBuddy Executive Brief"
date: 2026-08-14
status: hypothesis-to-validate
owner: Shibin Antony
tags:
  - ai-director
  - private-ai
  - sovereign-ai
  - regulated-industries
  - business-case
---

# Executive brief

## Core insight

Private AI should not be sold as a model running on a laptop. It should be managed as a business capability that keeps approved knowledge work inside a defined trust boundary, gives employees a sanctioned alternative to shadow AI, and earns the right to scale through measured value and control evidence.

Sovereign AI iBuddy is the reference implementation for that first decision. It proves a useful local baseline and exposes, rather than hides, the controls still required for regulated production.

## Decision requested

Approve a constrained pilot for one internal knowledge-work scenario and one accountable business owner.

The pilot is not approval to process unrestricted sensitive data or to automate a consequential decision. Its purpose is to answer five questions:

1. **Value:** Does a named workflow improve?
2. **Feasibility:** Can the organization operate the service within its approved technology boundary?
3. **Risk:** Does the private-by-default design reduce exposure to an acceptable residual level?
4. **Adoption:** Will employees use it correctly instead of an unapproved alternative?
5. **Economics:** Is the confidence-adjusted benefit greater than full lifecycle cost?

## Business problem

Sensitive organizations often face an unproductive choice:

- block public generative AI and leave employees without a useful alternative;
- accept cloud tools before data, legal, security, and model-risk boundaries are understood; or
- allow fragmented experiments that cannot prove value or be governed consistently.

The result can be shadow AI, duplicated spend, slow approval cycles, untraceable use of sensitive information, and pilots that never become accountable products.

## Proposed intervention

Start with the smallest operational footprint that can test the workflow safely:

- local Qwen generation through a verified llama.cpp runtime;
- local conversation persistence;
- strict offline mode by default;
- optional, explicitly enabled web retrieval;
- a visible boundary between implemented controls and production requirements;
- a pilot scorecard with owners, evidence, scale criteria, and stop criteria.

## Portfolio choice

| Choice | Assessment |
|---|---|
| **Adopt** | Yes, as a single-user reference implementation for a controlled pilot. |
| **Extend** | Only when approved organizational knowledge, identity, retention, and audit controls are required for the pilot. |
| **Build** | Only if the workflow is strategically valuable and evidence justifies an enterprise service with ongoing product ownership. |
| **Defer or retire** | Required when there is no measurable outcome, accountable owner, permitted data set, safe human-control model, adoption path, or credible economics. |

**Recommendation:** adopt the reference implementation for one low-risk scenario; defer regulated production until the control and scale gates pass.

## Outcome hypotheses

All entries below are proposals. The business owner must establish baselines and approve targets before the pilot begins.

| Outcome | Baseline | Proposed target | Evidence | Status |
|---|---:|---:|---|---|
| Time from approved input to reviewable first draft | TBD | Set after baseline | Workflow timestamps and sampled task study | Unvalidated |
| Rework required before human acceptance | TBD | Set by risk and quality owner | Structured reviewer rubric | Unvalidated |
| Use of unapproved external AI for the chosen workflow | TBD | Directional reduction | Anonymous adoption survey and security signals | Unvalidated |
| Correct use of citations or approved source material | TBD | Set by use-case materiality | Blind evaluation set | Unvalidated |
| Active use in the target workflow | TBD | Set by adoption owner | Eligible-user and task-level measures | Unvalidated |
| Cost per accepted task | TBD | Below the approved alternative | Hardware, support, energy, and labor allocation | Unvalidated |

Capacity released is not automatically a cash saving. It becomes financial value only when it enables avoided spend, additional throughput, faster revenue or risk reduction, or productive redeployment.

## Principal risks

| Risk | Executive implication | Pilot response |
|---|---|---|
| Confident but incorrect output | A local model can still create operational or customer harm | Limit to reviewable drafts; use representative evaluation and named human approval |
| Sensitive data retained in plaintext | Locality does not equal encryption or records compliance | Use approved test data and device controls; do not scale until encryption and retention are designed |
| Unapproved external traffic | Search or hosted generation can cross the boundary | Keep strict offline mode enabled unless an explicit egress decision is approved |
| Weak user identity and accountability | The current API is single-user and unauthenticated | Keep it loopback-only; require enterprise identity before shared use |
| Pilot-to-platform leap | A workstation success does not prove concurrency, resilience, or TCO | Run capacity, recovery, support, and economics gates before architecture investment |
| Automation bias | Users may treat fluent text as a decision | Train for verification, show sources where relevant, and prohibit consequential automation |

The complete working register is in [Risk register](../governance/RISK_REGISTER.md).

## Accountability model

| Role | Decision right |
|---|---|
| Executive sponsor | Funds or stops the pilot; accepts the intended business outcome |
| Business outcome owner | Owns workflow baseline, target, adoption, and benefit realization |
| Data owner | Approves data classes, purpose, access, retention, and residency |
| Product/technology owner | Owns architecture, service operation, support, change, and exit |
| Security and privacy owners | Approve threat, egress, identity, device, and privacy controls |
| Model-risk/responsible-AI owner | Approves intended use, evaluation, limitations, and human oversight |
| Risk acceptance owner | Accepts residual risk within delegated authority |
| Finance partner | Validates cost, capacity conversion, and economic claims |

One person may fill more than one role in a small pilot, but every decision right must remain explicit.

## Pilot design

### Gate 0 - entry

- One workflow, population, owner, and permitted data classification are named.
- Prohibited uses and human approval are documented.
- A baseline and evaluation set exist before users are exposed.
- The device, installation sources, model license, and external-egress choice are approved.
- Incident, rollback, data deletion, and pilot end dates are agreed.

### Gate 1 - controlled operation

- Run with a small eligible group and approved test or low-risk internal data.
- Capture task outcome, reviewer quality, adoption, incidents, support effort, and cost.
- Test offline behavior, failure modes, deletion, model change, and misleading-output scenarios.
- Record every assumption and separate observed evidence from anecdote.

### Gate 2 - decision

Choose one:

- **Scale:** all material value, quality, adoption, risk, economics, and operational gates pass.
- **Revise:** the outcome remains credible and failed gates have funded owners and dates.
- **Stop:** value is weak, residual risk is unacceptable, adoption is absent, or operating cost is unjustified.

## Economics template

```text
Annual gross benefit
  = eligible tasks
  x adoption rate
  x verified time or quality benefit per accepted task
  x approved value-conversion rate

Annual lifecycle cost
  = hardware and facilities
  + engineering and integration
  + security, privacy, model-risk, and validation effort
  + licenses and external services
  + operations, support, energy, monitoring, and training
  + change, incident, resilience, and exit cost

Confidence-adjusted net benefit
  = (gross benefit x evidence confidence)
  - annual lifecycle cost
```

Do not monetize the same released capacity and avoided cost twice. Keep hard savings, cost avoidance, capacity, revenue enablement, and risk avoidance separate.

## 60-second executive proposition

> We have an opportunity to give sensitive knowledge workers a sanctioned AI workspace without making local prompts and history dependent on a public model service. I recommend a constrained, offline-by-default pilot using Sovereign AI iBuddy for one reviewable internal workflow. The pilot is owned by the business, with explicit data, technology, security, model-risk, adoption, and finance accountability. It will not make regulated decisions or process unrestricted sensitive data. We will scale only if measured workflow value, human-reviewed quality, correct adoption, residual risk, operating readiness, and full lifecycle economics meet agreed thresholds; otherwise we will revise or stop.

## Next action

Complete the [pilot scorecard](../governance/PILOT_SCORECARD.md), name each owner, and schedule the Gate 0 decision. No deployment should begin with ownership or permitted data marked `TBD`.
