# Initial risk register

## Method

This is a qualitative starting assessment for the public reference implementation. Ratings are hypotheses based on the documented deployment boundary, not a substitute for an adopter's risk method. Owners are roles until a pilot names people.

| ID | Risk scenario | Potential impact | Inherent | Current controls | Initial residual | Accountable role | Next treatment / gate |
|---|---|---|---|---|---|---|---|
| R-01 | A fluent but false or incomplete answer is trusted | Incorrect work, customer/patient harm, poor decision, reputation or regulatory exposure | High | Draft-only intended use, source cards, human-review guidance | High | Business and model-risk owners | Locked representative evaluation, acceptance thresholds, reviewer training, abstention/escalation, prohibit consequential use |
| R-02 | Sensitive prompts/history remain in plaintext SQLite or device remnants | Confidentiality breach, privacy or contractual harm | High | Device-local storage; `.env`/database excluded from Git | High | Data, privacy, and security owners | Approved low-risk data only; managed disk protection for pilot; application encryption, KMS, retention and erasure before scale |
| R-03 | Another local process or a remotely exposed API accesses conversations/model | Unauthorized read, change, deletion, or generation | High | Loopback default, trusted hosts, narrow CORS | High | Security and product owners | Never expose current API; add identity, authorization, service auth, rate limits, tenant ownership, security test |
| R-04 | Search or hosted mode sends data outside the approved boundary | Data leakage, residency/contract breach, loss of trust | High | Strict offline default, hosted/offline incompatibility, explicit search modes | Medium | Data, privacy, security, and procurement owners | Network deny test; approve endpoints/contracts/data fields; DLP and central egress before enabling |
| R-05 | Retrieved content injects instructions or misleading evidence | Manipulated output, data disclosure, unsafe recommendation | High | Untrusted-evidence prompt, JSON escaping, bounded fetch, source visibility | Medium-High | Security and model-risk owners | Adversarial retrieval suite, source policy, bind DNS validation to connection, isolation from tools/actions |
| R-06 | General system behavior is inappropriate for a regulated context | Harmful, biased, disallowed, or non-compliant advice | High | Prohibited-use documentation only | High | Business, compliance, and model-risk owners | Use-case policy layer, domain evaluation, output controls, human approval, independent validation |
| R-07 | Upstream model/runtime/package is malicious, compromised, or changed | Code execution, data leakage, unavailable or altered output | High | Model/runtime revision and SHA256 pins; installed manifest; dependency locks | Medium | Security, engineering, and license owners | Private registry, signatures/provenance, SBOM, malware/license checks, reproducible offline bundle, revocation |
| R-08 | Model or dependency license/data obligations are misunderstood | Distribution restriction, legal dispute, forced change | Medium | Apache-2.0 project license and third-party notices | Medium | Legal/license and product owners | Automated inventory; legal review by distribution profile; track upstream changes and notices |
| R-09 | A workstation pilot is treated as enterprise-ready | Outage, data mixing, lost ordering, unsupported users, uncontrolled cost | High | Explicit limitations and scale architecture | Medium-High | Executive sponsor and product owner | Enforce deployment profiles; shared use requires identity, shared data, orchestration, load/recovery evidence, SRE funding |
| R-10 | Users over-rely on AI or bypass required work | Automation bias, degraded professional judgment, incomplete review | High | Human-control documentation and excluded uses | Medium-High | Business, adoption, and model-risk owners | Workflow training, review rubric, sampled oversight, correction/rejection telemetry, stop rule |
| R-11 | Deletion appears complete but data remains in WAL, backups, logs, or caches | Privacy, records, legal-hold, or confidentiality failure | High | Conversation delete endpoint | High | Data, privacy, and operations owners | Map all copies; retention/hold/erasure design; verify deletion and backup propagation |
| R-12 | Failure of model, storage, policy, or network is handled inconsistently | Lost work, silent bypass, incorrect records, prolonged outage | Medium-High | Health state, local fallback for search, partial-response persistence | Medium | Product and operations owners | Approved failure policy, bounded retries, backup/restore, dependency-loss tests, RTO/RPO and incident exercise |
| R-13 | Model quality differs by language, group, topic, or prompt style | Unequal service, hidden error concentration, exclusion | High | Not currently evaluated | High | Model-risk, business, and inclusion owners | Population/task definition, subgroup/error analysis, accessibility and language tests, usage limits |
| R-14 | Telemetry/audit introduced for scale over-collects prompt content | A governance control creates a new sensitive-data store | High | No enterprise telemetry today | High | Privacy, security, and operations owners | Minimized event schema, content separation, access/retention controls, privacy review and sampling |
| R-15 | Regulation, guidance, provider terms, or model facts become stale | Incorrect assurance, prohibited processing, control gap | Medium-High | Dated source register and change triggers | Medium | Legal/compliance and product owners | Named review cadence, event-driven revalidation, versioned mapping, counsel/regulator consultation |
| R-16 | Benefits are estimated from anecdotes while lifecycle cost is ignored | Misallocated investment, zombie pilot, reputational loss | Medium | Five-dimension framework and pilot scorecard | Medium | Business and finance owners | Baseline before pilot, accepted-task economics, confidence adjustment, scale/stop decision |

## Risk acceptance rule

No table entry is accepted merely because a mitigation is documented. Risk acceptance requires:

- a defined deployment and context of use;
- evidence that the control operates;
- named authority with delegated approval;
- residual rating and rationale;
- conditions, exceptions, and compensating controls;
- review/expiry date and reversal trigger.

Critical or high residual risk involving unauthorized data access, consequential decisions, or untraceable material actions blocks scale unless the accountable organization formally determines otherwise within applicable law and policy.

## Review triggers

Review the register when the intended use, data, user population, model, prompt, provider, retrieval, persistence, deployment, scale, jurisdiction, law/guidance, owner, or material dependency changes, and after every significant incident or failed control test.
