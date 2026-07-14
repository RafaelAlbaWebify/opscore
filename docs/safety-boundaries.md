# OPSCORE safety boundaries

OPSCORE is read-only first.

## Allowed

- Process synthetic or sanitized incident evidence.
- Import bounded DNS Audit Tool CSV and WATCH JSON evidence.
- Normalize, correlate and report evidence locally.
- Identify contradictions, missing evidence and safe next checks.
- Collect DNS, HTTP and TLS evidence for one explicitly supplied HTTP or HTTPS URL.
- Apply a fixed timeout and record the operator-defined collection source location.
- Preserve failed bounded operations as partial evidence.

## Not allowed without explicit design and approval

- Modify DNS records, certificates, services or remote systems.
- Perform broad network or tenant scans.
- Crawl links, enumerate neighboring hosts or scan port ranges.
- Follow redirects automatically during live collection.
- Store credentials, tokens or private client data.
- Claim confirmed root cause from incomplete evidence.
- Automatically remediate production infrastructure.
- Bypass authentication, rate limits or access controls.

## Evidence rule

Observations are not automatically findings. Findings are not automatically root causes. A confirmed root cause must be explicitly supported by sufficient evidence and must expose contradictory or missing evidence.

## Public repository rule

Only neutral sample names, documentation IP ranges and sanitized evidence belong in this repository.
