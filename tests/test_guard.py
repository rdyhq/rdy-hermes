"""Saved cases for the approval guard. Every project here is made up."""

import time

import pytest

import guard

PERSON = "Relays are off"
AUTH = "auth token prints hub access"
ACTOR = "RDY_ACTOR may be set only to agent:hermes"
EMPTY = "emptied or replaced environment"

# --- shell commands -----------------------------------------------------------

# (command, kind of block)
BLOCK_COMMANDS = [
    # bare person-only acts
    ("rdy approve P-abc123@1", PERSON),
    ("rdy tag v1", PERSON),
    ("rdy land P-abc123@1", PERSON),
    ("rdy answer --all-recommended P-abc123@1", PERSON),
    ("rdy sign P-abc123@1", PERSON),
    ("rdy sign tag:v1", PERSON),
    ("rdy publish v1", PERSON),
    ("rdy redact n-ABCDE", PERSON),
    ("rdy redact n-ABCDE --reason-class personal --reason test --dry-run", PERSON),
    ("rdy dispute L-1a2b", PERSON),
    ("rdy dispute open L-1a2b --reason wrong", PERSON),
    ("rdy resolve T-1a2b --dismiss --reason fine", PERSON),
    ("rdy key bind ssh-ed25519-sample", PERSON),
    ("rdy key retire K-1a2b", PERSON),
    ("rdy key revoke K-1a2b", PERSON),
    # auth: only state and installs pass
    ("rdy auth token", AUTH),
    ("rdy auth sign-in", AUTH),
    ("rdy auth sign-out", AUTH),
    ("rdy auth", AUTH),
    # relays and the relay flags
    ("rdy approve P-abc123@1 --relayed-by agent:hermes --evidence approve", PERSON),
    ("RDY_ACTOR=agent:hermes rdy approve P-abc123@1 --relayed-by agent:hermes --evidence ok", PERSON),
    ("rdy tag v1 --relayed-by agent:hermes --evidence tag-it", PERSON),
    ("x=rdy; $x approve P-x@1 --relayed-by agent:hermes --evidence ok", PERSON),
    ("y=rdy; $y propose --title t --relayed-by agent:hermes --evidence ok", PERSON),
    ("grep -- --evidence README.md", PERSON),  # stated false block
    ("echo --relayed-by", PERSON),  # stated false block
    # program forms
    ("cd garden-planner && rdy approve P-abc123@1", PERSON),
    ("rdy --project ./garden-planner approve P-abc123@1", PERSON),
    ("rdy --json approve P-abc123@1", PERSON),
    ("$(command -v rdy) approve P-abc123@1", PERSON),
    ("`which rdy` approve P-abc123@1", PERSON),
    ("rdy status\nrdy approve P-abc123@1", PERSON),
    ("rdy status; rdy approve P-abc123@1", PERSON),
    ('"rdy" approve P-abc123@1', PERSON),
    ("'rdy' approve P-abc123@1", PERSON),
    ('rdy approve "P-abc123@1"', PERSON),
    ('bash -c "rdy approve P-abc123@1"', PERSON),
    ("sh -c 'rdy approve P-abc123@1'", PERSON),
    ("echo P-abc123@1 | xargs rdy approve", PERSON),
    ("RDY_ACTOR=agent:hermes rdy approve P-abc123@1", PERSON),
    ("/opt/bin/rdy-1a2b answer P-abc123@1 yes", PERSON),
    ("Rdy approve P-x@1", PERSON),
    ("RDY.EXE approve P-x@1", PERSON),
    ("C:\\tools\\rdy.exe tag v1.0.0", PERSON),
    ("~/bin/rdy-0.41.0 land P-x@1", PERSON),
    ("rdy\tapprove P-x@1", PERSON),
    ('rdy "approve" P-x@1', PERSON),
    ("rdy 'approve' P-x@1", PERSON),
    ('rdy ap""prove P-x@1', PERSON),
    ("rdy a\\pprove P-x@1", PERSON),
    ("rdy \\\n  approve P-x@1", PERSON),
    ("rdy approve P-abc123@1 && rdy approve P-abc123@2 --relayed-by agent:hermes --evidence ok", PERSON),
    ("rdy approve P-x@1 && rdy approve --help", PERSON),
    ("rdy approve P-x@1 # --help", PERSON),
    # a relay sent to rdy's MCP server by hand
    ("printf '%s' '{\"method\":\"tools/call\",\"params\":{\"name\":\"rdy_land\"}}' | rdy mcp", PERSON),
    ("echo rdy_answer | rdy mcp --project .", PERSON),
    # RDY_ACTOR: only the exact agent:hermes value passes
    ("RDY_ACTOR=human:x rdy status", ACTOR),
    ("RDY_ACTOR= rdy status", ACTOR),
    ("RDY_ACTOR=agent:other rdy status", ACTOR),
    ("export RDY_ACTOR=human:x", ACTOR),
    ("export RDY_ACTOR=", ACTOR),
    ("RDY_ACTOR+=x rdy status", ACTOR),
    ("env -u RDY_ACTOR rdy status", ACTOR),
    ("env --unset=RDY_ACTOR rdy status", ACTOR),
    ("unset RDY_ACTOR; rdy status", ACTOR),
    ('$env:RDY_ACTOR = "human:x"', ACTOR),
    ("Remove-Item Env:RDY_ACTOR", ACTOR),
    ("declare -x RDY_ACTOR=human:x", ACTOR),
    ("local RDY_ACTOR=human:x", ACTOR),
    # forms that drop or replace RDY_ACTOR without a plain assignment
    ("export -n RDY_ACTOR; x=rdy; $x approve P-x@1", ACTOR),
    ("export -n RDY_ACTOR=agent:hermes", ACTOR),
    ("declare +x RDY_ACTOR; x=rdy; $x approve P-x@1", ACTOR),
    ("typeset +x RDY_ACTOR; x=rdy; $x approve P-x@1", ACTOR),
    ("unset -v RDY_ACTOR; x=rdy; $x approve P-x@1", ACTOR),
    ("x=rdy; env --uns RDY_ACTOR $x approve P-x@1", ACTOR),
    ("printf -v RDY_ACTOR human:x; export RDY_ACTOR; x=rdy; $x approve P-x@1", ACTOR),
    ("read RDY_ACTOR <<< human:x; export RDY_ACTOR; x=rdy; $x approve P-x@1", ACTOR),
    (": ${RDY_ACTOR:=human:x}; x=rdy; $x approve P-x@1", ACTOR),
    ("echo RDY_ACTOR=agent:hermes >> .env", ACTOR),
    ("echo RDY_ACTOR=human:x | tee -a .env", ACTOR),
    # an emptied or replaced environment next to an rdy token
    ("x=rdy; env -i PATH=$PATH $x approve P-x@1", EMPTY),
    ("x=rdy; env --ignore-environment PATH=$PATH $x approve P-x@1", EMPTY),
    ("x=rdy; env - PATH=$PATH $x approve P-x@1", EMPTY),
    ("x=rdy; env -iv PATH=$PATH $x approve P-x@1", EMPTY),
    ("env -i PATH=$PATH rdy status", EMPTY),
    ("x=rdy; sudo $x approve P-x@1", EMPTY),
    ("x=rdy; ssh localhost $x approve P-x@1", EMPTY),
    ("x=rdy; exec -c $x approve P-x@1", EMPTY),
    ("x=rdy; env --ignore PATH=$PATH $x approve P-x@1", EMPTY),
    ("x=rdy; env --ign PATH=$PATH $x approve P-x@1", EMPTY),
    ("x=rdy; setpriv --reset-env $x approve P-x@1", EMPTY),
    # stated false blocks, named in the README
    ("grep -rn rdy_land docs/", PERSON),
    ("env -i PATH=$PATH make sign", EMPTY),
    ("env -i PATH=$PATH ./build.sh --key v2", EMPTY),  # stated false block: "key" is an rdy verb
]

