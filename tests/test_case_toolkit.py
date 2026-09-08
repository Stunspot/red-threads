"""Meaningful acceptance tests for the standard-library RED THREADS toolkit."""
from __future__ import annotations

import copy
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "src" / "red-threads" / "scripts"
FIXTURE = ROOT / "src" / "red-threads" / "examples" / "meridian-case.json"
sys.path.insert(0, str(SCRIPTS))
import red_threads as toolkit


def minimal():
    return {
        "schema_version": 1,
        "case": {"id": "test", "title": "Test case", "question": "Which mechanism?", "updated_at": "2026-09-08"},
        "nodes": [{"id": "a", "label": "Actor A", "type": "organization"},
                  {"id": "b", "label": "Actor B", "type": "organization"}],
        "sources": [{"id": "primary", "title": "Primary record", "locator": "Fixture page 2"}],
        "edges": [{"id": "relation", "source": "a", "target": "b", "relation": "funded",
                   "layer": "money", "status": "documented", "source_ids": ["primary"],
                   "summary": "Record establishes a grant, not a command relationship."}],
        "hypotheses": [{"id": "explanation", "title": "Possible mechanism", "statement": "Funding may provide leverage.",
                        "status": "open", "supports": ["relation"]}],
        "leads": [], "games": [],
    }


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="red-threads-test-")
        self.directory = Path(self.temporary.name).resolve()
        self.assertTrue(self.directory.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.addCleanup(self.temporary.cleanup)

    def save(self, data=None, name="case.json"):
        path = self.directory / name
        path.write_text(json.dumps(minimal() if data is None else data), encoding="utf-8")
        return path

    def cli(self, *args):
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "red_threads.py"), *map(str, args)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertNotIn("Traceback", result.stderr + result.stdout)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def assert_invalid(self, data, contains):
        result = toolkit.validate_case(data)
        self.assertFalse(result["valid"], result)
        self.assertTrue(any(contains in item["message"] for item in result["errors"]), result)

    def test_fictional_fixture_is_valid_and_contains_the_promised_case_scale(self):
        data = toolkit.read_case(FIXTURE)
        result = toolkit.validate_case(data)
        self.assertTrue(result["valid"], result)
        self.assertTrue(14 <= len(data["nodes"]) <= 20)
        self.assertTrue(22 <= len(data["edges"]) <= 30)
        self.assertTrue(8 <= len(data["sources"]) <= 12)
        self.assertEqual(len(data["hypotheses"]), 3)
        self.assertTrue(all("url" not in source for source in data["sources"]))
        self.assertIn("fictional", data["case"]["scope"].lower())

    def test_sparse_init_and_refusal_to_overwrite(self):
        destination = self.directory / "new"
        code, result = self.cli("init", destination, "--title", "Sparse case", "--question", "Who can decide?")
        self.assertEqual(code, 0, result)
        target = destination / "case.json"
        original = target.read_bytes()
        code, result = self.cli("validate", target)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["counts"]["nodes"], 0)
        code, result = self.cli("init", destination, "--title", "Replacement", "--question", "Ignored?")
        self.assertNotEqual(code, 0)
        self.assertIn("overwrite", result["error"])
        self.assertEqual(original, target.read_bytes())

    def test_duplicate_ids_and_schema_migration_are_errors(self):
        data = minimal()
        data["nodes"].append(copy.deepcopy(data["nodes"][0]))
        self.assert_invalid(data, "Duplicate ID")
        for version in (True, "1", 2):
            with self.subTest(version=version):
                data = minimal()
                data["schema_version"] = version
                self.assert_invalid(data, "schema version 1")

    def test_all_cross_collection_references_are_checked(self):
        mutations = [
            lambda d: d["edges"][0].update(target="missing"),
            lambda d: d["edges"][0].update(source_ids=["missing"]),
            lambda d: d["edges"][0].update(hypothesis_ids=["missing"]),
            lambda d: d["sources"][0].update(origin_id="missing"),
            lambda d: d["hypotheses"][0].update(challenges=["missing"]),
            lambda d: d["leads"].append({"id":"lead","question":"Why?","rationale":"Matter of access","status":"open","node_ids":["missing"]}),
            lambda d: d["games"].append({"id":"game","title":"Bargain","summary":"Conditional","players":[{"node_id":"missing","objective":"Obtain access"}]}),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                data = minimal()
                mutate(data)
                self.assert_invalid(data, "Unknown")

    def test_source_cycles_and_self_origin_are_rejected(self):
        for sources in (
            [{"id":"one","title":"One","origin_id":"one"}],
            [{"id":"one","title":"One","origin_id":"two"},{"id":"two","title":"Two","origin_id":"one"}],
            [{"id":"primary","title":"Primary"},{"id":"one","title":"One","origin_id":"two"},{"id":"two","title":"Two","origin_id":"one"}],
        ):
            data = minimal()
            data["sources"] = sources
            data["edges"][0]["source_ids"] = [sources[0]["id"]]
            self.assert_invalid(data, "ancestry cycle")

    def test_long_acyclic_source_chain_does_not_hit_python_recursion(self):
        data = minimal()
        data["sources"] = [{"id": "primary", "title": "Primary", "locator":"Fixture"}]
        for index in range(1200):
            data["sources"].append({"id":str(index),"title":str(index),"origin_id":"primary" if index == 0 else str(index-1),"locator":"Fixture"})
        self.assertTrue(toolkit.validate_case(data)["valid"])
        self.assertEqual(len(toolkit.source_impact(data, "primary")["descendant_source_ids"]), 1200)

    def test_impossible_dates_and_inverted_effective_intervals_fail(self):
        for fields in ({"start":"2025-02-30"}, {"start":"2025-05-01","end":"2025-01-01"},
                       {"observed_at":"2025-02-29"}, {"start":"2025-01-01T01:00:00Z"}):
            with self.subTest(fields=fields):
                data = minimal()
                data["edges"][0].update(fields)
                self.assertFalse(toolkit.validate_case(data)["valid"])
        data = minimal()
        data["case"]["updated_at"] = "not a date"
        self.assertFalse(toolkit.validate_case(data)["valid"])

    def test_unknown_and_open_ended_intervals_remain_valid(self):
        for fields in ({"start":None,"end":None},{"start":"2025-01-01"},{"end":"2025-01-01"}):
            data = minimal()
            data["edges"][0].update(fields)
            self.assertTrue(toolkit.validate_case(data)["valid"])

    def test_documentary_status_needs_sources_but_hunch_is_permitted(self):
        for status in ("documented", "reported"):
            data = minimal()
            data["edges"][0].update(status=status, source_ids=[])
            self.assert_invalid(data, "require at least one source")
        data["edges"][0].update(status="hypothesis", summary="Requester suspects an undisclosed approval route.")
        self.assertTrue(toolkit.validate_case(data)["valid"])

    def test_malformed_optional_records_report_errors_without_crashing(self):
        mutations = [
            lambda d: d["nodes"][0].update(aliases="one alias"),
            lambda d: d["nodes"][0].update(core=1),
            lambda d: d["edges"][0].update(amount={"value":True,"currency":"USD","kind":"grant award","period":"2025"}),
            lambda d: d["edges"][0].update(amount={"value":float("inf"),"currency":"USD","kind":"grant award","period":"2025"}),
            lambda d: d["hypotheses"][0].update(probability={"range":[0.8,0.2],"basis":"Explicit scenario","assessed_at":"2026-09-08"}),
            lambda d: d["games"].append({"id":"game","title":"Bargain","summary":"Conditional","players":[False],"scenarios":[{"label":"Scenario","assumptions":"wrong"}]}),
            lambda d: d["edges"][0].update(source_ids=[{"id":"primary"}]),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                data = minimal()
                mutate(data)
                self.assertFalse(toolkit.validate_case(data)["valid"])

    def test_numeric_estimates_need_basis_and_do_not_promote_status(self):
        data = minimal()
        data["hypotheses"][0]["probability"] = {"value":0.7}
        self.assertFalse(toolkit.validate_case(data)["valid"])
        data["hypotheses"][0]["probability"].update(basis="Author's explicit conditional estimate, not measured frequency.", assessed_at="2026-09-08")
        original = copy.deepcopy(data)
        self.assertTrue(toolkit.validate_case(data)["valid"])
        self.assertEqual(data, original)

    def test_unsafe_source_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "file:///private/report.pdf", "data:text/html,test",
                    "https:///missing-host", "https://user:secret@example.test/x", "https://example.test/\ncontrol"):
            with self.subTest(url=url):
                data = minimal()
                data["sources"][0]["url"] = url
                self.assert_invalid(data, "http/https")
        data["sources"][0]["url"] = "https://example.test/report?q=one"
        self.assertTrue(toolkit.validate_case(data)["valid"])

    def test_duplicate_json_keys_nonfinite_numbers_and_bad_json_are_safe_errors(self):
        for text in ('{"case":1,"case":2}', '{"value":NaN}', '{"broken":'):
            path = self.directory / "malformed.json"
            path.write_text(text, encoding="utf-8")
            code, result = self.cli("validate", path)
            self.assertNotEqual(code, 0)
            self.assertFalse(result["ok"])
        data = minimal()
        data["extension"] = float("inf")
        self.assert_invalid(data, "finite")

    def test_nonobject_case_and_missing_fields_return_validation_errors(self):
        for data in ([], None, {}, {"schema_version":1,"case":{},"nodes":[4]}):
            self.assertFalse(toolkit.validate_case(data)["valid"])

    def test_impact_follows_copied_origins_and_preserves_every_status(self):
        data = toolkit.read_case(FIXTURE)
        original = copy.deepcopy(data)
        impact = toolkit.source_impact(data, "s-direction")
        self.assertEqual(set(impact["descendant_source_ids"]), {"s-digest","s-stream","s-correction"})
        self.assertIn("e-direction", impact["affected_edge_ids"])
        self.assertNotIn("e-approval", impact["affected_edge_ids"])
        self.assertEqual(set(impact["affected_hypothesis_ids"]), {"h-direction","h-bounded"})
        retracted = next(item for item in impact["affected_edges"] if item["id"] == "e-retracted-overlap")
        self.assertEqual(retracted["remaining_source_ids"], ["s-appointments"])
        self.assertEqual(data, original)
        with self.assertRaises(toolkit.CaseError):
            toolkit.source_impact(data, "not-present")

    def test_export_preserves_unknown_json_and_protects_csv_text(self):
        data = minimal()
        data["future_extension"] = {"preserve":[1,{"nested":True}]}
        data["nodes"][0]["private_annotation"] = {"text":"Keep me","tags":["a","b"]}
        data["nodes"][0]["label"] = '=HYPERLINK("https://example.test","read")'
        destination = self.directory / "export"
        files = toolkit.export_case(data, destination)
        self.assertEqual(len(files), 4)
        self.assertEqual(json.loads((destination/"case.json").read_text(encoding="utf-8")), data)
        with (destination/"nodes.csv").open(encoding="utf-8",newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["label"], "'" + data["nodes"][0]["label"])
        self.assertEqual(json.loads(rows[0]["private_annotation"]), data["nodes"][0]["private_annotation"])

    def test_export_refuses_any_preexisting_output_without_partial_new_files(self):
        destination = self.directory / "export"
        destination.mkdir()
        (destination/"sources.csv").write_text("Original source table",encoding="utf-8")
        with self.assertRaises(toolkit.CaseError):
            toolkit.export_case(minimal(), destination)
        self.assertEqual({path.name for path in destination.iterdir()}, {"sources.csv"})
        self.assertEqual((destination/"sources.csv").read_text(), "Original source table")

    def test_export_to_canonical_case_directory_cannot_overwrite_case(self):
        case = self.save()
        original = case.read_bytes()
        code, result = self.cli("export", case, "--output", self.directory)
        self.assertNotEqual(code, 0)
        self.assertIn("overwrite", result["error"])
        self.assertEqual(case.read_bytes(), original)
        self.assertFalse((self.directory/"nodes.csv").exists())

    def test_atomic_writer_refuses_a_racing_destination_and_cleans_its_temp(self):
        target = self.directory / "atlas.html"
        real_link = toolkit._publish_new
        def racing_link(source, destination):
            Path(destination).write_text("Concurrent owner content", encoding="utf-8")
            return real_link(source, destination)
        with mock.patch.object(toolkit, "_publish_new", side_effect=racing_link):
            with self.assertRaises(toolkit.CaseError):
                toolkit.atomic_write_text(target, "Our content")
        self.assertEqual(target.read_text(), "Concurrent owner content")
        self.assertEqual({path.name for path in self.directory.iterdir()}, {"atlas.html"})

    def test_export_rolls_back_only_its_own_files_after_a_racing_collision(self):
        destination = self.directory / "export"
        real_link, calls = toolkit._publish_new, []
        def racing_link(source, target):
            calls.append(target)
            if len(calls) == 2:
                Path(target).write_text("Concurrent export", encoding="utf-8")
            return real_link(source, target)
        with mock.patch.object(toolkit, "_publish_new", side_effect=racing_link):
            with self.assertRaises(toolkit.CaseError):
                toolkit.export_case(minimal(), destination)
        self.assertEqual({path.name for path in destination.iterdir()}, {"edges.csv"})
        self.assertEqual((destination/"edges.csv").read_text(), "Concurrent export")

    def test_render_uses_contract_and_never_overwrites_case_or_atlas(self):
        case = self.save()
        target = self.directory / "atlas.html"
        seen = []
        renderer = types.SimpleNamespace(render=lambda data: seen.append(copy.deepcopy(data)) or "<!doctype html><title>Offline</title>")
        with mock.patch.dict(sys.modules, {"render_atlas":renderer}):
            args = toolkit.make_parser().parse_args(["render",str(case),"--output",str(target)])
            result, code = toolkit.run(args)
            self.assertEqual(code, 0)
            self.assertEqual(seen, [minimal()])
            self.assertTrue(target.read_text().startswith("<!doctype html>"))
            with self.assertRaises(toolkit.CaseError):
                toolkit.run(args)
            args.output = case
            with self.assertRaises(toolkit.CaseError):
                toolkit.run(args)
        self.assertEqual(json.loads(case.read_text()), minimal())

    def test_invalid_case_never_reaches_renderer_or_creates_output(self):
        data = minimal()
        data["edges"][0]["target"] = "missing"
        case = self.save(data)
        target = self.directory / "atlas.html"
        render = mock.Mock(return_value="unused")
        with mock.patch.dict(sys.modules, {"render_atlas":types.SimpleNamespace(render=render)}):
            args = toolkit.make_parser().parse_args(["render",str(case),"--output",str(target)])
            with self.assertRaises(toolkit.CaseError):
                toolkit.run(args)
        render.assert_not_called()
        self.assertFalse(target.exists())

    def test_generated_artifacts_stay_outside_installed_skill(self):
        with self.assertRaises(toolkit.CaseError):
            toolkit._new_destination(toolkit.SKILL_ROOT / "case-that-must-not-be-created.json")

    def test_existing_dangling_symlink_is_not_followed_as_a_new_output(self):
        target = self.directory / "atlas.html"
        missing = self.directory / "missing.html"
        try:
            target.symlink_to(missing)
        except OSError as exc:
            self.skipTest("Host does not permit symlink creation: " + str(exc))
        resolved = toolkit._new_destination(target)
        with self.assertRaises(toolkit.CaseError):
            toolkit.atomic_write_text(resolved, "Must not be written")
        self.assertFalse(missing.exists())
        self.assertTrue(target.is_symlink())

    def test_invalid_cli_usage_is_json_not_a_traceback(self):
        for args in (("impact",), ("unknown-command",), ("validate",self.directory/"missing.json")):
            code, result = self.cli(*args)
            self.assertNotEqual(code, 0)
            self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
