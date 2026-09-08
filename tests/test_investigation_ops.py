"""Regression evidence for transitive correction, selective change and resumable investigation."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "src" / "red-threads" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import red_threads as toolkit
import investigation_ops as ops


def case():
    return {
        "schema_version": 1,
        "case": {"id": "dependency-test", "title": "Contract correction", "question": "Which advice must change?",
                 "updated_at": "2026-09-08", "journal": [{"date": "2026-09-07", "change": "Original research"}],
                 "campaign": {"phase": "mechanism", "resume": "Obtain the signed schedule.",
                              "coverage": [{"id": "contracts", "question": "Who can approve?", "status": "partial",
                                            "source_ids": ["s"], "lead_ids": ["l"], "searches": ["Exact agreement title"],
                                            "remaining_gap": "Signed schedule absent"}],
                              "tasks": [{"id": "obtain", "question": "Find the schedule", "status": "active", "owner": "researcher",
                                         "return_condition": "Actual clause or exact access gap", "lead_ids": ["l"]}],
                              "future_setting": {"retain": True}}},
        "nodes": [{"id": "a", "label": "Funder", "type": "organization", "group": "Resources"},
                  {"id": "b", "label": "Institute", "type": "organization", "group": "Policy"},
                  {"id": "c", "label": "Agency", "type": "organization", "group": "Policy", "depends_on": ["sources:other"]}],
        "sources": [{"id": "s", "title": "Contract", "locator": "Section 4", "access_state": "read",
                     "note_path": "evidence/contract.md"},
                    {"id": "other", "title": "Separate register", "locator": "Entry 12", "access_state": "read"},
                    {"id": "copy", "title": "Combined account", "origin_id": "s", "origin_ids": ["other"],
                     "locator": "Paragraph 7"}],
        "edges": [{"id": "base", "source": "a", "target": "b", "relation": "can approve the deliverable of",
                   "layer": "governance", "status": "documented", "source_ids": ["copy"], "summary": "A limited contract right.",
                   "future_field": {"retain": True, "edit": "old"}},
                  {"id": "derived", "source": "a", "target": "b", "relation": "may constrain",
                   "layer": "governance", "status": "inferred", "source_ids": [],
                   "depends_on": ["edges:base"], "summary": "Practical leverage derives from the contract right."},
                  {"id": "separate", "source": "b", "target": "c", "relation": "submitted to",
                   "layer": "policy", "status": "documented", "source_ids": ["other"], "summary": "Separate agency access.",
                   "start": "2025-01-01", "end": "2025-12-31"}],
        "hypotheses": [{"id": "h", "title": "Bounded control", "statement": "Contract rights limit one deliverable.",
                        "status": "supported", "supports": ["derived"]}],
        "games": [{"id": "g", "title": "Renewal", "summary": "Conditional bargaining",
                   "depends_on": ["hypotheses:h"], "players": [{"node_id": "b", "objective": "Publish the brief"}]}],
        "leads": [{"id": "l", "question": "What threat is credible?", "rationale": "The next move depends on the contract game.",
                   "status": "answered", "answer": "Contest out-of-scope demands.", "depends_on": ["games:g"],
                   "source_ids": [], "node_ids": ["a"]}],
        "extension": {"unknown": ["preserve", 1]},
    }


class OperationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="red-threads-ops-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def save(self, data, name):
        path = self.directory / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def cli(self, *args):
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "red_threads.py"), *map(str, args)],
                                text=True, capture_output=True, encoding="utf-8")
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def patch(self, source, **fields):
        return {"base_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "reason": "The signed clause narrows the right.", **fields}

    def test_correction_crosses_derived_edge_hypothesis_game_and_answer_preserving_unrelated(self):
        data = case()
        original = copy.deepcopy(data)
        self.assertTrue(toolkit.validate_case(data)["valid"])
        impact = toolkit.source_impact(data, "s")
        self.assertEqual(impact["affected_ids"], {
            "nodes": [], "sources": ["copy", "s"], "edges": ["base", "derived"],
            "hypotheses": ["h"], "games": ["g"], "leads": ["l"]})
        self.assertEqual(impact["untracked_analytical_records"], [])
        self.assertEqual(original, data)
        self.assertNotIn("separate", impact["affected_edge_ids"])
        self.assertEqual(impact["affected_hypotheses"][0]["status"], "supported")

    def test_multiparent_ancestry_and_legacy_origin_are_both_effective(self):
        data = case()
        for source in ("s", "other"):
            result = toolkit.source_impact(data, source)
            self.assertIn("copy", result["descendant_source_ids"])
            self.assertIn("g", result["affected_game_ids"])
        self.assertIn("c", toolkit.source_impact(data, "other")["affected_node_ids"])
        data["sources"][2]["origin_ids"] = ["other", "s"]
        self.assertTrue(toolkit.validate_case(data)["valid"])
        self.assertEqual(ops.source_parents(data["sources"][2]), ["s", "other"])

    def test_prose_only_inference_and_game_are_visible_coverage_gaps(self):
        data = case()
        del data["edges"][1]["depends_on"]
        del data["games"][0]["depends_on"]
        result = toolkit.validate_case(data)
        self.assertTrue(result["valid"])
        tokens = {row["token"] for row in ops.dependency_coverage(data)["untracked_analytical_records"]}
        self.assertEqual(tokens, {"edges:derived", "games:g"})
        impact = toolkit.source_impact(data, "s")
        self.assertEqual({row["token"] for row in impact["untracked_analytical_records"]}, tokens)

    def test_contextual_node_links_do_not_silently_become_evidence(self):
        data = case()
        data["nodes"][0]["depends_on"] = ["sources:s"]
        data["leads"][0].pop("depends_on")
        impact = toolkit.source_impact(data, "s")
        self.assertIn("a", impact["affected_node_ids"])
        self.assertNotIn("l", impact["affected_lead_ids"])

    def test_edge_hypothesis_tags_flow_from_edge_to_hypothesis(self):
        data = case()
        data["edges"][1]["hypothesis_ids"] = ["h"]
        self.assertTrue(toolkit.validate_case(data)["valid"])
        self.assertEqual(ops.dependency_graph(data)["hypotheses:h"], {"edges:derived"})
        self.assertIn("h", toolkit.source_impact(data, "s")["affected_hypothesis_ids"])

    def test_mixed_dependency_and_multiple_origin_cycles_are_rejected(self):
        data = case()
        data["edges"][1]["depends_on"] = ["hypotheses:h"]
        result = toolkit.validate_case(data)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Dependency cycle" in issue["message"] for issue in result["errors"]))
        data = case()
        data["sources"][0]["origin_ids"] = ["copy"]
        result = toolkit.validate_case(data)
        self.assertFalse(result["valid"])
        self.assertTrue(any("ancestry cycle" in issue["message"] for issue in result["errors"]))

    def test_additive_contract_rejects_malformed_refs_access_campaign_and_views(self):
        changes = [
            lambda d: d["edges"][1].update(depends_on=["edge:base"]),
            lambda d: d["sources"][0].update(origin_ids=["missing"]),
            lambda d: d["sources"][0].update(access_state=[]),
            lambda d: d["sources"][0].update(note_path="../private.txt"),
            lambda d: d["sources"][0].update(note_path="C:/private.txt"),
            lambda d: d["case"]["campaign"]["coverage"][0].update(lead_ids=["missing"]),
            lambda d: d["case"]["campaign"]["tasks"][0].update(status="finished"),
            lambda d: d["case"].update(views={"overview_limit": True}),
            lambda d: d["case"].update(views={"overview": {"Resources": ["b"]}}),
            lambda d: d["case"].update(views={"group_hubs": {"Resources": "missing"}}),
            lambda d: d["leads"][0].update(effort="trivial"),
        ]
        for change in changes:
            with self.subTest(change=change):
                data = case()
                change(data)
                self.assertFalse(toolkit.validate_case(data)["valid"])

    def test_curated_overview_is_not_capped_at_the_automatic_limit(self):
        data = case()
        data["nodes"] += [{"id": "extra-" + str(i), "label": "Extra " + str(i), "type": "person", "group": "Resources"}
                          for i in range(12)]
        data["case"]["views"] = {"group_order": ["Policy", "Resources"], "group_hubs": {"Resources": "a"},
                                 "overview": {"Resources": ["a"] + ["extra-" + str(i) for i in range(12)]},
                                 "pinned_nodes": ["c"], "overview_limit": 2}
        self.assertTrue(toolkit.validate_case(data)["valid"])

    def test_scan_distinguishes_documented_topology_parallel_edges_and_collection_gaps(self):
        data = case()
        data["edges"] = [
            {"id": "ab", "source": "a", "target": "b", "relation": "funded", "status": "documented",
             "source_ids": ["s"], "layer": "money", "summary": "Grant"},
            {"id": "ab-copy", "source": "a", "target": "b", "relation": "renewed a grant to", "status": "documented",
             "source_ids": ["s"], "layer": "money", "summary": "Renewal"},
            {"id": "bc", "source": "b", "target": "c", "relation": "advised", "status": "documented",
             "source_ids": ["other"], "layer": "policy", "summary": "Advice", "start": "2025-01-01", "end": "2025-12-31"},
            {"id": "ac", "source": "a", "target": "c", "relation": "may contact", "status": "hypothesis",
             "source_ids": [], "layer": "policy", "summary": "Test alternate route"}]
        data["hypotheses"], data["games"], data["leads"] = [], [], []
        data["case"].pop("campaign")
        result = ops.scan_case(data)
        self.assertEqual(result["active"]["articulation_node_ids"], [])
        self.assertEqual(result["documented_only"]["articulation_node_ids"], ["b"])
        self.assertEqual(result["sensitivity"]["new_articulation_node_ids"], ["b"])
        bridge = next(pair for pair in result["documented_only"]["bridge_pairs"] if pair["node_ids"] == ["a", "b"])
        self.assertEqual(bridge["edge_ids"], ["ab", "ab-copy"])
        self.assertEqual(set(result["cross_group_edge_ids"]), {"ab", "ab-copy", "ac"})
        self.assertNotIn("bc", [row["edge_id"] for row in result["date_gaps"]])

    def test_frontier_ranks_only_supplied_assessments_and_open_leads(self):
        data = case()
        base = {"question": "Find the clause", "rationale": "Separates the mechanisms", "status": "open"}
        data["leads"] += [
            {"id": "expensive", **base, "decision_value": "high", "priority": "high", "effort": "high"},
            {"id": "cheap", **base, "decision_value": "high", "priority": "high", "effort": "low",
             "custodian": "Procurement office", "record_type": "Signed schedule", "query": "Exact contract ID"},
            {"id": "missing", **base, "priority": "high"},
            {"id": "parked", **base, "status": "parked", "decision_value": "high"}]
        result = ops.frontier_case(data)
        self.assertEqual([row["id"] for row in result["leads"]], ["cheap", "expensive", "missing"])
        self.assertEqual(result["leads"][0]["acquisition_gaps"], [])
        self.assertIn("No decision_value assessment supplied", result["leads"][2]["ranking_reasons"])
        self.assertEqual(result["coverage_gaps"][0]["id"], "contracts")

    def test_apply_rejects_stale_duplicate_or_dangling_change_without_output(self):
        for number, mode in enumerate(("stale", "duplicate", "conflict", "dangling")):
            with self.subTest(mode=mode):
                original = self.save(case(), "case-" + str(number) + ".json")
                patch = self.patch(original, upsert={"sources": [{"id": "s", "note": "Revised clause"}]})
                if mode == "stale":
                    patch["base_sha256"] = "0" * 64
                elif mode == "duplicate":
                    patch["upsert"]["sources"].append({"id": "s", "note": "Competing change"})
                elif mode == "conflict":
                    patch["remove"] = {"sources": ["s"]}
                else:
                    patch = self.patch(original, remove={"sources": ["s"]})
                changes = self.save(patch, "patch-" + str(number) + ".json")
                output = self.directory / ("output-" + str(number) + ".json")
                raw = original.read_bytes()
                code, result = self.cli("apply", original, "--changes", changes, "--output", output)
                self.assertNotEqual(code, 0, result)
                self.assertFalse(output.exists())
                self.assertEqual(original.read_bytes(), raw)

    def test_apply_preserves_unknowns_case_custody_and_all_unrelated_records(self):
        original_data = case()
        original = self.save(original_data, "case.json")
        changes = self.save(self.patch(original,
            upsert={"edges": [{"id": "base", "summary": "Approval covers one brief only.",
                               "future_field": {"edit": "new"}}]},
            case={"campaign": {"resume": "Read renewal conditions next.",
                               "coverage": [{"id": "contracts", "question": "Who can approve?", "status": "covered",
                                             "source_ids": ["s"], "lead_ids": ["l"]}]}}), "patch.json")
        output = self.directory / "revised.json"
        raw = original.read_bytes()
        code, result = self.cli("apply", original, "--changes", changes, "--output", output)
        self.assertEqual(code, 0, result)
        updated = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(original.read_bytes(), raw)
        self.assertEqual(updated["extension"], original_data["extension"])
        self.assertEqual(updated["edges"][0]["future_field"], {"retain": True, "edit": "new"})
        self.assertEqual(updated["edges"][2], original_data["edges"][2])
        self.assertEqual(updated["case"]["campaign"]["future_setting"], {"retain": True})
        self.assertEqual(updated["case"]["journal"][0], original_data["case"]["journal"][0])
        self.assertEqual(updated["case"]["journal"][-1]["changed_tokens"], ["edges:base"])
        self.assertEqual(result["review_frontier"]["affected_game_ids"], ["g"])
        self.assertEqual(result["review_frontier"]["affected_lead_ids"], ["l"])
        self.assertEqual(updated["hypotheses"][0]["status"], "supported")
        self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), result["result_sha256"])
        code, checkpoint = self.cli("resume", output)
        self.assertEqual(code, 0)
        self.assertEqual(checkpoint["checkpoint"], "Read renewal conditions next.")
        self.assertEqual(checkpoint["unresolved_tasks"][0]["id"], "obtain")
        self.assertEqual(checkpoint["coverage_gaps"], [])
        again, result = self.cli("apply", original, "--changes", changes, "--output", output)
        self.assertNotEqual(again, 0)

    def test_apply_review_frontier_retains_dependencies_removed_in_the_same_patch(self):
        data = case()
        original = self.save(data, "case.json")
        patch = self.patch(original,
                           upsert={"hypotheses": [{"id": "h", "supports": ["separate"]}]},
                           remove={"edges": ["derived"]})
        changes = self.save(patch, "patch.json")
        output = self.directory / "revised.json"
        code, result = self.cli("apply", original, "--changes", changes, "--output", output)
        self.assertEqual(code, 0, result)
        self.assertIn("edges:derived", result["removed_tokens"])
        self.assertIn("g", result["review_frontier"]["affected_game_ids"])
        self.assertIn("l", result["review_frontier"]["affected_lead_ids"])
        self.assertIn("derived", result["review_frontier"]["affected_edge_ids"])

    def test_new_cli_operations_are_json_and_leave_case_bytes_unchanged(self):
        original = self.save(case(), "case.json")
        raw = original.read_bytes()
        for command in ("scan", "frontier", "resume"):
            code, result = self.cli(command, original)
            self.assertEqual(code, 0, result)
            self.assertEqual(result["case_id"], "dependency-test")
        self.assertEqual(original.read_bytes(), raw)

    def test_empty_campaign_and_sparse_case_have_explicit_resumption_gaps(self):
        data = case()
        data["case"].pop("campaign")
        data["leads"] = []
        checkpoint = ops.resume_case(data)
        self.assertIsNone(checkpoint["checkpoint"])
        self.assertEqual(checkpoint["unresolved_tasks"], [])
        self.assertEqual(checkpoint["available_views"], {})


if __name__ == "__main__":
    unittest.main()
