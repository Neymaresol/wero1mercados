-- PARADIGMA Wero1Mercados | PostgreSQL 18/17 shared-schema preflight
-- 2026-10-24 22:15 BRT | READ ONLY (single SELECT, no DDL/DML)
-- Run separately on Render production and Neon staging; compare per-table rows.
-- For the 11 shared tables, column_hash, index_hash, n_* and
-- constraint_type_hash should agree. Staging has two additional audit tables.
-- Constraint names are deliberately excluded from constraint_type_hash:
-- PostgreSQL 18 and 17 use different names for implicit NOT NULL checks.
-- A match DOES NOT prove FK targets/semantics, data equality, restored backup,
-- PostgreSQL downgrade compatibility, or app DATABASE_URL identity.
WITH col AS (
  SELECT table_name, count(*) AS n_columns,
         md5(string_agg(column_name || ':' || data_type || ':' || is_nullable || ':' ||
                        coalesce(column_default,''), '|' ORDER BY ordinal_position)) AS column_hash
  FROM information_schema.columns
  WHERE table_schema = 'public'
  GROUP BY table_name
), idx AS (
  SELECT tablename AS table_name, count(*) AS n_indexes,
         md5(string_agg(indexname || ':' || indexdef, '|' ORDER BY indexname)) AS index_hash
  FROM pg_indexes WHERE schemaname = 'public' GROUP BY tablename
), con AS (
  SELECT table_name, count(*) AS n_constraints,
         md5(string_agg(constraint_type, '|' ORDER BY constraint_type)) AS constraint_type_hash
  FROM information_schema.table_constraints
  WHERE table_schema = 'public' GROUP BY table_name
)
SELECT col.table_name, col.n_columns, col.column_hash, coalesce(idx.n_indexes,0) AS n_indexes,
       idx.index_hash, coalesce(con.n_constraints,0) AS n_constraints,
       con.constraint_type_hash
FROM col LEFT JOIN idx USING(table_name) LEFT JOIN con USING(table_name)
ORDER BY col.table_name;