PASS_COMMANDS = [
    "rdy status",
    "rdy init",
    "rdy setup",
    "rdy tags",
    "rdy publication check",
    "rdy dispute list",
    "rdy auth state",
    "rdy auth installs",
    "rdy key show",
    "rdy key",
    "rdy approve --help",
    "rdy approve -h",
    "rdy land --help",
    "rdy show P-abc123@1 --json",
    'rdy propose --title "Garden planner" --summary "A first plan"',
    "rdy instructions",
    "rdy help approve",
    "RDY_ACTOR=agent:hermes rdy status",
    'RDY_ACTOR="agent:hermes" rdy status',
    "export RDY_ACTOR=agent:hermes",
    "env RDY_ACTOR=agent:hermes rdy status",
    "FOO=1 RDY_ACTOR=agent:hermes rdy status",
    "echo $RDY_ACTOR",
    'echo "actor is ${RDY_ACTOR:-unset}"',
    "echo RDY_ACTOR should be agent:hermes",
    "printenv RDY_ACTOR",
    "env -i PATH=$PATH ls",
    "ssh -i ~/.ssh/id_garden host ls",
    # sudo and ssh pass unless the rdy program comes with a person verb or a P-ref
    "ssh host 'cd rdy-hermes-plugin && git pull'",
    "cd rdy-garden && ssh build-host make",
    "sudo apt-get install -y rdy-tools",
    "sudo install -m755 rdy /usr/local/bin/rdy",
    "ls",
    "echo rdy is ready to land",
    "cd rdy-garden && ls",
    "git commit -m 'approve the plan'",
    "hermes rdy doctor",
    "hermes rdy setup",
    "hermes mcp add rdy --command rdy --env RDY_ACTOR=agent:hermes --args mcp --project '${workspaceFolder}'",
    "hermes -p garden mcp add rdy --command rdy --env RDY_ACTOR=agent:hermes --args mcp --project '${workspaceFolder}'",
    "python3 -m pytest -q",
]


