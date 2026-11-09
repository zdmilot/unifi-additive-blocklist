import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("gateway_sync", Path(__file__).with_name("sync.py"))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.profile = {"_id": "profile", "enabled": True, "name": "AD Blocking Filter",
                        "network_ids": ["network"], "client_macs": [],
                        "categories": ["ADVERTISEMENT"], "block_list": ["old.example"],
                        "allow_list": ["allowed.example"], "safe_search": [],
                        "schedule": {"mode": "ALWAYS"}, "future_option": {"keep": True}}

    def test_union_preserves_history_existing_settings_and_allowlist(self):
        before = copy.deepcopy(self.profile)
        result = sync.plan(self.profile, {"new.example"}, {"historical.example"}, 10)
        self.assertEqual(result["block_list"], ["historical.example", "new.example", "old.example"])
        self.assertEqual(result["allow_list"], ["allowed.example"])
        for key in before.keys() - {"block_list", "allow_list"}:
            self.assertEqual(result[key], before[key])
        self.assertEqual(self.profile, before)

    def test_manual_allowlist_remains_and_no_exceptions_are_injected(self):
        result = sync.plan(self.profile, {"allowed.example"}, set(), 10)
        self.assertIn("allowed.example", result["block_list"])
        self.assertEqual(result["allow_list"], ["allowed.example"])
        empty = copy.deepcopy(self.profile)
        empty["allow_list"] = []
        self.assertEqual(sync.plan(empty, {"new.example"}, set(), 10)["allow_list"], [])

    def test_capacity_failure_preserves_original_profile(self):
        before = copy.deepcopy(self.profile)
        with self.assertRaises(ValueError):
            sync.plan(self.profile, {"new.example"}, {"historic.example"}, 2)
        self.assertEqual(before, self.profile)

    def test_verification_catches_truncated_lists_or_other_setting_changes(self):
        expected = sync.plan(self.profile, {"new.example"}, set(), 10)
        actual = copy.deepcopy(expected)
        actual["block_list"].pop()
        with self.assertRaises(ValueError):
            sync.verify(expected, actual)
        actual = copy.deepcopy(expected)
        actual["categories"] = []
        with self.assertRaises(ValueError):
            sync.verify(expected, actual)
        actual = copy.deepcopy(expected)
        actual["allow_list"] = []
        with self.assertRaises(ValueError):
            sync.verify(expected, actual)
        sync.verify(expected, expected)

    def test_rejects_ips_regex_wildcards_and_unsafe_names(self):
        for name in ["1.2.3.4", "*.example.com", r"cdn.cookielaw\.org", "https://example.com", "UPPER.example", "one.example two.example", "bad.example\n"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                sync.domains([name])


if __name__ == "__main__":
    unittest.main()
