# rdy for Hermes Agent

Plan with rdy from Hermes. The agent reads, writes and
proposes. Only you approve.

rdy keeps what a team intends and decided, and gives it to people as a docs site
and to agents as briefings and rules. This plugin connects a Hermes agent to rdy,
teaches it the rdy loop, and stops it from ever approving or landing on its own.

## What you get

- **An approval guard.** A `pre_tool_call` hook that blocks every rdy act only a
  person may do: approve, land, tag, answer, sign, publish, redact, dispute,
  resolve, hub sign-in, and signing-key changes. It blocks in every Hermes
  approval mode, YOLO included. It never asks and never allows on its own.
- **Two skills.** `rdy:start` sets up a first project. `rdy:loop` is the
  day-to-day loop: read, write, clear tensions, propose, hand you the approve
  command.
- **`hermes rdy doctor` and `hermes rdy setup`.** Doctor checks the setup and
  changes nothing. Setup prints the three things to add and writes nothing.

The agent uses rdy's own MCP server, so it always gets rdy's current tools. The
plugin adds no tools of its own.

## Requirements

- Hermes Agent 0.22.2 or newer.
- rdy 0.41.0 or newer, installed separately from rdy's official install page. The
  plugin never installs or downloads rdy.
- Linux or macOS. Windows is not supported yet.

## Install

1. Install the plugin:

   ```
   hermes plugins install <owner>/rdy-hermes-plugin
   ```

   Once it is in the Hermes plugin catalog, `hermes plugins install rdy` works
   too.

2. Turn it on. Plugins stay off until you enable them:

   ```
   hermes plugins enable rdy
   ```

3. Check that it loaded: `hermes plugins list` shows rdy as enabled, with 1 hook.

## Connect Hermes to rdy

Run `hermes rdy setup`. It prints three things to add. Add them yourself:

1. **The rdy MCP server.** In a folder that is already an rdy project (no
   project yet? run `rdy init` there first), run this line exactly as printed:

   ```
   hermes mcp add rdy --command rdy --env RDY_ACTOR=agent:hermes --args mcp --project '${workspaceFolder}'
   ```

   Hermes starts rdy once to check the line, and rdy needs a project for that.
   If the check fails, Hermes saves the server turned off, and doctor tells you.
   Keep the single quotes: without them the shell empties `${workspaceFolder}`
   before Hermes sees it. `--env` must come before `--args`, because `--args`
   takes the rest of the line. Hermes may offer a tool picker. Keep every tool.

2. **One line in your profile's `.env`:**

   ```
   RDY_ACTOR=agent:hermes
   ```

3. **RDY_ACTOR in `terminal.env_passthrough`** in your profile's `config.yaml`:

   ```yaml
   terminal:
     env_passthrough:
       - RDY_ACTOR
   ```

Then type `/reload-mcp` in a session, or start a new one, and run
`hermes rdy doctor`:

```
rdy for Hermes: doctor

  ok       rdy 0.41.0 found (needs 0.41.0 or newer)
  ok       rdy MCP server entry
  ok       RDY_ACTOR=agent:hermes on the rdy MCP server
  ok       --project '${workspaceFolder}' kept in the server's arguments
  ok       RDY_ACTOR=agent:hermes in this profile's environment (.env)
  ok       RDY_ACTOR in terminal.env_passthrough
  ok       approval guard loaded

All set. The agent can use rdy; only you approve.
```

**Why steps 2 and 3 matter.** The MCP entry's `env` reaches only the MCP
server. Steps 2 and 3 give the agent's terminal and code runs the same agent
name. Without them, an rdy command the agent runs in its terminal counts as
yours.

## First run

1. Open Hermes in your project folder and ask it to start with rdy.
2. The agent loads `rdy:start` and runs `hermes rdy doctor`.
3. It asks before `rdy init` makes an rdy project, then asks you to type
   `/reload-mcp`.
4. It asks before `rdy setup` adds a three-line note at the top of `CLAUDE.md` and
   `AGENTS.md`. The note tells agents to call `rdy_instructions`.
