"""hermes rdy doctor and setup, fed made-up facts. No Hermes needed."""

import shutil
import subprocess
from pathlib import Path

import pytest

import cli

GOOD_CONFIG = {
    "mcp_servers": {
        "rdy": {
            "command": "rdy",
            "args": ["mcp", "--project", "${workspaceFolder}"],
            "env": {"RDY_ACTOR": "agent:hermes"},
        }
    },
    "terminal": {"env_passthrough": ["RDY_ACTOR"]},
    "plugins": {"enabled": ["rdy"]},
}


def facts(**changes):
    base = {
        "program_found": True,
        "rdy_version": (0, 41, 0),
        "program": "rdy",
        "config": GOOD_CONFIG,
        "env_actor_ok": True,
        "guard_registered": True,
        "hermes_md": False,
    }
    base.update(changes)
    return base


def test_doctor_all_ok():
    lines, code = cli.doctor_lines(facts())
    assert code == 0
    assert not any(line.strip().startswith("missing") for line in lines)
    assert sum(1 for line in lines if line.strip().startswith("ok")) == 7
    assert lines[-1].startswith("All set.")


def test_doctor_stops_when_rdy_is_missing():
    lines, code = cli.doctor_lines(facts(program_found=False, rdy_version=None))
    assert code == 1
    text = "\n".join(lines)
    assert "rdy program not found" in text and "official install page" in text
    assert "MCP server" not in text


def test_doctor_names_an_old_rdy():
    lines, code = cli.doctor_lines(facts(rdy_version=(0, 40, 2)))
    assert code == 1
    assert any("rdy 0.40.2 found" in line for line in lines)
    assert any("0.41.0 or newer" in line for line in lines)


def test_doctor_without_server_entry():
    config = dict(GOOD_CONFIG, mcp_servers={})
    lines, code = cli.doctor_lines(facts(config=config))
    assert code == 1
    text = "\n".join(lines)
    assert "missing  rdy MCP server entry" in text
    assert "missing  RDY_ACTOR=agent:hermes on the rdy MCP server" in text


def test_doctor_server_turned_off():
    server = dict(GOOD_CONFIG["mcp_servers"]["rdy"], enabled=False)
    config = dict(GOOD_CONFIG, mcp_servers={"rdy": server})
    lines, code = cli.doctor_lines(facts(config=config))
    assert code == 1 and any("turned off" in line for line in lines)


def test_doctor_server_with_expanded_workspace():
    server = dict(GOOD_CONFIG["mcp_servers"]["rdy"], args=["mcp", "--project", ""])
    config = dict(GOOD_CONFIG, mcp_servers={"rdy": server})
    lines, code = cli.doctor_lines(facts(config=config))
    assert code == 1
    assert any(line.strip().startswith("missing") and "workspaceFolder" in line for line in lines)


def test_doctor_server_with_other_actor():
    server = dict(GOOD_CONFIG["mcp_servers"]["rdy"], env={"RDY_ACTOR": "human:x"})
    config = dict(GOOD_CONFIG, mcp_servers={"rdy": server})
    lines, code = cli.doctor_lines(facts(config=config))
    assert code == 1
    assert "human:x" not in "\n".join(lines)  # never prints a value


def test_doctor_finds_a_server_under_another_name():
    config = dict(GOOD_CONFIG, mcp_servers={"plans": GOOD_CONFIG["mcp_servers"]["rdy"]})
    _, code = cli.doctor_lines(facts(config=config))
    assert code == 0


def test_doctor_env_and_passthrough_missing():
    config = dict(GOOD_CONFIG, terminal={})
    lines, code = cli.doctor_lines(facts(config=config, env_actor_ok=False))
    text = "\n".join(lines)
    assert code == 1
    assert "missing  RDY_ACTOR=agent:hermes in this profile's environment (.env)" in text
    assert "missing  RDY_ACTOR in terminal.env_passthrough" in text
    assert "count as yours" in text


def test_doctor_passthrough_as_text():
    config = dict(GOOD_CONFIG, terminal={"env_passthrough": "LANG, RDY_ACTOR"})
    _, code = cli.doctor_lines(facts(config=config))
    assert code == 0


def test_doctor_guard_not_loaded():
    config = dict(GOOD_CONFIG, plugins={"enabled": ["rdy"], "disabled": ["rdy"]})
    lines, code = cli.doctor_lines(facts(config=config))
    assert code == 1 and any("hermes plugins enable rdy" in line for line in lines)


def test_doctor_warns_about_hermes_md():
    lines, code = cli.doctor_lines(facts(hermes_md=True))
    assert code == 0
    assert any(line.strip().startswith("warn") and ".hermes.md" in line for line in lines)


def test_hermes_md_search(tmp_path):
    project = tmp_path / "garden"
    (project / ".git").mkdir(parents=True)
    (project / "beds").mkdir()
    assert cli._hermes_md_hides_agents(project / "beds") is False
    (project / ".hermes.md").write_text("garden rules\n")
    assert cli._hermes_md_hides_agents(project / "beds") is True


EXPECTED_LINE = ("hermes mcp add rdy --command rdy --env RDY_ACTOR=agent:hermes "
                 "--args mcp --project '${workspaceFolder}'")


def test_setup_prints_the_exact_line():
    lines, code = cli.setup_lines("rdy", None, Path("/tmp/garden-home"))
    assert code == 0
    assert f"   {EXPECTED_LINE}" in lines
    assert "   RDY_ACTOR=agent:hermes" in lines
    assert "       - RDY_ACTOR" in lines
    line = next(l for l in lines if "mcp add" in l)
    assert line.index("--env") < line.index("--args")


def test_setup_names_a_profile_and_a_custom_program():
    lines, _ = cli.setup_lines("/opt/tools/my rdy", "garden", None)
    line = next(l for l in lines if "mcp add" in l)
    assert line.strip().startswith("hermes -p garden mcp add rdy --command '/opt/tools/my rdy' ")
    assert lines[-4].endswith("hermes -p garden rdy doctor")


@pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")
def test_printed_line_keeps_the_placeholder_in_a_shell():
    lines, _ = cli.setup_lines("rdy", None, None)
    line = next(l for l in lines if "mcp add" in l).strip()
    script = "hermes() { printf '%s\\n' \"$@\"; }\n" + line + "\n"
    out = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True).stdout
    args = out.splitlines()
    assert args[-3:] == ["mcp", "--project", "${workspaceFolder}"]
    assert args.index("--env") < args.index("--args")
    assert args[args.index("--env") + 1] == "RDY_ACTOR=agent:hermes"


def test_handler_without_subcommand_exits_2(capsys):
    handler = cli.make_handler(lambda: "rdy", lambda: True)
    with pytest.raises(SystemExit) as stop:
        handler(type("Args", (), {"rdy_command": None})())
    assert stop.value.code == 2
    assert "hermes rdy doctor" in capsys.readouterr().out
