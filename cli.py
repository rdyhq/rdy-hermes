"""hermes rdy doctor and hermes rdy setup.

doctor checks the setup and changes nothing. It prints ok or missing for each
line and never prints a setting's value, so the agent may run it too.
setup prints the lines a person adds by hand. It writes nothing.

Hermes imports, both on the public list that plugins validate checks:
hermes_cli.config (load_config) and hermes_constants (get_hermes_home,
profile_name_for_home). Catalog rule 11: a plugin never reads a .env file, so
doctor checks RDY_ACTOR in the environment Hermes loaded from the profile's .env.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional

RDY_FLOOR = (0, 41, 0)
AGENT_ACTOR = "agent:hermes"
WORKSPACE = "${workspaceFolder}"
_ENV_NAME = "RDY_ACTOR"


def setup_parser(parser: Any) -> None:
    subs = parser.add_subparsers(dest="rdy_command", metavar="{doctor,setup}")
    subs.add_parser("doctor", help="check the rdy setup (changes nothing, prints no values)")
    subs.add_parser("setup", help="print the lines that connect Hermes to rdy (writes nothing)")


def make_handler(program: Callable[[], str], guard_registered: Callable[[], bool]) -> Callable:
    def handler(args: Any = None, **_: Any) -> int:
        command = getattr(args, "rdy_command", None)
        if command == "doctor":
            code = print_lines(doctor_lines(gather_facts(program(), guard_registered())))
        elif command == "setup":
            code = print_lines(setup_lines(program(), _profile_name(), _hermes_home()))
        else:
            print("Usage: hermes rdy doctor | hermes rdy setup")
            code = 2
        if code:
            sys.exit(code)
        return code

    return handler


def print_lines(result: tuple) -> int:
    lines, code = result
    print("\n".join(lines))
    return code


# --- doctor -------------------------------------------------------------------


def gather_facts(program: str, guard_registered: bool) -> dict:
    """Everything doctor looks at, read once. No file is written."""
    from hermes_cli.config import load_config

    config = load_config() or {}
    return {
        "program_found": _which(program) is not None,
        "rdy_version": _rdy_version(program),
        "program": program,
        "config": config,
        "env_actor_ok": os.environ.get(_ENV_NAME) == AGENT_ACTOR,
        "guard_registered": guard_registered,
        "hermes_md": _hermes_md_hides_agents(Path.cwd()),
    }


def doctor_lines(facts: dict) -> tuple:
    """(lines, exit code). Pure: tests feed it made-up facts."""
    lines = ["rdy for Hermes: doctor", ""]
    missing = 0

    def row(ok: bool, text: str, fix: str = "") -> None:
        nonlocal missing
        lines.append(f"  {'ok' if ok else 'missing':<8} {text}")
        if not ok:
            missing += 1
            if fix:
                lines.append(f"  {'':<8} {fix}")

    if not facts.get("program_found"):
        row(False, "rdy program not found",
            "Install rdy from its official install page, then run hermes rdy doctor again.")
        lines += ["", "Stopped: nothing else can be checked without rdy."]
        return lines, 1

    floor = ".".join(str(n) for n in RDY_FLOOR)
    version = facts.get("rdy_version")
    if version is None:
        row(False, "rdy version unknown", f"This plugin needs rdy {floor} or newer.")
    elif version < RDY_FLOOR:
        found = ".".join(str(n) for n in version)
        row(False, f"rdy {found} found", f"This plugin needs rdy {floor} or newer. Update rdy.")
    else:
        row(True, f"rdy {'.'.join(str(n) for n in version)} found (needs {floor} or newer)")

    config = facts.get("config") or {}
    name, entry = find_server(config, facts.get("program") or "rdy")
    setup_fix = "Run hermes rdy setup and add the line it prints."
    if entry is None:
        row(False, "rdy MCP server entry", setup_fix)
    elif entry.get("enabled") is False:
        row(False, "rdy MCP server entry is turned off (enabled: false)",
            "Turn it on in config.yaml, or add it again with the line hermes rdy setup prints.")
    else:
        row(True, "rdy MCP server entry")

    env = (entry or {}).get("env") or {}
    row(isinstance(env, dict) and env.get(_ENV_NAME) == AGENT_ACTOR,
        "RDY_ACTOR=agent:hermes on the rdy MCP server", setup_fix)

    row(entry is not None and _keeps_workspace(entry.get("args")),
        f"--project '{WORKSPACE}' kept in the server's arguments", setup_fix)

    env_ok = bool(facts.get("env_actor_ok"))
    row(env_ok, "RDY_ACTOR=agent:hermes in this profile's environment (.env)",
        "Add the .env line that hermes rdy setup prints, then start a new session.")

    passthrough_ok = _ENV_NAME in _passthrough(config)
    row(passthrough_ok, "RDY_ACTOR in terminal.env_passthrough",
        "Add RDY_ACTOR to terminal.env_passthrough in config.yaml (hermes rdy setup shows how).")

    guard_ok = bool(facts.get("guard_registered")) and plugin_enabled(config)
    row(guard_ok, "approval guard loaded", "Run hermes plugins enable rdy, then start a new session.")

    if facts.get("hermes_md"):
        lines.append(f"  {'warn':<8} .hermes.md here hides AGENTS.md, so rdy's note there does not load")
        lines.append(f"  {'':<8} The rdy:start skill asks before adding rdy's note to .hermes.md too.")

    lines.append("")
    if missing == 0:
        lines.append("All set. The agent can use rdy; only you approve.")
        return lines, 0
    lines.append(f"{missing} to fix.")
    if not (env_ok and passthrough_ok):
        lines.append("Until both RDY_ACTOR lines are in place, rdy commands the agent runs "
                     "in its terminal count as yours.")
    return lines, 1


def find_server(config: dict, program: str = "rdy") -> tuple:
    """The rdy entry under mcp_servers: the one named rdy, else one that runs rdy mcp."""
    servers = config.get("mcp_servers")
    if not isinstance(servers, dict):
        return None, None
    entry = servers.get("rdy")
    if isinstance(entry, dict):
        return "rdy", entry
    wanted = {"rdy", _base(program)}
    for name, item in servers.items():
        if not isinstance(item, dict):
            continue
        args = item.get("args") or []
        if _base(str(item.get("command") or "")) in wanted and isinstance(args, list) and "mcp" in args:
            return name, item
    return None, None


def plugin_enabled(config: dict) -> bool:
    plugins = config.get("plugins")
    if not isinstance(plugins, dict):
        return False
    enabled = plugins.get("enabled") or []
    disabled = plugins.get("disabled") or []
    return isinstance(enabled, list) and "rdy" in enabled and not (
        isinstance(disabled, list) and "rdy" in disabled)


def _keeps_workspace(args: Any) -> bool:
    if not isinstance(args, list):
        return False
    items = [str(a) for a in args]
    for i, item in enumerate(items):
        if item == "--project" and i + 1 < len(items) and items[i + 1] == WORKSPACE:
            return True
        if item == f"--project={WORKSPACE}":
            return True
    return False


def _passthrough(config: dict) -> list:
    terminal = config.get("terminal")
    if not isinstance(terminal, dict):
        return []
    value = terminal.get("env_passthrough")
    if isinstance(value, str):
        return [part.strip() for part in value.split(",")]
    return [str(v) for v in value] if isinstance(value, list) else []


def _base(program: str) -> str:
    base = re.split(r"[/\\]", program or "")[-1]
    return re.sub(r"\.(?:exe|cmd|bat|com)$", "", base, flags=re.I).lower()


def _which(program: str) -> Optional[str]:
    if not program:
        return None
    if os.sep in program or "/" in program:
        return program if os.access(program, os.X_OK) else None
    return shutil.which(program)


def _rdy_version(program: str) -> Optional[tuple]:
    path = _which(program)
    if path is None:
        return None
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", out.stdout or "")
    return tuple(int(n) for n in match.groups()) if match else None


def _hermes_md_hides_agents(start: Path) -> bool:
    """A .hermes.md in this folder or above it, up to the repo root."""
    folder = start
    for _ in range(64):
        if (folder / ".hermes.md").is_file():
            return True
        if (folder / ".git").exists() or folder.parent == folder:
            return False
        folder = folder.parent
    return False


# --- setup --------------------------------------------------------------------


def setup_lines(program: str, profile: Optional[str], home: Optional[Path]) -> tuple:
    """(lines, 0). Pure: tests feed it made-up values."""
    hermes = "hermes" if not profile or profile == "default" else f"hermes -p {shlex.quote(profile)}"
    command = shlex.quote(program or "rdy")
    env_file = f" ({home / '.env'})" if home else ""
    config_file = f" ({home / 'config.yaml'})" if home else ""
    lines = [
        "rdy for Hermes: setup",
        "This writes nothing. Do these three steps yourself, then check with hermes rdy doctor.",
        "",
        "1. Add rdy's MCP server. Run this line exactly as it is:",
        "",
        f"   {hermes} mcp add rdy --command {command} --env RDY_ACTOR=agent:hermes "
        f"--args mcp --project '{WORKSPACE}'",
        "",
        "   It starts rdy once to list its tools and may offer a tool picker. Keep every tool.",
        "",
        f"2. Add this line to this profile's .env file{env_file}:",
        "",
        "   RDY_ACTOR=agent:hermes",
        "",
        f"3. Add RDY_ACTOR to terminal.env_passthrough in this profile's config.yaml{config_file}:",
        "",
        "   terminal:",
        "     env_passthrough:",
        "       - RDY_ACTOR",
        "",
        "   Keep any names already in that list.",
        "",
        f"Then type /reload-mcp in a session, or start a new one, and run: {hermes} rdy doctor",
        "",
        "Why steps 2 and 3: they give the agent's terminal and code runs the same",
        "agent name as the MCP server, so rdy refuses an approval the agent tries itself.",
    ]
    return lines, 0


def _hermes_home() -> Optional[Path]:
    try:
        from hermes_constants import get_hermes_home
        return Path(get_hermes_home())
    except Exception:
        return None


def _profile_name() -> Optional[str]:
    try:
        from hermes_constants import get_hermes_home, profile_name_for_home
        return profile_name_for_home(get_hermes_home())
    except Exception:
        return None