5. It drafts a first plan from your topic and proposes it.

You end with an rdy project, a first proposal, and the command to approve it.

## Day to day

The agent loads `rdy:loop`. It checks the setup, reads and briefs, writes,
clears tensions and suspects, and proposes. Then it shows you the proposal and
the command to type in your own terminal:

```
rdy approve P-<id>@<n>
```

## How approval works

Only a person approves, lands or tags in rdy. Three stops make that hold:

1. **The guard blocks the rdy tools by name:** `rdy_land`, `rdy_tag`,
   `rdy_answer`, `rdy_sign`, `rdy_publish`, `rdy_redact`, `rdy_dispute`,
   `rdy_resolve`, `rdy_auth`, `rdy_key_bind`, `rdy_key_retire` and
   `rdy_key_revoke`, whatever you named the MCP server.
2. **The guard reads commands and code the agent runs** (the terminal, code
   execution, process tools). There it blocks rdy commands for those acts, the
   relay flags `--relayed-by` and `--evidence`, any `RDY_ACTOR` other than
   `agent:hermes`, and an emptied environment (`env -i` and the like) next to an
   rdy command.
3. **rdy itself** refuses a bare approve, land, tag or answer from an agent,
   because the agent carries `RDY_ACTOR=agent:hermes`.

**Relays are off here.** rdy's own docs describe relays, where an agent passes on
your approval with `--relayed-by` and `--evidence`, or through `rdy_answer` and
`rdy_resolve`. Hermes can skip its own approval prompts (YOLO mode, approvals
off, cron and single-query runs), so a relay could not be trusted. The guard
blocks all of them. You approve by typing the command yourself.

These pass: `--help` on any command, `rdy dispute list`, `rdy tags`,
`rdy publication check`, `rdy auth state`, `rdy auth installs` and
`rdy key show`. `rdy auth token` is always blocked, because it prints hub access.

If you use Hermes only through a chat app (Discord, Telegram and the like), you
cannot approve from the chat. Approve in a terminal.

## Honest limits

- The guard reads the text of commands and code the agent runs. It cannot follow
  a command the agent encodes on purpose, or writes to a file and then runs with
  `bash <file>`. The same holds for a script that a no-agent cron job runs, and
  for keys typed into a desktop terminal through computer use. rdy still refuses
  a bare approve there; a relay there is not stopped. Your own typed approve is
  the real stop: read what you approve.
- The guard never reads file writes, so writing a plan or a README that mentions
  these commands is fine.
- It blocks a few harmless commands that only mention a relay flag, such as
  `grep -- --evidence`, and an `env -i` command that mentions a word like `key`.
- The agent's terminal can rewrite the profile's `.env` or `config.yaml`. That
  change takes effect in the next session. `rdy:loop` runs `hermes rdy doctor`
  at the start of every session and stops when an RDY_ACTOR line is missing.
- The guard sees a tool call's original arguments. Another plugin's `modify`
  changes are merged in after it looks.

## What it runs on your machine

- The local rdy program only: `hermes rdy doctor` runs `rdy --version`.
- The guard reads each tool call's arguments in memory and keeps nothing.
- No network calls, no stored credentials, no state, no telemetry, no
  background process of its own. The rdy MCP server is started by Hermes from
  your own config.
- Doctor reads your Hermes config and the environment Hermes loaded. It never
  opens your `.env` file and never prints a setting's value.

## Settings

One setting, `rdy_path` (default `rdy`): the rdy program to check and guard.
Set it in the Desktop's plugin settings, or in `config.yaml`:

```yaml
plugins:
  entries:
    rdy:
      settings:
        rdy_path: /opt/rdy/bin/rdy
```

If you set it, use the same path in the `hermes mcp add` line.

## Remove it

```
hermes plugins disable rdy
hermes plugins remove rdy
hermes mcp remove rdy
```

Then delete the `RDY_ACTOR` lines from your profile's `.env` and
`terminal.env_passthrough`.

## License

MIT. See [LICENSE](LICENSE).