def _code(command):
    """The same command as code-execution text."""
    return "import subprocess\nsubprocess.run(%r, shell=True)\n" % command


@pytest.mark.parametrize("command,kind", BLOCK_COMMANDS)
def test_terminal_blocks(check, command, kind):
    result = check("terminal", {"command": command})
    assert result is not None and result["action"] == "block"
    assert kind in result["message"]


@pytest.mark.parametrize("command,kind", BLOCK_COMMANDS)
def test_code_blocks(check, command, kind):
    result = check("execute_code", {"code": _code(command)})
    assert result is not None and result["action"] == "block"


@pytest.mark.parametrize("command", PASS_COMMANDS)
def test_terminal_passes(check, command):
    assert check("terminal", {"command": command}) is None


@pytest.mark.parametrize("command", PASS_COMMANDS)
def test_code_passes(check, command):
    assert check("execute_code", {"code": _code(command)}) is None


# --- code-execution text --------------------------------------------------------

BLOCK_CODE = [
    ('subprocess.run(["rdy", "approve", "P-x@1"])', PERSON),
    ('subprocess.run([\n    "rdy",\n    "approve",\n    "P-x@1",\n])', PERSON),
    ('subprocess.run(["/usr/local/bin/rdy", "--json", "land", "P-x@1"])', PERSON),
    ('subprocess.run(["rdy", "auth", "token"], capture_output=True)', AUTH),
    ('subprocess.run(["rdy", "key", "bind", "k"])', PERSON),
    ('subprocess.run("rdy status\\nrdy approve P-x@1", shell=True)', PERSON),
    ('subprocess.run([x, "approve", "P-x@1", "--relayed-by", "agent:hermes", "--evidence", "ok"])', PERSON),
    ('import os\nos.environ["RDY_ACTOR"] = "human:x"', ACTOR),
    ('os.environ.pop("RDY_ACTOR")', ACTOR),
    ('os.environ.pop("RDY_ACTOR", None)', ACTOR),
    ('del os.environ["RDY_ACTOR"]', ACTOR),
    ('os.putenv("RDY_ACTOR", "human:x")', ACTOR),
    ('os.unsetenv("RDY_ACTOR")', ACTOR),
    ('os.environ.setdefault("RDY_ACTOR", "human:x")', ACTOR),
    ('os.environ.update(RDY_ACTOR="human:x")', ACTOR),
    ('subprocess.run(["rdy", "status"], env={**os.environ, "RDY_ACTOR": "human:x"})', ACTOR),
    ('subprocess.run([x, "approve", "P-x@1"], env={"PATH": p})', EMPTY),
    ('os.environ.clear()\nsubprocess.run([x, "approve", "P-x@1"])', EMPTY),
    ('subprocess.run(["rdy", "status"], env={"PATH": p})', EMPTY),
    # positional environments
    ('os.execve(x, [x, "approve", "P-x@1"], {"PATH": p})', EMPTY),
    ('os.execvpe(x, [x, "approve", "P-x@1"], {"PATH": p})', EMPTY),
    ('os.posix_spawn(x, [x, "approve", "P-x@1"], {"PATH": p})', EMPTY),
    ('os.posix_spawnp(x, [x, "approve", "P-x@1"], {"PATH": p})', EMPTY),
    ('os.spawnve(os.P_WAIT, x, [x, "approve", "P-x@1"], {"PATH": p})', EMPTY),
    ('os.execle(x, x, "approve", "P-x@1", {"PATH": p})', EMPTY),
    # dunder forms
    ('os.environ.__setitem__("RDY_ACTOR", "human:x")', ACTOR),
    ('os.environ.__delitem__("RDY_ACTOR")', ACTOR),
    # writes of the right value are blocked too (allowlist; harmless false blocks)
    ('os.environ["RDY_ACTOR"] = "agent:hermes"', ACTOR),
    ('subprocess.run(["rdy", "status"], env={**os.environ, "RDY_ACTOR": "agent:hermes"})', ACTOR),
    # stated false blocks, named in the README
    ('subprocess.run(["npm", "publish"], env={"CI": "1"})', EMPTY),
    ('print("run rdy approve P-x@1 yourself")', PERSON),
]

