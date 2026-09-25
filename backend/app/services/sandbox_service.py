"""Multi-language code execution service.

Every child process is launched through
:mod:`app.services.sandbox_runner`, which enforces the environment whitelist, the
throwaway working directory and the whole-process-tree timeout kill. Read the
security model documented at the top of that module before changing anything
here -- in particular, this sandbox is for **local demo use only** and is not an
isolation boundary. A production deployment must run submissions inside a real
isolation layer (gVisor / Firecracker microVM / disposable container).
"""
from __future__ import annotations

import os
import shutil
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
    "SandboxResult",
    "cleanup_sandbox_temp_dir",
    "create_sandbox_temp_dir",
    "execute_sandbox",
    "execute_sandbox_cpp",
    "execute_sandbox_java",
    "execute_sandbox_javascript",
    "execute_sandbox_python",
]


@dataclass
class SandboxResult:
    success: bool
    output: str
    error: str
    runtime_ms: int
    # Always 0.0: this sandbox does not measure or limit memory. See the note in
    # app/services/sandbox_runner.py on why a setrlimit-based cap is not used.
    memory_mb: float
    status: str


def create_sandbox_temp_dir() -> str:
    return tempfile.mkdtemp(prefix="algo_sandbox_")


def cleanup_sandbox_temp_dir(tmpdir: str) -> None:
    shutil.rmtree(tmpdir, ignore_errors=True)


def _checked_write(path: str, code: str) -> None:
    """Refuse to follow a symlink out of the sandbox when writing user code."""
    if os.path.islink(path):
        raise RuntimeError("sandbox file path was replaced by a symlink")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(code)


