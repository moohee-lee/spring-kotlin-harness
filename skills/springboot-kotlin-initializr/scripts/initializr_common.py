#!/usr/bin/env python3
"""Shared helpers for the Spring Boot Kotlin Initializr skill."""

from __future__ import annotations

import io
import json
import re
import subprocess
import shutil
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


INITIALIZR_URL = "https://start.spring.io"
USER_AGENT = "codex-springboot-kotlin-initializr/1.0"
METADATA_ACCEPT = "application/vnd.initializr.v2.3+json"
CHECKLIST = "SPRING_INITIALIZR_DEPENDENCIES.md"

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

DEFAULT_PLUGIN_VERSIONS = {
    "DETEKT": "2.0.0-alpha.2",
    "KOTLIN": "2.3.20",
    "SPRING_BOOT": "4.0.5",
    "SPRING_DEPENDENCY_MANAGEMENT": "1.1.7",
    "JOOQ": "3.19.31",
    "JIB": "3.5.2",
}
DEFAULT_DEPENDENCY_VERSIONS = {
    "SPRING_RESTDOCS_WEBTESTCLIENT": "4.0.0",
    "MOCKK": "1.14.9",
}
PLUGIN_VERSION_ORDER = [
    "DETEKT",
    "KOTLIN",
    "SPRING_BOOT",
    "SPRING_DEPENDENCY_MANAGEMENT",
    "JOOQ",
    "JIB",
]
DEPENDENCY_VERSION_ORDER = [
    "SPRING_RESTDOCS_WEBTESTCLIENT",
    "MOCKK",
]


class InitializrError(RuntimeError):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fetch_bytes(path: str, params: dict[str, str] | None = None, accept: str | None = None) -> bytes:
    url = path if path.startswith("http") else f"{INITIALIZR_URL}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except Exception:
        command = ["curl", "-fsSL", "-H", f"User-Agent: {USER_AGENT}"]
        if accept:
            command.extend(["-H", f"Accept: {accept}"])
        command.append(url)
        completed = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return completed.stdout


def fetch_json(path: str, params: dict[str, str] | None = None, accept: str | None = None) -> dict[str, Any]:
    data = fetch_bytes(path, params, accept or "application/json")
    return json.loads(data.decode("utf-8"))


def fetch_metadata() -> dict[str, Any]:
    return fetch_json("metadata/client", accept=METADATA_ACCEPT)


def default_from_capability(capability: dict[str, Any], stable_boot: bool = False) -> str | None:
    if "default" in capability:
        return str(capability["default"])
    values = capability.get("values", [])
    for value in values:
        if value.get("default") is True:
            return str(value["id"])
    if stable_boot:
        for value in values:
            version = str(value.get("id", ""))
            if all(marker not in version.upper() for marker in ("SNAPSHOT", "-M", "-RC")):
                return version
    return str(values[0]["id"]) if values else None


def current_artifact(project_root: Path) -> str:
    return project_root.resolve().name


def is_valid_package_segment(value: str) -> bool:
    return bool(IDENTIFIER_RE.match(value))


def suggest_package_segment(value: str) -> str:
    suggestion = re.sub(r"[^A-Za-z0-9_]", "", value).lower()
    if not suggestion:
        return "app"
    if suggestion[0].isdigit():
        return f"app{suggestion}"
    return suggestion


def parse_request_text(text: str | None) -> dict[str, str]:
    result: dict[str, str] = {}
    if not text:
        return result
    for part in text.split(","):
        item = part.strip()
        if not item:
            continue
        if "=" not in item:
            raise InitializrError(f"Invalid request item: {item!r}. Expected key=value.")
        key, value = item.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def validate_package_segment(value: str, label: str) -> None:
    if not is_valid_package_segment(value):
        raise InitializrError(
            f"{label}={value!r} is not a valid Kotlin package segment. "
            "Use letters, digits, or underscore, and do not start with a digit. Hyphens are not allowed."
        )


def validate_group(value: str) -> None:
    parts = value.split(".")
    if not parts or any(not part for part in parts):
        raise InitializrError(f"group={value!r} is not a valid dotted package.")
    for part in parts:
        validate_package_segment(part, "group segment")


