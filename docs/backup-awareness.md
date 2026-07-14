# Backup-awareness evidence

OPSCORE records operator-supplied backup context for one existing incident service. It does not run, schedule, modify or verify backup jobs.

## Supported context

- protection status: `protected`, `degraded`, `unprotected` or `unknown`;
- last successful backup timestamp;
- last restore-test timestamp;
- optional RPO and RTO values in minutes;
- public-safe retention summary and notes;
- source system and source-location provenance.

## API

`POST /api/incidents/{incident_id}/backup-awareness`

The target reference must already exist in the incident service inventory. A `protected` record must include a timezone-aware `last_successful_backup_at` value.

## Safety boundary

The endpoint does not:

- start or stop backup jobs;
- change schedules, retention, storage policies or media state;
- perform restores;
- validate credentials or connect to backup platforms;
- claim recoverability from status metadata alone;
- promote backup context to root cause automatically.

The resulting evidence explicitly records that backup and restore operations were not independently verified.
