# OPSCORE

> Infrastructure and production operations incident evidence workbench.

OPSCORE is a local-first, read-only workbench for correlating infrastructure and production-service evidence around an incident. It imports public-safe DNS Audit Tool CSV evidence and WATCH JSON run evidence, normalizes source provenance, applies deterministic correlation rules, and generates support-ready Markdown and JSON reports.

## Portfolio purpose

OPSCORE is Rafael Alba's flagship project for the **Infrastructure / Production Operations Engineer** path.

It is deliberately separated from:

- **WATCH**, which controls recurring operational checks, changes and actions.
- **TRACE**, which structures IAM and access evidence.
- **CustosOps**, which structures defensive security evidence.
- **DNS Audit Tool**, which remains a specialist OPSCORE evidence provider.

## Current verified capability

```text
incident and service context
+ DNS Audit Tool CSV
+ WATCH JSON run
→ source validation
→ normalized evidence with provenance
→ cross-source correlation
→ timeline and findings
→ missing-evidence identification
→ Markdown and JSON incident reports
```

Current deterministic findings include:

- successful DNS resolution with failed HTTP reachability;
- contradictory availability evidence;
- forward/reverse DNS consistency requiring review;
- TLS certificate expiry risk;
- missing evidence for required dependencies.

OPSCORE does not claim root cause unless the available evidence explicitly supports that conclusion.

## Quick start

```powershell
.\OPSCORE.ps1 setup
.\OPSCORE.ps1 verify
.\OPSCORE.ps1 demo
.\OPSCORE.ps1 correlate
.\OPSCORE.ps1 export
```

Direct Python commands:

```powershell
python -m opscore.cli demo --workspace .opscore-data
python -m opscore.cli correlate --workspace .opscore-data\imported
```

## Automated proof

The repository is configured to run on Linux and Windows:

- Ruff linting;
- strict mypy checks;
- pytest with an enforced 85% coverage minimum;
- deterministic demo generation;
- DNS CSV and WATCH JSON import correlation;
- PowerShell operator verification;
- review artifact generation.

## Safety boundary

OPSCORE is read-only first. It does not modify DNS, certificates, services, remote systems or production infrastructure. Public repository data must remain synthetic or sanitized.

See `docs/safety-boundaries.md` for the full boundary.
