# Rebuild the current source kit

Extract into a short, new folder. The `RED-THREADS-v0.1.1` root includes `src`, `tools`, `tests`, public site `docs`, customer `documentation`, `distribution`, configuration and current bound authorship references. Codex uses `codex/red-threads`; Claude imports `claude/red-threads-v0.1.1.zip`. Private evaluation history, case originals and unrelated estate records are excluded.

From that release root with Python3.10 or newer run `python -B tools/build_release.py --output path/to/new-candidate`. The destination must be new, outside src/, tools/, tests/, docs/, documentation/, distribution/ and .github/; existing outputs are preserved. The output contains the full customer ZIP, artwork, install prompt, companion guide, release manifest and checksum list. Current documentation references are checked before packaging; materially changed guides need their own current authorship/review, not a stale receipt.

The inner SHA256SUMS.txt covers the complete extracted payload except itself. A match proves byte custody, not evidence truth, useful investigation or installed host discovery. An unchanged-source rebuild does not create fresh qualification. Read [Evidence and licenses](evidence-and-licenses.md) for retained limits.
