#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from initializr_common import (
    InitializrError,
    current_artifact,
    fetch_metadata,
    is_valid_package_segment,
    parse_request_text,
    probe_build_versions,
    resolve_config,
    suggest_package_segment,
)


def request_text(values: dict[str, str]) -> str:
    order = ["boot", "java", "kotlin", "artifact", "group"]
    return ", ".join(f"{key}={values[key]}" for key in order if key in values)


def main() -> int:
    parser = argparse.ArgumentParser(description="Spring Initializr 추천값을 조회합니다.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--request", help="예: boot=default, java=default, kotlin=default, artifact=default, group=com.example")
    args = parser.parse_args()

    metadata = fetch_metadata()
    request = parse_request_text(args.request)
    artifact_default = current_artifact(args.project_root)
    artifact_default_valid = is_valid_package_segment(artifact_default)
    artifact_suggestion = suggest_package_segment(artifact_default)

    resolution_request = dict(request)
    artifact_request = resolution_request.get("artifact", "default") or "default"
    default_artifact_requires_input = artifact_request == "default" and not artifact_default_valid
    if default_artifact_requires_input:
        resolution_request["artifact"] = artifact_suggestion

    config = resolve_config(request_text(resolution_request), args.project_root, metadata)

    probe = {}
    try:
        probe = probe_build_versions(config)
    except Exception as exc:  # 추천 출력은 metadata만으로도 가능해야 한다.
        probe = {"error": str(exc)}

    print("추천 생성 값")
    print(f"- Spring Boot: {config['boot_effective']}" + (" (Initializr default)" if config["boot_request"] == "default" else ""))
    print(f"- Java: {config['java_effective']}" + (" (Initializr default)" if config["java_request"] == "default" else ""))
    if "error" in probe:
        print(f"- Kotlin: probe 실패, Initializr 생성 기본값을 사용하세요. ({probe['error']})")
    else:
        print(f"- Kotlin: Spring Boot {config['boot_effective']} 생성 기본값은 {probe.get('kotlin') or 'unknown'}")
        if probe.get("java") and probe["java"] != config["java_effective"] and config["java_request"] != "default":
            print(f"- Java 생성 확인: 요청 {config['java_effective']} / build.gradle.kts 생성값 {probe['java']}")
    if artifact_default_valid:
        print(f"- Artifact 기본값: {artifact_default}")
    else:
        print(f"- Artifact 기본값: {artifact_default} (사용 불가: Kotlin package segment 형식 위반)")
        print(f"- Artifact 입력 필수: artifact={artifact_suggestion}")
    print()
    if default_artifact_requires_input:
        print("현재 폴더명으로는 artifact=default를 사용할 수 없습니다.")
        print("반드시 artifact를 형식에 맞게 직접 입력해야 계속 진행할 수 있습니다.")
        print()
    print("입력 형식:")
    print("boot=<boot-version>, java=<java-version>, kotlin=default, artifact=default, group=com.example")
    if default_artifact_requires_input:
        print("예:")
        print(
            "boot="
            + request.get("boot", "default")
            + ", java="
            + request.get("java", "default")
            + ", kotlin="
            + request.get("kotlin", "default")
            + ", artifact="
            + artifact_suggestion
            + ", group="
            + request.get("group", "com.example")
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InitializrError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
