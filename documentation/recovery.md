# Revise, resume, and recover

Preserve the current case before trying to restore a result. RED THREADS writes material revisions to a new file so you can inspect the change and retain the prior state. A saved atlas view restores presentation; `case.json` and its evidence preserve the investigation.

Commands in this guide run from the skill folder. Replace uppercase placeholders with quoted absolute paths or actual IDs. See [the command reference](reference.md) for every operation.

## A source was corrected

Start with the current case and the actual correction. Read both the changed passage and the context that narrows or replaces it.

1. Inspect the declared dependency frontier.

   ```text
   python scripts/red_threads.py impact "CASE_JSON" --source "SOURCE_ID"
   ```

   Read affected sources, relationships, nodes, hypotheses, games, and leads. The frontier is a review list. Check surviving support and untracked prose premises before deciding what changes.

2. Calculate the current case's SHA-256 over its exact bytes.

   ```text
   python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "CASE_JSON"
   ```

   Copy the 64-character digest. Formatting changes also change this hash.

3. Ask the host to prepare a JSON patch with that digest as `base_sha256`, a nonempty `reason`, and only intended changes. The [patch contract and example](../src/red-threads/references/case-format.md#apply-a-material-revision) explain `upsert`, `remove`, and partial `case` updates. Existing objects merge recursively, while supplied arrays replace their previous arrays. Inspect the complete intended support and dependency arrays before applying.

4. Apply to a new file.

   ```text
   python scripts/red_threads.py apply "CASE_JSON" --changes "PATCH_JSON" --output "NEW_CASE_JSON"
   ```

   Expect `ok: true`, base and result hashes, changed records, and a `review_frontier`. The tool validates the complete result before writing. It appends a dated journal entry and updates the case timestamp.

5. Inspect the revision and its affected conclusions. Then use `NEW_CASE_JSON` as the explicit input to future work, generate a new atlas, and update the campaign checkpoint.

The review frontier uses the union of recorded dependencies before and after the patch, so a removed premise remains visible for that revision's review. Statuses change only when your patch changes them. Do not mark all dependent claims false merely because one source changed.

You are done when the corrected scope, surviving support, affected interpretations, and next lead are clear, and the old case remains available.

## A patch says its base hash does not match

The current bytes differ from the case used to prepare the patch. Stop and reread the current file. Compare the patch's intended changes with the intervening revision, reconcile both, calculate the current digest, and prepare a new patch.

Replacing only the digest can hide a stale assumption or overwrite a newer array. The guard exists to make you notice the difference. Retain the old patch and case until the reconciled result is accepted.

## Resume a paused investigation

With the last accepted case, run:

```text
python scripts/red_threads.py resume "CASE_JSON"
```

Read the saved checkpoint, unfinished tasks, ranked leads, coverage gaps, and relevant journal entries. Reopen the actual evidence needed for the next decision. If new records change a premise, use the correction procedure before continuing downstream analysis.

A useful checkpoint names the changed finding, serious remaining rival, next obtainable record, and routes already exhausted. If no checkpoint was saved, the tool reports that absence. Reconstruct one from the case and evidence without inventing prior research.

Load a compatible saved view if useful, then verify the filters, selection, and case revision. Saving a reopening trigger for a parked lead does not schedule a monitor.

## The output already exists

Render, apply, init, and export protect existing target files. Read the returned path and choose a new explicit destination, such as `atlas-02.html` or `case-02.json`. For export, use a fresh directory when any of its target files already exists.

Do not delete the previous result merely to get past the error. Once you have inspected the new result, keep or archive earlier revisions according to your case's retention needs.

## Validation fails

Read the reported field path or reference. Correct the specific malformed value, missing object, invalid status, date order, unresolved ID, or dependency cycle, then rerun `validate`.

For a cycle, separate contextual relationships from evidentiary reliance. An edge supporting a hypothesis cannot also rely on that same hypothesis as its justification. For a removed record, reconcile every remaining reference before retrying.

If the cause is unclear, preserve the original case and create a minimal fictional reproduction for [support](privacy-and-support.md#ask-for-help). A valid case can still contain analytical mistakes; passing validation does not resolve those.

## Python or the renderer is unavailable

If `python --version` fails, try the appropriate installed command, such as `python3` or Windows `py -3`. If no Python 3.10+ interpreter is available, use the public fictional demo and conversational workflow, or install Python through your normal supported route.

If the tool reports that the atlas renderer is unavailable, check that `scripts/red_threads.py`, `scripts/render_atlas.py`, `scripts/investigation_ops.py`, and `assets/atlas.html` remain in the complete skill folder. Restore the complete release rather than copying one script.

If writing fails despite a new filename, check destination access. Use a normal writable local filesystem for generation, then copy the finished artifact where needed. Unsupported atomic-write behavior fails safely.

## The atlas is blank, blocked, or missing expected links

Open the generated HTML in a modern browser with JavaScript, not a text preview. Confirm that generation returned success. If your agent's local browser route is blocked, respect the restriction; you can open the artifact yourself through an allowed route. Keep the case and a textual explanation usable while display access is unavailable.

For unexpected omissions, inspect current layer/status/date filters, **Keep unknown intervals**, structural removal, and focused workstream. **Reset filters** resets filter choices; **No removal · observed graph** restores a removed node; **Clear trace** clears a path; **Overview** returns to the map overview. Retracted relationships are excluded by default but remain selectable through status filters.

A source without a web link may have an authorized local locator. The atlas displays evidence-note paths as text; it does not open private files automatically.

## A saved view will not load

Use a snapshot from the same case ID. Missing objects or invalid filters are rejected; a path that no longer exists returns to an explained overview. A newer case revision can make an older view incomplete even when loading succeeds.

Return to **Overview**, choose the intended current records, and save a new snapshot. Keep the rejected snapshot if it helps explain the issue. Loading or discarding a view does not change the canonical case.