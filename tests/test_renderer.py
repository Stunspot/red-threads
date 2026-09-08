import copy
import importlib.util
import json
import re
import unittest
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("render_atlas", ROOT / "src" / "red-threads" / "scripts" / "render_atlas.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class RendererTests(unittest.TestCase):
    def test_hostile_case_strings_remain_inert_and_round_trip(self):
        payload = {"case": {"title": "</script><script>globalThis.PWNED=true</script>&\u2028\u2029", "question": "<img src=x onerror=alert(1)>"}, "nodes": [], "edges": [], "sources": []}
        original = copy.deepcopy(payload)
        html = MODULE.render(payload)
        match = re.search(r'<script id="case-data" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(match)
        embedded = match.group(1)
        self.assertNotIn("<", embedded)
        self.assertNotIn(">", embedded)
        self.assertNotIn("&", embedded)
        self.assertNotIn("\u2028", embedded)
        self.assertNotIn("\u2029", embedded)
        self.assertEqual(payload, json.loads(embedded))
        self.assertEqual(original, payload)
        self.assertEqual(2, len(re.findall(r"<script(?: |>)", html)))
        self.assertNotIn(MODULE.TOKEN, html)

    def test_empty_case_renders_portable_document(self):
        html = MODULE.render({"case": {"title": "Empty"}, "nodes": [], "edges": [], "sources": [], "hypotheses": [], "leads": [], "games": []})
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("connect-src 'none'", html)
        self.assertNotRegex(html, r'<script\s+[^>]*src=')
        self.assertNotRegex(html, r'<link\s+[^>]*href=')

    def test_rejects_non_json_numeric_values(self):
        with self.assertRaises(ValueError):
            MODULE.render({"amount": float("nan")})

    def test_rejects_non_object_root(self):
        with self.assertRaises(TypeError):
            MODULE.render([])

    @unittest.skipUnless(shutil.which("node"), "Node is optional for DOM-free graph checks")
    def test_directed_trace_time_slices_and_structural_removal(self):
        template = (ROOT / "src" / "red-threads" / "assets" / "atlas.html").read_text(encoding="utf-8")
        functions = []
        for name in ("known", "temporal", "filtered", "components", "shortest"):
            match = re.search(r"function " + name + r"\([\s\S]+?(?=\nfunction )", template)
            self.assertIsNotNone(match, name)
            functions.append(match.group(0))
        checks = r'''
const assert=require('node:assert/strict');
const nodes=new Map(['a','b','c','d'].map(id=>[id,{id}]));
const edges=[
 {id:'ab',source:'a',target:'b',layer:'money',status:'documented',start:'2025-01-01',end:'2025-12-31'},
 {id:'bc',source:'b',target:'c',layer:'money',status:'documented',start:'2025-01-01',end:'2025-12-31'},
 {id:'cd',source:'c',target:'d',layer:'money',status:'retracted',start:'2025-01-01',end:'2025-12-31'}
];
const state={layers:new Set(['money']),statuses:new Set(['documented']),date:'',unknown:true,removed:''};
assert.deepEqual(shortest(filtered(),'a','c').links,['ab','bc']);
assert.equal(shortest(filtered(),'c','a'),null);
assert.equal(shortest(filtered(),'a','d'),null);
assert.equal(filtered().length,2);
state.date='2025-06-01';
assert.equal(temporal({}),true);
assert.equal(temporal({start:'2025-07-01'}),false);
assert.equal(temporal({end:'2025-05-01'}),false);
assert.equal(temporal({start:'2025-01-01'}),true);
state.unknown=false;
assert.equal(temporal({start:'2025-01-01'}),false);
assert.equal(temporal(edges[0]),true);
state.date='';state.unknown=true;
assert.equal(components(filtered()),1);
state.removed='b';
assert.equal(filtered().length,0);
assert.equal(components(filtered(),'b'),2);
assert.equal(shortest(filtered(),'a','c'),null);
'''
        result = subprocess.run([shutil.which("node"), "-e", "\n".join(functions) + checks], text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
if __name__ == "__main__":
    unittest.main()
