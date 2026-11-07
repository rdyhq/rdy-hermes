# rdy plugin for Hermes Agent: project rules

These rules hold for every builder and helper who works on this repo.

## What this repo is

A native Hermes Agent plugin for rdy: a `pre_tool_call` approval guard, two skills
(`rdy:start`, `rdy:loop`), the `hermes rdy doctor` and `hermes rdy setup` commands,
one setting (`rdy_path`) and a README. The agent reaches rdy through rdy's own MCP
server, which the person adds. The plugin has no tools of its own.

Files: `plugin.yaml`, `__init__.py` (register), `guard.py`, `cli.py`,
`skills/start/SKILL.md`, `skills/loop/SKILL.md`, `tests/`, `scripts/check.sh`,
`README.md`, `LICENSE`, `CLAUDE.md`, `AGENTS.md`, `.gitignore`.

## Data and names

- The repo's files, tests and history hold no names of people or businesses, no
  private paths, no store names, no emails, no keys and no tokens. That includes
  every commit's author and committer: rdy with a GitHub noreply address, set in the
  repo's own git config before the first commit. The leak scan proves it before
  every release.
- Tests and examples use made-up projects only, such as a garden planner. No real
  project's content goes in the repo.

## Safety rules

- Nobody working on this plugin changes rdy's code repo or Hermes's code. A need for
  a change goes to their makers as a note or an issue, outside this repo.
- The plugin never bundles, downloads or installs rdy, sends nothing over the
  network, reads no credentials and writes no state.
- The approval rules below hold for the guard and both skills. The guard only blocks
  or stays silent.
- Live tests run only in a new blank Hermes profile made for the test, never with
  `--clone`. Beyond the bundled skills Hermes seeds into every new profile, it gets
  only a model, the rdy MCP entry, the RDY_ACTOR lines and this plugin, and no memory
  files. Never install, enable, configure or test in any other profile, never start or
  restart a gateway, never run `hermes update`. Hash every other profile's
  `config.yaml`, `.env` and plugins folder, the default included, before and after.
  Removing the test profile needs the release owner's OK.

## Approval rules

- Only a person approves, lands or tags. The agent never runs these acts, as itself
  or for the person, in any Hermes approval mode.
- The guard blocks these rdy MCP tools by name, whatever the server is called:
  `rdy_land`, `rdy_tag`, `rdy_answer`, `rdy_sign`, `rdy_publish`, `rdy_redact`,
  `rdy_dispute`, `rdy_resolve`, `rdy_auth`, `rdy_key_bind`, `rdy_key_retire` and
  `rdy_key_revoke`.
- In tool calls that run something (the terminal, code execution, process tools, and
  any argument named command, cmd, code or script), the guard blocks an rdy command
  for approve, land, tag, answer, sign, publish, redact, dispute, resolve, auth, key
  bind, key retire or key revoke, and any text holding `--relayed-by` or `--evidence`.
  rdy's MCP tools and the file tools are judged by tool name only, never by their
  text.
- Exactly these pass: `--help` or `-h` on any verb, `rdy dispute list`, `rdy tags`,
  `rdy publication check`, `rdy auth state`, `rdy auth installs` and `rdy key show`.
  `rdy auth token`, `sign-in`, `sign-out` and the `rdy_auth` tool are always blocked.
- In tool calls that run something, only `RDY_ACTOR=agent:hermes` passes. Any other
  value, and clearing it, is blocked. An emptied environment (`env -i` and the like)
  is blocked when the same text holds an rdy token.
- The guard never returns approve or modify, and never waits for a person. If it
  fails, Hermes blocks the call (fail closed).
- The skills never edit rdy's store files, working copy or rendered site, and never
  ask a person to paste a key, token or password.

## Release rules

- Nothing is pushed, made public, tagged on a remote, or sent to the catalog, Discord
  or any person without the release owner's typed OK and the rdy creator's OK to
  publish under rdy's name. Each public step waits for its own OK. Builders and
  helpers stop and report instead.
- Every release passes the six checks on the exact commit that ships, raises version
  in `plugin.yaml`, and names the same lowest rdy in the README and doctor.

## Checks

1. Guard tests: `pytest tests/` (the rdy refusal tests need rdy on PATH or `RDY_BIN`).
2. `hermes plugins doctor <repo path> --ci`
3. `hermes plugins validate <repo path> --install-deps`
4. Leak scan: `scripts/check.sh --words <private word list outside the repo>`
5. A run in a blank throwaway Hermes profile, in every approval mode.
6. A first run on a clean machine, by the README alone.

The README, both SKILL.md files and the output of `hermes rdy doctor` and
`hermes rdy setup` also pass a design review and a second-AI words review.

## Known quirks

- Hermes skips a hook's approve request in YOLO mode and with approvals off, which is
  why the guard blocks.
- Hermes loads only one project context file: `.hermes.md` wins over `AGENTS.md`, so
  rdy's note in `AGENTS.md` is hidden when a `.hermes.md` exists.
- Enabled plugin skills appear in the skill index as `rdy:start` and `rdy:loop` (the
  code at 0.22.2; the developer guide says otherwise).
- Plugins are off after install until `hermes plugins enable rdy`. MCP servers added
  mid-session need `/reload-mcp`.
- Never commit `.pyc` or `__pycache__`: catalog rule 17 refuses committed bytecode.
- A `pre_tool_call` callback that raises or runs past the hook timeout blocks the tool
  call; keep the guard fast and free of input and output.
- `hermes mcp add` starts the server once at add time and may offer a tool picker; its
  `--args` takes the rest of the line, so `--env` comes before `--args`; and
  `${workspaceFolder}` must be in single quotes, or the shell empties it before Hermes
  sees it.
- `rdy mcp --project <folder>` exits when the folder is not an rdy project, so
  `hermes mcp add` must run inside an rdy project. If its check fails, Hermes saves
  the entry with `enabled: false`; doctor reports it.
- An MCP entry's env reaches only the MCP server. The agent's terminal gets RDY_ACTOR
  only through the profile's `.env` plus `terminal.env_passthrough`.
- Catalog rule 11: a plugin never reads `.env` files. Doctor checks RDY_ACTOR in the
  environment Hermes loaded from the profile's `.env`, not the file itself.
