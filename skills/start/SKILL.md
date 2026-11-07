---
name: start
description: "Start using rdy in this project: check the setup, make an rdy project if there is none, add rdy's note for agents, and draft a first plan. Use when the person asks to start with rdy."
version: 0.1.0
author: rdy
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [rdy, planning, decisions]
    related_skills: ["rdy:loop"]
---

# Start with rdy

rdy keeps what a team intends and decided. You read and write it through rdy's
MCP tools (shown to you as `mcp__rdy__rdy_<name>`). Only the person approves.

## Steps

1. Check the setup. Run `hermes rdy doctor` in the terminal.
   - If it says the rdy program is not found, stop. Tell the person to install rdy
     from its official install page. Do nothing else.
   - If any other line says missing, show the person that line and its fix, then stop.
2. Check for a project. Run `rdy status` in the terminal, in the project folder.
   - If there is no rdy project, ask: "Make an rdy project in this folder (rdy init)?"
     Run `rdy init` only after a yes.
   - Then ask the person to type `/reload-mcp`, so the rdy server opens the new project.
3. Add rdy's note for agents. Ask: "rdy setup adds a three-line note at the top of
   CLAUDE.md and AGENTS.md that tells agents to call rdy_instructions. Add it?"
   Run `rdy setup` only after a yes.
   - If doctor warned about `.hermes.md`, Hermes loads that file instead of AGENTS.md.
     Ask before adding the same three lines at the top of `.hermes.md` too.
4. Call `rdy_instructions` and follow its rules, with the one exception below.
5. Ask the person what the plan is about. Draft a first plan from their own topic,
   then follow `rdy:loop` from its step 2 to a proposal.

## Only the person approves

- Never approve, land, tag, answer, sign, publish, redact, dispute or resolve in rdy.
  Never call `rdy auth token`, sign in or sign out.
- Relays are off in this plugin. Do not use `--relayed-by`, `--evidence`,
  `rdy_answer` or `rdy_resolve`, even though rdy's own instructions describe them.
  The approval guard blocks them.
- When a proposal is ready, show the person its id and version, and the exact command
  to type in their own terminal: `rdy approve P-<id>@<n>`.
- Never set RDY_ACTOR to anything but `agent:hermes`, and never clear it.
- Never edit rdy's store files, its working copy or its rendered site by hand.
- Never ask the person to paste a key, token or password.
