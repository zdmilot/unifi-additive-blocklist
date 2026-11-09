"""Behavior checks for the append-only promise; all source data is local."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import update


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.txt"
        self.source.write_text("ads.example.com\nold.example.com\n")
        (self.root / "manual.txt").write_text("")
        (self.root / "excluded.txt").write_text("")
        self.config = {"output": "blocklist.txt", "report": "report.json",
                       "manual_additions": "manual.txt", "exclude_new": "excluded.txt",
                       "maximum_domains": 100,
                       "sources": [{"name": "Fixture", "path": "source.txt", "license": "CC0-1.0"}]}
        self.save_config()
        self.args = argparse.Namespace(config=self.root / "sources.json", write=True,
                                       check=False, baseline=None, initialize=True, import_file=[])

    def save_config(self):
        (self.root / "sources.json").write_text(json.dumps(self.config))

    def run_build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            update.run(self.args)

    def bootstrap(self):
        self.run_build()
        self.args.initialize = False

    def domains(self):
        return update.read_domains(self.root / "blocklist.txt")

    def test_upstream_removal_and_exclusion_never_remove_history(self):
        self.bootstrap()
        original = self.domains()
        self.source.write_text("new.example.com\n")
        (self.root / "excluded.txt").write_text("old.example.com\n")
        self.run_build()
        self.assertEqual(self.domains(), original | {"new.example.com"})

    def test_manual_import_and_exclude_only_new_domains(self):
        self.bootstrap()
        (self.root / "manual.txt").write_text("manual.example.com\nexcluded.example.com\n")
        (self.root / "excluded.txt").write_text("excluded.example.com\nimported.example.com\n")
        imported = self.root / "existing.txt"
        imported.write_text("0.0.0.0 imported.example.com\n")
        self.args.import_file = [imported]
        self.run_build()
        self.assertIn("manual.example.com", self.domains())
        self.assertIn("imported.example.com", self.domains())
        self.assertNotIn("excluded.example.com", self.domains())
        (self.root / "manual.txt").write_text("")
        self.args.import_file = []
        self.run_build()
        self.assertIn("manual.example.com", self.domains())
        self.assertIn("imported.example.com", self.domains())

    def test_failure_in_second_source_does_not_change_any_output(self):
        self.bootstrap()
        before = {name: (self.root / name).read_bytes() for name in ("blocklist.txt", "report.json")}
        self.source.write_text("new.example.com\n")
        self.config["sources"].append({"name": "Missing", "path": "absent.txt", "license": "CC0-1.0"})
        self.save_config()
        with self.assertRaises(OSError):
            self.run_build()
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)

    def test_malformed_empty_small_or_oversized_source_preserves_history(self):
        self.bootstrap()
        before = (self.root / "blocklist.txt").read_bytes()
        for content in ("<html>Service unavailable</html>", "", "||ads.example.com^"):
            with self.subTest(content=content):
                self.source.write_text(content)
                with self.assertRaises(ValueError):
                    self.run_build()
                self.assertEqual((self.root / "blocklist.txt").read_bytes(), before)
        self.source.write_text("single.example.com\n")
        self.config["sources"][0]["minimum_domains"] = 2
        self.save_config()
        with self.assertRaises(ValueError):
            self.run_build()
        self.config["sources"][0]["minimum_domains"] = 1
        self.config["maximum_domains"] = 2
        self.save_config()
        with self.assertRaises(ValueError):
            self.run_build()
        self.assertEqual((self.root / "blocklist.txt").read_bytes(), before)

    def test_missing_history_requires_explicit_initialization(self):
        self.args.initialize = False
        with self.assertRaisesRegex(ValueError, "Existing blocklist missing"):
            self.run_build()

    def test_dry_run_is_non_mutating_and_repeated_write_is_idempotent(self):
        self.bootstrap()
        before = (self.root / "blocklist.txt").read_bytes()
        self.run_build()
        self.assertEqual((self.root / "blocklist.txt").read_bytes(), before)
        self.args.write = False
        self.source.write_text("new.example.com\n")
        self.run_build()
        self.assertEqual((self.root / "blocklist.txt").read_bytes(), before)

    def test_history_baseline_detects_deletions_and_report_check_detects_tampering(self):
        self.bootstrap()
        baseline = self.root / "baseline.txt"
        baseline.write_text("missing.example.com\n")
        self.args.check = True
        self.args.write = False
        self.args.baseline = baseline
        with self.assertRaisesRegex(ValueError, "would be removed"):
            self.run_build()
        self.args.baseline = None
        self.run_build()
        (self.root / "blocklist.txt").write_text("tampered.example.com\n")
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.run_build()

    def test_parser_normalizes_domains_and_does_not_broaden_filter_rules(self):
        self.assertEqual(update.parse("# comment\n0.0.0.0 ADS.Example.com. tracker.example.com\n::1 localhost\n", hosts=True),
                         {"ads.example.com", "tracker.example.com"})
        self.assertEqual(update.normalize("bücher.example"), "xn--bcher-kva.example")
        for invalid in ("*.example.com", "||example.com^", "@@||example.com^", "https://example.com/a",
                        "192.168.1.1", "com", "-bad.example.com", "bad_.example.com"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                update.parse(invalid)

    def test_concurrent_imports_both_survive(self):
        self.bootstrap()
        processes = []
        for name in ("first.example.com", "second.example.com"):
            imported = self.root / name
            imported.write_text(name + "\n")
            processes.append(subprocess.Popen(
                [sys.executable, str(Path(update.__file__)), "--config", str(self.args.config),
                 "--write", "--import", str(imported)], stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, text=True))
        for process in processes:
            _, errors = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, errors)
        self.assertTrue({"first.example.com", "second.example.com"} <= self.domains())

    def test_protected_names_reject_parents_but_allow_ad_siblings(self):
        update.require_protected_names({"ads.yahoo.com"}, {"yahoo.com", "mail.yahoo.com"})
        for blocked in ({"yahoo.com"}, {"mail.yahoo.com"}):
            with self.subTest(blocked=blocked), self.assertRaisesRegex(ValueError, "Protected-domain"):
                update.require_protected_names(blocked, {"mail.yahoo.com"})
        update.require_protected_names({"notyahoo.com"}, {"yahoo.com"})

    def test_protected_collision_in_source_or_history_preserves_outputs(self):
        self.bootstrap()
        self.config["protected_domains"] = "protected.txt"
        (self.root / "protected.txt").write_text("login.example.com\n")
        self.save_config()
        before = {name: (self.root / name).read_bytes() for name in ("blocklist.txt", "report.json")}
        self.source.write_text("example.com\n")
        with self.assertRaisesRegex(ValueError, "Protected-domain"):
            self.run_build()
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)
        self.source.write_text("new.example.com\n")
        (self.root / "protected.txt").write_text("old.example.com\n")
        with self.assertRaisesRegex(ValueError, "Protected-domain"):
            self.run_build()
        self.args.check = True
        with self.assertRaisesRegex(ValueError, "Protected-domain"):
            self.run_build()

    def test_adblock_output_has_suffix_rules_and_detects_tampering(self):
        self.config["adblock_output"] = "adblock.txt"
        self.save_config()
        self.bootstrap()
        adblock = self.root / "adblock.txt"
        self.assertEqual(adblock.read_text(), "||ads.example.com^\n||old.example.com^\n")
        self.args.check = True
        self.run_build()
        adblock.write_text("||example.com^\n")
        with self.assertRaisesRegex(ValueError, "Adblock output"):
            self.run_build()

    def test_adblock_output_cannot_overwrite_canonical_list(self):
        self.config["adblock_output"] = "blocklist.txt"
        self.save_config()
        with self.assertRaisesRegex(ValueError, "paths must differ"):
            self.run_build()


if __name__ == "__main__":
    unittest.main()
