# Sovereign AI iBuddy development guide

This document describes the engineering state of the public reference implementation. Start with the [executive README](README.md) for the business decision and [AI system card](governance/AI_SYSTEM_CARD.md) for intended use and limitations.

## Product boundary

Sovereign AI iBuddy is a Windows-focused, single-user conversational and research workspace:

- local Qwen3-8B generation through a pinned llama.cpp runtime;
- local SQLite conversation history;
- strict offline operation by default;
- optional web retrieval with visible source cards;
- per-message automatic, forced-web, and no-web-search modes;
- an optional hosted Hugging Face adapter when strict offline mode is disabled;
- a React interface backed by a FastAPI streaming API.

It does not authenticate users, isolate tenants, encrypt the SQLite content, ingest an enterprise corpus, execute tools, modify arbitrary files, perform browser actions, enforce sector policy, or make regulated decisions.

## Architecture

```text
React UI  -- REST/SSE -->  FastAPI  -->  SQLite history
                              |
                              +--> local llama-server --> Qwen3-8B GGUF
                              |
                              +--> optional approved web retrieval --> cited evidence
                              |
                              +--> optional hosted generation (offline mode must be false)
```

FastAPI and llama.cpp are bound to loopback in the supported profile. Generation is serialized per conversation and llama.cpp runs with one parallel slot.

## Repository layout

```text
backend/        FastAPI application, model/search services, and tests
frontend/       React/Vite interface
scripts/        Windows setup, model installation, and installer-policy tests
docs/           Executive, industry, scale, and sovereignty decisions
governance/     System card, controls, risks, sources, and pilot scorecard
.github/        CI, CodeQL, dependency updates, ownership, and templates
.env.example    Non-secret configuration template
README.md       Executive proposition and operating guide
```

Model weights, llama.cpp binaries, SQLite data, `.env`, virtual environments, dependency folders, and build output are excluded from version control.

## Prerequisites

- Windows x64
- PowerShell 5.1+
- Python 3.11
- Node.js 20+
- npm 10+
- 16 GB RAM minimum practical local profile
- approximately 12 GB free during full installation

## Setup

Install application dependencies and build the UI without downloading a model:

```powershell
npm run setup:core
```

Install or verify the pinned llama.cpp runtime and Qwen GGUF:

```powershell
npm run model:install
```

Or run both:

```powershell
npm run setup
```

The installer writes the model, runtime, and database paths under `%LOCALAPPDATA%\iBuddy`. When repairing an existing `.env`, it changes only:

- `LLAMA_CPP_SERVER_PATH`
- `LLAMA_CPP_MODEL_PATH`
- `IBUDDY_DATABASE_PATH`

It preserves the user's backend, offline, search, credential, tuning, and policy values.

## Run

Development:

```powershell
npm run dev
```

Open `http://localhost:5173`.

Production-style local process:

```powershell
npm run build
$env:IBUDDY_ENV = "production"
npm start
```

Open `http://localhost:8000`. Keep one API worker. Do not expose the current unauthenticated service beyond the device.

## Configuration

### Generation and network policy

| Variable | Default | Purpose |
|---|---:|---|
| `IBUDDY_MODEL_BACKEND` | `llama_cpp` | `llama_cpp`, optional `local` Transformers adapter, or optional `hosted` |
| `IBUDDY_OFFLINE` | `true` | Blocks external search, rejects hosted generation, and forces the Transformers adapter to use local assets only |
| `HF_TOKEN` | empty | Optional hosted provider credential |
| `HF_MODEL` | `Qwen/Qwen2.5-7B-Instruct-1M` | Optional Transformers/hosted model ID |
| `HF_PROVIDER` | `auto` | Hugging Face hosted provider selection |
| `HF_BASE_URL` | unset | Optional hosted-compatible endpoint |
| `MAX_NEW_TOKENS` | `1200` | Maximum response tokens |
| `MODEL_TEMPERATURE` | `0.25` | Sampling temperature |
| `MODEL_TIMEOUT_SECONDS` | `120` | Model request/generation timeout |

`IBUDDY_MODEL_BACKEND=hosted` and `IBUDDY_OFFLINE=true` are intentionally incompatible. Disable strict offline mode only after the endpoint and data flow are approved.

### llama.cpp

| Variable | Default | Purpose |
|---|---:|---|
| `LLAMA_CPP_SERVER_PATH` | device-local installed path | Verified `llama-server.exe` |
| `LLAMA_CPP_MODEL_PATH` | device-local installed path | Verified Qwen3 GGUF |
| `LLAMA_CPP_HOST` | `127.0.0.1` | Must be explicit loopback |
| `LLAMA_CPP_PORT` | `18080` | Private inference port |
| `LLAMA_CPP_CONTEXT_SIZE` | `8192` | Model context supplied to llama.cpp |
| `LLAMA_CPP_THREADS` | `8` | CPU inference threads |
| `LLAMA_CPP_GPU_LAYERS` | `0` | CPU-only default; advanced users can test offload |
| `LLAMA_CPP_STARTUP_TIMEOUT_SECONDS` | `180` | Runtime readiness deadline |
| `LLAMA_CPP_ENABLE_THINKING` | `false` | Request direct answers without visible Qwen thinking traces |

