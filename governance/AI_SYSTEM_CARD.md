# AI system card

## Document control

| Field | Value |
|---|---|
| System | Sovereign AI iBuddy |
| Repository | `shibinantony/sovereign_ai_ibuddy` |
| Card version | 1.0 |
| Checked | 2026-08-14 |
| Status | Public reference implementation; controlled-pilot candidate |
| Owner | Shibin Antony |
| Review trigger | Model, prompt, data flow, provider, intended use, material dependency, or deployment-profile change |

## Purpose

The system provides a private-by-default conversational workspace for reviewable knowledge tasks. It demonstrates local language-model inference, device-local history, optional web retrieval, and explicit network choices on a Windows workstation.

It is not a regulated decision system, autonomous agent, clinical tool, financial decision engine, shared enterprise service, or compliance product.

## Components

| Component | Current selection | Role |
|---|---|---|
| User experience | React/Vite | Conversation, history, search choice, source display |
| Application service | FastAPI | API, SSE streaming, orchestration, health, and persistence access |
| Default model | `Qwen/Qwen3-8B-GGUF` / `Qwen3-8B-Q5_K_M.gguf` | Local text generation |
| Model revision | `4f02e7c52b572082828edf5058a87e2e7dc3e4d5` | Installer pin |
| Model SHA256 | `068bae163faa96ad48032daf4e071a6a28fe67d8dcc95367609c2ff165e52738` | Download verification |
| Runtime | `ggml-org/llama.cpp` Windows CPU x64, tag `b10408` | Loopback model server |
| Runtime archive SHA256 | `63790dfd3c754ef8838606926f1952d9a4f5d74b5e6d5925da1868f56d5d9049` | Release archive verification |
| History | SQLite with WAL | Device-local conversations and source metadata |
| Optional retrieval | Tavily, Brave, or DuckDuckGo plus public page fetch | Current public evidence |
| Optional hosted generation | Hugging Face client or configured endpoint | Non-local alternative, disabled in strict offline mode |

The repository does not redistribute model weights or llama.cpp binaries. Upstream terms are recorded in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Intended use

Appropriate current uses are:

- drafting, summarization, explanation, ideation, and research support;
- public, synthetic, or explicitly approved low-sensitivity information;
- one local user on a managed device;
- tasks where a qualified human can detect, correct, and reverse an error;
- pilots with measured outcome, quality, adoption, risk, cost, and exit criteria.

## Excluded use

Do not use the current implementation for:

- diagnosis, treatment, dosing, patient, safety, or clinical decisions;
- credit, insurance, fraud, AML/KYC, trading, investment, employment, legal-rights, or eligibility decisions;
- batch release, GxP records, regulatory submissions, or validated calculations;
- autonomous actions, external communications, or system-of-record updates;
- shared or remote access;
- unrestricted personal, customer, patient, trial, classified, export-controlled, or other prohibited data;
- any task where a plausible model error can directly create material harm.

## Users and affected people

The intended direct user is a knowledge worker participating in an approved pilot. People described in inputs or affected by downstream decisions are not system users and require separate protection. The current system has no mechanism to determine consent, authority, vulnerability, protected status, or downstream impact.

## Data flow

### Strict local profile

1. The browser sends a prompt to FastAPI on the same device.
2. The application stores messages in local SQLite.
3. FastAPI sends bounded conversation context to llama.cpp on loopback.
4. Generated text streams to the browser and is stored locally.
5. External search and hosted generation are blocked by configuration.

Initial installation still contacts package, GitHub, and Hugging Face sources to download dependencies and verified assets.

### Search-enabled profile

The search query is sent to the selected provider. The application resolves and fetches selected public pages, supplies bounded excerpts to the configured generation backend, and stores source metadata with the answer.

### Hosted profile

The selected conversation context and system instructions are sent to the configured Hugging Face provider or endpoint. `IBUDDY_OFFLINE=true` rejects this backend. Data handling then depends on endpoint location, contract, configuration, logs, and provider terms.

## Model and data limitations

- Qwen3-8B is a general-purpose upstream model; this project did not train or fine-tune it.
- The project has not independently characterized the upstream training corpus, memorization, language/population coverage, or all license/data risks.
- Q5_K_M quantization can alter quality compared with other model variants.
- The system can produce false, outdated, incomplete, biased, unsafe, or fabricated content.
- Search grounding can retrieve low-quality, hostile, stale, or misleading pages. Source display is not proof of correctness.
- Conversation context is truncated to a configured budget and does not provide durable semantic memory.
- The base prompt is general-purpose and is not a sector policy engine.
- No benchmark establishes fitness for BFSI, pharma, clinical, legal, or other regulated use.

## Current evaluation evidence

Automated tests cover API behavior, persistence, streaming and cancellation, model lifecycle, context trimming, search decision and ranking, public-URL filtering, installer configuration preservation, and strict-offline hosted-backend rejection.

Not yet assessed:

- domain task accuracy or hallucination rate;
- bias or performance across demographic, language, accessibility, or specialist groups;
- prompt injection across a representative adversarial corpus;
- privacy leakage, memorization, membership/model inversion, or sensitive-entity extraction;
- harmful-content, over-reliance, automation-bias, or sector-specific misuse;
- representative concurrency, endurance, recovery, RPO/RTO, or unit economics;
- independent security, privacy, model-risk, GxP, or regulatory validation.

## Human oversight

Outputs are drafts or research aids. The adopting organization must name a qualified reviewer with:

- authority and competence for the workflow;
- access to authoritative sources and sufficient review time;
- a clear reject, correct, escalate, and stop path;
- accountability for the final decision or action;
- training against automation bias and fabricated citations.

A user confirmation without these conditions is not an adequate control.

## Monitoring and incidents

The current application exposes health state and ordinary application logs. It does not provide enterprise metrics, immutable decision evidence, security analytics, model-drift monitoring, or an incident workflow.

For a controlled pilot, record at minimum:

- model/runtime and application version;
- selected network and data profile;
- task and evaluation outcome without over-collecting sensitive content;
- user correction/rejection and material quality failure;
- policy, security, privacy, availability, and data events;
- owner, remediation, retest, and closure decision.

## Change control

Re-evaluate this card and the pilot approval when any of the following changes:

- intended use, population, workflow, jurisdiction, or data class;
- model, quantization, runtime, system prompt, context size, or sampling;
- retrieval source, search provider, hosted endpoint, or network policy;
- persistence, retention, identity, authorization, interface, or human-control design;
- infrastructure, scale, dependency, license, or operating owner.

## Approval statement

Publication of this card is transparency, not production approval. Fitness and residual risk can be accepted only by the accountable adopting organization for a defined context of use.
