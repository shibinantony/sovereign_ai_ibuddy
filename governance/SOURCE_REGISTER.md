# Public source register

## Source policy

Only public, primary sources are used for the external framework references in this repository. They are inputs to an adopter's analysis, not legal interpretation, certification, or proof that a control operates.

Regulation, guidance, standards, model facts, provider terms, and software releases change. Revalidate the current official text and applicability with accountable legal, regulatory, quality, security, privacy, model-risk, procurement, and engineering owners before a production decision.

## Cross-sector AI risk

| Source | Use in this repository | Checked | Revalidation trigger |
|---|---|---|---|
| [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) | Cross-sector reference for govern, map, measure, and manage practices; NIST states AI RMF 1.0 is under revision | 2026-08-14 | Revised AI RMF, playbook, or applicable profile |
| [NIST AI 600-1: Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) | GenAI-specific risk and action reference; not a certification scheme | 2026-08-14 | New revision, errata, or replacement profile |

## India and BFSI

| Source | Use in this repository | Checked | Revalidation trigger |
|---|---|---|---|
| [RBI FREE-AI Committee Report - Framework for Responsible and Ethical Enablement of Artificial Intelligence](https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=1306&UrlPage=) | Official report dated 13 August 2025; sector reference for responsible and ethical AI analysis in Indian financial services; applicability must be assessed by the regulated entity | 2026-08-14 | RBI report/guidance/circular update or supervisory interpretation |
| [MeitY - Digital Personal Data Protection Rules 2025](https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa) | Official source page for the Rules, corrigendum, and commencement material; no legal conclusion is made here | 2026-08-14 | Amendment, corrigendum, commencement change, Board/court interpretation, or new guidance |

## Pharma and medicines

| Source | Use in this repository | Checked | Revalidation trigger |
|---|---|---|---|
| [EMA - Use of AI in the medicinal product lifecycle](https://www.ema.europa.eu/en/use-artificial-intelligence-ai-medicinal-product-lifecycle-scientific-guideline) | Official lifecycle/context reference for risk, data, model, and change considerations; scope/applicability requires qualified assessment | 2026-08-14 | Revised scientific guideline, new final guidance, or material regulatory decision |
| [EMA - Artificial intelligence](https://www.ema.europa.eu/en/about-us/how-we-work/data-regulation-big-data-other-sources/artificial-intelligence) | Official index for current medicines-regulatory AI work, observatory material, and joint good-AI-practice principles | 2026-08-14 | Page or linked-principles update |
| [FDA - Guiding principles of good AI practice in drug development](https://www.fda.gov/about-fda/artificial-intelligence-drug-development/guiding-principles-good-ai-practice-drug-development) | Official U.S. reference for lifecycle good-practice analysis; not a product approval or validation checklist | 2026-08-14 | FDA/EMA revision, new guidance, or enforcement/approval precedent |

## Model, runtime, and licensing

| Source | Use in this repository | Checked | Revalidation trigger |
|---|---|---|---|
| [Qwen3-8B-GGUF](https://huggingface.co/Qwen/Qwen3-8B-GGUF) | Upstream model files, revision metadata, model information, and Apache-2.0 license reference | 2026-08-14 | Selected revision/model/file/license change |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Upstream runtime source, releases, and MIT license | 2026-08-14 | Runtime tag/asset/build/license change or security advisory |
| [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) | Project source-license text and interpretation starting point | 2026-08-14 | Project licensing strategy or Apache license guidance change |

## Claim boundaries

| Statement | Classification |
|---|---|
| Local generation can reduce prompt transfer to an external model provider | Architectural property when the verified local profile and network boundary operate as designed |
| `IBUDDY_OFFLINE=true` blocks application search/hosted generation paths | Tested application behavior; network enforcement still belongs in the deployment environment |
| This implementation is sovereign AI | Explicitly rejected as a blanket claim; sovereignty is multi-dimensional and deployment-specific |
| This implementation is compliant with BFSI, pharma, privacy, AI, or security requirements | Explicitly rejected; no such assessment or certification has been completed |
| The pilot will save money or improve productivity | Business hypothesis requiring baseline, observed results, cost allocation, and confidence |
| A visible citation makes an answer correct | Explicitly rejected; source, entailment, freshness, and context still require review |
| Open-source or locally stored means safe to use with sensitive data | Explicitly rejected; authority, security, privacy, model, operational, and sector controls remain necessary |

## Freshness procedure

For a material decision:

1. open the official source rather than relying on this summary;
2. record the version/publication date and access date;
3. identify jurisdiction, entity, system role, data, and context of use;
4. distinguish mandatory requirements, regulator guidance, voluntary frameworks, vendor claims, and architecture recommendations;
5. obtain qualified interpretation where required;
6. link each adopted control to implementation and operating evidence;
7. set the next review date and event-driven trigger.
