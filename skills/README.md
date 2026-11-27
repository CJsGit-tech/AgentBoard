# AgentBoard skills

AgentBuild connects Codex or Claude Code to AgentBoard. It has four workflows: Setup, Create Documents, Create Visuals and Create Tickets.

| Folder | Contents |
| --- | --- |
| `agentbuild/` | Codex skill, plus the references and helper scripts both hosts use |
| `agentbuild-claude/` | Claude Code files: its entry file and host guide |

**Install with the script. Do not copy `agentbuild-claude/` by itself.** It needs the shared files, and the installer combines the two.

## Install

You need Python 3.12+ and Codex or Claude Code. Live board work also needs the AgentBoard service running in Docker; see the [setup guide](../README.en.md#install-the-service).

Run from the AgentBoard checkout. For every project on your machine:

```sh
python3 scripts/install-skill.py install --host claude --scope personal
```

For one project:

```sh
python3 scripts/install-skill.py install --host claude --scope project --project /path/to/your/project
```

For Codex, replace `claude` with `codex`. Use one scope per host to avoid duplicate copies.

## Connect to the board

Installing the skill does not register the board connection. Follow the [connection guide](agentbuild/references/connection.md).

## Use

Start a new session. In Claude Code, type `/agentbuild Setup My Project`. In Codex, type `$agentbuild Setup My Project`. The skill runs only when you call it.

## Update or remove

Pull the latest checkout, then rerun the installer with `update` or `uninstall` and the same host, scope and project options. `update` backs up the previous copy. The installer refuses to change a copy you edited or one it did not install; move that folder somewhere outside the skills folders first.

## Change the skill

- Shared rules: edit `agentbuild/references/` or `agentbuild/scripts/`.
- Claude behavior: edit `agentbuild-claude/`. Its `SKILL.md` replaces the shared one, so apply changes to core rules in both entry files.

Then run the checks and `update` your installed copy:

```sh
python3 -m pip install -r scripts/requirements-checks.txt
python3 scripts/check-skills.py
python3 -m unittest discover -s scripts/tests -v
```

Licensed under MIT; see [LICENSE.txt](agentbuild/LICENSE.txt).
