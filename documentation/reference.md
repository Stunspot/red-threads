# Commands and case reference

Use this page to find the right operation. The authoritative field contracts, optional extensions, and patch examples are in [case format 1](../src/red-threads/references/case-format.md).

Run commands from the `red-threads` skill folder with Python 3.10+. Replace uppercase placeholders with your own paths or IDs; use quoted absolute paths for case files and destinations outside the installed skill.

## Commands

| Task | Command |
|---|---|
| Create an empty case | `python scripts/red_threads.py init "CASE_DIR" --title "TITLE" --question "QUESTION"` |
| Check structure and references | `python scripts/red_threads.py validate "CASE_JSON"` |
| Generate a new offline atlas | `python scripts/red_threads.py render "CASE_JSON" --output "NEW_ATLAS_HTML"` |
| Export tables and the full case | `python scripts/red_threads.py export "CASE_JSON" --output "EXPORT_DIR"` |
| Inspect a source's declared correction impact | `python scripts/red_threads.py impact "CASE_JSON" --source "SOURCE_ID"` |
| Inspect structural and coverage candidates | `python scripts/red_threads.py scan "CASE_JSON"` |
| Rank recorded actionable leads | `python scripts/red_threads.py frontier "CASE_JSON"` |
| Read the saved campaign checkpoint | `python scripts/red_threads.py resume "CASE_JSON"` |
| Apply a reasoned patch to a new case file | `python scripts/red_threads.py apply "CASE_JSON" --changes "PATCH_JSON" --output "NEW_CASE_JSON"` |

Commands return JSON. `validate` reports `valid`; successful other operations report `ok`. Errors return a nonzero exit code and an error or validation details. Parser/help usage is available with `python scripts/red_threads.py --help` and each command's `--help`.

`impact`, `scan`, `frontier`, and `resume` are read-only. Render validates the case and writes self-contained HTML. Export writes `nodes.csv`, `edges.csv`, `sources.csv`, and complete `case.json`; the JSON preserves unknown fields. CSV text that could become a spreadsheet formula receives an apostrophe prefix.

Writes refuse existing target files. Use explicit new destinations for revisions and renders. The [recovery guide](recovery.md) explains error branches and safe stopping.

## What the analysis commands mean

`impact` follows recorded source origins, support references, and cross-collection dependencies. Its `affected_ids` covers all six record collections. An affected record needs review; it is not automatically false. Coverage warnings identify some analytical records without tracked premises, but cannot prove all dependencies were captured.

`scan` compares undirected simple topology over active, non-retracted relationships while retaining the original directed records. It reports cross-group relations, articulation nodes, bridge pairs, documented-only sensitivity, incomplete time intervals, and access or campaign gaps. Removing a bridge pair requires removing all parallel relationships on that pair. Structural importance depends on collection coverage and does not measure influence or wrongdoing.

`frontier` includes open and pursuing leads. It sorts supplied decision value high first, then priority high first, then effort low first, then ID; missing judgments sort after supplied values at their tier. It explains rankings and missing acquisition fields. This is editorial ordering, not a calculated expected-information score.

`resume` returns the recorded checkpoint, unresolved and parked tasks, open/partial coverage, up to ten ranked actionable leads with a remaining count, parked lead IDs, dependency coverage, and available view settings. Empty state is reported rather than invented.

## Case objects

The UTF-8 JSON document requires integer `schema_version: 1`, a `case` object, and six arrays: `nodes`, `edges`, `sources`, `hypotheses`, `leads`, and `games`. Arrays may be empty. IDs must be unique within each collection.

| Record | Purpose | Required core |
|---|---|---|
| `case` | Question, scope, revision, optional campaign and editorial views | `id`, `title`, `question`, `updated_at` |
| `nodes` | People, organizations, events, policies, resources, and other entities | `id`, `label`, `type` |
| `sources` | Records and their immediate upstream origins | `id`, `title` |
| `edges` | Precise directed relationships with status and evidence | `id`, `source`, `target`, `relation`, `layer`, `status`, `source_ids`, `summary` |
| `hypotheses` | Explanations, support/challenges, and discriminating tests | `id`, `title`, `statement`, `status` |
| `leads` | Research questions, rationale, acquisition details, and answers | `id`, `question`, `rationale`, `status` |
| `games` | Players, objectives, constraints, and conditional strategic scenarios | `id`, `title`, `summary`, `players` |

Each game player requires `node_id` and `objective`. All six collections can use `depends_on` with exact plural references such as `sources:s-contract` or `hypotheses:h-direction`. Every reference must resolve and the combined evidence dependency graph must be acyclic. Reciprocal real-world relationships are permitted; circular evidentiary support is not.

The [full schema reference](../src/red-threads/references/case-format.md) specifies dates, amounts, probability objects, multi-parent ancestry, coverage, tasks, curation, and patch merging.

## Status vocabulary

| Field | Values |
|---|---|
| Relationship `status` | documented, reported, inferred, hypothesis, disputed, retracted |
| Hypothesis `status` | open, supported, weakened, rejected, parked |
| Lead `status` | open, pursuing, answered, parked |
| Source `access_state` | discovered, inspected, read, inaccessible, excluded |
| Campaign coverage `status` | open, partial, covered, parked |
| Campaign task `status` | open, active, done, parked |

A documented or reported relationship requires at least one source. A hypothesis may remain unsourced and attributed. A “documented” status is a recorded judgment; validation does not inspect the source's truth.

Relationship `start` and `end` are inclusive effective dates. `observed_at` records evidence arrival. Unknown dates and open ends remain uncertainty; a date filter does not reconstruct what an actor knew then.

## Atlas controls

The atlas has **Atlas**, **Timeline**, **Explanations**, **Leads**, **Actor games**, and **Sources** views. Use **Find**, **Go**, and **Explore workstream** to focus attention; **Back** and **Overview** navigate the map.

**Layers, dates & structural tools** contains relation and evidence filters, **Effective on date**, **Keep unknown intervals**, path selectors, and structural node removal. **Trace directed path** follows the visible arrow direction. Its result establishes a route in the recorded graph.

**Save view** downloads presentation state. **Load view** accepts a compatible snapshot for the same case ID, checks its references and filters, and recomputes paths against the current case. It reports revision differences. Loading a view does not edit evidence. Canonical editorial layout is stored separately in `case.views`.

## Renderer API

`scripts/render_atlas.py` exposes `render(data: dict) -> str`. It reads the bundled `assets/atlas.html` template and returns HTML text. Use the CLI when you also need case validation and guarded file output.

Case strings are embedded as data and displayed as text. Only absolute HTTP/HTTPS source hyperlinks are clickable. Local evidence `note_path` values are inert relative references; the renderer does not open them or fetch sources. See [privacy and custody](privacy-and-support.md).