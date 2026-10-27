# Start an inquiry in the app

Run `Open Red Threads.cmd` on Windows or `Open Red Threads.command` on macOS from this folder. Python 3.10+ and a browser are required. Choose **New inquiry**, name it, and write the question you want to understand. A starting hunch is optional and remains attributed to the inquiry author.

Choose **Add a source or note**. Paste a passage, locate a record, or attach an ordinary document. TXT/Markdown and DOCX text become readable source notes. PDF, PNG, JPEG and WebP originals are retained for you to inspect; there is no OCR or automatic claim extraction. Each attachment is limited to 8 MiB. **Download original** returns the retained bytes.

Use **Add person, institution or thing** to name the entities the source concerns. Then **Connect two things** with a precise verb and a statement of what the evidence establishes. A reported or documented connection needs a selected source; a hypothesis may remain unsourced. Unknown dates stay unknown. The app does not decide whether a source is true or a relationship proves control.

The full existing atlas appears below the workbench. Open it in its own tab for more room. Inspect threads, trace directed paths, filter dates and status, compare explanations, and follow source ancestry. These views preserve the native case model, including hypotheses, leads, games and extension fields supplied through an existing case. The simple workbench authors sources, entities and relationships; advanced case operations remain available through the complete skill and CLI.

**Refine** edits an entity or relationship. **Read / correct** opens a source note and can replace its attached original. Download the current case before replacing an original you need to retain separately. Source corrections identify direct relationships using that source; inspect deeper dependencies through the atlas and native impact command before changing conclusions. The workbench records each saved material change in the case journal, but does not automatically retract or promote related claims.

## Save, return and take the case elsewhere

Successful actions report **Saved on this computer**. Cases live outside the installation in the current user's local application data, `Collaborative Dynamics/red-threads/work.json`. The actual folder is shown under Your inquiries. Closing and relaunching through the app returns to that collection even when its local browser port changes. Choose another collection with `--data-home FOLDER` or `RED_THREADS_HOME`; a folder path must be writable. The server binds only to loopback.

**Download case** exports the selected inquiry in the existing portable case format, including its retained originals and unknown extension fields. **Open case** reads a valid native case JSON into a separate working copy; it never replaces the input file or another inquiry. This is the compatibility route for prepared investigations, not a requirement for starting new work. Save/Load view inside the atlas retains presentation choices separately, as before.

When another desk has saved a newer collection, a stale save is refused. The dialog keeps your entered values so you can copy them before reloading. Download case exports the last successfully saved state, not an unfinished dialog. A malformed or precision-losing native JSON file is refused; preserve the original and correct it through the native tools. Files up to 32 MiB can be opened and the whole collection is limited to 40 MiB; keep large unrelated media outside the case.

## Boundaries and recovery

The app runs local case work and the existing atlas. It does not browse, contact people, purchase information or infer connections from attachments. Use your assistant's authorized research and document tools when that work is needed. Sensitive documents remain part of the case export: choose what is appropriate before sharing it.

A failed source read leaves the dialog and current saved case intact. Keep the extracted workspace, scripts and atlas assets together if the page cannot start. If the saved store is unreadable, preserve it and launch with an accessible `--data-home`; do not overwrite it with an empty collection. Back up the collection or exported cases separately from the installation. Native macOS launching has not been observed in this Windows verification.
