# Repository governance

## Purpose

This file defines how Sovereign AI iBuddy is maintained as a public reference implementation. It does not govern an adopter's production deployment. An organization using the code must establish its own accountable product, data, security, privacy, model-risk, legal, regulatory, operational, and business ownership.

## Model

The project uses an owner-led maintainer model.

- **Lead maintainer:** Shibin Antony (`@shibinantony`)
- **Contributors:** anyone submitting an issue, discussion, or pull request under the project policies
- **Reviewers:** people explicitly requested by the maintainer for technical, security, privacy, model, documentation, or licensing expertise

The lead maintainer has final repository decision authority, including scope, roadmap, release, security response, and acceptance of contributions. That authority does not replace specialist approval for a real regulated deployment.

## Principles

1. Lead with a business problem and a measurable outcome.
2. Separate current evidence, assumptions, proposals, and limitations.
3. Preserve private-by-default behavior and explicit external-egress controls.
4. Do not describe the project as compliant, certified, production-ready, safe, or sovereign without scoped evidence and accountable approval.
5. Prefer the smallest architecture that can prove value safely.
6. Treat model, dependency, policy, data, and prompt changes as system changes.
7. Make a stop or retirement decision when value or control evidence is insufficient.

## Decision rights

| Decision | Accountable repository role | Required consultation |
|---|---|---|
| Product scope and roadmap | Lead maintainer | Relevant business and technical reviewers |
| Merge to `main` | Lead maintainer or delegated maintainer | CODEOWNERS and CI |
| Security-sensitive change | Lead maintainer | Security reviewer; private handling when needed |
| Privacy or data-flow change | Lead maintainer | Privacy/data reviewer |
| Model, runtime, or provider change | Lead maintainer | Model, security, license, and operations reviewers |
| License or third-party term change | Lead maintainer | Legal/license review |
| Public release | Lead maintainer | Quality, security, documentation, and third-party checks |
| Deprecation or archive | Lead maintainer | Users and active contributors where practical |

## Change classes

| Class | Examples | Minimum evidence |
|---|---|---|
| Routine | Documentation correction, non-behavioral refactor, test improvement | Pull request, passing quality checks, accurate documentation |
| Material | Network behavior, data persistence, model/prompt, provider, security boundary, dependency, API contract | Threat/data-flow review, tests, system-card/control updates, rollback plan |
| Release-critical | License, vulnerability fix, data migration, runtime/model upgrade, breaking change | Maintainer approval, security/license review as applicable, release notes, verification and rollback evidence |

## Pull request gates

A change is eligible to merge only when:

- the problem and intended outcome are clear;
- the diff is scoped and reviewable;
- tests cover material behavior;
- `quality` and applicable security checks pass;
- data flows, configuration, system card, control matrix, notices, and user guidance are updated when affected;
- new dependencies or external endpoints have a purpose, owner, license, and security/privacy review;
- no secret, model weight, database, private dataset, customer material, or machine-specific path is committed;
- limitations and unvalidated claims remain visible;
- the contributor certifies the contribution under the Developer Certificate of Origin.

## Developer Certificate of Origin

Contributions use the [Developer Certificate of Origin 1.1](https://developercertificate.org/), not a contributor license agreement. Add this line to each commit:

```text
Signed-off-by: Your Name <your-email@example.com>
```

Use `git commit -s` to add it. The sign-off certifies that the contributor has the right to submit the work under the project's Apache-2.0 license.

## Release gate

Before a tagged release, the maintainer should confirm:

1. CI, CodeQL, dependency, secret, and license checks are reviewed.
2. Model/runtime pins and hashes are verified from official upstream sources.
3. `CHANGELOG.md`, the AI system card, third-party notices, configuration, and known limitations are current.
4. Upgrade, rollback, data compatibility, and support implications are documented.
5. No open critical vulnerability or unresolved release-blocking risk remains.
6. The tag and release artifacts are attributable to the reviewed commit.

Future production-grade distribution should add signed artifacts, an SBOM, build provenance, and a documented revocation path.

## Branch controls

The public repository should protect `main` against force pushes and deletion and require the `quality` status check before merge. Required human approvals should match the available maintainer team; a solo public project should not configure an approval rule that makes legitimate maintenance impossible.

## Security handling

Potential vulnerabilities must follow [SECURITY.md](SECURITY.md), not a public issue. The maintainer may temporarily withhold details, request a coordinated fix, revoke an artifact, or pause a release when disclosure could increase harm.

## Records

Material decisions should be recorded in the pull request, an issue, release notes, or a future architecture decision record. The record should include:

- decision and accountable owner;
- evidence and assumptions;
- alternatives considered;
- security, privacy, model, license, operational, and economic implications;
- rollback or reversal trigger;
- review or expiry date when the decision can become stale.

## Succession and continuity

The lead maintainer may delegate or transfer maintenance when a contributor demonstrates sustained stewardship. If the project becomes unmaintained, the repository should be clearly marked, security support should not be implied, and users should be directed to fork under Apache-2.0 or migrate. No contributor is entitled to use the maintainer's name or project branding to imply endorsement.

## Production adoption boundary

Repository governance cannot accept risk for an adopting organization. A production adopter must create its own:

- system and model inventory;
- intended-use and prohibited-use approval;
- data protection and records schedule;
- sector and jurisdiction control mapping;
- validation and independent assurance;
- service ownership, SLO, incident, continuity, and retirement process;
- benefit-realization and total-cost review.