### Search

| Variable | Default | Purpose |
|---|---:|---|
| `SEARCH_PROVIDER` | `auto` | Tavily, Brave, DuckDuckGo, or automatic selection |
| `SEARCH_SAFESEARCH` | `moderate` | `off`, `moderate`, or `strict` for providers that support it |
| `TAVILY_API_KEY` | empty | Optional Tavily credential |
| `BRAVE_SEARCH_API_KEY` | empty | Optional Brave credential |
| `SEARCH_RESULT_COUNT` | `4` | Ranked sources supplied to generation |
| `SEARCH_TIMEOUT_SECONDS` | `6` | Search/fetch deadline |

`auto` prefers Tavily when its key exists, then Brave, then keyless DuckDuckGo. Search is inactive while strict offline mode is enabled.

### Service and persistence

| Variable | Default | Purpose |
|---|---:|---|
| `IBUDDY_ENV` | `development` | Disables interactive API docs when `production` |
| `IBUDDY_DATABASE_PATH` | device-local path | SQLite conversation database |
| `IBUDDY_FRONTEND_DIST` | `frontend/dist` | Built client path |
| `HISTORY_MESSAGE_LIMIT` | `24` | Recent stored messages considered for generation |
| `MAX_USER_CHARS` | `12000` | Maximum submitted message length |
| `CORS_ORIGINS` | `http://localhost:5173` | Development browser origin |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost,testserver` | Trusted HTTP host names |
| `IBUDDY_DEBUG` | `false` | Application debug flag |

All values are in [`.env.example`](.env.example). `.env` is ignored by Git.

## Search behavior

| Composer mode | Behavior |
|---|---|
| Smart search | Retrieves when a freshness/factual cue is detected, if search is available |
| Search web | Requests retrieval before generation, if search is available |
| No web search | Suppresses retrieval for that message; generation still follows the configured backend |

Retrieved text is untrusted input. URLs are normalized, resolved to public addresses, restricted to HTTP(S) ports 80/443, redirect-checked, and content/size bounded. A residual DNS rebinding/time-of-check/time-of-use risk remains because validation and the actual connection are separate. Enterprise deployment needs network-layer egress enforcement.

## Verification

```powershell
npm run lint
npm test
npm run build
git diff --check
```

The automated suite covers:

- API validation, persistence, streaming, cancellation, and partial response recovery;
- model lifecycle, process startup/termination, context trimming, and operational state;
- strict-offline hosted-backend rejection;
- search decisions, normalization, ranking, public-address filtering, and bounded extraction;
- installer-owned path updates and preservation of policy/tuning/credential values;
- TypeScript and Python compilation.

To inspect a running model:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/api/health).model
```

A loaded local model reports `ready=True`, `operational=True`, and `state=operational`.

## Supply-chain verification

The model installer:

1. pins a Qwen repository revision, filename, and expected SHA256;
2. pins a llama.cpp release tag, asset URL, and expected archive SHA256;
3. compares GitHub's published asset digest;
4. hashes the downloaded archive;
5. records every installed runtime file in a manifest;
6. rehashes the executable and manifest files before reuse.

This is stronger than an unverified download but is not signed build provenance, a complete SBOM, or a reproducible air-gapped supply chain. See [Control matrix](governance/CONTROL_MATRIX.md).

## Privacy and security boundaries

- Strict offline is an application control; a sensitive deployment should also enforce egress at the OS/network layer.
- SQLite content is plaintext at the application layer.
- Loopback prevents normal remote listening but does not authenticate local processes.
- Search queries and hosted contexts cross the local boundary when those profiles are enabled.
- No user/topic policy engine, DLP, PII/PHI detection, immutable audit, retention schedule, or secure deletion is implemented.
- The current system must not be connected to autonomous actions or regulated decisions.

Read [SECURITY.md](SECURITY.md), [PRIVACY.md](PRIVACY.md), and the [risk register](governance/RISK_REGISTER.md) before changing a trust boundary.

## Known engineering limitations

- Windows AMD64 installer only
- one API worker and one generation slot
- single-device SQLite persistence
- no browser end-to-end test suite
- no representative domain/model evaluation suite
- no load, endurance, HA, DR, backup/restore, or RPO/RTO evidence
- no long-term semantic memory or enterprise RAG
- CPU latency varies with hardware, context, and output length

## Change checklist

When changing a model, prompt, provider, external endpoint, data store, API exposure, identity model, or intended use:

1. update tests and configuration;
2. update the system card, control matrix, risk register, privacy notice, and third-party notices;
3. document new data flows, failure behavior, migration, rollback, and operating cost;
4. re-run the relevant security/model evaluation;
5. obtain the decision rights required by [GOVERNANCE.md](GOVERNANCE.md).
