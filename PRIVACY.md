# Privacy and data-flow notice

## Scope

This notice describes the public reference implementation as shipped. It is not a privacy notice for an organization's deployment and does not establish a lawful basis, consent, data-controller/processor role, retention schedule, or individual-rights process.

Do not enter personal, customer, patient, employee, trial, classified, privileged, proprietary, or other sensitive data unless the adopting organization has explicitly approved the complete processing context.

## Data processed

| Data | Purpose | Default location | Default retention |
|---|---|---|---|
| Conversation title, prompt, answer, timestamp, and source metadata | Provide chat history and context | SQLite under `%LOCALAPPDATA%\iBuddy\data` | Until the user deletes the conversation or local data is removed |
| Search query | Retrieve current public information when enabled | Sent to the selected search provider | Provider-dependent; review provider terms/configuration |
| Public result URL and page excerpt | Ground an answer and display sources | Memory during processing; selected source metadata/content can be stored with the answer | Follows conversation retention |
| Model/runtime paths and configuration | Operate the local service | Local `.env` | Until changed or removed |
| Search/provider credentials | Authenticate optional external services | Local `.env`; server-side only | Until rotated or removed |
| UI preferences | Theme, search preference, and active conversation identifier | Browser local storage | Until browser/site storage is cleared |
| Application/runtime logs | Troubleshooting | Terminal/process environment | Depends on how the adopter captures logs |

The application does not intentionally put full conversation text in browser local storage. The current project does not include an application analytics or advertising SDK. Operating systems, browsers, package managers, upstream runtimes, providers, proxies, endpoint tools, and deployment platforms can have their own logging or telemetry.

## Processing profiles

### Strict local - default

With `IBUDDY_MODEL_BACKEND=llama_cpp` and `IBUDDY_OFFLINE=true`:

- prompts, bounded context, and model output flow between local browser, FastAPI, SQLite, and llama.cpp;
- external search is disabled;
- hosted generation is rejected;
- the local Transformers adapter, if selected, is instructed to use only already available assets.

Initial setup is not air-gapped: package managers and the installer contact package sources, GitHub, and Hugging Face to obtain dependencies, runtime, and model assets.

### Local generation plus web search

With `IBUDDY_OFFLINE=false`, search can be automatic or explicitly requested:

- the user's query is sent to Tavily, Brave, or DuckDuckGo according to configuration;
- selected public URLs are resolved and fetched by the application;
- bounded result text is supplied to the generation backend;
- source information is stored with the conversation.

The per-message **No web search** option suppresses retrieval for that message. It does not change where generation runs.

### Hosted generation

With `IBUDDY_MODEL_BACKEND=hosted` and `IBUDDY_OFFLINE=false`, system instructions and selected conversation context are sent to the configured Hugging Face provider or base URL. Provider handling, location, retention, access, training/use, subprocessor, and deletion terms are outside this repository and require review.

## Local storage is not automatically private

SQLite conversation content is plaintext at the application layer. Locality can reduce external transfer, but anyone or any process with sufficient device/file access may read it. OS disk encryption, device identity, malware protection, backups, crash dumps, paging, support tools, and administrator access remain part of the privacy boundary.

## Deletion limitations

Deleting a conversation removes its application records, but the project does not claim forensic or cryptographic erasure. Copies can remain temporarily or permanently in:

- SQLite free pages, WAL/journal files, or filesystem remnants;
- OS, enterprise, or user backups and snapshots;
- logs, crash dumps, support bundles, screen captures, clipboard, or exports;
- search/model provider systems when external processing was enabled.

A production deployment needs an approved retention, legal-hold, backup, deletion-propagation, device-disposal, and erasure-verification process.

## Data minimization

The application limits user message length, history supplied to the model, search result count, fetched-page size, and excerpts. These technical bounds do not determine whether the content is necessary or permitted.

Before use:

- remove unnecessary identifiers and secrets;
- prefer public, synthetic, anonymized, or approved low-sensitivity data;
- do not assume pseudonymization eliminates re-identification risk;
- define purpose, authority, access, retention, downstream use, and affected people;
- treat prompts, outputs, embeddings/indexes, caches, logs, and evaluations as potentially sensitive derived data.

## Individual rights and requests

This public repository does not receive or control data from deployed copies. Individuals must contact the organization that operates the relevant deployment. That organization is responsible for identity verification, access, correction, deletion, objection, consent/authority, complaint, and regulatory processes applicable to its role and jurisdiction.

## Children and vulnerable people

The reference implementation is not designed or assessed for children or vulnerable populations. Do not use it to make or support decisions about them without a separately approved context, safeguards, and qualified oversight.

## Changes

Reassess privacy when the model, provider, prompt, retrieval, user population, intended use, data class, location, retention, identity, logging, telemetry, or deployment profile changes. Update this notice and the [AI system card](governance/AI_SYSTEM_CARD.md) before the changed processing begins.
