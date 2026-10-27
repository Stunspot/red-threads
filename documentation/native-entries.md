# Open your atlas with a recognizable entry

## Start with your question

Open the portable inquiry desk at `codex/red-threads/workspace/Open Red Threads.cmd` (Windows) or `Open Red Threads.command` (macOS) in the extracted release. Start an inquiry from a question, add a source note or ordinary document, name entities, and describe a typed relationship. The existing interactive atlas shows the result. You do not need to manufacture a case JSON first. Follow the [app workflow guide](../src/red-threads/workspace/README.md) for saving, return, ordinary inputs and recovery.


Enter the complete `codex/red-threads` skill folder in a release, or `src/red-threads` in a source clone.

## Recognizable atlas entries

Render a new atlas with the documented command first. The atlas embeds the accepted product artwork as its tab icon and stays self-contained; a missing cosmetic image does not stop rendering. On Windows run `powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/Create desktop shortcut.ps1" -AtlasPath "E:/Cases/atlas.html" -ShortcutPath "$env:USERPROFILE\Desktop\RED THREADS.lnk"` from the skill folder. Choose an existing atlas and a new shortcut name in an existing directory. It opens that exact HTML file in the default browser.

On macOS run `sh scripts/create-desktop-app.sh --atlas "/Users/you/Cases/atlas.html" --destination "$HOME/Desktop/RED THREADS.app"`. The optional app opens the selected atlas and carries its native artwork. Mac execution remains unqualified. Keep your case files in your own workspace; recreate an entry after moving its target. These entries open a saved view of the case and do not perform research or revise evidence.
