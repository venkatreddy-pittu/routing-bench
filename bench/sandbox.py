"""Run model-written code against pytest in a throwaway dir.

This is NOT a security boundary. It limits time/memory (on Unix) and strips cloud credentials from the
environment, but generated code can still touch your filesystem and network. For anything beyond a
personal experiment, run the whole benchmark inside Docker with no network access.
"""
import os
import subprocess
import sys
import tempfile

try:
    import resource
except ImportError:  # Windows
    resource = None

TIMEOUT = 15


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))


def run_tests(code, tests, timeout=TIMEOUT):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("AWS_", "OLLAMA", "BEDROCK"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "solution.py"), "w") as f:
            f.write(code)
        with open(os.path.join(d, "test_solution.py"), "w") as f:
            f.write(tests)
        try:
            p = subprocess.run(
                [sys.executable, "-m", "pytest", "-x", "-q", "--no-header", "-p", "no:cacheprovider", "test_solution.py"],
                cwd=d, capture_output=True, text=True, timeout=timeout, env=env,
                preexec_fn=_limits if resource else None,
            )
        except subprocess.TimeoutExpired:
            return False, f"TIMEOUT: tests exceeded {timeout}s"
    return p.returncode == 0, (p.stdout + p.stderr)[-1500:]


def classify(output):
    if output.startswith("TIMEOUT"):
        return "timeout"
    if "SyntaxError" in output or "IndentationError" in output:
        return "syntax_error"
    return "test_failure"
