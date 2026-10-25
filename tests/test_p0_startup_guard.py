"""Offline Double Check for prewrite startup guard; no network or DB writes."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from p0_startup_guard import verify_prewrite_database

DSN = "postgresql://user:secret@staging.example.test:5432/neondb"
GOOD = ("neondb", True, True, True, True)


class Cursor:
    def __init__(self, row):
        self.row = row
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql):
        self.queries.append(sql)
        assert sql.strip().upper().startswith("SELECT ")

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, row):
        self.cursor_obj = Cursor(row)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return self.cursor_obj


class GuardTests(unittest.TestCase):
    def test_no_configuration_fails_closed_without_connect(self):
        called = []
        with self.assertRaisesRegex(RuntimeError, "P0 startup blocked"):
            verify_prewrite_database(DSN, "", "staging.example.test",
                                     connect=lambda *a, **k: called.append(1))
        self.assertEqual(called, [])

    def test_wrong_host_blocks_before_connect(self):
        called = []
        with self.assertRaisesRegex(RuntimeError, "P0 startup blocked"):
            verify_prewrite_database(DSN, "neondb", "production.example.test",
                                     connect=lambda *a, **k: called.append(1))
        self.assertEqual(called, [])

    def test_hostaddr_override_blocks(self):
        with self.assertRaisesRegex(RuntimeError, "P0 startup blocked"):
            verify_prewrite_database(DSN + "?hostaddr=127.0.0.1", "neondb",
                                     "staging.example.test", connect=lambda *a, **k: None)

    def test_wrong_database_name_blocks(self):
        with self.assertRaisesRegex(RuntimeError, "P0 startup blocked"):
            verify_prewrite_database(DSN, "wero1mercados", "staging.example.test",
                                     connect=lambda *a, **k: Connection(GOOD))

    def test_missing_table_blocks(self):
        with self.assertRaisesRegex(RuntimeError, "P0 startup blocked"):
            verify_prewrite_database(DSN, "neondb", "staging.example.test",
                                     connect=lambda *a, **k: Connection(("neondb", True, False, True, True)))

    def test_good_schema_only_select_read_only(self):
        calls = []
        conn = Connection(GOOD)
        def connect(*args, **kwargs):
            calls.append((args, kwargs))
            return conn
        verify_prewrite_database(DSN, "neondb", "staging.example.test", connect=connect)
        self.assertEqual(len(conn.cursor_obj.queries), 1)
        self.assertIn("default_transaction_read_only=on", calls[0][1]["options"])

    def test_startup_guard_precedes_all_writes(self):
        source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        startup = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "startup")
        calls = [n.value.func.id for n in startup.body
                 if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                 and isinstance(n.value.func, ast.Name)]
        self.assertEqual(calls[:4], [
            "check_startup_database", "init_db", "seed_amazon_campaigns",
            "seed_additional_amazon_campaigns",
        ])


if __name__ == "__main__":
    unittest.main()
