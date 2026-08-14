# Control matrix

## How to read this matrix

This matrix reports evidence in the public reference implementation. It is not a compliance statement and does not replace an adopter's control framework, legal analysis, risk assessment, or operating-effectiveness testing.

| Status | Meaning |
|---|---|
| Implemented | Present in the current code or repository with identifiable evidence |
| Partial | Some design or technical elements exist; the control objective is not fully met |
| Documented only | A required practice is described but not enforced by the application |
| Not implemented | No current mechanism meets the objective |
| Not assessed | Evidence has not been produced |

## Current control evidence

| ID | Control objective | Status | Current evidence | Production requirement or gap |
|---|---|---|---|---|
| GOV-01 | Assign accountable ownership | Partial | Repository owner and decision model in `GOVERNANCE.md` | Each deployment needs business, data, product, security, privacy, model-risk, risk, adoption, finance, and operations owners |
| GOV-02 | Define intended and prohibited use | Implemented | `README.md`, `docs/INDUSTRY_USE_CASES.md`, and `AI_SYSTEM_CARD.md` | Enforce use-case approval and periodically test actual use |
| GOV-03 | Record risk acceptance | Not implemented | Risks are listed, but no deployment authority exists | Named authority, scope, expiry/review date, evidence, conditions, and residual-risk sign-off |
| GOV-04 | Stop or retire weak use cases | Documented only | Pilot scorecard includes stop rules | Portfolio process, owner, funding stop, data disposition, and service retirement evidence |
| DAT-01 | Classify data and establish authority/purpose | Documented only | Industry and privacy documents define entry boundaries | Data catalog integration, purpose enforcement, rights/consent/legal basis as applicable, and owner approval |
| DAT-02 | Minimize prompt and retained context | Partial | User-character and history-message limits; bounded retrieved excerpts | Context-specific fields, DLP, redaction/tokenization, derived-data treatment, and minimization tests |
| DAT-03 | Apply retention, legal hold, and disposal | Not implemented | Individual conversation delete exists | Policy-driven retention, hold, backup propagation, deletion verification, and evidence |
| DAT-04 | Support complete export and verified erasure | Partial | Conversations can be read and deleted through the API | Authorized export, SQLite/WAL/backup treatment, secure device disposal, and erasure verification |
| DAT-05 | Protect data at rest with organization-controlled keys | Not implemented | SQLite content is plaintext; OS controls are external | Application/data encryption, KMS/HSM, rotation, revocation, separation of duties, and recovery |
| IAM-01 | Authenticate users and services | Not implemented | Loopback host boundary only | Enterprise OIDC/workload identity, device posture, session control, and service authentication |
| IAM-02 | Authorize by user, role, tenant, purpose, and data | Not implemented | No owner/tenant fields or RBAC | Deny-by-default policy, tenant isolation, least privilege, privileged access, and tests |
| NET-01 | Keep local inference bound to loopback | Implemented | Config rejects non-loopback llama host; runtime command and tests enforce it | Shared profiles require authenticated private networking and segmentation |
| NET-02 | Provide a strict external-egress-off mode | Implemented | Offline default; search suppression; hosted backend rejected; local Transformers uses local-only assets; tests | Network-layer deny policy and packet-level verification for regulated deployment |
| NET-03 | Control approved external endpoints | Partial | Provider selection, narrow search behavior, public URL/port checks | Central egress proxy, DNS policy, endpoint allowlist, contracts, monitoring, and emergency revoke |
| SUP-01 | Verify model and runtime artifacts | Implemented | Pinned model revision/hash, llama release/hash, installed-file manifest, tests | Signed provenance, private artifact registry, revocation, repeatable offline bundle, and independent verification |
| SUP-02 | Pin and review application dependencies | Partial | Exact direct Python pins; npm lockfiles; Dependabot and CodeQL | Hash-locked Python transitive set, license/security policy, malicious-package controls, and approved mirrors |
| SUP-03 | Produce SBOM and build/release provenance | Not implemented | Third-party notice exists | Machine-readable SBOM, signed attestations, release signing, retention, and consumer verification |
| MOD-01 | Inventory model, version, configuration, and license | Partial | System card and installer pins | Deployment registry, owner, approval, evaluation, rollout, exceptions, and retirement state |
| MOD-02 | Validate model for the context of use | Not assessed | Engineering tests only | Representative locked test sets, acceptance thresholds, independent review, subgroup/error analysis, and ongoing monitoring |
| RAI-01 | Maintain meaningful human oversight | Documented only | Intended-use and human-control guidance | Workflow enforcement, reviewer competence/authority, time, evidence, escalation, and sampled effectiveness |
| RAI-02 | Enforce harmful or consequential-use policy | Not implemented | General system prompt; no domain policy service | Configurable policy engine, use-case gates, output controls, red-team suite, override governance, and incident handling |
| RET-01 | Prevent retrieval of internal/private network resources | Partial | Scheme, credential, port, IP, DNS, redirect, size, and content-type checks | Bind validation to the actual connection to close DNS rebinding/TOCTOU risk; egress firewall |
| RET-02 | Treat retrieved content as untrusted | Partial | Evidence is JSON-encoded, delimiter-escaped, bounded, and described as non-instructional | Adversarial corpus, content sanitization policy, model-independent prompt-injection detection, and action isolation |
| AUD-01 | Create tamper-evident decision and control evidence | Not implemented | Ordinary database content and logs only | Event schema, immutable/tamper-evident store, clock/correlation, access control, retention, reconstruction, and integrity tests |
| SEC-01 | Limit local web/API attack surface | Partial | Trusted hosts, narrow CORS, loopback startup, input limits, no shell/file tools | Authentication, CSRF/session design as applicable, rate limits, headers/TLS, endpoint authorization, pentest, and secure packaging |
| SEC-02 | Report and remediate vulnerabilities | Partial | `SECURITY.md`, private-reporting route, CodeQL, Dependabot | Operational response team, SLAs, dependency policy, private vulnerability reporting enabled, patch/revoke exercises |
| PRV-01 | Make processing and external disclosures transparent | Implemented | `PRIVACY.md`, runtime profiles, UI search-mode wording | Context-specific privacy notice, individual rights process, contracts, DPIA/assessment, and effectiveness review |
| OPS-01 | Observe service health and model readiness | Partial | `/api/health`, state detail, application logs | Privacy-aware metrics/traces, SLI/SLO, alerting, SIEM, on-call, capacity and quality monitoring |
| OPS-02 | Respond to AI, security, privacy, and operational incidents | Documented only | Security escalation and risk register | Integrated incident plan, severity, evidence, regulator/customer routes, exercises, corrective action, and lessons |
| OPS-03 | Back up and recover authorized data and service | Not implemented | No application backup/restore procedure | Encrypted backup, restore test, RPO/RTO, corruption/failure exercises, key recovery, and data disposition |
| SCL-01 | Scale without losing isolation, ordering, or availability | Not implemented | Current code explicitly uses one worker and one generation slot | Stateless tier, shared database, distributed coordination, inference pools, quotas, HA/DR, and load evidence |
| CHG-01 | Test and review changes before merge | Implemented | Quality CI, CodeQL, CODEOWNERS, PR template, and governance gates | Protect `main`, review check results, add release signing/SBOM/license controls, measure operating effectiveness |
| LIC-01 | Publish source and third-party terms | Implemented | Apache-2.0 `LICENSE`, `NOTICE`, SPDX metadata, and third-party notices | Automated dependency license inventory and legal review for distribution profiles |

## Priority gates

### Before any controlled pilot

- name all owners and approved data;
- keep the API on loopback and strict offline mode on unless egress is explicitly approved;
- use a managed device and approved endpoint/disk controls;
- establish intended/prohibited use, human review, evaluation, incident, deletion, and stop procedures;
- use synthetic, public, or specifically approved low-sensitivity data.

### Before shared departmental use

IAM-01, IAM-02, DAT-03, DAT-05, AUD-01, OPS-02, OPS-03, SCL-01, and the required parts of RAI-01/02 must move from `Not implemented` or `Documented only` to independently tested implementation.

### Before regulated production

All applicable controls require context-specific design, traceable evidence, operating-effectiveness tests, accountable residual-risk acceptance, and periodic revalidation. Repository status alone is never sufficient.