PASS_CODE = [
    'subprocess.run(["ls"], env={"LANG": "C"})',
    'actor = os.environ.get("RDY_ACTOR")',
    'actor = os.getenv("RDY_ACTOR", "unset")',
    'subprocess.run(["rdy", "status"], env={**os.environ, "FOO": "1"})',
    'subprocess.run(["rdy", "status"], env=dict(os.environ))',
    'subprocess.run(["rdy", "status"], env=os.environ.copy())',
    'subprocess.run(["rdy", "status"], env=None)',
    'os.execve("/usr/local/bin/rdy", ["rdy", "status"], os.environ)',
    'os.execve(path, args, dict(os.environ, FOO="1"))',
    'print(os.environ.get("RDY_ACTOR", "unset"))',
    'subprocess.run(["rdy", "approve", "--help"])',
    'print("plan the garden beds")',
]


@pytest.mark.parametrize("code,kind", BLOCK_CODE)
def test_code_text_blocks(check, code, kind):
    result = check("execute_code", {"code": code})
    assert result is not None and result["action"] == "block"
    assert kind in result["message"]


@pytest.mark.parametrize("code", PASS_CODE)
def test_code_text_passes(check, code):
    assert check("execute_code", {"code": code}) is None


# --- rdy MCP tools, by name -------------------------------------------------------

PERSON_TOOLS = sorted(guard.PERSON_ONLY_TOOLS)


@pytest.mark.parametrize("server", ["rdy", "plans", "plugin_rdy_rdy"])
@pytest.mark.parametrize("tool", PERSON_TOOLS)
def test_person_only_tools_block(check, server, tool):
    result = check(f"mcp__{server}__{tool}", {"proposal": "P-abc123@1"})
    assert result is not None and result["action"] == "block"
    assert (AUTH if tool == "rdy_auth" else PERSON) in result["message"]


@pytest.mark.parametrize("tool", PERSON_TOOLS)
def test_person_only_tools_block_without_prefix(check, tool):
    assert check(tool, {}) is not None


def test_resolve_with_accept_body_blocks(check):
    args = {"accept": {"proposal": "P-abc123@1", "advised_digest": "d", "evidence": "accept"}}
    assert check("mcp__rdy__rdy_resolve", args) is not None


PASS_TOOLS = [
    "rdy_session", "rdy_instructions", "rdy_read", "rdy_write", "rdy_brief", "rdy_propose",
    "rdy_tensions", "rdy_suspects", "rdy_overview", "rdy_search", "rdy_key_show",
    "rdy_tags", "rdy_pending", "rdy_decide", "rdy_supersede", "rdy_revoke", "rdy_view",
]


@pytest.mark.parametrize("tool", PASS_TOOLS)
def test_other_rdy_tools_pass(check, tool):
    assert check(f"mcp__rdy__{tool}", {"title": "Garden planner"}) is None


# --- tools judged by name only -----------------------------------------------------