def execute_sandbox_python(
    code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> SandboxResult:
    tmpdir = None
    try:
        tmpdir = create_sandbox_temp_dir()
        script = os.path.join(tmpdir, "sandbox_main.py")
        _checked_write(script, code)

        result = run_sandboxed(
            python_argv(script), workdir=tmpdir, stdin_text=stdin, timeout=timeout
        )
        if result.timed_out:
            return SandboxResult(
                False, "", "Time Limit Exceeded", result.elapsed_ms, 0, "Timeout"
            )
        if result.returncode == 0:
            return SandboxResult(
                True, result.stdout, result.stderr, result.elapsed_ms, 0, "Accepted"
            )
        status = "Compile Error" if "SyntaxError" in result.stderr else "Runtime Error"
        return SandboxResult(
            False, result.stdout, result.stderr, result.elapsed_ms, 0, status
        )
    except FileNotFoundError:
        return SandboxResult(
            False, "", "Python interpreter not installed", 0, 0, "Error"
        )
    except Exception as exc:  # noqa: BLE001 - surface any failure to the caller
        return SandboxResult(False, "", str(exc), 0, 0, "Error")
    finally:
        if tmpdir:
            cleanup_sandbox_temp_dir(tmpdir)


def execute_sandbox_javascript(
    code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> SandboxResult:
    tmpdir = None
    try:
        tmpdir = create_sandbox_temp_dir()
        script = os.path.join(tmpdir, "sandbox_main.js")
        _checked_write(script, code)

        result = run_sandboxed(
            ["node", script], workdir=tmpdir, stdin_text=stdin, timeout=timeout
        )
        if result.timed_out:
            return SandboxResult(
                False, "", "Time Limit Exceeded", result.elapsed_ms, 0, "Timeout"
            )
        if result.returncode == 0:
            return SandboxResult(
                True, result.stdout, result.stderr, result.elapsed_ms, 0, "Accepted"
            )
        return SandboxResult(
            False, result.stdout, result.stderr, result.elapsed_ms, 0, "Runtime Error"
        )
    except FileNotFoundError:
        return SandboxResult(False, "", "Node.js not installed", 0, 0, "Error")
    except Exception as exc:  # noqa: BLE001
        return SandboxResult(False, "", str(exc), 0, 0, "Error")
    finally:
        if tmpdir:
            cleanup_sandbox_temp_dir(tmpdir)


def execute_sandbox_java(
    code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> SandboxResult:
    tmpdir = None
    try:
        tmpdir = create_sandbox_temp_dir()
        class_name = "SandboxMain"
        java_file = os.path.join(tmpdir, f"{class_name}.java")
        _checked_write(java_file, code)

        compile_result = run_sandboxed(
            ["javac", java_file], workdir=tmpdir, timeout=timeout
        )
        if compile_result.timed_out:
            return SandboxResult(
                False, "", "Time Limit Exceeded", compile_result.elapsed_ms, 0, "Timeout"
            )
        if compile_result.returncode != 0:
            return SandboxResult(
                False,
                "",
                compile_result.stderr,
                compile_result.elapsed_ms,
                0,
                "Compile Error",
            )

        class_file = os.path.join(tmpdir, f"{class_name}.class")
        if not os.path.exists(class_file):
            return SandboxResult(
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
            return SandboxResult(
                False, "", "Time Limit Exceeded", result.elapsed_ms, 0, "Timeout"
            )
        if result.returncode == 0:
            return SandboxResult(
                True, result.stdout, result.stderr, result.elapsed_ms, 0, "Accepted"
            )
        return SandboxResult(
            False, result.stdout, result.stderr, result.elapsed_ms, 0, "Runtime Error"
        )
    except FileNotFoundError as exc:
        return SandboxResult(False, "", f"{exc}. Please install JDK.", 0, 0, "Error")
    except Exception as exc:  # noqa: BLE001
        return SandboxResult(False, "", str(exc), 0, 0, "Error")
    finally:
        if tmpdir:
            cleanup_sandbox_temp_dir(tmpdir)


def execute_sandbox_cpp(
    code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> SandboxResult:
    tmpdir = None
    try:
        tmpdir = create_sandbox_temp_dir()
        cpp_file = os.path.join(tmpdir, "main.cpp")
        # On POSIX the extension is irrelevant; on Windows the .exe suffix is what
        # CreateProcess needs, so one portable name is used for both.
        exe_file = os.path.join(tmpdir, "main.exe")
        _checked_write(cpp_file, code)

        compile_result = run_sandboxed(
            ["g++", cpp_file, "-o", exe_file, "-std=c++17"],
            workdir=tmpdir,
            timeout=timeout,
        )
        if compile_result.timed_out:
            return SandboxResult(
                False, "", "Time Limit Exceeded", compile_result.elapsed_ms, 0, "Timeout"
            )
        if compile_result.returncode != 0:
            return SandboxResult(
                False,
                "",
                compile_result.stderr,
                compile_result.elapsed_ms,
                0,
                "Compile Error",
            )
        if not os.path.exists(exe_file):
            return SandboxResult(
                False, "", "Compilation failed", compile_result.elapsed_ms, 0,
                "Compile Error",
            )

        result = run_sandboxed(
            [exe_file], workdir=tmpdir, stdin_text=stdin, timeout=timeout
        )
        if result.timed_out:
            return SandboxResult(
                False, "", "Time Limit Exceeded", result.elapsed_ms, 0, "Timeout"
            )
        if result.returncode == 0:
            return SandboxResult(
                True, result.stdout, result.stderr, result.elapsed_ms, 0, "Accepted"
            )
        return SandboxResult(
            False, result.stdout, result.stderr, result.elapsed_ms, 0, "Runtime Error"
        )
    except FileNotFoundError as exc:
        return SandboxResult(
            False, "", f"{exc}. Please install MinGW/GCC.", 0, 0, "Error"
        )
    except Exception as exc:  # noqa: BLE001
        return SandboxResult(False, "", str(exc), 0, 0, "Error")
    finally:
        if tmpdir:
            cleanup_sandbox_temp_dir(tmpdir)


def execute_sandbox(
    language: str, code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT
) -> SandboxResult:
    lang = (language or "").lower()
    if lang == "python":
        return execute_sandbox_python(code, stdin, timeout)
    if lang == "javascript":
        return execute_sandbox_javascript(code, stdin, timeout)
    if lang == "java":
        return execute_sandbox_java(code, stdin, timeout)
    if lang == "cpp":
        return execute_sandbox_cpp(code, stdin, timeout)
    return SandboxResult(False, "", f"Unsupported language: {language}", 0, 0, "Error")
