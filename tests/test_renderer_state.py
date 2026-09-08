"""Independent save/load regressions; actual state functions, no browser claim.

The reviewer reproduced these failures before the root agent repaired the atlas.
DOM and download shells are stubbed; state transitions and validation are real.
"""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "red-threads" / "assets" / "atlas.html"

STATE_FIXTURE = r"""
const assert = require('node:assert/strict');
const data = {
  schema_version: 1,
  case: {id: 'state-review', title: 'State review', question: 'Which path survives?', updated_at: '2026-09-08'},
  nodes: ['a', 'b', 'c'].map(id => ({id, label: id.toUpperCase(), type: 'organization', group: 'Funds'})),
  edges: [
    {id: 'ab', source: 'a', target: 'b', relation: 'funded', layer: 'money', status: 'documented', source_ids: ['s'], summary: 'First grant'},
    {id: 'bc', source: 'b', target: 'c', relation: 'funded', layer: 'money', status: 'documented', source_ids: ['s'], summary: 'Second grant'}
  ],
  sources: [{id: 's', title: 'Grant record', locator: 'Case record 1'}],
  hypotheses: [], leads: [], games: []
};
const meta = data.case, edges = data.edges;
const originalEvidence = JSON.stringify(data);
const state = {
  tab: 'atlas', mode: 'node', focus: 'a', group: null, edge: null,
  source: null, selected: {collection: 'nodes', id: 'a'}, pins: new Set(),
  date: '', unknown: true, layers: new Set(['money']), statuses: new Set(['documented']),
  removed: '', path: [], pathNodes: [], history: []
};
const elements = Object.fromEntries([
  'path-from', 'path-to', 'save-status', 'date-filter', 'include-unknown',
  'remove-node', 'layer-filters', 'status-filters'
].map(id => [id, {value: '', querySelectorAll: () => []}]));
const $ = id => elements[id];
let saved;
const Blob = class {constructor(parts) {saved = JSON.parse(parts[0]);}};
const URL = {createObjectURL: () => '', revokeObjectURL: () => {}};
const document = {body: {append: () => {}}};
const el = () => ({click: () => {}, remove: () => {}});
const setTimeout = () => {};
const renderGraph = () => {};
const renderLinked = () => {};
const showTab = tab => {state.tab = tab;};
"""


@unittest.skipUnless(shutil.which("node"), "Node is required for executable renderer state checks")
class RendererStateTests(unittest.TestCase):
    def run_state_check(self, checks):
        template = TEMPLATE.read_text(encoding="utf-8")
        functions = []
        for name in ("validateView", "known", "temporal", "filtered", "shortest",
                     "filterChanged", "saveView", "loadView"):
            match = re.search(r"function " + name + r"\([\s\S]+?(?=\n(?:async )?function )", template)
            self.assertIsNotNone(match, name)
            functions.append(match.group(0))
        result = subprocess.run(
            [shutil.which("node"), "-"],
            input=STATE_FIXTURE + "\n" + "\n".join(functions) + "\n" + checks,
            text=True, encoding="utf-8", capture_output=True, timeout=10,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_removing_focused_entity_keeps_saved_view_loadable(self):
        self.run_state_check(r"""
// Open A's neighborhood, remove A structurally, save, then load the same case.
state.removed = 'a';
filterChanged();
saveView();
assert.doesNotThrow(() => loadView(saved));
assert.equal(state.mode, 'all');
assert.equal(state.focus, null);
assert.equal(state.selected, null);
assert.equal(state.removed, 'a');
assert.deepEqual(filtered().map(e => e.id), ['bc']);
assert.equal(JSON.stringify(data), originalEvidence, 'view removal must not change evidence');
""")

    def test_pending_trace_selectors_do_not_replace_displayed_trace_on_load(self):
        self.run_state_check(r"""
// A -> B -> C is displayed. The user edits the pending selectors without tracing.
state.mode = 'trace';
state.focus = null;
state.selected = null;
state.path = ['ab', 'bc'];
state.pathNodes = ['a', 'b', 'c'];
elements['path-from'].value = 'c';
elements['path-to'].value = 'a';
assert.equal(shortest(filtered(), 'c', 'a'), null);
saveView();
loadView(saved);
assert.equal(state.mode, 'trace');
assert.deepEqual(state.path, ['ab', 'bc']);
assert.deepEqual(state.pathNodes, ['a', 'b', 'c']);
assert.equal(elements['path-from'].value, 'a');
assert.equal(elements['path-to'].value, 'c');
assert.doesNotMatch(elements['save-status'].textContent, /no longer exists/);
assert.equal(JSON.stringify(data), originalEvidence, 'view resumption must not change evidence');
""")


if __name__ == "__main__":
    unittest.main()
