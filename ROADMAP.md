# Roadmap

The roadmap is evidence-gated, not date-driven. A later stage is funded only when the preceding stage proves value and control effectiveness.

## Current - publish a defensible reference

- [x] Private-by-default local inference and history
- [x] Strict offline behavior and accurate UI language
- [x] Verified model/runtime assets, exact direct Python pins, and npm lockfiles
- [x] Business, industry, governance, risk, privacy, security, and scale documentation
- [x] CI, CodeQL, Dependabot, CODEOWNERS, and public contribution controls
- [ ] Complete first clean CI run and security review
- [ ] Produce machine-readable SBOM and signed release provenance

## Gate 1 - controlled pilot evidence

- [ ] Select one low-risk workflow, owner, permitted data set, and human decision
- [ ] Establish baselines and locked representative evaluation data
- [ ] Test outcome, accuracy, unsupported claims, misuse, prompt injection, privacy, deletion, failure, and recovery
- [ ] Measure user adoption, reviewer effort, support effort, capacity, energy, and cost per accepted task
- [ ] Record risk acceptance, scale rule, stop rule, and end-of-pilot data disposition

**Exit:** steering group chooses scale, revise, or stop using observed evidence.

## Gate 2 - shared enterprise control plane

- [ ] OIDC/workload identity, RBAC/ABAC, tenant and purpose isolation
- [ ] Encrypted shared persistence, KMS, retention, hold, export, deletion, and tested restore
- [ ] Policy/DLP, model inventory, approved retrieval, human approval, and tamper-evident evidence
- [ ] Stateless application nodes, durable queues/locks, inference pools, quotas, backpressure, and canary/rollback
- [ ] Metrics, traces, SIEM, SLO, on-call, FinOps, incident, capacity, and DR exercises

**Exit:** independent security, privacy, model-risk, operational, and business acceptance for the defined shared use.

## Gate 3 - regulated product

- [ ] Sector/jurisdiction obligations mapped to implemented and tested controls
- [ ] Context-specific independent model/system validation
- [ ] Quality, consumer/patient, fairness, accessibility, human-oversight, records, and change controls
- [ ] HA/DR, support, third-party, exit, and periodic assurance
- [ ] Benefit realization and total lifecycle economics reviewed

**Exit:** accountable authorities approve a bounded context of use. No blanket “compliant” status.

## Gate 4 - sovereign or air-gapped operation

- [ ] Jurisdiction-bound compute, storage, keys, privileged operations, and support
- [ ] Private source/package/model registries and signed offline install/update/revoke bundles
- [ ] Complete SBOM, provenance, license inventory, independent supply-chain verification
- [ ] Multi-site continuity and provider/technology exit exercised
- [ ] Sovereignty definition and evidence independently assured

**Exit:** the organization demonstrates control across data, technology, operations, legal, supply chain, economics, mission continuity, and exit.
