# Security policy

## Supported versions

Security fixes are applied to the latest code on `main` and, when releases exist, the latest tagged release. Older commits, forks, local modifications, downloaded models, deployment environments, and third-party services are not maintained by this project.

This is a best-effort public reference project, not a production support or incident-response service.

## Report a vulnerability

Do not open a public issue for a suspected vulnerability, exposed secret, or exploit.

Use GitHub's private vulnerability reporting for this repository:

`https://github.com/shibinantony/sovereign_ai_ibuddy/security/advisories/new`

Include, when safe:

- affected commit/version and component;
- deployment assumptions and prerequisites;
- reproduction steps or a minimal proof of concept;
- potential confidentiality, integrity, availability, privacy, model, or safety impact;
- whether the issue is already public or actively exploited;
- suggested mitigation, if known.

Do not include real customer, patient, employee, credential, secret, or regulated data. Use synthetic evidence.

## Response process

The maintainer will aim to:

1. acknowledge a complete report within five business days;
2. validate scope and severity;
3. coordinate a fix, mitigation, advisory, or upstream report;
4. test affected boundaries and document upgrade/rollback guidance;
5. publish details after a fix or agreed disclosure point when doing so is safe.

These are targets, not contractual service levels. Complex upstream or supply-chain issues can take longer. The reporter will receive status updates when practical.

## Current trust boundary

The supported reference profile is:

- one user;
- one managed Windows x64 device;
- browser, API, SQLite, llama.cpp, and model on that device;
- FastAPI and llama.cpp bound to loopback;
- strict external-egress-off mode by default;
- no shared, remote, internet-facing, or multi-tenant service.

Loopback is a boundary, not authentication. A malicious or compromised local process can still attempt to reach the service or read unprotected files.

## Implemented security properties

- non-loopback llama.cpp binding is rejected;
- trusted-host and narrow CORS defaults reduce accidental exposure;
- strict offline mode disables search, rejects hosted generation, and prevents first-use Transformers downloads;
- secrets and runtime data are excluded from Git by default;
- model and llama.cpp release archives are pinned and SHA256-verified;
- installed runtime files are recorded and reverified through a local manifest;
- retrieved URLs reject credentials, unsupported schemes/ports, localhost, and non-public addresses;
- redirects are revalidated and page content is type/size bounded;
- retrieved evidence is encoded and separated from system instructions;
- input/context/output limits, conversation turn serialization, timeouts, cancellation, and partial-response persistence are present;
- CI, CodeQL, Dependabot, tests, and CODEOWNERS are configured.

These controls reduce specific risks. They do not make the application suitable for sensitive production data.

## Known security gaps

- no application authentication, authorization, tenant ownership, service identity, or rate limiting;
- plaintext SQLite prompts/outputs and no application-managed encryption or key lifecycle;
- no DLP, secret/PII/PHI detection, policy engine, immutable audit log, or human-approval enforcement;
- no TLS in the local reference process;
- no sandbox around the upstream model/runtime process;
- no enterprise secrets manager, SIEM, SLO, backup/restore, HA/DR, or incident automation;
- DNS validation is separate from the outbound HTTP connection, leaving a residual rebinding/time-of-check/time-of-use risk;
- no complete SBOM, signed release/provenance, reproducible air-gapped bundle, or dependency license/security gate;
- no independent penetration test or sector-specific red-team evidence.

See [CONTROL_MATRIX.md](governance/CONTROL_MATRIX.md) and [RISK_REGISTER.md](governance/RISK_REGISTER.md).

## Secure deployment rules

For the current code:

1. Keep FastAPI and llama.cpp on loopback.
2. Keep `IBUDDY_OFFLINE=true` unless every external data flow is approved.
3. Do not use hosted generation with data that is not approved for that endpoint.
4. Use a managed device with OS disk encryption, patched software, endpoint protection, least-privilege user access, and secure screen/session controls.
5. Do not enter live customer, patient, classified, export-controlled, production secret, or other prohibited data.
6. Do not expose port 8000 or 18080 to a LAN, VPN, container bridge, reverse proxy, or the internet.
7. Install from reviewed sources and verify model/runtime hashes.
8. Protect `.env`, `%LOCALAPPDATA%\iBuddy`, logs, terminal history, crash dumps, backups, and support bundles.
9. Review generated content before use; never connect the current system to an unattended action.
10. Delete pilot data and runtime assets according to the approved end-of-pilot procedure.

Shared or regulated deployment requires a new threat model and the controls identified in [Scalability and sovereignty](docs/SCALABILITY_AND_SOVEREIGNTY.md).

## Secret exposure

If a credential or sensitive artifact is committed:

1. revoke or rotate it immediately at the source;
2. assess access and downstream use;
3. remove it from the current tree and coordinate history remediation;
4. do not assume deletion from Git history makes the credential safe;
5. record and learn from the incident without publishing the secret.

## Dependency and model vulnerabilities

Report issues in this repository privately. When the root cause belongs upstream, the maintainer may coordinate with the upstream project and publish a local advisory or pin change. Users remain responsible for monitoring the selected model, runtime, packages, provider, operating system, and hardware/driver supply chain.

## Safe research

Good-faith testing should:

- stay within systems and data you own or are authorized to test;
- avoid privacy violation, persistence, lateral movement, denial of service, or real-user impact;
- use the minimum proof needed;
- stop and report when sensitive information is encountered;
- allow a reasonable remediation period before public disclosure.