RELAY_TEXT = "Run rdy approve P-x@1 --relayed-by agent:hermes --evidence ok, then RDY_ACTOR=human:x"


def test_rdy_write_text_is_not_read(check):
    args = {"ops": [{"op": "add", "body": RELAY_TEXT, "code": "rdy approve P-x@1"}]}
    assert check("mcp__rdy__rdy_write", args) is None


@pytest.mark.parametrize("tool", ["write_file", "patch", "memory", "delegate_task", "cronjob_manage", "skill_manage"])
def test_name_only_tools_pass(check, tool):
    args = {"path": "notes/plan.md", "content": RELAY_TEXT, "command": RELAY_TEXT,
            "script": "rdy approve P-x@1", "prompt": RELAY_TEXT}
    assert check(tool, args) is None


# --- other tools that run something --------------------------------------------------


def test_process_manage_stdin_blocks(check):
    args = {"action": "submit", "session_id": "proc_1", "data": "rdy approve P-x@1\n"}
    assert check("process_manage", args) is not None


def test_browser_exec_code_blocks(check):
    args = {"code": "import subprocess; subprocess.run(['rdy', 'land', 'P-x@1'])"}
    assert check("browser_exec", args) is not None


@pytest.mark.parametrize("key", ["command", "cmd", "code", "script"])
def test_running_argument_on_other_tool_blocks(check, key):
    assert check("mcp__shell__run", {key: "rdy approve P-x@1"}) is not None


def test_nested_running_argument_blocks(check):
    assert check("mcp__shell__run", {"job": {"steps": [{"cmd": "rdy land P-x@1"}]}}) is not None


def test_other_argument_on_other_tool_passes(check):
    assert check("mcp__notes__save", {"text": RELAY_TEXT}) is None


# --- the rdy_path setting -------------------------------------------------------------


def test_renamed_program_from_setting_blocks(check):
    guard.set_program("/opt/tools/planstore")
    result = check("terminal", {"command": "planstore approve P-abc123@1"})
    assert result is not None


def test_renamed_program_from_setting_with_emptied_env_blocks(check):
    guard.set_program("/opt/tools/planstore.exe")
    result = check("terminal", {"command": "env -i PATH=$PATH planstore status"})
    assert result is not None


def test_renamed_program_not_set_passes(check):
    assert check("terminal", {"command": "planstore approve P-abc123@1"}) is None


# --- shape of every answer ------------------------------------------------------------


def test_never_approves_or_modifies():
    calls = [("terminal", {"command": c}) for c, _ in BLOCK_COMMANDS]
    calls += [("terminal", {"command": c}) for c in PASS_COMMANDS]
    calls += [(f"mcp__rdy__{t}", {}) for t in PERSON_TOOLS + PASS_TOOLS]
    for name, args in calls:
        result = guard.check(name, args)
        assert result is None or (set(result) == {"action", "message"} and result["action"] == "block")


def test_block_message_names_the_persons_command():
    result = guard.check("terminal", {"command": "rdy approve P-x@1"})
    assert "rdy approve P-<id>@<n>" in result["message"]
    assert "their own terminal" in result["message"]


@pytest.mark.parametrize("args", [None, "rdy approve P-x@1", 42, [], {}, {"command": None},
                                  {"command": ["rdy", "status"]}, {1: "x"}, {"command": b"rdy"}])
def test_odd_arguments_do_not_raise(args):
    guard.check("terminal", args)
    guard.check("mcp__shell__run", args)
    guard.check(None, args)


def test_accepts_extra_keywords():
    assert guard.check(tool_name="terminal", args={"command": "ls"}, task_id="t", session_id="s",
                       tool_call_id="c", turn_id="u", api_request_id="a", middleware_trace=[]) is None


def test_fast_on_large_input():
    code = ("x = 1  # garden bed row\n" * 8000) + 'subprocess.run(["rdy", "approve", "P-x@1"])\n'
    start = time.perf_counter()
    result = guard.check("execute_code", {"code": code})
    elapsed = time.perf_counter() - start
    assert result is not None
    assert elapsed < 0.5, elapsed


def test_fast_on_typical_call():
    start = time.perf_counter()
    for _ in range(100):
        guard.check("terminal", {"command": "rdy status && rdy propose --title t --summary s"})
    assert (time.perf_counter() - start) / 100 < 0.05
