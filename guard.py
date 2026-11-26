"""rdy approval guard for Hermes Agent (a pre_tool_call hook).

Only a person approves, lands, tags or answers in rdy. This hook stops an agent
from doing any of those, in every Hermes approval mode. It only ever blocks or
stays silent: it never asks, never allows on its own and never changes a call,
because Hermes skips its own approval gate in YOLO mode, with approvals off,
in cron and single-query runs and after an "always" pick.

What it reads:
  - Every tool call's name. The rdy MCP tools for person-only acts are blocked
    by name, whatever the MCP server is called.
  - The text of tools that run something: the terminal, code execution,
    process and browser-exec tools, and any argument named command, cmd, code
    or script. File tools and rdy's own MCP tools are never judged by text, so
    writing a plan or a README that mentions these commands is fine.

In that text it blocks:
  - an rdy command for approve, land, tag, answer, sign, publish, redact,
    dispute, resolve, auth, or key bind, retire or revoke;
  - the relay flags --relayed-by and --evidence, and the names of the rdy MCP
    tools above (a relay sent to rdy's server by hand);
  - any mention of RDY_ACTOR except the exact assignment RDY_ACTOR=agent:hermes
    and plain reads (an allowlist: the shell has too many ways to change it);
  - an emptied environment (env -i and the like) next to an rdy token, because
    rdy acts as the person when RDY_ACTOR is missing.

Limits: a text guard cannot follow a command the agent encodes on purpose, or
writes to a file and then runs. rdy's own stop (RDY_ACTOR=agent:hermes) still
refuses a bare approve there; the person's own typed approve is the real stop.

The guard keeps nothing and does no input or output. Standard library only.
"""

from __future__ import annotations

import re
from typing import Any, Iterator, Optional

__all__ = ["check", "set_program", "PERSON_ONLY_TOOLS", "RUNNING_TOOLS", "RUNNING_ARGS", "NAME_ONLY_TOOLS"]

AGENT_ACTOR = "agent:hermes"

# rdy MCP tools that only a person may use. Hermes names an MCP tool
# mcp__<server>__<tool>, so only the part after the last "__" is compared.
PERSON_ONLY_TOOLS = frozenset({
    "rdy_land", "rdy_tag", "rdy_answer", "rdy_sign", "rdy_publish", "rdy_redact",
    "rdy_dispute", "rdy_resolve", "rdy_auth", "rdy_key_bind", "rdy_key_retire",
    "rdy_key_revoke",
})

# Hermes 0.22 tools that run something: all of their arguments are read.
RUNNING_TOOLS = frozenset({"terminal", "execute_code", "process_manage", "browser_exec"})

# On any other tool, these argument names hold something to run.
RUNNING_ARGS = frozenset({"command", "cmd", "code", "script"})

# Tools judged by name only, never by their text: they write or store text,
# they do not run it.
NAME_ONLY_TOOLS = frozenset({
    "read_file", "write_file", "patch", "search_files", "memory", "todo_list",
    "skill_manage", "skill_view", "skills_list", "delegate_task", "cronjob_manage",
})

# rdy verbs a person runs. dispute, auth and key also have read-only subcommands.
_PERSON_VERBS = frozenset({
    "approve", "land", "tag", "answer", "sign", "publish", "redact", "dispute",
    "resolve", "auth", "key",
})
_KEY_WRITES = frozenset({"bind", "retire", "revoke"})
_AUTH_READS = frozenset({"state", "installs"})
_HELP = frozenset({"--help", "-h"})

_MSG_PERSON = (
    "rdy: blocked. Only a person approves, lands, tags or answers in rdy. "
    "Relays are off in this plugin: --relayed-by, --evidence, rdy_answer and "
    "rdy_resolve are blocked here, even though rdy's own instructions describe "
    "them. Show the person the proposal and ask them to type the command in "
    "their own terminal, for example: rdy approve P-<id>@<n>"
)
_MSG_AUTH = (
    "rdy: blocked. Hub sign-in, sign-out and auth token are for the person only "
    "(auth token prints hub access). Ask the person to run it in their own "
    "terminal. rdy auth state and rdy auth installs are allowed."
)
_MSG_ACTOR = (
    "rdy: blocked. In this plugin the agent runs rdy as agent:hermes. "
    "RDY_ACTOR may be set only to agent:hermes, never to another value or cleared. "
    "If the person wants to act themselves, they run rdy in their own terminal."
)
_MSG_EMPTY_ENV = (
    "rdy: blocked. This runs rdy with an emptied or replaced environment, so rdy "
    "would lose RDY_ACTOR=agent:hermes and act as the person. Keep the "
    "environment. Approvals are the person's: ask them to type "
    "rdy approve P-<id>@<n> in their own terminal."
)

