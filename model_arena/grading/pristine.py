from __future__ import annotations

import filecmp
import shutil
import subprocess
from pathlib import Path


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def workspace_diff(base: Path, changed: Path) -> dict[str, tuple[str, str]]:
    """Retorna mapa rel_path -> (status, content) para arquivos alterados."""
    diff: dict[str, tuple[str, str]] = {}
    if not base.is_dir():
        return diff
    for path in changed.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(changed).as_posix()
        orig = base / rel
        if not orig.is_file():
            diff[rel] = ("added", path.read_text(encoding="utf-8", errors="replace"))
        elif not filecmp.cmp(orig, path, shallow=False):
            diff[rel] = ("modified", path.read_text(encoding="utf-8", errors="replace"))
    return diff


def apply_diff_to_pristine(pristine: Path, diff: dict[str, tuple[str, str]], grade_work: Path) -> None:
    copy_tree(pristine, grade_work)
    for rel, (_status, content) in diff.items():
        target = grade_work / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def prepare_grade_workspace(
    *,
    hidden_fixtures: Path,
    workspace_base: Path,
    workspace_current: Path,
    grade_work: Path,
) -> dict[str, tuple[str, str]]:
    diff = workspace_diff(workspace_base, workspace_current)
    apply_diff_to_pristine(hidden_fixtures, diff, grade_work)
    return diff


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> dict[str, object]:
    import os

    merged = dict(os.environ)
    if env:
        merged.update(env)
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged,
            check=False,
        )
        return {
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": completed.stdout[:20_000],
            "stderr": completed.stderr[:20_000],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit_code": None, "stdout": "", "stderr": "timeout", "timed_out": True}
