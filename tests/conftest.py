"""Test setup: import the plugin's modules from the repo root.

RDY_GUARD_OFF=1 swaps the guard for one that never blocks. Run the suite that
way to prove every block test fails without the guard.
"""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import guard as _guard  # noqa: E402


def _off(tool_name="", args=None, **kwargs):
    return None


@pytest.fixture
def check():
    if os.environ.get("RDY_GUARD_OFF") == "1":
        return _off
    return _guard.check


@pytest.fixture(autouse=True)
def _reset_program():
    _guard.set_program(None)
    yield
    _guard.set_program(None)
