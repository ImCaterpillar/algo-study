import subprocess
import tempfile
import os
import time
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    runtime_ms: int
    memory_mb: float
    status: str

DEFAULT_TIMEOUT = 10
MAX_OUTPUT_SIZE = 1024 * 1024

def execute_python(code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> ExecutionResult:
    start = time.time()
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_path = f.name
        try:
            result = subprocess.run(
                ['python', temp_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = int((time.time() - start) * 1000)
            if result.returncode == 0:
                return ExecutionResult(True, (result.stdout or "")[:MAX_OUTPUT_SIZE], "", elapsed, 0, "Accepted")
            else:
                return ExecutionResult(False, (result.stdout or "")[:MAX_OUTPUT_SIZE], (result.stderr or "")[:MAX_OUTPUT_SIZE], elapsed, 0, "Runtime Error")
        finally:
            os.unlink(temp_path)
    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", "Time Limit Exceeded", elapsed, 0, "Timeout")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", str(e), elapsed, 0, "Error")

def execute_javascript(code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> ExecutionResult:
    start = time.time()
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_path = f.name
        try:
            result = subprocess.run(
                ['node', temp_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = int((time.time() - start) * 1000)
            if result.returncode == 0:
                return ExecutionResult(True, (result.stdout or "")[:MAX_OUTPUT_SIZE], "", elapsed, 0, "Accepted")
            else:
                return ExecutionResult(False, (result.stdout or "")[:MAX_OUTPUT_SIZE], (result.stderr or "")[:MAX_OUTPUT_SIZE], elapsed, 0, "Runtime Error")
        finally:
            os.unlink(temp_path)
    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", "Time Limit Exceeded", elapsed, 0, "Timeout")
    except FileNotFoundError:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", "Node.js not installed", elapsed, 0, "Error")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", str(e), elapsed, 0, "Error")

def execute_java(code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> ExecutionResult:
    start = time.time()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            class_name = "Main"
            java_file = os.path.join(tmpdir, f"{class_name}.java")
            with open(java_file, 'w', encoding='utf-8') as f:
                f.write(code)
            compile_result = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if compile_result.returncode != 0:
                elapsed = int((time.time() - start) * 1000)
                return ExecutionResult(False, "", (compile_result.stderr or "")[:MAX_OUTPUT_SIZE], elapsed, 0, "Compile Error")
            class_file = os.path.join(tmpdir, f"{class_name}.class")
            if not os.path.exists(class_file):
                return ExecutionResult(False, "", "Compilation failed", int((time.time() - start) * 1000), 0, "Compile Error")
            result = subprocess.run(
                ['java', '-cp', tmpdir, class_name],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = int((time.time() - start) * 1000)
            if result.returncode == 0:
                return ExecutionResult(True, (result.stdout or "")[:MAX_OUTPUT_SIZE], "", elapsed, 0, "Accepted")
            else:
                return ExecutionResult(False, (result.stdout or "")[:MAX_OUTPUT_SIZE], (result.stderr or "")[:MAX_OUTPUT_SIZE], elapsed, 0, "Runtime Error")
    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", "Time Limit Exceeded", elapsed, 0, "Timeout")
    except FileNotFoundError as e:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", f"{str(e)}. Please install JDK.", elapsed, 0, "Error")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", str(e), elapsed, 0, "Error")

def execute_cpp(code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> ExecutionResult:
    start = time.time()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            cpp_file = os.path.join(tmpdir, "main.cpp")
            exe_file = os.path.join(tmpdir, "main.exe")
            with open(cpp_file, 'w', encoding='utf-8') as f:
                f.write(code)
            compile_result = subprocess.run(
                ['g++', cpp_file, '-o', exe_file, '-std=c++17'],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if compile_result.returncode != 0:
                elapsed = int((time.time() - start) * 1000)
                return ExecutionResult(False, "", (compile_result.stderr or "")[:MAX_OUTPUT_SIZE], elapsed, 0, "Compile Error")
            if not os.path.exists(exe_file):
                return ExecutionResult(False, "", "Compilation failed", int((time.time() - start) * 1000), 0, "Compile Error")
            result = subprocess.run(
                [exe_file],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = int((time.time() - start) * 1000)
            if result.returncode == 0:
                return ExecutionResult(True, (result.stdout or "")[:MAX_OUTPUT_SIZE], "", elapsed, 0, "Accepted")
            else:
                return ExecutionResult(False, (result.stdout or "")[:MAX_OUTPUT_SIZE], (result.stderr or "")[:MAX_OUTPUT_SIZE], elapsed, 0, "Runtime Error")
    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", "Time Limit Exceeded", elapsed, 0, "Timeout")
    except FileNotFoundError as e:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", f"{str(e)}. Please install MinGW/GCC.", elapsed, 0, "Error")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(False, "", str(e), elapsed, 0, "Error")

def execute_code(language: str, code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> ExecutionResult:
    lang = language.lower()
    if lang == "python":
        return execute_python(code, stdin, timeout)
    elif lang == "javascript":
        return execute_javascript(code, stdin, timeout)
    elif lang == "java":
        return execute_java(code, stdin, timeout)
    elif lang == "cpp":
        return execute_cpp(code, stdin, timeout)
    else:
        return ExecutionResult(False, "", f"Unsupported language: {language}", 0, 0, "Error")