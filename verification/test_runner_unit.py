"""Unit tests for the verification harness itself; no compiler toolchain needed."""
import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("run_tests.py")
spec = importlib.util.spec_from_file_location("minic_run_tests", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


class NormalizeOutputTests(unittest.TestCase):
    def test_ignores_whitespace_differences(self):
        self.assertEqual(module.normalize_output("  3\n  8  13\n"), "3 8 13")

    def test_preserves_output_order(self):
        self.assertNotEqual(module.normalize_output("3 8"), module.normalize_output("8 3"))

    def test_empty_output(self):
        self.assertEqual(module.normalize_output(" \n\t "), "")


class CaseDiscoveryTests(unittest.TestCase):
    def test_all_manifests_have_source_files(self):
        cases = module.load_cases()
        self.assertGreaterEqual(len(cases), 5)
        for case in cases:
            self.assertTrue(case["source"].is_file(), case["name"])
            self.assertIn("expected_output", case)

    def test_filter(self):
        cases = module.load_cases("factorial")
        self.assertEqual([case["name"] for case in cases], ["recursive_factorial"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
