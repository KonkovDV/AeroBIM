-- RT16-DDL-01 / HD5-PGSQL-02
-- Deploy-time DDL for a DML-only runtime role.
-- Pilot default still applies the same ALTER at boot when AEROBIM_POSTGRES_APPLY_DDL
-- is unset or true. Set AEROBIM_POSTGRES_APPLY_DDL=0 only after this file has run.
-- Missing reports.tenant_id must fail closed — never skip the column.

ALTER TABLE reports ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128);
