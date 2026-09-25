"""Hardened subprocess helper shared by the code-execution services.

SECURITY MODEL -- READ BEFORE CHANGING
======================================
This is a **local, single-user demo sandbox**. It reduces the blast radius of
submitted code; it is **not** an isolation boundary. The child process still runs
as the same OS user, with the same filesystem and network access as the server.

What this module does enforce
-----------------------------
1. **Environment whitelist.** A child only receives the variables named in
   ``_ENV_ALLOWLIST`` (plus the overrides built here). Everything the server
   holds -- ``SECRET_KEY`` (the JWT signing key), ``DATABASE_URL``, ``*_API_KEY``,
   OAuth tokens, proxy credentials -- is never inherited. An earlier revision
   copied ``os.environ`` wholesale, which handed every submitted snippet the
   server's secrets.
2. **Explicit working directory.** Children run inside a throwaway temp
   directory, and ``HOME`` / ``TEMP`` / ``TMP`` are repointed at it, so
   home-relative lookups (``~/.aws/credentials``, ``~/.npmrc``,
   ``~/.git-credentials``) do not resolve to the real user profile.
3. **Whole-process-tree timeout kill.** A child is started in its own session /
   process group, so on timeout the *group* is killed instead of only the direct
   child. Code that spawns a helper process can no longer outlive the request.
4. **Bounded captured output.** stdout/stderr are truncated to
   ``MAX_OUTPUT_SIZE`` before they reach the API response.

What this module does **not** do
--------------------------------
* No CPU or memory quota -- see the note above ``_ENV_ALLOWLIST``.
* No network isolation, no seccomp/syscall filtering, no filesystem jail and no
  read-only root. Submitted code can still read any file the server user can
  read, including the server's own source and database.
* The interpreter may be the server's own virtualenv interpreter, so submitted
  Python can still ``import`` server packages.

Production requirement
----------------------
For any shared, multi-user or internet-facing deployment, replace this module
with a real isolation boundary -- gVisor, Firecracker/microVM, or one disposable
container per execution (cgroup limits, read-only rootfs, no network) -- and add
rate limiting, resource quotas and audit logging. Do not expose the endpoints
that call this module to the public internet.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

DEFAULT_TIMEOUT = 10
MAX_OUTPUT_SIZE = 1024 * 1024

# NOTE: this module intentionally imposes no memory ceiling.
# An earlier revision declared ``MAX_MEMORY_MB = 256``, but nothing ever read it:
# the advertised ceiling was dead code and no limit was applied. It is not
# reinstated because the obvious implementation is unsound -- RLIMIT_AS caps
# *virtual address space*, and both V8 (node) and the JVM reserve multiple GB of
# address space at startup, so a 256 MB RLIMIT_AS makes those runtimes fail to
# boot instead of limiting the submitted code. RLIMIT_DATA has the same weakness
# on modern allocators. A real memory limit needs a cgroup inside a container,
# which is out of scope here. Do not describe this sandbox as memory-limited.

# Only non-secret variables that a language runtime genuinely needs. Credential,
# token, proxy and database names are absent by construction, and
# _ENV_DENY_PATTERN re-checks every name as defence in depth.
_ENV_ALLOWLIST = (
    # Interpreter / compiler lookup
    "PATH",
    "PATHEXT",
    "PYTHONHASHSEED",
    "JAVA_HOME",
    "NODE_PATH",
    # Locale and timezone
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TZ",
    # Windows runtime prerequisites
    "COMSPEC",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "WINDIR",
    "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
)

# Defence in depth: if a credential-ish name is ever added to the allowlist by
# mistake, it is dropped here instead of leaking. test_sandbox_security.py
# asserts that no allowlisted name matches this pattern.
_ENV_DENY_PATTERN = re.compile(
    r"KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|AUTH|SESSION|COOKIE|JWT"
    r"|DATABASE|DSN|PROXY|SSH|AWS|GCP|AZURE|OPENAI|ANTHROPIC|API_|_API",
    re.IGNORECASE,
)

# Variables set explicitly for every child; never inherited from the server.
_ENV_FORCED = {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUNBUFFERED": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    # Do not let submitted code pull in the invoking user's site-packages.
    "PYTHONNOUSERSITE": "1",
    # Belt-and-braces: leave no proxy configuration reachable.
    "HTTP_PROXY": "",
    "HTTPS_PROXY": "",
    "http_proxy": "",
    "https_proxy": "",
    "NO_PROXY": "*",
    "no_proxy": "*",
}


@dataclass
class CommandResult:
    """Outcome of one sandboxed child process."""

    returncode: int
    stdout: str
    stderr: str
    elapsed_ms: int
    timed_out: bool


def build_sandbox_env(
    workdir: str, extra: Optional[Mapping[str, str]] = None
) -> dict[str, str]:
    """Return the minimal environment a sandboxed child is allowed to see.

    ``workdir`` becomes the child's ``HOME`` / ``TEMP`` / ``TMP`` so home- and
    temp-relative lookups stay inside the throwaway directory.
    """
    env: dict[str, str] = {}
    for name in _ENV_ALLOWLIST:
        if _ENV_DENY_PATTERN.search(name):
            continue
        value = os.environ.get(name)
        if value:
            env[name] = value

    env.update(_ENV_FORCED)
    env["HOME"] = workdir
    env["USERPROFILE"] = workdir
    env["TEMP"] = workdir
    env["TMP"] = workdir
    env["TMPDIR"] = workdir

    if extra:
        env.update(extra)
    return env


def python_argv(script_path: str) -> list[str]:
    """Interpreter argv for a submitted Python script.

    The exact interpreter running the server is used, so the child always finds
    its own runtime even when ``PATH`` is unusual. ``-s`` keeps the invoking
    user's site-packages out of ``sys.path`` while still honouring
    ``PYTHONIOENCODING`` (``-I`` would ignore it and garble non-ASCII output on
    Windows). ``PYTHONPATH`` is never passed through, so there is no
    environment-based path injection.
    """
    return [sys.executable or "python", "-s", script_path]


def _safe_kill(proc: subprocess.Popen) -> None:
    try:
        proc.kill()
    except OSError:
        pass


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kill ``proc`` together with every process it spawned, then reap it."""
    if proc.poll() is not None:
        return

    if os.name == "posix":
        # start_new_session=True made the child a process-group leader, so the
        # process-group form reaches the whole tree.
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            _safe_kill(proc)
    else:
        # Windows cannot signal a process group; taskkill /T walks the tree.
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass
        _safe_kill(proc)

    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def run_sandboxed(
    argv: Sequence[str],
    *,
    workdir: str,
    stdin_text: str = "",
    timeout: int = DEFAULT_TIMEOUT,
    extra_env: Optional[Mapping[str, str]] = None,
) -> CommandResult:
    """Run ``argv`` as a sandboxed child and always return a result.

    Raises ``FileNotFoundError`` when the executable is not installed, so callers
    can surface a language-specific "please install X" message.
    """
    popen_kwargs: dict = {}
    if os.name == "posix":
        # Own session => own process group, so the timeout kill reaches the tree.
        popen_kwargs["start_new_session"] = True
    else:
        popen_kwargs["creationflags"] = getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )

    env = build_sandbox_env(workdir, extra_env)
    started = time.monotonic()

    proc = subprocess.Popen(
        list(argv),
        cwd=workdir,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        **popen_kwargs,
    )

    timed_out = False
    try:
        stdout, stderr = proc.communicate(input=stdin_text or "", timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_tree(proc)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", ""

    elapsed_ms = int((time.monotonic() - started) * 1000)
    return CommandResult(
        returncode=proc.returncode if proc.returncode is not None else -1,
        stdout=(stdout or "")[:MAX_OUTPUT_SIZE],
        stderr=(stderr or "")[:MAX_OUTPUT_SIZE],
        elapsed_ms=elapsed_ms,
        timed_out=timed_out,
    )
