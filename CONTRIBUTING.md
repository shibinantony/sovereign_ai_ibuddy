# Contributing

Thank you for improving Sovereign AI iBuddy. Contributions should preserve its honest boundary: a private-by-default workstation reference implementation with explicit gaps to regulated production.

## Before starting

- Use an issue for a material feature, architecture, model, provider, data-flow, or behavior change.
- Use [private vulnerability reporting](SECURITY.md) for security issues; do not open a public issue.
- Do not submit employer, client, customer, patient, employee, proprietary, classified, or otherwise restricted material.
- Confirm that you have the right to contribute all code, documentation, data, tests, and assets.

## Development setup

Prerequisites: Windows x64, PowerShell 5.1+, Python 3.11, Node.js 20+, and npm 10+.

```powershell
npm run setup:core
npm run dev
```

Core setup does not download the 6 GB model. Install the pinned local runtime/model only when needed:

```powershell
npm run model:install
```

## Quality checks

Run before opening a pull request:

```powershell
npm run lint
npm test
npm run build
git diff --check
```

Do not weaken or skip a check to make a change pass. Explain any platform limitation in the pull request.

## Pull request expectations

- Keep the change focused and explain the business/user problem.
- Add or update tests for behavior.
- Describe security, privacy, data, model, network, license, operations, and compatibility effects.
- Update README, configuration, system card, control matrix, risk register, notices, and changelog when affected.
- Label assumptions and proposals; do not introduce unsupported compliance, safety, sovereignty, performance, or ROI claims.
- Add dependencies only when their value justifies lifecycle, license, supply-chain, and operating cost.
- Never commit `.env`, credentials, databases, model weights, runtime binaries, logs, build output, or machine-specific data.

The merge and release rules are in [GOVERNANCE.md](GOVERNANCE.md).

## Code style

- Python targets 3.11 and uses Ruff.
- TypeScript uses the repository TypeScript project checks.
- Keep the API loopback-safe and preserve strict-offline semantics.
- Treat external content as untrusted.
- Prefer explicit, testable policy over ambiguous UI language.
- Avoid broad exception handling that hides security, persistence, or model failures.

## Documentation style

Lead with the problem and decision. Separate:

- implemented behavior;
- observed evidence;
- unvalidated hypothesis;
- planned capability;
- known limitation.

Include source version/date and a revalidation trigger for time-sensitive external claims. Prefer official primary sources.

## Commit sign-off

The project uses the [Developer Certificate of Origin 1.1](https://developercertificate.org/). Sign each commit:

```powershell
git commit -s
```

The commit must contain:

```text
Signed-off-by: Your Name <your-email@example.com>
```

## License

By contributing, you agree that your contribution is licensed under [Apache-2.0](LICENSE). Third-party material remains subject to its own terms and must be identified.
