"""Dependency-free regression tests for the inline startup DDL/seed gate.

The tests compile only the small gate function from main.py; they never import
the application, invoke startup, or connect to a database.
"""
import ast
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.p0_database_identity import diagnose, startup_database_identity_matches


def staging_identity_env():
    env = {
        "DATABASE_URL": "postgresql://ci-staging-user:ci-placeholder@staging.example:5432/neondb",
        "DB_DIAGNOSTIC_KEY": "ci-diagnostic-key-that-is-long-enough-32",
        "WERO_DEPLOYMENT_ENV": "staging",
        "WERO_ALLOW_STARTUP_DB_MUTATIONS": "true",
    }
    env["WERO_STAGING_DATABASE_FINGERPRINT"] = diagnose(env)["fingerprint"]
    return env


class StartupBootstrapGateTests(unittest.TestCase):
    def load_gate(self, mode="homologation"):
        source = Path("main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "startup_bootstrap_enabled"
        )
        namespace = {
            "os": os,
            "WERO_MODE": mode,
            "startup_database_identity_matches": startup_database_identity_matches,
        }
        module = ast.Module(body=[function], type_ignores=[])
        exec(compile(module, "main.py", "exec"), namespace)
        return namespace["startup_bootstrap_enabled"]

    def test_requires_explicit_staging_opt_in_and_matching_database_identity(self):
        with patch.dict(os.environ, staging_identity_env(), clear=True):
            self.assertTrue(self.load_gate()())

    def test_rejects_missing_or_false_opt_in(self):
        env = staging_identity_env()
        for value in ("", "false", "0", "no"):
            with self.subTest(value=value):
                env["WERO_ALLOW_STARTUP_DB_MUTATIONS"] = value
                with patch.dict(os.environ, env, clear=True):
                    self.assertFalse(self.load_gate()())

    def test_rejects_non_staging_environment(self):
        env = staging_identity_env()
        env["WERO_DEPLOYMENT_ENV"] = "production"
        with patch.dict(os.environ, env, clear=True):
            self.assertFalse(self.load_gate()())

    def test_production_mode_overrides_staging_opt_in_and_identity(self):
        with patch.dict(os.environ, staging_identity_env(), clear=True):
            self.assertFalse(self.load_gate(mode="production")())

    def test_missing_fingerprint_rejects_bootstrap(self):
        env = staging_identity_env()
        env.pop("WERO_STAGING_DATABASE_FINGERPRINT")
        with patch.dict(os.environ, env, clear=True):
            self.assertFalse(self.load_gate()())

    def test_database_url_change_invalidates_fingerprint(self):
        env = staging_identity_env()
        env["DATABASE_URL"] = "postgresql://ci-staging-user:changed-placeholder@staging.example:5432/neondb"
        with patch.dict(os.environ, env, clear=True):
            self.assertFalse(self.load_gate()())

    def test_fingerprint_is_full_sha256_and_matches(self):
        env = staging_identity_env()
        fingerprint = env["WERO_STAGING_DATABASE_FINGERPRINT"]
        self.assertEqual(len(fingerprint), 64)
        self.assertTrue(startup_database_identity_matches(env))

    def test_rejects_truncated_fingerprint(self):
        env = staging_identity_env()
        env["WERO_STAGING_DATABASE_FINGERPRINT"] = env["WERO_STAGING_DATABASE_FINGERPRINT"][:16]
        self.assertFalse(startup_database_identity_matches(env))

    def test_bootstrap_gate_calls_database_identity_guard(self):
        source = Path("main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        gate = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "startup_bootstrap_enabled"
        )
        calls = [
            node for node in ast.walk(gate)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "startup_database_identity_matches"
        ]
        self.assertEqual(len(calls), 1)

    def test_all_startup_mutations_are_behind_the_fail_closed_gate(self):
        source = Path("main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        startup = next(
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "startup"
        )
        gate = next(
            node for node in startup.body
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.UnaryOp)
            and isinstance(node.test.op, ast.Not)
            and isinstance(node.test.operand, ast.Call)
            and isinstance(node.test.operand.func, ast.Name)
            and node.test.operand.func.id == "startup_bootstrap_enabled"
        )
        self.assertTrue(any(isinstance(statement, ast.Return) for statement in gate.body))
        mutators = {"init_db", "seed_amazon_campaigns", "seed_additional_amazon_campaigns"}
        calls = [
            node for node in ast.walk(startup)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in mutators
        ]
        self.assertEqual(mutators, {node.func.id for node in calls})
        self.assertTrue(all(node.lineno > gate.lineno for node in calls))
        calls_inside_gate = {
            node.func.id for statement in gate.body for node in ast.walk(statement)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue(mutators.isdisjoint(calls_inside_gate))


if __name__ == "__main__":
    unittest.main()