# The rdy program name to guard besides rdy itself (the rdy_path setting).
_extra_program: Optional[str] = None


def set_program(path: Optional[str]) -> None:
    """Also guard the program named in the rdy_path setting (its base name)."""
    global _extra_program
    base = _program_base(path or "")
    _extra_program = base if base and base != "rdy" else None


def check(tool_name: str = "", args: Any = None, **kwargs: Any) -> Optional[dict]:
    """pre_tool_call hook: a block directive, or None to stay silent."""
    name = str(tool_name or "").strip().lower()

    base = name.rsplit("__", 1)[-1]
    if base in PERSON_ONLY_TOOLS:
        return _block(_MSG_AUTH if base == "rdy_auth" else _MSG_PERSON)

    text = _running_text(name, args)
    if not text:
        return None
    for variant in _variants(text):
        message = _check_text(variant)
        if message:
            return _block(message)
    return None


def _block(message: str) -> dict:
    return {"action": "block", "message": message}


# --- what to read ---------------------------------------------------------

_RDY_TOOL_NAME = re.compile(r"(?:^|__)rdy_[a-z0-9_]+$")


def _running_text(name: str, args: Any) -> str:
    if name in RUNNING_TOOLS:
        return "\n".join(_strings(args))
    if name in NAME_ONLY_TOOLS or _RDY_TOOL_NAME.search(name):
        return ""
    return "\n".join(_strings_under(args, RUNNING_ARGS))


def _strings(value: Any, depth: int = 0) -> Iterator[str]:
    if depth > 32:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item, depth + 1)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item, depth + 1)


def _strings_under(value: Any, keys: frozenset, depth: int = 0) -> Iterator[str]:
    if depth > 32:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and key.lower() in keys:
                yield from _strings(item, depth + 1)
            else:
                yield from _strings_under(item, keys, depth + 1)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings_under(item, keys, depth + 1)


def _variants(text: str) -> list:
    """The text as the shell would read it, with quote marks dropped: as it
    is (a path like C:\\tools\\rdy.exe), with escaped newlines and tabs read
    as real ones (code that builds a command string), and each of those with
    backslashes gone, so rdy a\\pprove reads as rdy approve."""
    plain = text.replace("\r", "\n").replace("\t", " ").replace('"', "").replace("'", "")
    escaped = re.sub(r"\\[nr]", "\n", plain).replace("\\t", " ")
    out = []
    for variant in (plain, escaped, plain.replace("\\", ""), escaped.replace("\\", "")):
        if variant not in out:
            out.append(variant)
    return out


# --- the text rules ---------------------------------------------------------

_RELAY_FLAG = re.compile(r"--relayed-by|--evidence", re.I)
_PERSON_TOOL_WORD = re.compile(
    r"(?<![a-z0-9])rdy_(?:land|tag|answer|sign|publish|redact|dispute|resolve|auth"
    r"|key_bind|key_retire|key_revoke)(?![a-z0-9_])",
    re.I,
)


def _check_text(text: str) -> Optional[str]:
    if _RELAY_FLAG.search(text) or _PERSON_TOOL_WORD.search(text):
        return _MSG_PERSON
    message = _check_commands(text)
    if message:
        return message
    if _actor_changed(text):
        return _MSG_ACTOR
    if _environment_emptied(text):
        return _MSG_EMPTY_ENV
    return None


# Commands: rdy, a path ending in rdy or rdy-<version>, with an optional
# Windows ending, then global options, then a verb.
_NL = "\n"
_SEP = ";"
_TOKEN = re.compile(r"\n|[;&|]+|[^\s,\[\](){}`<>$;&|]+")
_PROGRAM = re.compile(r"^rdy(?:-[a-z0-9._]+)?$", re.I)
_WINDOWS_END = re.compile(r"\.(?:exe|cmd|bat|com)$", re.I)


