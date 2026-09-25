"""Single-language quick execution service (the ``/api/execute`` endpoint).

Like :mod:`app.services.sandbox_service`, every child is launched through
:mod:`app.services.sandbox_runner`, so the environment whitelist, the throwaway
working directory and the whole-process-tree timeout kill all apply. Read the
security model at the top of that module before changing anything here -- this is
a **local demo sandbox**, not an isolation boundary, and must not be exposed to
untrusted users.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

from .sandbox_runner import (
    DEFAULT_TIMEOUT,
    MAX_OUTPUT_SIZE,
    python_argv,
    run_sandboxed,
)

__all__ = [
    "DEFAULT_TIMEOUT",
    "MAX_OUTPUT_SIZE",
    "ExecutionResult",
    "execute_code",
    "execute_cpp",
    "execute_java",
    "execute_javascript",
    "execute_python",
]


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    runtime_ms: int
    # Always 0.0: this service does not measure or limit memory. See the note in
    # app/services/sandbox_runner.py on why a setrlimit-based cap is not used.
    memory_mb: float
    status: str


def _checked_write(path: str, code: str) -> None:
    """Refuse to follow a symlink out of the sandbox when writing user code."""
    if os.path.islink(path):
        raise RuntimeError("sandbox file path was replaced by a symlink")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(code)


def execute_python(
    code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> ExecutionResult:
    try:
        with tempfile.TemporaryDirectory(prefix="algo_exec_") as tmpdir:
            script = os.path.join(tmpdir, "main.py")
            _checked_write(script, code)

            result = run_sandboxed(
                python_argv(script),
                workdir=tmpdir,
                stdin_text=stdin,
                timeout=timeout,
            )
            if result.timed_out:
                return ExecutionResult(
                    False, "", "Time Limit Exceeded", result.elapsed_ms, 0, "Timeout"
                )
            if result.returncode == 0:
                return ExecutionResult(
                    True, result.stdout, "", result.elapsed_ms, 0, "Accepted"
                )
            return ExecutionResult(
                False,
                result.stdout,
                result.stderr,
                result.elapsed_ms,
                0,
                "Runtime Error",
            )
    except FileNotFoundError:
        return ExecutionResult(
            False, "", "Python interpreter not installed", 0, 0, "Error"
        )
    except Exception as exc:  # noqa: BLE001 - surface any failure to the caller
        return ExecutionResult(False, "", str(exc), 0, 0, "Error")


def execute_javascript(
    code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> ExecutionResult:
    try:
        with tempfile.TemporaryDirectory(prefix="algo_exec_") as tmpdir:
            script = os.path.join(tmpdir, "main.js")
            _checked_write(script, code)

            result = run_sandboxed(
                ["node", script], workdir=tmpdir, stdin_text=stdin, timeout=timeout
            )
            if result.timed_out:
                return ExecutionResult(
                    False, "", "Time Limit Exceeded", result.elapsed_ms, 0, "Timeout"
                )
            if result.returncode == 0:
                return ExecutionResult(
                    True, result.stdout, "", result.elapsed_ms, 0, "Accepted"
                )
            return ExecutionResult(
                False,
                result.stdout,
                result.stderr,
                result.elapsed_ms,
                0,
                "Runtime Error",
            )
    except FileNotFoundError:
        return ExecutionResult(False, "", "Node.js not installed", 0, 0, "Error")
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult(False, "", str(exc), 0, 0, "Error")


def execute_java(
    code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> ExecutionResult:
    try:
        with tempfile.TemporaryDirectory(prefix="algo_exec_") as tmpdir:
            class_name = "Main"
            java_file = os.path.join(tmpdir, f"{class_name}.java")
            _checked_write(java_file, code)

            compile_result = run_sandboxed(
                ["javac", java_file], workdir=tmpdir, timeout=timeout
            )
            if compile_result.timed_out:
                return ExecutionResult(
                    False, "", "Time Limit Exceeded", compile_result.elapsed_ms, 0,
                    "Timeout",
                )
            if compile_result.returncode != 0:
                return ExecutionResult(
                    False, "", compile_result.stderr, compile_result.elapsed_ms, 0,
                    "Compile Error",
                )

            class_file = os.path.join(tmpdir, f"{class_name}.class")
            if not os.path.exists(class_file):
                return ExecutionResult(
                    False, "", "Compilation failed", compile_result.elapsed_ms, 0,
                    "Compile Error",
                )

            result = run_sandboxed(
                ["java", "-cp", tmpdir, class_name],
                workdir=tmpdir,
                stdin_text=stdin,
                timeout=timeout,
            )
            if result.timed_out:
                return ExecutionResult(
                    False, "", "Time Limit Exceeded", result.elapsed_ms, 0, "Timeout"
                )
            if result.returncode == 0:
                return ExecutionResult(
                    True, result.stdout, "", result.elapsed_ms, 0, "Accepted"
                )
            return ExecutionResult(
                False,
                result.stdout,
                result.stderr,
                result.elapsed_ms,
                0,
                "Runtime Error",
            )
    except FileNotFoundError as exc:
        return ExecutionResult(False, "", f"{exc}. Please install JDK.", 0, 0, "Error")
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult(False, "", str(exc), 0, 0, "Error")


def execute_cpp(
    code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> ExecutionResult:
    try:
        with tempfile.TemporaryDirectory(prefix="algo_exec_") as tmpdir:
            cpp_file = os.path.join(tmpdir, "main.cpp")
            exe_file = os.path.join(tmpdir, "main.exe")
            _checked_write(cpp_file, code)

            compile_result = run_sandboxed(
                ["g++", cpp_file, "-o", exe_file, "-std=c++17"],
                workdir=tmpdir,
                timeout=timeout,
            )
            if compile_result.timed_out:
                return ExecutionResult(
                    False, "", "Time Limit Exceeded", compile_result.elapsed_ms, 0,
                    "Timeout",
                )
            if compile_result.returncode != 0:
                return ExecutionResult(
                    False, "", compile_result.stderr, compile_result.elapsed_ms, 0,
                    "Compile Error",
                )
            if not os.path.exists(exe_file):
                return ExecutionResult(
                    False, "", "Compilation failed", compile_result.elapsed_ms, 0,
                    "Compile Error",
                )

            result = run_sandboxed(
                [exe_file], workdir=tmpdir, stdin_text=stdin, timeout=timeout
            )
            if result.timed_out:
                return ExecutionResult(
                    False, "", "Time Limit Exceeded", result.elapsed_ms, 0, "Timeout"
                )
            if result.returncode == 0:
                return ExecutionResult(
                    True, result.stdout, "", result.elapsed_ms, 0, "Accepted"
                )
            return ExecutionResult(
                False,
                result.stdout,
                result.stderr,
                result.elapsed_ms,
                0,
                "Runtime Error",
            )
    except FileNotFoundError as exc:
        return ExecutionResult(
            False, "", f"{exc}. Please install MinGW/GCC.", 0, 0, "Error"
        )
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult(False, "", str(exc), 0, 0, "Error")


def execute_code(
    language: str, code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> ExecutionResult:
    lang = (language or "").lower()
    if lang == "python":
        return execute_python(code, stdin, timeout)
    if lang == "javascript":
        return execute_javascript(code, stdin, timeout)
    if lang == "java":
        return execute_java(code, stdin, timeout)
    if lang == "cpp":
        return execute_cpp(code, stdin, timeout)
    return ExecutionResult(False, "", f"Unsupported language: {language}", 0, 0, "Error")
