# RED THREADS case format 1

`case.json` is the portable canonical investigation. Keep UTF-8 JSON with integer `schema_version: 1`; preserve unknown properties and stable IDs. The atlas, CSV and saved views are projections. Place case and evidence files in the user's chosen directory, outside the installed skill. None of these fields is executable.

Top level requires `schema_version`, `case`, and six arrays: `nodes`, `edges`, `sources`, `hypotheses`, `leads`, `games`. Arrays may be empty. IDs are unique within their collection. `case` requires `id`, `title`, `question`, `updated_at` (ISO date or datetime). Optional `notes` and `scope` are strings; `priors` holds attributed starting statements; `journal` holds dated material revisions. Optional campaign and view fields are described below.

## Declare the evidence path

Every record in all six collections may have `depends_on`, an array of exact plural `COLLECTION:ID` strings. A declaration on a game, for example `"depends_on": ["hypotheses:h-bounded", "edges:e-approval"]`, means that the game relies on those records. Changing either premise brings the game into the review frontier. Declare all substantive player and scenario premises on the game record.

Use dependency links for evidential reliance. Node participation, a similar topic and visual proximity are contextual relationships. A person's appearance in `lead.node_ids`, or as an edge endpoint, does not silently make that node's description evidential support.

The dependency graph also includes these existing references:

| Supplied field | Record that relies on the referenced evidence |
|---|---|
| source `origin_id` and `origin_ids` | That source relies on each upstream source |
| edge `source_ids` | That edge relies on each source |
| hypothesis `supports` and `challenges` | That hypothesis assessment relies on each edge |
| edge `hypothesis_ids` | Each named hypothesis relies on this edge |
| lead `source_ids` and `edge_ids` | That lead relies on the sources and edges |

All references must resolve. The combined dependency graph must be acyclic. If a hypothesis depends on an edge, making that same edge depend on the hypothesis creates circular support. Preserve alternative explanations or contextual relations in their appropriate fields instead.

`impact` traces this entire declared graph, including source → derived edge → hypothesis → game → answered lead. It returns `affected_ids` for all six collections and preserves the original keys `descendant_source_ids`, `affected_source_ids`, `affected_edge_ids`, `affected_hypothesis_ids`, `affected_edges` and `affected_hypotheses`. Added convenience keys are `affected_node_ids`, `affected_game_ids` and `affected_lead_ids`. Results include coverage warnings and `untracked_analytical_records`.

An inferred edge, hypothesis, game or answered lead with no declared evidentiary prerequisites is flagged as untracked. An attributed open hunch remains valid; the flag tells the investigator that prose alone cannot participate in mechanical correction tracing. Coverage always remains limited to declared dependencies. A nonempty declaration does not prove that every premise was captured. Inspect qualifications and unknown extension fields before calling a correction review complete.

## Nodes

Required: `id`, `label`, `type`. Optional: `group`, `summary`, `aliases` (strings), `identifiers` (object), `core` (boolean), `depends_on`.

Types are open vocabulary: person, organization, event, policy, program, resource, publication, audience. Represent a shared venue or committee as a node rather than inventing pairwise collaboration. Separate legal identities until evidence earns reconciliation. Group and core markers are editorial placement aids, not measurements of power.

## Sources

Required: `id`, `title`. Optional: `url`, `locator`, `publisher`, `published_at`, `retrieved_at`, `origin_id`, `origin_ids`, `note`, `access_state`, `note_path`, `depends_on`.

`origin_ids` is an array of upstream source IDs. It is combined with the legacy singular `origin_id`; either or both may be supplied. Multi-origin reporting can therefore retain all recorded parents. Split distinct assertions where their provenance differs, or record the unresolved allocation in a source note. A URL or ancestry-root count does not establish independent corroboration.

Use `access_state`: discovered, inspected, read, inaccessible or excluded. Preserve what actually happened. A discovered title is not a read source. Dates may be ISO dates or datetimes. Public hyperlinks must be absolute HTTP/HTTPS URLs without embedded credentials. Local/private records use a locator instead. Optional `note_path` names an evidence note relative to the case directory; absolute paths, URLs and parent traversal are rejected. Neither CLI scan nor renderer fetches, opens or executes that path.

The fictional fixture uses invented summaries and locators clearly labeled as teaching material, never fabricated real citations.

## Edges

Required: `id`, `source` (node ID), `target` (node ID), `relation` (precise verb), `layer`, `status`, `source_ids` (array), `summary`.

