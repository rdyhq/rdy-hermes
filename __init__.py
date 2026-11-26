"""rdy for Hermes Agent: an approval guard, two skills and the hermes rdy command.

The agent reaches rdy through rdy's own MCP server, which the person adds with
the line hermes rdy setup prints. This plugin adds no tools of its own.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import cli, guard

_SKILLS = Path(__file__).resolve().parent / "skills"
_state = {"guard_registered": False, "program": "rdy"}


def _pre_tool_call(tool_name: str = "", args: Any = None, **kwargs: Any) -> Any:
    return guard.check(tool_name, args, **kwargs)


def register(ctx: Any) -> None:
    program = ctx.get_config("rdy_path", "rdy") or "rdy"
    _state["program"] = str(program)
    guard.set_program(_state["program"])

    ctx.register_hook("pre_tool_call", _pre_tool_call)
    _state["guard_registered"] = True

    for folder in sorted(_SKILLS.iterdir()):
        skill = folder / "SKILL.md"
        if folder.is_dir() and skill.is_file():
            ctx.register_skill(folder.name, skill)

    ctx.register_cli_command(
        name="rdy",
        help="check and set up rdy for Hermes",
        description="hermes rdy doctor checks the setup; hermes rdy setup prints the lines to add.",
        setup_fn=cli.setup_parser,
        handler_fn=cli.make_handler(lambda: _state["program"], lambda: _state["guard_registered"]),
    )
