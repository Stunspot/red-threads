# Make evidence survive interpretation

Read the source as an investigator who will have to revise the case later. Preserve what it establishes, what it merely asserts, and where interpretation begins. The goal is a source-linked model another operator can inspect and correct without reconstructing your thought process.

## Open a source into a reusable evidence note

Assign a stable source ID before it becomes a premise. Use `access_state` honestly: discovered for a lead not opened; inspected for a bounded look sufficient to classify it; read when the relevant source context has actually been read; inaccessible or excluded with a reason. A report's bibliography does not make its listed works read. Record publication and retrieval dates separately, URL or authorized locator, and immediate upstream sources in `origin_id`/`origin_ids`.

For a source that carries a material conclusion, save a short note in the user's case directory and link it through relative `note_path`, such as `evidence/s-contract.md`. The renderer treats that path as inert text; the operator uses authorized file tools to open it. Keep the original file or an authorized retrievable location beside the note. Preserve useful page numbers, section names, table rows, timestamps, document identifiers and version distinctions.

A note should let the next reader answer: what was inspected; what exact observations matter; what the source can establish; what remains asserted or inferred; what scope and limitations apply; which case objects rely on it; what other record would resolve its principal gap. Write prose where it is clearer. A small extraction table helps when one source makes several different claims.

For a fictional contract:

| Passage actually read | Atomic observation | Case interpretation |
|---|---|---|
| Schedule B: sponsor approves workshop slides; publications are expressly excluded | Approval right applies to workshop slides | Documented limited approval edge; broader publication control remains a separate hypothesis |
| Clause 8: renewal is discretionary after twelve months | Sponsor may decline a future award | Possible leverage through renewal; no proof it was used |
| Financial annex: up to $600,000 reimbursable expenses | A ceiling, not proof of disbursement | Record contract value with period; seek payment records for actual flow |

A compact note can say: “Read executed agreement and Schedule B, supplied fictional original. Supports e-slide-approval and e-renewal-option. Does not establish editorial intervention or payment. Missing: revisions to slides and payment ledger.” This is more useful than a summary that the parties “worked closely.”

## Extract claims at the right granularity

Separate actor, action or state, object, applicable period, quantity and modality. Preserve “may,” “up to,” “alleged,” “proposed,” “former” and “subject to approval.” Resolve pronouns against the actual document. A source can support the existence of a claim without supporting the claimed event.

Encode consequential relational claims as precise edges. Use event or policy nodes to retain context and state changes. Keep a disputed interpretation distinct from the underlying documented transaction. An assertion that has no useful graph representation can remain in its note, but label it as outside automatic dependency tracking if it matters to the answer. Do not create empty relationships solely to satisfy a diagram.

Attach provenance to the proposition actually used. An edge citing a long article should identify the paragraph or table that supports its verb. If the article derives its financial number from a registry but adds an interview-based account of intent, those observations have different origins and limitations. Use the registry for the financial edge and the attributed interview for the reported intention; retain the article's multiple-parent ancestry.

## Reconcile entities without erasing uncertainty

Match legal entities through registry identifiers, jurisdiction, formation history and names. Match people through role, organization, dates and other relevant professional identifiers. Similar names, a shared office or the same service provider suggest a candidate match; they do not settle identity. Preserve aliases and merger histories with dates. Distinguish a person from a role, a parent from a subsidiary, and an organization from an event it hosts.

When workers return duplicate candidates, compare identifying records before merging. Choose one stable ID, rewrite every affected reference deliberately, and preserve the discarded identifier as an alias or journal note where appropriate. Keep separate nodes and an open reconciliation lead when evidence is insufficient. A shared website or tracking identifier may belong to a contractor serving many clients; determine the actual operator and time interval before using it as common control evidence.

Treat names that change after acquisition or reorganization as time-bearing identities. A former employer, later board appointment and current consulting role may describe three different opportunities for access. Reconstruct the role intervals before drawing a simultaneous influence path.

## Make contradictions specific

Place incompatible propositions side by side with their sources, scopes and dates. Test whether they concern the same entity, accounting period, currency, gross/net basis, commitment/disbursement, draft/final document, or event stage. “$600,000 award” and “$180,000 received this quarter” can both be true. “No sponsor approval over publications” and “sponsor approves workshop slides” can coexist. An apparent contradiction disappears only after its scope is resolved explicitly.

When the conflict remains, preserve both accounts and mark the disputed proposition. Ask which custodian or observation can distinguish reporting error, changed circumstances, selective disclosure, organizational disagreement or deception. Reconcile against better evidence; do not average incompatible quantities or upgrade the more confident speaker.

## Declare the dependency before the conclusion spreads

The case contains two different graphs. Entity relations describe the world. Evidence dependencies describe why an analytical record should be reviewed when another changes. A cycle of payments may exist in the first; a circular justification cannot validate itself in the second.

On a record, `depends_on: ["edges:e-approval"]` means this record relies on that edge. Use exact plural collection names. Source origins, edge `source_ids`, hypothesis supports/challenges and edge `hypothesis_ids` already carry the specified evidence flow. `edge.hypothesis_ids` points the edge's evidence toward the hypothesis; it does not mean the edge was inferred from that hypothesis. An edge actually derived from a hypothesis needs an explicit `depends_on` and must not feed back as evidence for its own premise.

Declare material premises for games, inferred edges, identity summaries and downstream leads. A game's `depends_on` covers its player objectives and scenario assumptions that rely on case evidence. Node IDs on a lead are context; use source/edge IDs or explicit dependencies for evidence. A premise left only in prose cannot be found reliably by the impact tool.

## Correct without rewriting history

Use `impact` on a challenged source and inspect all affected collections. Affected means review, not false. Examine remaining independent support, limit the changed claim, update the hypothesis or game where warranted, and replace next leads that now pursue an obsolete premise. Preserve unaffected records.

For governed case edits, use `apply` with the raw input `base_sha256`, a material reason and a new output path. Merge only intended fields; arrays replace their prior values, so supply the complete intended support/dependency list. Validate the proposed result and inspect its before/after review frontier. Keep the previous case and evidence notes. Record the change, its trigger and unresolved consequences in the journal, then save the next useful campaign resume point.