Layers include money, governance, personnel, policy, infrastructure, narrative and coordination; additional names are permitted. Status is documented, reported, inferred, hypothesis, disputed or retracted. Documented/reported edges require at least one source. Hypothesis edges may remain unsourced. An inference may state its basis in summary/evidence, but declare source or record dependencies when that basis should be traced after correction.

Optional: `evidence` (short supporting extract or paraphrase with locator), `mechanism`, `start`/`end` (inclusive YYYY-MM-DD effective interval; null/omitted unknown), `date_note`, `observed_at` (YYYY-MM-DD evidence arrival), `hypothesis_ids`, `amount`, `depends_on`.

`amount` contains numeric `value` plus `currency`, `kind` and `period`. Distinguish award, disbursement, investment, commitment, contract value, stock and flow. Preserve incompatible amounts rather than summing them. A single start and no end is open-ended, not proof of currentness. A relationship date slice does not reconstruct what actors knew at that time.

## Hypotheses

Required: `id`, `title`, `statement`, `status` (open, supported, weakened, rejected or parked). Optional: `assumptions` (strings), `supports` and `challenges` (edge IDs), `predictions` (strings), `next_test`, `alternative`, `prior` (attributed statement), `probability`, `depends_on`.

Support/challenge assignments describe analytical use, not automatic promotion. A probability object requires `value` or ordered `range` within 0–1, `basis`, and `assessed_at`. The toolkit checks the representation; it does not calculate or calibrate probabilities.

## Leads

Required: `id`, `question`, `rationale`, `status` (open, pursuing, answered or parked). Optional: `edge_ids`, `node_ids`, `source_ids`, `priority`, `expected_observation`, `alternative_result`, `answer`, `depends_on`.

To make a lead obtainable, add `custodian`, `record_type` and `query` strings. Add `decision_value` and `effort` using high, medium or low when the case supports those editorial judgments. `priority` uses the same vocabulary. Preserve an answered lead's dependencies: a changed source or strategic premise can require revisiting its answer.

`frontier` includes only open/pursuing leads. It orders supplied decision value high first, then priority high first, then effort low first, then stable ID. Missing assessments sort after supplied values at their tier. Each result states its ranking reasons and absent acquisition fields. This is ordinal editorial ordering, not an invented expected-information score. Parked leads retain their revival conditions.

## Games

Required: `id`, `title`, `summary`, `players` (array). Each player requires `node_id` and `objective`; optional `basis`, `constraints`, `outside_options`, `moves`. The last three are string arrays.

Optional game fields: `kind` (bargaining, signaling, coordination, principal-agent, coalition or commitment), `sequence` (strings), `scenarios` (objects with `label` plus `assumptions`, `implications`, `signals` string arrays), `depends_on`.

Place traceable dependencies for the whole strategic model on the game. Keep the distinction between evidenced terms and inferred objectives in its player/scenario prose. Qualitative or ordinal reasoning can be useful; the renderer displays that reasoning and does not claim to solve a simulated equilibrium.

## Campaign checkpoint

Optional `case.campaign` holds `phase` and `resume` strings plus `coverage` and `tasks` arrays. Use it when an investigation needs re-entry or bounded workers. A short connection question does not require campaign administration.

A coverage entry requires `id`, `question`, `status` (open, partial, covered or parked); optional `source_ids`, `lead_ids`, `searches` (strings), `remaining_gap`. Record the actual search boundary and why the remaining gap matters.

A task requires `id`, `question`, `status` (open, active, done or parked); optional `owner`, `return_condition`, `source_ids`, `lead_ids`. IDs are unique within each campaign array. All supplied source/lead references resolve to the case.

`resume` returns the saved checkpoint, unresolved and parked tasks, up to ten ranked actionable leads with a remaining count, parked lead IDs, open/partial coverage, dependency coverage and available view definition. It reports absent state without inventing completed research.

## Editorial views and visual resumption

Optional `case.views` contains `group_order` (group-name array), `group_hubs` (group → node ID), `overview` (group → ordered node IDs), `pinned_nodes` (node IDs), and `overview_limit` (integer 1–50, default 9). Group mappings reference members of that group. Explicit overview entries are curated choices; the automatic limit never truncates them. These fields express placement and attention, not causal importance.