def resolve_config(request_text: str | None, project_root: Path, metadata: dict[str, Any]) -> dict[str, str]:
    request = parse_request_text(request_text)
    boot_default = default_from_capability(metadata.get("bootVersion", {}), stable_boot=True)
    java_default = default_from_capability(metadata.get("javaVersion", {}))
    group_default = metadata.get("groupId", {}).get("value", "com.example")

    artifact_request = request.get("artifact", "default") or "default"
    artifact = current_artifact(project_root) if artifact_request == "default" else artifact_request
    group = request.get("group", group_default) or group_default
    boot_request = request.get("boot", "default") or "default"
    java_request = request.get("java", "default") or "default"
    kotlin_request = request.get("kotlin", "default") or "default"

    validate_group(group)
    if artifact_request == "default" and not is_valid_package_segment(artifact):
        suggestion = suggest_package_segment(artifact)
        raise InitializrError(
            f"artifact=default를 사용할 수 없습니다. 현재 폴더명 {artifact!r}은 Kotlin package segment로 유효하지 않습니다. "
            "반드시 artifact를 형식에 맞게 직접 입력해야 합니다. "
            f"예: boot={boot_request}, java={java_request}, kotlin={kotlin_request}, artifact={suggestion}, group={group}"
        )
    validate_package_segment(artifact, "artifact")

    boot_effective = boot_default if boot_request == "default" else boot_request
    java_effective = java_default if java_request == "default" else java_request
    if not boot_effective:
        raise InitializrError("Unable to resolve a Spring Boot version from Initializr metadata.")
    if not java_effective:
        raise InitializrError("Unable to resolve a Java version from Initializr metadata.")

    return {
        "boot_request": boot_request,
        "boot_effective": boot_effective,
        "java_request": java_request,
        "java_effective": java_effective,
        "kotlin_request": kotlin_request,
        "group": group,
        "artifact": artifact,
        "package": f"{group}.{artifact}",
    }


def starter_params(config: dict[str, str], dependencies: list[str] | None = None) -> dict[str, str]:
    params = {
        "type": "gradle-project-kotlin",
        "language": "kotlin",
        "packaging": "jar",
        "configurationFileFormat": "yaml",
        "groupId": config["group"],
        "artifactId": config["artifact"],
        "name": config["artifact"],
        "packageName": config["package"],
    }
    if config.get("boot_request") != "default":
        params["bootVersion"] = config["boot_effective"]
    if config.get("java_request") != "default":
        params["javaVersion"] = config["java_effective"]
    if dependencies:
        params["dependencies"] = ",".join(sorted(set(dependencies)))
    return params


def probe_build_versions(config: dict[str, str]) -> dict[str, str | None]:
    probe_config = dict(config)
    probe_config.update({"group": "com.example", "artifact": "probe", "package": "com.example.probe"})
    data = fetch_bytes("starter.zip", starter_params(probe_config))
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        build_gradle = archive.read("build.gradle.kts").decode("utf-8")
    return extract_build_versions(build_gradle)


def extract_build_versions(build_gradle: str) -> dict[str, str | None]:
    def first(pattern: str) -> str | None:
        match = re.search(pattern, build_gradle)
        return match.group(1) if match else None

    return {
        "kotlin": first(r'kotlin\("jvm"\)\s+version\s+"([^"]+)"'),
        "spring_boot": first(r'id\("org\.springframework\.boot"\)\s+version\s+"([^"]+)"'),
        "dependency_management": first(r'id\("io\.spring\.dependency-management"\)\s+version\s+"([^"]+)"'),
        "java": first(r"JavaLanguageVersion\.of\((\d+)\)"),
    }


def parse_const_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        match.group(1): match.group(2)
        for match in re.finditer(r'const val\s+([A-Z0-9_]+)\s*=\s*"([^"]+)"', read_text(path))
    }


def java_version_expression(version: str | None) -> str:
    if not version:
        return 'JavaVersion.toVersion("17")'
    constant = version.replace(".", "_")
    if re.fullmatch(r"\d+(?:_\d+)?", constant):
        return f"JavaVersion.VERSION_{constant}"
    return f'JavaVersion.toVersion("{version}")'


def ordered_const_items(values: dict[str, str], preferred_order: list[str]) -> list[tuple[str, str]]:
    ordered = [(key, values[key]) for key in preferred_order if key in values]
    ordered_keys = {key for key, _ in ordered}
    ordered.extend((key, values[key]) for key in sorted(values) if key not in ordered_keys)
    return ordered


def format_const_object(name: str, values: dict[str, str], preferred_order: list[str]) -> str:
    lines = [f"object {name} {{"]
    for key, value in ordered_const_items(values, preferred_order):
        lines.append(f'    const val {key} = "{value}"')
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_buildsrc_build_gradle(project_root: Path, skeleton_root: Path | None = None) -> None:
    source = skeleton_root / "buildSrc/build.gradle.kts" if skeleton_root else None
    if source and source.exists():
        shutil.copy2(source, project_root / "buildSrc/build.gradle.kts")
        return
    write_text(
        project_root / "buildSrc/build.gradle.kts",
        """plugins {
    `kotlin-dsl`
}

repositories {
    mavenCentral()
}
""",
    )


