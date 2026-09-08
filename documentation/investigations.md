# Run an investigation

Begin with the question that matters to you and the records the host is allowed to inspect. A transcript, agreement, event, institution, or attributed hunch is enough to start. You do not need to complete an intake ritual before following a useful lead.

You need [a discovered RED THREADS skill](installation.md), access to relevant material, and a chosen workspace for cases and evidence. Research uses your host's permitted tools. If a record is inaccessible, preserve that gap and identify what an obtainable substitute could establish.

## Start the case

Give the host the source material and a working directory, then use this request:

```text
Use RED THREADS to investigate the question in these records.
Begin with the smallest useful map of actors, resources, obligations,
and decision rights. Read the relevant source contents, preserve
locators and limits, and distinguish documented relations from
reported claims and hypotheses. Keep the case and evidence notes
in my chosen workspace. Follow the next obtainable record that
could change the explanation.
```

For a durable case, the host can create the initial file using the bundled tool. Run from the skill folder, replacing `CASE_DIR` with an absolute path in your workspace:

```text
python scripts/red_threads.py init "CASE_DIR" --title "Investigation title" --question "Which mechanism explains this decision?"
```

The result gives the path to a new `case.json`. Its empty collections are a starting point, not completed research. Save originals or authorized retrieval locations and evidence notes alongside it. Keep the installed skill separate so an upgrade does not disturb your work.

## Open the record before strengthening the claim

Ask the host to read the actual clause, annex, table, or passage that carries the conclusion. Preserve page numbers, dates, document versions, and qualifications such as “may,” “up to,” or “alleged.” A signed contract can establish an approval right; showing that the right was exercised may require revisions or acceptance correspondence.

Record whether a source was discovered, inspected, read, inaccessible, or excluded. “Discovered” is a lead, not a reading receipt. Preserve each claim's immediate origins: several publications can repeat one account, while one article can combine several independent records.

An evidence note should explain what was read, what it supports, what it cannot establish, and which case objects use it. The [evidence and reconciliation guide](../src/red-threads/references/evidence-and-reconciliation.md) gives worked extraction and correction examples.

## Follow identities, resources, and rights

For an identity match, use legal identifiers, jurisdiction, role, and dates. Similar names or a shared service provider are candidate matches. Keep separate nodes until the evidence supports reconciliation. Preserve the old identity or alias and update references deliberately.

For money, compare the same entity, currency, period, and amount kind. An award, installment, reimbursement, loan, and contract ceiling can describe very different obligations. Follow what the money purchased or enabled, then inspect appointment rights, approval, termination, renewal, and alternatives. A payment is an excellent lead. It is not a remote control.

For institutions, separate access, drafting, advice, veto, adoption, and implementation. A submission can establish access to a consultation without proving its recommendations were adopted. A shared summit is an event; it does not create collaboration between every attendee.

Use [record families and custodians](../src/red-threads/knowledge/record-family-playbook.md) when the next document is unclear. It connects money, ownership, policy, procurement, personnel, and narrative questions to records likely to resolve them.

## Give the explanation a rival worth beating

Preserve your starting suspicion as an attributed prior. Split a broad account into propositions that can receive different answers: who supplied resources, who directed work, who reached the decision-maker, and what changed in the final outcome.

Then ask:

```text
Compare the strongest plausible explanations for this pattern.
For each, name its assumptions, the observation it explains,
and a prediction that differs from its rivals. Choose the next
obtainable record that would most change this comparison.
Keep my starting belief separate from evidence confidence.
```

Qualitative judgments are often sufficient. If you use probabilities, record their basis, date, alternatives, and sensitivity to assumptions. The toolkit stores and validates a probability's representation; it does not calculate truth or calibrate your estimate. See [hypotheses and strategy](../src/red-threads/references/hypotheses-and-strategy.md).

For actor games, examine objectives, constraints, outside options, timing, feasible moves, and credible responses. Ask who can actually withhold or replace a resource, then what would show willingness to use that ability. The atlas displays conditional scenarios; it does not solve an empirical equilibrium.

## Use the atlas to choose the next record

Generate a fresh atlas after a material case revision. Inspect the relevant neighborhood, relationship status, dates, and evidence. Use source ancestry to locate dependence. Compare a broad view with documented-only relations or a relevant date. A disappearing route tells you which assumption carries the apparent connection.

The case's `views` settings preserve deliberate group order, overview members, hubs, and pinned entities. Those choices guide attention. They are editorial choices, not measurements of control. [Visual investigation](../src/red-threads/references/visual-investigation.md) explains curation and when another diagram would serve the question better.

Run `scan` to surface structural candidates and coverage gaps, `frontier` to order recorded open leads, and `resume` to recover the saved checkpoint. None performs new research. A lead becomes useful when it names a custodian, record type, query, expected observation, and meaningful alternative result.

## Preserve the correction path

The entity network says **who relates to whom**. The evidence dependency graph says **which record relies on which premise**. A source correction must reach derived explanations, actor games, and answered leads as well as the obvious relationship.

Declare that reliance with source links and exact `depends_on` references such as `"edges:e-approval"`. A name appearing in a lead is context, not automatic evidence dependence. Important premises left only in prose need manual review. Use [revision and recovery](recovery.md) for `impact` and guarded patches.

## Stop with a usable handoff

For a substantial pass, save the current case, evidence notes, relevant atlas, and optional view snapshot. Record what changed, what explanation currently leads and why, what remains unresolved, and the next obtainable record. Keep unsuccessful search boundaries and parked branches with a reopening condition.

Parallel workers should return bounded evidence and candidate changes into one authoritative case. Reconcile identities, dates, money, and source origins before merging their returns. See [campaign operations](../src/red-threads/references/campaign-operations.md).

The handoff is ready when you can state the supported mechanism at its proper scope, show the evidence that carries it, preserve the meaningful uncertainty, and resume without rebuilding the investigation from memory.