The atlas Save view action downloads a presentation snapshot. Load view accepts `red-threads-view-1` or `red-threads-view-2` snapshots for the same case ID, validates referenced objects/filters and recomputes paths against the current case. A changed case revision is reported. Missing objects or invalid state are rejected; a path that no longer exists returns to an explained overview. Store the snapshot with the case. Loading changes presentation state only; it never updates evidence.

## Commands

Run from the installed skill directory with Python 3.10+:

```text
python scripts/red_threads.py init CASE_DIR --title TITLE --question QUESTION
python scripts/red_threads.py validate CASE_JSON
python scripts/red_threads.py render CASE_JSON --output NEW_ATLAS_HTML
python scripts/red_threads.py export CASE_JSON --output NEW_EXPORT_DIRECTORY
python scripts/red_threads.py impact CASE_JSON --source SOURCE_ID
python scripts/red_threads.py scan CASE_JSON
python scripts/red_threads.py frontier CASE_JSON
python scripts/red_threads.py resume CASE_JSON
python scripts/red_threads.py apply CASE_JSON --changes PATCH_JSON --output NEW_CASE_JSON
```

All commands emit JSON; errors return nonzero. Validation checks structure, references, dependency cycles, date ordering and explicit evidence boundaries. It does not decide truth. Scan/frontier/resume/impact are read-only. Render validates then assembles a self-contained offline HTML file. Export writes nodes.csv, edges.csv, sources.csv and complete case.json; JSON preserves unknown fields.

`scan` returns stable record IDs for cross-group relations, articulation nodes and bridge pairs, documented-only sensitivity, incomplete effective intervals, source-access gaps and campaign coverage gaps. It treats the active graph as undirected simple topology for structural comparison, excluding retracted edges; exact direction and verbs remain in the edge records. Parallel assertions are grouped into a pair: disconnecting a bridge pair requires removing every edge on that pair. A component count or articulation is a prompt to inspect resources, substitutes and missing collection, not an influence, guilt or truth score.

## Apply a material revision

Read the current case and calculate SHA-256 over its exact bytes. For example:

```text
python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "CASE_JSON"
```

Replace `CASE_JSON` with the absolute path of the current case.

Write a patch using a proper JSON serializer. The shape below illustrates the fields; replace the digest and IDs with values from the actual case.

```json
{
  "base_sha256": "REPLACE_WITH_THE_64_HEX_DIGEST",
  "reason": "The signed amendment narrows the approval right.",
  "upsert": {
    "edges": [
      {"id": "e-approval", "summary": "Approval applies only to the named deliverable."}
    ],
    "games": [
      {"id": "g-renewal", "depends_on": ["edges:e-approval"]}
    ]
  },
  "case": {
    "campaign": {"resume": "Inspect the renewal clause before revising the threat scenario."}
  }
}
```

`upsert` maps collection names to records; existing IDs receive recursive object merges, new IDs add records. `remove` maps collection names to IDs of records to remove. `case` is a partial object. Omitted fields survive, nested object properties merge, and supplied arrays replace their previous arrays. Inspect array contents before replacing them; preserve every dependency still needed.

The patch requires matching original-byte `base_sha256` and a nonempty `reason`. Unknown patch control fields, duplicate operations, upsert/remove conflicts, missing removal targets and dangling references are rejected. The complete result is validated before a new atomic file is written. Existing output files and the original case are never overwritten. A concurrent change detected in the original input requires rereading and reconciling the patch.

A successful apply updates `case.updated_at`, appends a UTC-dated material revision to `case.journal`, and returns base/result hashes plus a review frontier over the union of before/after declared dependencies. A removed or detached premise therefore remains visible for review in that revision. Every affected status remains the author's recorded status until an explicit analytical revision changes it. Supply the new case path for subsequent work.

## Output and recovery

Correct the field paths returned by validation, then rerun. Choose a new explicit destination when one exists. Writes use atomic no-overwrite rename on Windows and atomic no-overwrite link creation on POSIX; unsupported filesystems fail safely. Use a normal writable local filesystem for generation, then copy finished artifacts where needed. CSV text that could be interpreted as a formula is prefixed with an apostrophe; JSON retains its original value.

The renderer module `scripts/render_atlas.py` exposes `render(data: dict) -> str` and reads `assets/atlas.html` relative to its packaged directory. It safely embeds serialized case JSON; case strings remain inert text and only HTTP/HTTPS source hyperlinks are clickable. No renderer, scan or impact operation performs research or makes network calls. A passed render is evidence of file generation; inspect actual browser behavior through an allowed route when claiming interactive usability.
