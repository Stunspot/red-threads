# Contribute to RED THREADS

Useful contributions make an investigation easier to inspect, correct, or resume. Start with the smallest reproducible problem and the user outcome it affects.

## Report a problem

Search [existing issues](https://github.com/Stunspot/red-threads/issues), then open a focused issue with version, environment, expected behavior, actual behavior, and a minimal fictional reproduction. For a documentation problem, name the page and the first instruction that fails.

Keep private cases, credentials, and source records out of issues and pull requests. Use the [private security route](SECURITY.md) for vulnerabilities.

## Work on the software

Clone the repository, use Python 3.10+ and Node.js, and work on a separate branch. Python uses the standard library; Node runs tests against the bundled JavaScript. The runtime is in `src/red-threads`, tests in `tests`, build tools in `tools`, public guides in `documentation`, and the static site in `docs`.

Run from the repository root:

```text
python -B -m unittest discover -s tests -v
python -B tools/build_release.py
python -B tools/check_site.py
```

Inspect every result. The release builder writes the distribution under `dist`. Tests exercise local code; they do not prove host installation, live research accuracy, or browser usability. State the actual environment and any skips.

Keep stable case IDs, unknown extension fields, evidence dependency direction, explicit uncertainty, and no-overwrite output behavior intact. Add a focused regression when a change fixes a concrete defect. Use fictional records in fixtures.

A pull request should explain the triggering problem, resulting behavior, validation, and any changed limitation. Update the affected guide and changelog when the user-facing contract changes. A schema or migration change needs an explicit compatibility story.

## Respect authored-material rights

Deterministic software is MIT-licensed. Original instructions, teaching narratives, documentation, and artwork have a separate CC BY-ND 4.0 license, with existing upstream CC BY 4.0 rights preserved. Read [LICENSE.md](LICENSE.md) before redistributing changes.

For authored-material corrections, describe the proposed change in an issue and obtain the necessary permission before publicly distributing an adapted version. Do not assume that the software license covers a rewritten skill or modified artwork. Maintainers can coordinate authorized changes to the official material.

## Review and maintenance

The maintainer is Sam “stunspot” Walker / Collaborative Dynamics. Source or interface changes reopen the corresponding documentation review. New public claims must describe what actually ran; clean packaging, host discovery, browser interaction, and investigation results remain separate evidence states.

Avoid turning a bounded repair into a redesign. A useful fix and a clear explanation beat a ceremonial test parade.