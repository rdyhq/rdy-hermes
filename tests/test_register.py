"""register(ctx) wires one hook, two skills and one command, and nothing else."""

import importlib.util
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_plugin():
    spec = importlib.util.spec_from_file_location(
        "rdy_plugin_under_test", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeContext:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.hooks, self.skills, self.commands, self.tools = [], [], [], []

    def get_config(self, key, default=None):
        return self.settings.get(key, default)

    def register_hook(self, name, callback):
        self.hooks.append((name, callback))

    def register_skill(self, name, path, description="", frontmatter=None):
        self.skills.append((name, Path(path)))

    def register_cli_command(self, name, help, setup_fn, handler_fn=None, description=""):
        self.commands.append((name, setup_fn, handler_fn))

    def register_tool(self, *args, **kwargs):
        self.tools.append(args)


def test_register_wires_hook_skills_and_command():
    plugin = _load_plugin()
    ctx = FakeContext()
    plugin.register(ctx)
    assert [name for name, _ in ctx.hooks] == ["pre_tool_call"]
    assert sorted(name for name, _ in ctx.skills) == ["loop", "start"]
    assert all(path.name == "SKILL.md" and path.is_file() for _, path in ctx.skills)
    assert [name for name, _, _ in ctx.commands] == ["rdy"]
    assert ctx.tools == []


def test_hook_accepts_kwargs_and_blocks():
    plugin = _load_plugin()
    ctx = FakeContext()
    plugin.register(ctx)
    callback = ctx.hooks[0][1]
    kinds = {p.kind for p in inspect.signature(callback).parameters.values()}
    assert inspect.Parameter.VAR_KEYWORD in kinds
    result = callback(tool_name="terminal", args={"command": "rdy approve P-x@1"}, task_id="t")
    assert result["action"] == "block"
    assert callback(tool_name="terminal", args={"command": "rdy status"}, task_id="t") is None


def test_setting_renames_the_guarded_program():
    plugin = _load_plugin()
    ctx = FakeContext({"rdy_path": "/opt/tools/planstore"})
    plugin.register(ctx)
    callback = ctx.hooks[0][1]
    assert callback(tool_name="terminal", args={"command": "planstore land P-x@1"}) is not None


def test_skill_files_have_names_that_match_their_folders():
    for folder in (ROOT / "skills").iterdir():
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert f"\nname: {folder.name}\n" in text


def test_manifest_declares_exactly_the_hook():
    text = (ROOT / "plugin.yaml").read_text(encoding="utf-8")
    assert "provides_tools: []" in text
    assert "provides_hooks:\n  - pre_tool_call\n" in text
    assert "homepage" not in text and "repository" not in text
