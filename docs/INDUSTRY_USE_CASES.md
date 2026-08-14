# Industry use cases and decision boundaries

## Purpose

This document helps a business, risk, and technology team choose a pilot that is useful enough to measure and contained enough to govern. It does not declare any use case compliant. Applicable law, regulation, policy, contracts, data rights, and sector guidance must be assessed for the adopting organization and jurisdiction.

## Common entry test

A scenario is eligible for the current workstation pilot only when every answer is `yes`:

1. Is the outcome a reviewable draft, research aid, explanation, or learning artifact?
2. Is a named human accountable for checking the output before it affects another person or a system of record?
3. Is the input data approved for the selected device, model, storage, and network profile?
4. Can a wrong, missing, or delayed answer be detected and reversed without material harm?
5. Are the baseline, evaluation set, owner, pilot end date, and stop rule defined?
6. Can the scenario remain single-user and loopback-only during the pilot?

If any answer is `no`, use an enterprise control path or defer the scenario.

## BFSI

### Candidate pilots

| Problem | Useful pilot outcome | Minimum evidence |
|---|---|---|
| Analysts spend time converting public or approved internal material into a first draft | Faster reviewable brief with clear source boundaries | Blind quality review, factual-error rate, cycle time, reviewer effort |
| Employees struggle to navigate approved policy or procedure content | Faster route to the relevant policy section and escalation owner | Retrieval accuracy, abstention behavior, version control, user task success |
| Control teams repeat non-customer research and drafting | Consistent first-pass working paper for human completion | Template adherence, unsupported-claim rate, rework, audit sampling |
| Training teams need private role-play or explanation | Locally available learning support using synthetic scenarios | Learning outcome, harmful advice tests, adoption, facilitator review |

### Excluded from the current implementation

- creditworthiness, affordability, limit, pricing, underwriting, or eligibility decisions;
- fraud, sanctions, AML, KYC, adverse-media, or suspicious-activity disposition;
- trading, execution, investment advice, market communication, or portfolio action;
- insurance claims approval, denial, settlement, or customer vulnerability decisions;
- autonomous regulatory reporting, complaint resolution, or system-of-record changes;
- processing live customer secrets or regulated records without approved identity, encryption, retention, audit, and data-loss controls.

### Controls before a BFSI production path

- enterprise identity, least privilege, segregation of duties, and customer/tenant isolation;
- approved data lineage, purpose, minimization, retention, residency, and deletion;
- model inventory, intended-use approval, independent validation, outcome monitoring, and material-change control;
- immutable evidence for prompts or events where policy requires it, with access and retention controls;
- human approval and four-eyes controls for material outputs;
- fairness, explainability, consumer-harm, conduct, and operational-resilience assessment appropriate to context;
- incident reporting, customer redress, rollback, business continuity, and third-party exit.

## Pharma and life sciences

### Candidate pilots

| Problem | Useful pilot outcome | Minimum evidence |
|---|---|---|
| Teams spend time locating and explaining approved public guidance | Faster, traceable research draft | Source correctness, freshness, reviewer agreement, cycle time |
| Authors need a private first draft from synthetic or approved content | Structured draft for qualified human review | Completeness rubric, unsupported statements, rework, provenance |
| Quality teams prepare non-GxP investigation notes or training scenarios | Consistent preparation artifact | Template accuracy, omission rate, user review, clear non-record status |
| Researchers need local brainstorming without patient or proprietary study data | Reusable hypotheses or search terms | Novelty/usefulness review, hallucination tests, no sensitive input |

### Excluded from the current implementation

- diagnosis, prognosis, triage, dosing, treatment, or patient-specific guidance;
- clinical decision support or medical-device functions;
- pharmacovigilance case assessment, signal disposition, or regulatory reporting;
- batch disposition, release, stability, manufacturing control, or quality-system decisions;
- generation of a GxP record, submission claim, clinical endpoint, or validated calculation;
- processing patient, trial, genomic, safety, manufacturing, or proprietary molecule data without the full approved control environment.

### Controls before a pharma production path

- documented context of use, risk classification, data provenance, representativeness, and scientific validity;
- GxP or other applicable computerized-system validation and electronic-record controls;
- qualified human oversight, defined escalation, and traceable review;
- locked evaluation data, predefined acceptance criteria, reproducibility, and change impact assessment;
- privacy, consent or other lawful authority, minimization, retention, residency, and re-identification risk controls;
- model/version traceability, vendor and open-source qualification, monitoring, deviation, CAPA, rollback, and retirement;
- regulatory, quality, safety, medical, security, and privacy approval appropriate to the intended use.

## Government and other sensitive enterprises

### Candidate pilots

- drafting or summarizing public information;
- local learning and controlled synthetic-data exercises;
- non-classified procedure explanation with a human verifying the authoritative source;
- business-continuity support where external model services are unavailable;
- private ideation that does not include protected personal, national-security, export-controlled, client, or privileged data.

### Excluded from the current implementation

- classified, secret, export-controlled, law-enforcement-sensitive, or operational-security data;
- benefits, immigration, employment, legal, disciplinary, or other rights-affecting decisions;
- surveillance, biometric identification, emotion inference, or targeting;
- autonomous public communication, enforcement, physical control, or records changes;
- shared service use before identity, authorization, tenancy, audit, and resilience controls exist.

## Human-control pattern

The current safe operating pattern is:

```text
approved input
  -> private AI produces a draft or research aid
  -> qualified human checks source, correctness, policy, and impact
  -> human edits or rejects
  -> human performs any material action in the authorized system
```

The AI must not be the final approval point. A person clicking “accept” without adequate time, competence, evidence, and authority is not meaningful human oversight.

## Data decision

| Data class | Current pilot position |
|---|---|
| Public or synthetic | Preferred, subject to source and license review |
| Internal, low sensitivity | Possible only with business/data owner approval and a managed device |
| Confidential, personal, customer, patient, trial, or proprietary | Defer until the required identity, encryption, retention, privacy, audit, and endpoint controls are implemented and approved |
| Secret, classified, export-controlled, or prohibited by contract/policy | Not permitted |

Local storage reduces one transfer risk; it does not establish authority to use the data.

## Scenario decision record

Before a pilot, record:

- business problem and beneficiary;
- baseline, target, and evaluation method;
- input/output data classes and authority;
- selected runtime profile and every external endpoint;
- intended use, excluded use, and human decision;
- material failure modes and reversibility;
- owners for business, data, product, security, privacy, model risk, adoption, and finance;
- incident, deletion, exit, and review dates;
- scale rule and stop rule.

Use [PILOT_SCORECARD.md](../governance/PILOT_SCORECARD.md) as the working record.
