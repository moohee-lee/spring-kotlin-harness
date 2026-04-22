#!/usr/bin/env python3
"""Spring Boot Kotlin 헥사고날 프로젝트 구조 참고 점검 스크립트."""

from __future__ import annotations

import argparse
from pathlib import Path


CORE_PACKAGES = [
    "adapter/input/web",
    "adapter/output",
    "application/port/input",
    "application/port/output",
    "application/service",
    "domain",
    "common/config",
    "common/constant",
    "common/enums",
    "common/errors",
    "common/exception",
    "common/extensions",
    "common/utils",
]

RESOURCE_PATHS = [
    "src/main/resources/errors",
    "src/main/resources/enums",
    "src/main/resources/messages",
    "src/main/resources/validations",
]

BUILD_FILES = [
    "build.gradle.kts",
    "settings.gradle.kts",
]


def package_dir(project_root: Path, base_package: str) -> Path:
    package_path = Path(*base_package.split("."))
    return project_root / "src/main/kotlin" / package_path


def status_line(label: str, path: Path) -> str:
    if path.exists():
        return f"PASS {label}: {path}"
    return f"MISSING {label}: {path}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Spring Boot Kotlin 헥사고날 백엔드의 권장 package family를 점검합니다.",
    )
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--base-package", required=True, help="예: com.example.skeleton")
    args = parser.parse_args()

    root = args.project_root.resolve()
    base = package_dir(root, args.base_package)

    print(f"프로젝트 루트: {root}")
    print(f"Base package 디렉터리: {base}")
    print()

    missing = 0

    for rel in BUILD_FILES:
        path = root / rel
        print(status_line("build", path))
        missing += 0 if path.exists() else 1

    for rel in CORE_PACKAGES:
        path = base / rel
        print(status_line("package", path))
        missing += 0 if path.exists() else 1

    for rel in RESOURCE_PATHS:
        path = root / rel
        print(status_line("resource", path))
        missing += 0 if path.exists() else 1

    print()
    if missing:
        print(f"요약: 권장 경로 {missing}개가 없습니다.")
        print("이 결과는 참고용입니다. partial 또는 multi-module 프로젝트에서는 일부 경로를 의도적으로 생략할 수 있습니다.")
        return 1

    print("요약: skeleton 스타일의 권장 package family가 모두 존재합니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