def write_buildsrc_version_management(
    project_root: Path,
    versions: dict[str, str | None],
    config: dict[str, str],
    skeleton_root: Path | None = None,
) -> None:
    """Write skeleton-style buildSrc version files for Initializr output."""
    buildsrc = project_root / "buildSrc"
    skeleton_buildsrc = skeleton_root / "buildSrc" if skeleton_root else None
    if skeleton_buildsrc and skeleton_buildsrc.exists():
        shutil.copytree(skeleton_buildsrc, buildsrc, dirs_exist_ok=True)
    else:
        buildsrc.mkdir(parents=True, exist_ok=True)

    write_buildsrc_build_gradle(project_root, skeleton_root)

    skeleton_src = skeleton_buildsrc / "src/main/kotlin" if skeleton_buildsrc else None
    skeleton_plugin_versions = parse_const_values(skeleton_src / "PluginVersions.kt") if skeleton_src else {}
    skeleton_dependency_versions = parse_const_values(skeleton_src / "DependencyVersions.kt") if skeleton_src else {}

    kotlin_version = config.get("kotlin_request")
    if not kotlin_version or kotlin_version == "default":
        kotlin_version = versions.get("kotlin") or skeleton_plugin_versions.get("KOTLIN") or DEFAULT_PLUGIN_VERSIONS["KOTLIN"]

    plugin_versions = dict(DEFAULT_PLUGIN_VERSIONS)
    plugin_versions.update(skeleton_plugin_versions)
    plugin_versions.update(
        {
            "KOTLIN": kotlin_version,
            "SPRING_BOOT": versions.get("spring_boot") or config["boot_effective"],
            "SPRING_DEPENDENCY_MANAGEMENT": (
                versions.get("dependency_management")
                or skeleton_plugin_versions.get("SPRING_DEPENDENCY_MANAGEMENT")
                or DEFAULT_PLUGIN_VERSIONS["SPRING_DEPENDENCY_MANAGEMENT"]
            ),
        }
    )

    dependency_versions = dict(DEFAULT_DEPENDENCY_VERSIONS)
    dependency_versions.update(skeleton_dependency_versions)

    write_text(
        buildsrc / "src/main/kotlin/BuildVersions.kt",
        f"""import org.gradle.api.JavaVersion

/**
 * @author MooHee Lee
 */
object BuildVersions {{
    val JAVA = {java_version_expression(versions.get("java") or config["java_effective"])}
}}
""",
    )
    write_text(
        buildsrc / "src/main/kotlin/PluginVersions.kt",
        format_const_object("PluginVersions", plugin_versions, PLUGIN_VERSION_ORDER),
    )
    write_text(
        buildsrc / "src/main/kotlin/DependencyVersions.kt",
        format_const_object("DependencyVersions", dependency_versions, DEPENDENCY_VERSION_ORDER),
    )


def patch_initializr_build_gradle_version_refs(project_root: Path) -> dict[str, str | None]:
    path = project_root / "build.gradle.kts"
    text = read_text(path)
    versions = extract_build_versions(text)
    text = re.sub(r'kotlin\("jvm"\)\s+version\s+"[^"]+"', 'kotlin("jvm") version PluginVersions.KOTLIN', text)
    text = re.sub(r'kotlin\("plugin\.spring"\)\s+version\s+"[^"]+"', 'kotlin("plugin.spring") version PluginVersions.KOTLIN', text)
    text = re.sub(r'id\("org\.springframework\.boot"\)\s+version\s+"[^"]+"', 'id("org.springframework.boot") version PluginVersions.SPRING_BOOT', text)
    text = re.sub(r'id\("io\.spring\.dependency-management"\)\s+version\s+"[^"]+"', 'id("io.spring.dependency-management") version PluginVersions.SPRING_DEPENDENCY_MANAGEMENT', text)
    text = re.sub(r"JavaLanguageVersion\.of\(\d+\)", "JavaLanguageVersion.of(BuildVersions.JAVA.majorVersion.toInt())", text)
    write_text(path, text)
    return versions


def metadata_dependency_ids(metadata: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for group in metadata.get("dependencies", {}).get("values", []):
        for value in group.get("values", []):
            if "id" in value:
                ids.add(value["id"])
    return ids


def parse_checklist(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    meta_match = re.search(r"<!--\s*spring-initializr:\s*(.*?)\s*-->", text)
    if not meta_match:
        raise InitializrError(f"{path} does not contain spring-initializr metadata comment.")

    config: dict[str, str] = {}
    for item in meta_match.group(1).split():
        if "=" in item:
            key, value = item.split("=", 1)
            config[key] = value

    listed = set(re.findall(r"- \[[ xX]\]\s+`([^`]+)`", text))
    selected = re.findall(r"- \[[xX]\]\s+`([^`]+)`", text)
    unknown = sorted(set(selected) - listed)
    if unknown:
        raise InitializrError(f"Checked dependencies are not listed in the checklist: {', '.join(unknown)}")

    required = {"boot_effective", "java_effective", "group", "artifact", "package"}
    missing = sorted(required - set(config))
    if missing:
        raise InitializrError(f"Checklist metadata is missing: {', '.join(missing)}")

    return {"config": config, "dependencies": selected}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
