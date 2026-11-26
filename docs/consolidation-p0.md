# Consolidation P0 — evidence precision

Baseline: 36f3ed43dc23b097763152e3572a34e55189be18.

This branch groups regression corrections before any migration of external collectors.

- DNS and HTTP transport failures: same target, source system, compatible known context and a provisional five-minute window. Missing context reduces confidence; it does not prove identical endpoints.
- HTTP 5xx: a server response, distinct from a transport failure.
- CPU snapshots: no sustained-load claim.
- Repeated finding codes: disambiguate by supporting evidence identifiers. Existing unique codes retain their IDs.

The five-minute window is a provisional engineering assumption, not a measured incident-specific threshold. Existing stored assessments referencing repeated codes may require human review after reanalysis.

Acceptance: full existing CI plus new regression tests. No merge or repository deletion until acceptance and review. No live networking changes, no new dependencies.

Next: assess WATCH collector safety without enabling redirects, log sanitization licensing, and offline Windows event/log adapters. Do not copy INFIOS code before license clarification.
