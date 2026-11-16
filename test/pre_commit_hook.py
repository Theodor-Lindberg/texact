import subprocess
import sys
from pathlib import Path


def test_published_pre_commit_hook(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parent.parent
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    config = tmp_path / ".pre-commit-config.yaml"
    config.write_text(
        f"repos:\n- repo: {repository.as_uri()}\n"
        f"  rev: {revision}\n  hooks:\n  - id: texact-check\n",
        encoding="utf-8",
    )
    (tmp_path / "clean.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
    (tmp_path / "invalid.tex").write_text("asic\n", encoding="utf-8")

    def run_hook(filename: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pre_commit",
                "run",
                "texact-check",
                "--verbose",
                "--files",
                filename,
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )

    clean = run_hook("clean.tex")
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert "All passed" in clean.stdout
    assert "Skipped" not in clean.stdout

    invalid = run_hook("invalid.tex")
    assert invalid.returncode != 0, invalid.stdout + invalid.stderr
    assert "[CAS001]" in invalid.stdout
