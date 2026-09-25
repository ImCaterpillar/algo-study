"""Security regression tests for the code-execution sandbox.

These pin the hardening that must not silently regress:

* an allowlist that cannot contain a credential-shaped variable name;
* submitted code cannot read the server's secrets (JWT signing key, database
  URL, API keys) out of its environment, in **either** execution service;
* children run inside a throwaway working directory, with ``HOME`` / ``TEMP``
  redirected into it;
* a timeout kills the whole process tree -- a helper process spawned by the
  submitted code must not survive the request.

They call the service layer directly, so they need no running server. Run with:

    python -m pytest test_sandbox_security.py -q
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest

from app.services import sandbox_runner
from app.services.execution_service import execute_code
from app.services.sandbox_service import execute_sandbox

# Secrets are planted under names that a naive implementation would forward.
_LEAK_CANARY_NAMES = (
    "SECRET_KEY",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "ALGOSTUDY_TEST_API_KEY",
    "ALGOSTUDY_TEST_TOKEN",
)
_LEAK_CANARY_VALUE = "leak-canary-value-do-not-forward"

_PRINT_ENV = "import json, os\nprint(json.dumps(sorted(os.environ)))\n"


@pytest.fixture
def planted_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Put credential-shaped variables into the server's own environment."""
    for name in _LEAK_CANARY_NAMES:
        monkeypatch.setenv(name, _LEAK_CANARY_VALUE)


def test_allowlist_contains_no_credential_names() -> None:
    """The deny pattern must never reject an allowlisted runtime variable.

    If it did, the child would silently lose a variable its runtime needs.
    """
    for name in sandbox_runner._ENV_ALLOWLIST:  # noqa: SLF001 - deliberate
        assert not sandbox_runner._ENV_DENY_PATTERN.search(name), name


def test_build_sandbox_env_drops_secrets(
    planted_secrets: None, tmp_path: Path
) -> None:
    env = sandbox_runner.build_sandbox_env(str(tmp_path))

    for name in _LEAK_CANARY_NAMES:
        assert name not in env, f"{name} leaked into the child environment"
    assert _LEAK_CANARY_VALUE not in env.values()
    # Home and temp lookups must stay inside the throwaway directory.
    assert env["HOME"] == str(tmp_path)
    assert env["USERPROFILE"] == str(tmp_path)
    assert env["TEMP"] == str(tmp_path)
    assert env["TMPDIR"] == str(tmp_path)
    # No proxy configuration may be reachable.
    assert env["HTTP_PROXY"] == ""
    assert env["HTTPS_PROXY"] == ""


@pytest.mark.parametrize(
    "run", [execute_sandbox, execute_code], ids=["sandbox_service", "execution_service"]
)
def test_submitted_code_cannot_read_server_secrets(
    run: Callable[..., object], planted_secrets: None
) -> None:
    """End-to-end: a real child process must not see the planted secrets."""
    result = run("python", _PRINT_ENV)
    assert result.success is True, result.error
    for name in _LEAK_CANARY_NAMES:
        assert name not in result.output, f"{name} reached submitted code"
    assert _LEAK_CANARY_VALUE not in result.output


@pytest.mark.parametrize(
    "run", [execute_sandbox, execute_code], ids=["sandbox_service", "execution_service"]
)
def test_child_runs_in_a_throwaway_directory(run: Callable[..., object]) -> None:
    """Relative paths must not resolve against the server's own working tree."""
    result = run("python", "import os; print(os.getcwd())")
    assert result.success is True, result.error
    # Neither service may hand the child the repository or the backend folder.
    assert "algo_sandbox_" in result.output or "algo_exec_" in result.output
    assert not result.output.strip().endswith("backend")


def test_timeout_kills_the_whole_process_tree(tmp_path: Path) -> None:
    """A helper process spawned by submitted code must die with its parent."""
    marker = tmp_path / "grandchild-survived.txt"
    # The child spawns a grandchild that would write `marker` 4s from now, then
    # blocks. The 2s timeout must kill the group before that write happens.
    # Both snippets are embedded with repr() so Windows path backslashes survive.
    grandchild_code = (
        "import pathlib, time\n"
        "time.sleep(4.0)\n"
        f"pathlib.Path({str(marker)!r}).write_text('survived')\n"
    )
    code = (
        "import subprocess, sys, time\n"
        f"grandchild = {grandchild_code!r}\n"
        "subprocess.Popen([sys.executable, '-c', grandchild])\n"
        "time.sleep(60)\n"
    )

    started = time.monotonic()
    result = execute_sandbox("python", code, timeout=2)
    elapsed = time.monotonic() - started

    assert result.status == "Timeout", f"{result.status}: {result.error}"
    assert elapsed < 30, "the timeout did not fire promptly"

    # Wait past the moment the grandchild would have written the marker.
    time.sleep(max(0.0, 6.0 - elapsed))
    assert not marker.exists(), "a grandchild process survived the timeout kill"
