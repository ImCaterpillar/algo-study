import subprocess
import tempfile
import os
import time
from dataclasses import dataclass

@dataclass
class SandboxResult:
    success: bool
    output: str
    error: str
    runtime_ms: int
    memory_mb: float
    status: str

DEFAULT_TIMEOUT = 10
MAX_OUTPUT_SIZE = 1024 * 1024
MAX_MEMORY_MB = 256

def create_sandbox_temp_dir():
    tmpdir = tempfile.mkdtemp(prefix="algo_sandbox_")
    return tmpdir

def cleanup_sandbox_temp_dir(tmpdir):
    import shutil
    try:
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass

def execute_sandbox_python(code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> SandboxResult:
    start = time.time()
    tmpdir = None
    try:
        tmpdir = create_sandbox_temp_dir()
        python_file = os.path.join(tmpdir, "sandbox_main.py")
        with open(python_file, 'w', encoding='utf-8') as f:
            f.write(code)
        env = os.environ.copy()
        env['HTTP_PROXY'] = ''
        env['HTTPS_PROXY'] = ''
        env['http_proxy'] = ''
        env['https_proxy'] = ''
        result = subprocess.run(
            ['python', python_file],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tmpdir,
            env=env,
        )
        elapsed = int((time.time() - start) * 1000)
        output = result.stdout[:MAX_OUTPUT_SIZE] if result.stdout else ""
        error = result.stderr[:MAX_OUTPUT_SIZE] if result.stderr else ""
        if result.returncode == 0:
            return SandboxResult(True, output, error, elapsed, 0, "Accepted")
        else:
            if "SyntaxError" in error:
                return SandboxResult(False, output, error, elapsed, 0, "Compile Error")
            elif "ImportError" in error or "ModuleNotFoundError" in error:
                return SandboxResult(False, output, error, elapsed, 0, "Runtime Error")
            else:
                return SandboxResult(False, output, error, elapsed, 0, "Runtime Error")
    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", "Time Limit Exceeded", elapsed, 0, "Timeout")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", str(e), elapsed, 0, "Error")
    finally:
        if tmpdir:
            cleanup_sandbox_temp_dir(tmpdir)

def execute_sandbox_javascript(code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> SandboxResult:
    start = time.time()
    tmpdir = None
    try:
        tmpdir = create_sandbox_temp_dir()
        js_file = os.path.join(tmpdir, "sandbox_main.js")
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(code)
        env = os.environ.copy()
        env['HTTP_PROXY'] = ''
        env['HTTPS_PROXY'] = ''
        env['http_proxy'] = ''
        env['https_proxy'] = ''
        result = subprocess.run(
            ['node', js_file],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tmpdir,
            env=env,
        )
        elapsed = int((time.time() - start) * 1000)
        output = result.stdout[:MAX_OUTPUT_SIZE] if result.stdout else ""
        error = result.stderr[:MAX_OUTPUT_SIZE] if result.stderr else ""
        if result.returncode == 0:
            return SandboxResult(True, output, error, elapsed, 0, "Accepted")
        else:
            return SandboxResult(False, output, error, elapsed, 0, "Runtime Error")
    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", "Time Limit Exceeded", elapsed, 0, "Timeout")
    except FileNotFoundError:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", "Node.js not installed", elapsed, 0, "Error")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", str(e), elapsed, 0, "Error")
    finally:
        if tmpdir:
            cleanup_sandbox_temp_dir(tmpdir)

