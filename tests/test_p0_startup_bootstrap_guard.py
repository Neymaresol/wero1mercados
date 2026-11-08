"""Offline tests: startup DDL and seeders require explicit staging opt-in."""
import ast
import unittest
from pathlib import Path

from p0_startup_guard import startup_bootstrap_enabled


class StartupBootstrapGuardTests(unittest.TestCase):
    def test_disabled_without_explicit_environment_or_opt_in(self):
        self.assertFalse(startup_bootstrap_enabled(
            deployment_env="", allow_mutations="", mode="homologation"
        ))
        self.assertFalse(startup_bootstrap_enabled(
            deployment_env="staging", allow_mutations="false", mode="homologation"
        ))
        self.assertFalse(startup_bootstrap_enabled(
            deployment_env="production", allow_mutations="true", mode="homologation"
        ))

    def test_enabled_only_for_explicit_staging_opt_in(self):
        self.assertTrue(startup_bootstrap_enabled(
            deployment_env="staging", allow_mutations="true", mode="homologation"
        ))
        self.assertTrue(startup_bootstrap_enabled(
            deployment_env="STAGING", allow_mutations="YES", mode="staging"
        ))

    def test_production_mode_overrides_staging_opt_in(self):
        self.assertFalse(startup_bootstrap_enabled(
            deployment_env="staging", allow_mutations="1", mode="production"
        ))

    def test_main_startup_places_all_mutations_inside_guard(self):
        source = Path("main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        startup = next(
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "startup"
        )
        guard = next(
            node for node in startup.body
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Call)
            and isinstance(node.test.func, ast.Name)
            and node.test.func.id == "startup_bootstrap_enabled"
        )
        guarded_calls = {
            node.func.id for stmt in guard.body for node in ast.walk(stmt)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue({"init_db", "seed_amazon_campaigns", "seed_additional_amazon_campaigns"}.issubset(guarded_calls))
        unguarded_calls = {
            node.func.id for stmt in startup.body if stmt is not guard for node in ast.walk(stmt)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue(unguarded_calls.isdisjoint({"init_db", "seed_amazon_campaigns", "seed_additional_amazon_campaigns"}))


if __name__ == "__main__":
    unittest.main()
