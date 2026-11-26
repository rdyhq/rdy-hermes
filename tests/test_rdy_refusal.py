"""rdy's own stop, proved against a real rdy in a made-up garden project.

These tests need the rdy program: on PATH, or named by RDY_BIN. They are
skipped without it. They write only inside pytest's temporary folder.

What they prove:
  - Under RDY_ACTOR=agent:hermes, rdy refuses a bare approve, with --no-daemon
    and through a daemon the person started, and with the name hidden.
  - Under the same value rdy ACCEPTS a relayed approve, and with an emptied
    environment it approves as the person. Both are why the guard must block
    the relay flags and an emptied environment.
"""

import json
import os
import re
import shutil
import subprocess

import pytest

import guard

RDY = os.environ.get("RDY_BIN") or shutil.which("rdy")
pytestmark = pytest.mark.skipif(
    not RDY or not shutil.which("bash"), reason="needs the rdy program (PATH or RDY_BIN) and bash")

AGENT = {"RDY_ACTOR": "agent:hermes"}


def run(args, project, env_extra=None, person=False):
    env = {k: v for k, v in os.environ.items() if k != "RDY_ACTOR"}
    if not person:
        env.update(AGENT)
    env.update(env_extra or {})
    return subprocess.run([RDY, *args], cwd=project, env=env, capture_output=True, text=True, timeout=60)


def bash(script, project, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k != "RDY_ACTOR"}
    env.update(AGENT)
    env["RDY"] = RDY
    env.update(env_extra or {})
    return subprocess.run(["bash", "-c", script], cwd=project, env=env,
                          capture_output=True, text=True, timeout=60)


def new_proposal(project, title):
    """A made-up proposal, written and proposed by the person."""
    nd = {"RDY_NO_DAEMON": "1"}
    assert run(["new", "doc", re.sub(r"\W+", "-", title.lower()), "--title", title],
               project, nd, person=True).returncode == 0
    out = run(["propose", "--title", title, "--summary", "A made-up plan", "--json"],
              project, nd, person=True)
    assert out.returncode == 0, out.stderr
    ref = re.search(r"P-[0-9a-f]+@\d+", out.stdout)
    assert ref, out.stdout
    return ref.group(0)


def landed(project):
    out = run(["status"], project, {"RDY_NO_DAEMON": "1"}, person=True)
    match = re.search(r"\((\d+) landings?", out.stdout)
    return int(match.group(1)) if match else 0


def last_landing(project):
    out = run(["log", "--json"], project, {"RDY_NO_DAEMON": "1"}, person=True)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)[-1]


@pytest.fixture
def project(tmp_path):
    folder = tmp_path / "garden-planner"
    folder.mkdir()
    out = run(["init"], folder, {"RDY_NO_DAEMON": "1"}, person=True)
    assert out.returncode == 0, out.stderr
    yield folder
    run(["serve", "--stop"], folder, person=True)


def test_rdy_refuses_bare_agent_approve_without_daemon(project):
    ref = new_proposal(project, "Garden beds")
    out = run(["approve", ref, "--no-daemon"], project)
    assert out.returncode != 0
    assert "E_PERMISSION" in out.stderr
    assert landed(project) == 0


def test_rdy_refuses_bare_agent_approve_through_a_persons_daemon(project):
    ref = new_proposal(project, "Garden paths")
    try:
        # Any command the person runs starts the project's daemon as the person.
        status = run(["status"], project, person=True)
        assert "daemon: none" not in status.stdout, status.stdout
        out = run(["approve", ref], project)
        assert out.returncode != 0
        assert "E_PERMISSION" in out.stderr
    finally:
        run(["serve", "--stop"], project, person=True)
    assert landed(project) == 0


def test_rdy_refuses_hidden_name_bare_approve(project):
    ref = new_proposal(project, "Garden water")
    script = f'x="$RDY"; $x approve {ref} --no-daemon'
    out = bash(script, project)
    assert out.returncode != 0 and "E_PERMISSION" in out.stderr
    assert landed(project) == 0
    # rdy stops this one itself; the guard cannot see the hidden name.
    assert guard.check("terminal", {"command": "x=rdy; $x approve P-x@1"}) is None


def test_hidden_name_relay_is_accepted_by_rdy_so_the_guard_blocks_it(project, check):
    ref = new_proposal(project, "Garden seeds")
    command = f"x=rdy; $x approve {ref} --relayed-by agent:hermes --evidence ok"
    assert check("terminal", {"command": command})["action"] == "block"
    out = bash(f'x="$RDY"; $x approve {ref} --relayed-by agent:hermes --evidence ok --no-daemon', project)
    assert out.returncode == 0, out.stderr
    assert landed(project) == 1
    assert last_landing(project)["relayed_by"]["actor"] == "agent:hermes"


def test_emptied_environment_approves_as_the_person_so_the_guard_blocks_it(project, check):
    ref = new_proposal(project, "Garden tools")
    command = f"x=rdy; env -i PATH=$PATH $x approve {ref}"
    assert check("terminal", {"command": command})["action"] == "block"
    out = bash(f'x="$RDY"; env -i PATH="$PATH" HOME="$HOME" $x approve {ref} --no-daemon', project)
    assert out.returncode == 0, out.stderr
    assert landed(project) == 1
    landing = last_landing(project)
    assert landing["approved_by"].startswith("human:")
    assert landing["relayed_by"] is None
