# OPSCORE safety boundaries

OPSCORE is read-only first.

## Allowed

- Process synthetic or sanitized incident evidence.
- Import bounded DNS Audit Tool CSV and WATCH JSON evidence.
- Normalize, correlate and report evidence locally.
- Identify contradictions, missing evidence and safe next checks.
- Collect DNS, HTTP and TLS evidence for one explicitly supplied HTTP or HTTPS URL.
- Perform one bounded read-only TCP connection attempt against one explicitly supplied hostname or IP address and one explicit port, without sending application data, reading a banner or enumerating other targets.
- Apply a fixed timeout and record the operator-defined collection source location.
- Preserve failed bounded operations as partial evidence.
- Record explicit operator hypotheses and root-cause assessments.
- Validate assessment references against the current persisted incident analysis.
- Append local immutable bundle, analysis and assessment revisions.
- List and retrieve historical revision metadata and validated JSON payloads without changing state.

## Not allowed without explicit design and approval

- Modify DNS records, certificates, services or remote systems.
- Perform broad network or tenant scans.
- Crawl links, enumerate neighboring hosts or scan port ranges.
- Follow redirects automatically during live collection.
- Store credentials, tokens or private client data.
- Generate hypotheses automatically.
- Infer or promote root-cause status automatically.
- Claim confirmed root cause from incomplete evidence.
- Automatically remediate production infrastructure.
- Bypass authentication, rate limits or access controls.
- Restore, roll back, rewrite or delete incident-history revisions.
- Connect to a production database or external history service.

## Evidence and assessment rule

Observations are not automatically findings. Findings are not automatically hypotheses or root causes. Hypotheses and root-cause assessments require explicit operator input.

A confirmed root-cause record requires an explicit statement, supporting evidence and no unresolved required-evidence entries. This validates the record structure; it does not independently prove that the operator conclusion is correct.

Historical revisions prove only what OPSCORE stored at a point in the local investigation workflow. They do not independently prove that source evidence was complete, correct or sufficient.

## Public repository rule

Only neutral sample names, documentation IP ranges and sanitized evidence belong in this repository.
