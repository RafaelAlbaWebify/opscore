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

## P0-B collector adaptation

Pin HTTP and TLS to the first resolved address, preserve Host and SNI, disable ambient proxies, keep redirects disabled and avoid reading bodies. Public-only is opt-in; internal explicitly authorized targets remain supported. Query URLs are rejected to reduce accidental secret persistence. Error classes replace raw exception strings. DNS resolution still uses the OS resolver and is not governed by the socket timeout; this is not a hard total deadline. The first address may not represent all instances. Public-only is not a substitute for authorization or network isolation. Adapted from WATCH (MIT, Rafael Alba, source commit 1ba2e2ebe4dc0f82298e475c8c412d97f0660e01); OPSCORE retains its MIT notice.

## P0-C operational imports

POST /api/incidents/{incident_id}/operational-import accepts kind (application-log, windows-event, iis), target_reference, timezone-aware collected_at and content (JSON string). Application records accept status_code, raw or message; Windows records accept event_id, provider and log_name; IIS accepts services (name/status), sites and application_pools (state). Only signal counts, up to ten record positions per signal, total count and source SHA256 persist. No raw messages, host/user names or filenames are retained by this adapter. This is structured JSON only, not a native EVTX or arbitrary plaintext parser. Invalid input is rejected; no signal is not evidence of health. The 2 MiB/10000-record limits apply after request decoding. Operators must retain originals separately and use sanitized service metadata. Rule subset adapted from CustosOps, MIT, commit a76c540de8e0dbac845d8b4b32dfb1a6824e82c2. Full original license notice retained in docs/licenses/CustosOps.txt. No INFIOS source copied.