def _program_base(token: str) -> str:
    base = re.split(r"[/\\]", token)[-1]
    return _WINDOWS_END.sub("", base).lower()


def _is_program(token: str) -> bool:
    base = _program_base(token)
    if not base:
        return False
    return bool(_PROGRAM.match(base)) or (_extra_program is not None and base == _extra_program)


def _tokens(text: str) -> list:
    out = []
    for match in _TOKEN.finditer(text):
        tok = match.group(0)
        if tok == "\n":
            out.append(_NL)
        elif tok[0] in ";&|":
            out.append(_SEP)
        else:
            out.append(tok)
    return out


def _check_commands(text: str) -> Optional[str]:
    tokens = _tokens(text)
    count = len(tokens)
    for i, tok in enumerate(tokens):
        if tok in (_NL, _SEP) or not _is_program(tok):
            continue
        # Walk past global options (and an option's value) to the verb.
        j = i + 1
        after_option = False
        verb = None
        while j < count:
            t = tokens[j]
            if t == _SEP:
                break
            if t == _NL:
                j += 1
                continue
            if t.startswith("-"):
                after_option = "=" not in t
                j += 1
                continue
            if after_option and t.lower() not in _PERSON_VERBS:
                after_option = False
                j += 1
                continue
            verb = t.lower()
            break
        if verb not in _PERSON_VERBS:
            continue
        rest = tokens[j + 1:]
        if _asks_for_help(rest):
            continue
        sub = _subcommand(rest)
        if verb == "dispute" and sub == "list":
            continue
        if verb == "key" and sub not in _KEY_WRITES:
            continue
        if verb == "auth":
            if sub in _AUTH_READS:
                continue
            return _MSG_AUTH
        return _MSG_PERSON
    return None


def _asks_for_help(rest: list) -> bool:
    """--help or -h in this one command, on its own line, before any comment."""
    for t in rest:
        if t in (_NL, _SEP) or t.startswith("#"):
            return False
        if t in _HELP:
            return True
    return False


def _subcommand(rest: list) -> Optional[str]:
    for t in rest:
        if t == _SEP:
            return None
        if t == _NL or t.startswith("-") or t.startswith("#"):
            continue
        return t.lower()
    return None



# RDY_ACTOR: an allowlist. In running text every mention of RDY_ACTOR is
# blocked, except the exact assignment RDY_ACTOR=agent:hermes and plain reads.
# The shell has many ways to change or drop a variable (unset -v, export -n,
# declare +x, read, printf -v, env --uns...), so naming the safe forms is
# safer than listing the unsafe ones.
_ACTOR = re.compile(r"RDY_ACTOR", re.I)
_ACTOR_EXACT_AFTER = re.compile(r"=agent:hermes(?=[\s;&|),]|$)")
_ACTOR_PARAM_READ_AFTER = re.compile(r"(?:\}|:?[-+])")
_ACTOR_PY_READ_BEFORE = re.compile(r"(?:os\.environ\.get|os\.getenv|\.get)\s*\(\s*$", re.I)
_ASSIGNMENT_TOKEN = re.compile(r"^[A-Za-z_]\w*=\S*$")
_ACTOR_PREFIX_WORDS = frozenset({"export", "env", "--env"})


def _actor_mention_allowed(text: str, start: int, end: int) -> bool:
    before = text[max(0, start - 80):start]
    after = text[end:end + 40]
    # $RDY_ACTOR and ${RDY_ACTOR}, ${RDY_ACTOR:-x}, ${RDY_ACTOR+x} (not := or =).
    if before.endswith("${"):
        return bool(_ACTOR_PARAM_READ_AFTER.match(after)) and not after.startswith(":=")
    if before.endswith("$"):
        return True
    if _ACTOR_PY_READ_BEFORE.search(before):
        return True
    seg_start = max(text.rfind(c, 0, start) for c in "\n;&|(`") + 1
    prefix_words = text[seg_start:start].split()
    line_end = text.find("\n", end)
    line = text[seg_start:line_end if line_end != -1 else len(text)]
    if prefix_words == ["printenv"]:
        return True
    # echo that only prints: no redirect and no pipe into another program.
    if prefix_words and prefix_words[0].lower() == "echo" and ">" not in line and "|" not in line:
        return True
    if not _ACTOR_EXACT_AFTER.match(after):
        return False
    if not prefix_words:
        return True
    last = prefix_words[-1]
    return last.lower() in _ACTOR_PREFIX_WORDS or bool(_ASSIGNMENT_TOKEN.match(last))


