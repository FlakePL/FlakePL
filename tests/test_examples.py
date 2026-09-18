from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def run_example(name: str) -> str:
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / name)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(ROOT / "src"),
        },
    )
    if result.returncode != 0:
        raise AssertionError(
            f"{name} failed with exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout


def test_communication_example_runs() -> None:
    output = run_example("communication.py")
    assert "Available transitions:" in output
    assert "Tau()" in output


def test_state_space_example_runs() -> None:
    output = run_example("state_space.py")
    assert "Reachable states:" in output
    assert "TRANSITIONS" in output


def test_epistemic_example_runs() -> None:
    output = run_example("epistemic.py")
    assert "Alice knows p: True" in output
    assert "Bob knows p: False" in output


def test_communication_epistemic_example_runs() -> None:
    output = run_example("communication_epistemic.py")
    assert "Bob knows that he received secret: True" in output


def test_two_phase_commit_example_runs() -> None:
    output = run_example("two_phase_commit.py")
    assert "Correct 2PC" in output
    assert "Buggy coordinator" in output
