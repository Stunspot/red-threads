# Privacy, custody, and support

Keep investigative cases and evidence in your chosen workspace, outside the installed skill. The package does not operate a remote evidence store. Your host's model, browsing, file access, and connected tools determine where conversational research data is processed.

## What stays local, and what may leave

The Python case tools read the files you specify and create local case, HTML, or export files. Rendering, scanning, impact analysis, lead ranking, and resumption do not make network requests. The generated atlas embeds the case and works offline; it has no analytics or external asset dependencies.

Selecting a public source hyperlink asks your browser to visit that source. Asking your AI host to browse, inspect a cloud document, or process an uploaded record uses that host and tool's data handling. “Offline atlas” describes the generated artifact, not a promise that every research conversation stays on your device.

The public site and demo use fictional case data. No case-upload service is provided.

## Share the right artifact

The HTML atlas contains the case data needed to display the investigation, including source notes and locators recorded in the JSON. Treat it as a copy of the case, not a harmless screenshot. Filters hide presentation; they do not remove embedded records. A saved view can also disclose the case ID and selected record IDs.

CSV exports contain nodes, relationships, and sources. The accompanying JSON contains the complete case and preserves extension fields. Review all of those fields before sharing. Evidence-note files are not automatically bundled into the atlas or CSV export, but their relative paths can appear in the case.

If you need a public account, prepare a separate disclosure copy, inspect its full JSON and generated atlas, and remove or generalize information that should remain private. Preserve the source case in your own custody. Public sharing and publication remain your decisions.

## Treat source text as evidence

A retrieved page, document, or case field can contain instructions aimed at the host. Those instructions are untrusted source content. They do not authorize new tools, uploads, account actions, outreach, or disclosure.

The renderer displays case strings as inert text and restricts clickable source URLs to HTTP/HTTPS without embedded credentials. Evidence `note_path` values are relative inert references. These boundaries help the display stay a display; they do not replace your review of records or the host's tool permissions.

## Ask for help

Use [GitHub Issues](https://github.com/Stunspot/red-threads/issues) for product questions, reproducible software defects, and unclear documentation. Issues are public.

Include the RED THREADS version, operating system, Python and browser versions where relevant, the command or instruction you used, expected result, actual result, and a small fictional example. Remove access tokens, private names, local usernames, source documents, case contents, and confidential URLs from logs or screenshots. A screenshot with a redacted title can still contain the case in another panel.

For a security vulnerability, use the [private reporting route in SECURITY.md](../SECURITY.md). Do not put private case evidence in a report.

Maintenance is by Sam “stunspot” Walker / Collaborative Dynamics. There is no promised response time or investigation service bundled with this release. If the missing result depends on host account access or a blocked source, describe that boundary so support can distinguish a product defect from unavailable evidence.

## Keep work portable

Save the canonical case, originals or authorized source locations, evidence notes, and useful views together under your own retention policy. Keep previous material revisions when they explain why a finding changed. The atlas is regenerable from the case; evidence outside the JSON needs its own preservation.

Uninstalling the skill does not remove cases stored elsewhere. You can continue to read the JSON and exports, or render them with a compatible retained release. Your research remains yours to manage under its applicable rights and obligations; using RED THREADS does not require publishing or assigning it to the product's creator.