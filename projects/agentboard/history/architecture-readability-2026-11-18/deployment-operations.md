# Compose, migration, backup and recovery

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## 10. Deployment & Operations

Compose network: web ↔ backend ↔ db; maintenance/migrate reach db. Only web publishes loopback port. Use healthchecks and dependency conditions: db healthy → migrate success → backend/maintenance; web proxies only to ready backend and shows an explicit unavailable state otherwise. Docker documents that startup order alone does not establish readiness.

Pin image and dependency versions after testing; use a stable Compose project/volume name. Secrets come from local restricted configuration or mounted secret files, not source control or frontend build variables. Vite's production build runs in a Node image stage; production web serves static assets. Alembic migrations run once as a Compose job; no concurrent worker migrations. Startup cleans/filters expired events before serving. Maintenance uses a database lock to avoid duplicate cleanup if restarted twice.

Backup proposal: daily local `pg_dump` archive outside the data volume, rolling retention no longer than 30 days; matching roles/setup configuration stored separately without exposing secrets. A dump can provide a consistent single-database export, but backup validity requires restore tests. Restore into a fresh volume, apply startup expiry and revision limits, then test document reads and task counts before switching. Historical backups may contain subsequently pruned revisions until backup expiry; the live API always exposes only current+three previous versions. Clarify stricter physical erasure needs before implementation if that is unacceptable.

Rollback uses the matching pre-upgrade database backup; older images are not assumed compatible with newer schemas. Compose down preserves named volumes; removing the database volume destroys live data. Build-time internet access is distinct from runtime provider access. No containers have been started or client integrations configured in this task.
