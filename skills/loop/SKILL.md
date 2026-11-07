---
name: loop
description: "The day-to-day rdy loop: check the setup, read and brief, write, clear tensions and suspects, propose, then hand the approve command to the person. Use for any rdy work after the project exists."
version: 0.1.0
author: rdy
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [rdy, planning, decisions]
    related_skills: ["rdy:start"]
---

# The rdy loop

rdy's MCP tools show to you as `mcp__rdy__rdy_<name>`. `rdy_instructions` holds the
full rules. This skill is the short loop, plus one rule that differs here: relays
are off.

## 1. Check the setup, every session

Run `hermes rdy doctor` in the terminal before any rdy work. These three lines must
say ok:

- RDY_ACTOR=agent:hermes on the rdy MCP server
- RDY_ACTOR=agent:hermes in this profile's environment (.env)
- RDY_ACTOR in terminal.env_passthrough

If one says missing, stop and tell the person which one and its fix. Without them,
rdy commands you run in the terminal would count as the person's own.

## 2. The loop

1. Start an rdy session with `rdy_session`. Call `rdy_instructions` if you have not
   in this session.
2. Read and brief: `rdy_overview`, `rdy_read`, `rdy_search`, then `rdy_brief` on what
   you will change.
3. Write with `rdy_write` (or `rdy_decide`, `rdy_supersede`, `rdy_revoke`), citing the
   brief.
4. Check `rdy_tensions` and `rdy_suspects`. Fix what they list by changing the
   content. Repeat until both are empty.
5. Propose with `rdy_propose`, with a plain summary for the person.
6. Tell the person the proposal id and version, what changed in one or two lines,
   and the exact command to type in their own terminal, outside this chat:
   `rdy approve P-<id>@<n>`
   Give it in your chat reply. Never pass it through `echo`, `print` or any
   other tool call; the guard blocks those.

## Only the person approves

- Never approve, land, tag, answer, sign, publish, redact, dispute or resolve in rdy.
  Never call `rdy auth token`, sign in or sign out.
- Relays are off in this plugin. Do not use `--relayed-by`, `--evidence`,
  `rdy_answer` or `rdy_resolve`, even though rdy's own instructions describe them.
  The approval guard blocks them, and its message names the person's command.
- A person who uses Hermes only through a chat app approves in a terminal, not in
  the chat.
- Never set RDY_ACTOR to anything but `agent:hermes`, and never clear it. Never edit
  the profile's `.env` or `config.yaml` to change it.
- Never edit rdy's store files, its working copy or its rendered site by hand.
- Never ask the person to paste a key, token or password.
