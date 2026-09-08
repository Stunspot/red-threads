# Install RED THREADS

Install the complete `red-threads` skill folder, then confirm that your host can discover and use it. An ordinary chat attachment can provide reference material; it does not by itself register a skill.

## Before you start

[Download the v0.1.0 skill ZIP](https://github.com/Stunspot/red-threads/releases/download/v0.1.0/red-threads-v0.1.0.zip). Its root folder is `red-threads`, containing `SKILL.md`, references, knowledge, scripts, assets, examples, and license notices. Keep the folder intact.

You can also use the Codex installer route in this guide or the maintained [GitHub source folder](https://github.com/Stunspot/red-threads/tree/main/src/red-threads). To obtain a local source copy with Git:

```text
git clone https://github.com/Stunspot/red-threads.git
```

In that clone, the complete skill folder is `src/red-threads`. Use that folder for local installation or the first-case commands; the repository itself is not the skill folder.

You need a host that supports local or uploaded skills. The host provides the model and research tools; RED THREADS does not contain a standalone model. The package has no required paid API or server. Your host's own access and usage terms still apply.

For local case commands and atlas generation, check your Python installation:

```text
python --version
```

The result must be Python 3.10 or newer. On some systems the command is `python3`; on Windows it may be `py -3`. Use the working command consistently in this guide. Python is optional for conversational work. An already generated atlas needs only a modern browser with JavaScript.

## Codex: local skill

Ask Codex to use its built-in installer:

```text
$skill-installer Install the skill from https://github.com/Stunspot/red-threads/tree/main/src/red-threads
```

For a manual installation instead:

1. Extract the ZIP. Copy its complete `red-threads` folder into `.agents/skills/` inside your project, or into `~/.agents/skills/` for personal use. If you use a source clone, copy its `src/red-threads` folder. The final path must end in `red-threads/SKILL.md`, with no extra nested `red-threads` folder.
2. Open Codex in that project. In CLI or IDE, use `/skills` or type `$` to find `red-threads`. If it does not appear, restart Codex and check the folder.
3. Invoke the skill explicitly for the fictional first case. Confirm that the host reads the installed `SKILL.md` and can reach its bundled example.

After using the installer, perform the same discovery and first-case checks in steps 2 and 3. This is a standalone skill distribution, not a plugin-directory listing. These locations and discovery steps follow [official OpenAI skill documentation](https://learn.chatgpt.com/docs/build-skills), checked 2026-09-08. Local installation and discovery of this release have not been tested on a fresh host.

## Claude: uploaded custom skill

Use the [v0.1.0 skill ZIP](https://github.com/Stunspot/red-threads/releases/download/v0.1.0/red-threads-v0.1.0.zip) for this route.

1. Enable **Code execution and file creation** in **Settings > Capabilities**. Organization settings may govern availability.
2. Open **Customize > Skills**, select **+**, then **+ Create skill**, then **Upload a skill**.
3. Upload the release ZIP containing the intact skill folder. Confirm that `red-threads` appears and is enabled.
4. In a new conversation, ask Claude to use RED THREADS for the fictional Meridian walkthrough.

Use the supported skills interface rather than attaching the ZIP to an ordinary conversation. These labels follow [Anthropic's custom-skill instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude), checked 2026-09-08. Availability depends on the account and organization. This release has not been installed and exercised on a fresh Claude account.

## Claude Code: local skill

Copy the complete `red-threads` folder from the extracted ZIP into `~/.claude/skills/` for personal use or `.claude/skills/` within the project. If you use a source clone, copy its `src/red-threads` folder. Confirm that the final file is `red-threads/SKILL.md`, then invoke `/red-threads`. Restart if a newly created skills directory is not detected. See [Claude Code's official skill instructions](https://code.claude.com/docs/en/skills), checked 2026-09-08. Fresh-host discovery for this release remains untested.

## Confirm your first result

Give the host a writable case directory outside the skill folder and ask:

```text
Use RED THREADS to walk me through the included fictional Meridian
case. Render a copy of its atlas into my case directory. Show the
narrow approval right, trace the copied reporting to its origin,
compare the rival explanations, and name the next record that would
change the case. Identify any tool or file access you actually lack.
```

Successful file installation means the folder is present. Successful discovery means the host exposes or loads the skill. Successful use means it reads the example and produces the requested result. Check all three without treating one as proof of the others.

Continue with [your first case](first-case.md). If discovery, Python, or rendering fails, use [recovery](recovery.md).

## Update or remove the skill

Before replacing an installed copy, finish the current pass and save the case, evidence notes, and views in your workspace. Preserve the old skill folder separately if you need rollback. Replace the installed folder with the complete new release, then repeat discovery and the fictional check.

To remove a local skill, remove only its installed `red-threads` folder. For an uploaded skill, disable or remove it through the host's skills management interface. Your cases remain in their separate workspace. Read the new release's changelog before migrating case data; v0.1.0 uses case format 1.