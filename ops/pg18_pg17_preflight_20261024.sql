-- PARADIGMA Wero1Mercados | P0 PostgreSQL migration preflight
-- Read-only: one SELECT. Compatible with PostgreSQL 17 and 18.
-- Run independently on Render production, Neon staging, and destination Neon.
-- Compare table_count, columns_fingerprint and audit/ledger presence.
-- The fingerprint covers column metadata only. It is NOT a row checksum,
-- backup verification, proof of DATABASE_URL, or migration authorization.
-- PostgreSQL 18 -> 17 downgrade via ordinary pg_dump/pg_restore is NOT
-- guaranteed; require an isolated restore and explicit compatibility tests.
WITH cols AS (
 SELECT table_name, column_name, ordinal_position, data_type, is_nullable,
        COALESCE(column_default, '') AS col_default
 FROM information_schema.columns
 WHERE table_schema = 'public'
), tabs AS (
 SELECT table_name
 FROM information_schema.tables
 WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
)
SELECT current_database() AS database_name,
       current_setting('server_version') AS server_version,
       clock_timestamp() AS checked_at,
       (SELECT count(*) FROM tabs) AS public_table_count,
       (SELECT md5(COALESCE(string_agg(
           table_name || ':' || column_name || ':' || data_type || ':' ||
           is_nullable || ':' || col_default,
           E'\n' ORDER BY table_name, ordinal_position
       ), '')) FROM cols) AS columns_fingerprint,
       to_regclass('public.affiliate_conversion_audit') IS NOT NULL AS has_conversion_audit,
       to_regclass('public.affiliate_conversion_ledger') IS NOT NULL AS has_conversion_ledger,
       to_regclass('public.conversions') IS NOT NULL AS has_conversions;
