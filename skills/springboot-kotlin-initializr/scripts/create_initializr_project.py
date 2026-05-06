#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from initializr_common import (
    CHECKLIST,
    InitializrError,
    fetch_bytes,
    generated_version_mismatches,
    patch_initializr_build_gradle_version_refs,
    read_json,
    starter_params,
    write_buildsrc_version_management,
)


def safe_extract(archive: zipfile.ZipFile, target: Path) -> None:
    root = target.resolve()
    for member in archive.infolist():
        destination = (target / member.filename).resolve()
        if not str(destination).startswith(str(root)):
            raise InitializrError(f"Unsafe zip entry: {member.filename}")
    archive.extractall(target)


def copy_generated(source: Path, target: Path, force: bool) -> None:
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        destination = target / relative
        if item.is_dir():
            if destination.exists() and not destination.is_dir():
                raise InitializrError(f"Refusing to replace existing file with directory: {destination}")
            destination.mkdir(parents=True, exist_ok=True)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not force:
            raise InitializrError(f"Refusing to overwrite existing file: {destination}")
        if destination.exists() and force:
            destination.unlink()
        shutil.copy2(item, destination)


def find_conflicts(source: Path, target: Path) -> list[Path]:
    conflicts: list[Path] = []
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        destination = target / relative
        if item.is_dir():
            if destination.exists() and not destination.is_dir():
                conflicts.append(destination)
            continue
        if destination.exists():
            conflicts.append(destination)
    return conflicts


def ensure_target_exists(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Spring Initializr starter.zip으로 프로젝트를 생성합니다.")
    parser.add_argument("--selection-json", type=Path, required=True)
    parser.add_argument("--target-dir", type=Path, default=Path("."))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--keep-checklist", action="store_true")
    args = parser.parse_args()

    selection = read_json(args.selection_json)
    config = selection["config"]
    dependencies = selection.get("dependencies", [])
    params = starter_params(config, dependencies)

    target = args.target_dir.resolve()
    ensure_target_exists(target)
    if (target / "buildSrc").exists() and not args.force:
        raise InitializrError(
            f"Refusing to overwrite existing buildSrc version management: {target / 'buildSrc'}\n"
            "Re-run with --force only after user approval."
        )

    data = fetch_bytes("starter.zip", params)
    with tempfile.TemporaryDirectory(prefix="spring-initializr-") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            safe_extract(archive, tmp_path)
        conflicts = find_conflicts(tmp_path, target)
        if conflicts and not args.force:
            conflict_list = "\n".join(f"  - {path}" for path in conflicts[:50])
            more = f"\n  ... and {len(conflicts) - 50} more" if len(conflicts) > 50 else ""
            raise InitializrError(
                "Generated project would overwrite existing paths:\n"
                + conflict_list
                + more
                + "\nRe-run with --force only after user approval."
            )
        copy_generated(tmp_path, target, args.force)

    gradlew = target / "gradlew"
    if gradlew.exists():
        gradlew.chmod(gradlew.stat().st_mode | 0o755)

    build_gradle = target / "build.gradle.kts"
    if build_gradle.exists():
        versions = patch_initializr_build_gradle_version_refs(target)
        write_buildsrc_version_management(target, versions, config)
        for mismatch in generated_version_mismatches(versions, config):
            print(f"WARN: {mismatch}")

    checklist = target / CHECKLIST
    if checklist.exists() and not args.keep_checklist:
        checklist.unlink()

    print(f"Created Spring Initializr project in {target}")
    print("Configured Gradle version management under buildSrc")
    print(f"Dependencies: {', '.join(dependencies) if dependencies else '(none selected)'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InitializrError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