def _actor_changed(text: str) -> bool:
    for match in _ACTOR.finditer(text):
        start, end = match.span()
        if start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
            continue
        if end < len(text) and (text[end].isalnum() or text[end] == "_"):
            continue
        if not _actor_mention_allowed(text, start, end):
            return True
    return False


# An emptied or replaced environment, next to an rdy token.
_EMPTY_ENV = re.compile(
    r"(?:^|[^\w-])env\s+(?:-[a-z0-9]*i[a-z0-9]*|--ign(?!ore-s)[a-z-]*|-)(?=\s|$)"
    r"|environ\s*\.\s*clear\s*\("
    r"|\bexec\s+(?:-[a-z]+\s+)*-[a-z]*c[a-z]*(?=\s|$)"
    r"|\bsetpriv\b[^\n;]*--reset-env",
    re.I | re.M,
)
_ENV_ARG = re.compile(r"(?<![\w.-])env\s*(?:=(?!=)|:)[ \t]*", re.I)
# Python calls that take the environment as a positional argument: name -> index
# (-1 means the last argument).
_ENV_POSITIONAL = {
    "execve": 2, "execvpe": 2, "spawnve": 3, "spawnvpe": 3, "posix_spawn": 2,
    "posix_spawnp": 2, "execle": -1, "execlpe": -1, "spawnle": -1, "spawnlpe": -1,
}
_ENV_CALL = re.compile(r"\b(" + "|".join(_ENV_POSITIONAL) + r")\s*\(")
_FRESH_SESSION = re.compile(
    r"(?:^|[\s;&|(`])(?:sudo|su|doas|runuser|ssh|systemd-run)(?=\s|$)", re.I | re.M
)
_RDY_WORD = re.compile(r"(?<![\w.-])rdy(?:-[a-z0-9._]+)?(?![\w])", re.I)
_PROPOSAL_REF = re.compile(r"\bP-[a-z0-9]+@\d+\b", re.I)
_VERB_WORD = re.compile(
    r"\b(?:approve|land|tag|answer|sign|publish|redact|dispute|resolve|auth|key)\b", re.I
)


def _call_arguments(text: str, open_paren: int) -> list:
    """Top-level arguments of a call, from the index just after its "("."""
    args, depth, current = [], 0, []
    for ch in text[open_paren:open_paren + 2000]:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                args.append("".join(current))
                return args
            depth -= 1
        elif ch == "," and depth == 0:
            args.append("".join(current))
            current = []
            continue
        current.append(ch)
    args.append("".join(current))
    return args


def _carries_environ(expression: str) -> bool:
    expression = expression.strip()
    return (not expression or expression.startswith("None")
            or "environ" in expression or "process.env" in expression)


def _environment_emptied(text: str) -> bool:
    program = bool(_RDY_WORD.search(text)) or (
        _extra_program is not None
        and re.search(r"(?<![\w.-])" + re.escape(_extra_program) + r"(?![\w])", text, re.I)
        is not None
    )
    strong = program or bool(_PROPOSAL_REF.search(text))
    any_token = strong or bool(_VERB_WORD.search(text))
    if not any_token:
        return False
    if _EMPTY_ENV.search(text):
        return True
    for match in _ENV_ARG.finditer(text):
        expression = text[match.end():match.end() + 300].split("\n", 1)[0]
        if not _carries_environ(expression):
            return True
    for match in _ENV_CALL.finditer(text):
        args = _call_arguments(text, match.end())
        index = _ENV_POSITIONAL[match.group(1)]
        if index == -1 or len(args) > index:
            if not _carries_environ(args[index]):
                return True
    # A new login or another user's session starts without RDY_ACTOR: only
    # when the rdy program comes with a person verb or a proposal ref.
    act = bool(_PROPOSAL_REF.search(text) or _VERB_WORD.search(text))
    return program and act and bool(_FRESH_SESSION.search(text))