def execute_sandbox_java(code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> SandboxResult:
    start = time.time()
    tmpdir = None
    try:
        tmpdir = create_sandbox_temp_dir()
        class_name = "SandboxMain"
        java_file = os.path.join(tmpdir, f"{class_name}.java")
        with open(java_file, 'w', encoding='utf-8') as f:
            f.write(code)
        env = os.environ.copy()
        env['HTTP_PROXY'] = ''
        env['HTTPS_PROXY'] = ''
        compile_result = subprocess.run(
            ['javac', java_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if compile_result.returncode != 0:
            elapsed = int((time.time() - start) * 1000)
            compile_error = compile_result.stderr[:MAX_OUTPUT_SIZE]
            return SandboxResult(False, "", compile_error, elapsed, 0, "Compile Error")
        class_file = os.path.join(tmpdir, f"{class_name}.class")
        if not os.path.exists(class_file):
            return SandboxResult(False, "", "Compilation failed", int((time.time() - start) * 1000), 0, "Compile Error")
        result = subprocess.run(
            ['java', '-cp', tmpdir, class_name],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        elapsed = int((time.time() - start) * 1000)
        output = result.stdout[:MAX_OUTPUT_SIZE] if result.stdout else ""
        error = result.stderr[:MAX_OUTPUT_SIZE] if result.stderr else ""
        if result.returncode == 0:
            return SandboxResult(True, output, error, elapsed, 0, "Accepted")
        else:
            return SandboxResult(False, output, error, elapsed, 0, "Runtime Error")
    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", "Time Limit Exceeded", elapsed, 0, "Timeout")
    except FileNotFoundError as e:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", f"{str(e)}. Please install JDK.", elapsed, 0, "Error")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", str(e), elapsed, 0, "Error")
    finally:
        if tmpdir:
            cleanup_sandbox_temp_dir(tmpdir)

def execute_sandbox_cpp(code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> SandboxResult:
    start = time.time()
    tmpdir = None
    try:
        tmpdir = create_sandbox_temp_dir()
        cpp_file = os.path.join(tmpdir, "main.cpp")
        exe_file = os.path.join(tmpdir, "main.exe")
        with open(cpp_file, 'w', encoding='utf-8') as f:
            f.write(code)
        env = os.environ.copy()
        env['HTTP_PROXY'] = ''
        env['HTTPS_PROXY'] = ''
        compile_result = subprocess.run(
            ['g++', cpp_file, '-o', exe_file, '-std=c++17'],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if compile_result.returncode != 0:
            elapsed = int((time.time() - start) * 1000)
            compile_error = compile_result.stderr[:MAX_OUTPUT_SIZE]
            return SandboxResult(False, "", compile_error, elapsed, 0, "Compile Error")
        if not os.path.exists(exe_file):
            return SandboxResult(False, "", "Compilation failed", int((time.time() - start) * 1000), 0, "Compile Error")
        result = subprocess.run(
            [exe_file],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        elapsed = int((time.time() - start) * 1000)
        output = result.stdout[:MAX_OUTPUT_SIZE] if result.stdout else ""
        error = result.stderr[:MAX_OUTPUT_SIZE] if result.stderr else ""
        if result.returncode == 0:
            return SandboxResult(True, output, error, elapsed, 0, "Accepted")
        else:
            return SandboxResult(False, output, error, elapsed, 0, "Runtime Error")
    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", "Time Limit Exceeded", elapsed, 0, "Timeout")
    except FileNotFoundError as e:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", f"{str(e)}. Please install MinGW/GCC.", elapsed, 0, "Error")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return SandboxResult(False, "", str(e), elapsed, 0, "Error")
    finally:
        if tmpdir:
            cleanup_sandbox_temp_dir(tmpdir)

def execute_sandbox(language: str, code: str, stdin: str = "", timeout: int = DEFAULT_TIMEOUT) -> SandboxResult:
    lang = language.lower()
    if lang == "python":
        return execute_sandbox_python(code, stdin, timeout)
    elif lang == "javascript":
        return execute_sandbox_javascript(code, stdin, timeout)
    elif lang == "java":
        return execute_sandbox_java(code, stdin, timeout)
    elif lang == "cpp":
        return execute_sandbox_cpp(code, stdin, timeout)
    else:
        return SandboxResult(False, "", f"Unsupported language: {language}", 0, 0, "Error")