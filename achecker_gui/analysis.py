"""Run the bundled AChecker CLI on a bytecode file and parse the result."""

import os
import subprocess
import sys

from .report import Report, parse_report

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACHECKER_SCRIPT = os.path.join(BASE_DIR, "bin", "achecker.py")


class AnalysisError(Exception):
    """Raised when AChecker could not be run or exited with an error."""


def run_analysis(
    file_path,
    *,
    timeout,
    memory_gb=6,
    script=ACHECKER_SCRIPT,
    cwd=BASE_DIR,
    runner=subprocess.run,
) -> Report:
    cmd = [sys.executable, script, "-f", file_path, "-b", "-m", str(memory_gb)]
    try:
        proc = runner(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise AnalysisError(f"Analysis timed out after {timeout} seconds.") from None
    except OSError as exc:
        raise AnalysisError(f"Could not start AChecker: {exc}") from exc

    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "").strip()
        raise AnalysisError(message or "AChecker exited with an error.")

    return parse_report(proc.stdout)
