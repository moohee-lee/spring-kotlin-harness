#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from initializr_common import CHECKLIST, InitializrError, fetch_json, fetch_metadata, resolve_config


def render_dependency(value: dict, resolved_ids: set[str]) -> str | None:
    dep_id = value.get("id")
    if not dep_id or dep_id not in resolved_ids:
        return None
    name = value.get("name", dep_id)
    description = value.get("description", "").replace("\n", " ").strip()
    suffix = f": {description}" if description else ""
    version_range = value.get("versionRange")
    range_text = f" _(range: {version_range})_" if version_range else ""
    return f"- [ ] `{dep_id}` - {name}{suffix}{range_text}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Initializr dependency 체크박스 파일을 생성합니다.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", type=Path, default=Path(CHECKLIST))
    args = parser.parse_args()

    metadata = fetch_metadata()
    config = resolve_config(args.request, args.project_root, metadata)
    deps = fetch_json("dependencies", {"bootVersion": config["boot_effective"]})
    resolved_ids = set(deps.get("dependencies", {}).keys())

    lines = [
        "# Spring Initializr Dependencies",
        "",
        "<!-- spring-initializr: "
        f"boot_request={config['boot_request']} boot_effective={config['boot_effective']} "
        f"java_request={config['java_request']} java_effective={config['java_effective']} "
        f"kotlin_request={config['kotlin_request']} group={config['group']} "
        f"artifact={config['artifact']} package={config['package']} -->",
        "",
        "## 생성 값",
        "",
        f"- Spring Boot: {config['boot_request']} -> {config['boot_effective']}",
        f"- Java: {config['java_request']} -> {config['java_effective']}",
        f"- Kotlin: {config['kotlin_request']}",
        f"- Group: {config['group']}",
        f"- Artifact: {config['artifact']}",
        f"- Package: {config['package']}",
        "",
        "## 사용 방법",
        "",
        "- 설치할 dependency의 `[ ]`를 `[x]`로 바꾸세요.",
        "- backtick 안의 dependency id는 수정하지 마세요.",
        "- 수정을 마치면 Codex에게 계속 진행하라고 알려주세요.",
        "",
    ]

    for group in metadata.get("dependencies", {}).get("values", []):
        rendered = [render_dependency(value, resolved_ids) for value in group.get("values", [])]
        rendered = [line for line in rendered if line]
        if not rendered:
            continue
        lines.append(f"## {group.get('name', 'Dependencies')}")
        lines.append("")
        lines.extend(rendered)
        lines.append("")

    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Created {args.output}")
    print("사용자가 체크박스를 수정한 뒤 계속 진행하세요.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InitializrError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
