# CI baseline verification

This documentation-only change exists to exercise the permanent OPSCORE pull-request verification workflow after the initial repository publication.

The pull request is expected to prove:

- Linux linting, strict typing, tests, coverage and deterministic evidence generation;
- Windows linting, strict typing, tests and PowerShell operator workflows;
- proof-artifact creation and upload;
- no production, credential or external-system writes.

The file can remain as a record of the first cross-platform CI baseline once the workflow succeeds.
