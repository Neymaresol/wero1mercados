"""Regression tests for the inline startup DDL/seed fail-closed gate.

These tests import the application module but never invoke its startup handler
or connect to a database. They verify only environment gating and AST placement.
"""
import ast
import os
import unittest
from pathlib import Path
from unittest.mock import patch

class StartupBootstrapGateTests(unittest.TestCase):
    def load_gate(self, mode="homologation"):
        source = Path("main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "startup_bootstrap_enabled"
        )
        namespace = {"os": os, "WERO_MODE": mode}
        module = ast.Module(body=[function], type_ignores=[])
        exec(compile(module, "main.py", "exec"), namespace)
        return namespace["startup_bootstrap_enabled"]
    def test_requires_explicit_staging_and_opt_in(self):
        with patch.dict(os.environ, {
            "WERO_DEPLOYMENT_ENV": "staging",
            "WERO_ALLOW_STARTUP_DB_MUTATIONS": "true",
        }, clear=False):
            self.assertTrue(self.load_gate()())

    def test_rejects_missing_or_false_opt_in(self):
        for value in ("", "false", "0", "no"):
            with self.subTest(value=value):
                with patch.dict(os.environ, {
                    "WERO_DEPLOYMENT_ENV": "staging",
                    "WERO_ALLOW_STARTUP_DB_MUTATIONS": value,
                }, clear=False):
                    self.assertFalse(self.load_gate()())

    def test_rejects_non_staging_environment(self):
        with patch.dict(os.environ, {
            "WERO_DEPLOYMENT_ENV": "production",
            "WERO_ALLOW_STARTUP_DB_MUTATIONS": "true",
        }, clear=False):
            self.assertFalse(self.load_gate()())

    def test_production_mode_overrides_staging_opt_in(self):
        with patch.dict(os.environ, {
            "WERO_DEPLOYMENT_ENV": "staging",
            "WERO_ALLOW_STARTUP_DB_MUTATIONS": "true",
        }, clear=False):
            self.assertFalse(self.load_gate(mode="production")())

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
