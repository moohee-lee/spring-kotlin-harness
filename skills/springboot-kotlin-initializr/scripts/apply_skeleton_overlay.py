#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
import tempfile
import urllib.parse
import zipfile
from pathlib import Path

from initializr_common import (
    InitializrError,
    extract_build_versions,
    fetch_bytes,
    fetch_json,
    read_json,
    write_buildsrc_version_management,
)


SOURCE_PACKAGE = "com.example.skeleton"


def package_path(package_name: str) -> Path:
    return Path(*package_name.split("."))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_extract_zip(data: bytes, target: Path) -> Path:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = target.resolve()
        for member in archive.infolist():
            destination = (target / member.filename).resolve()
            if not str(destination).startswith(str(root)):
                raise InitializrError(f"Unsafe zip entry: {member.filename}")
        archive.extractall(target)
    entries = [entry for entry in target.iterdir() if entry.is_dir()]
    if len(entries) != 1:
        raise InitializrError("Unable to locate extracted skeleton root.")
    return entries[0]


def github_archive_url(source: str, ref: str) -> str:
    parsed = urllib.parse.urlparse(source)
    if parsed.netloc.lower() != "github.com":
        return source
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise InitializrError(f"Invalid GitHub repository URL: {source}")
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if len(parts) >= 5 and parts[2] in {"archive", "refs"}:
        return source
    if len(parts) >= 4 and parts[2] in {"tree", "blob"}:
        ref = "/".join(parts[3:])
    return f"https://github.com/{owner}/{repo}/archive/refs/heads/{ref}.zip"


def load_skeleton(args: argparse.Namespace) -> tuple[tempfile.TemporaryDirectory[str] | None, Path]:
    source = args.skeleton_source
    if not source:
        raise InitializrError("Missing --skeleton-source. Provide a GitHub repository/archive URL or local directory.")

    local = Path(source).expanduser()
    if local.exists():
        root = local.resolve()
        if not root.exists():
            raise InitializrError(f"Skeleton directory does not exist: {root}")
        return None, root

    archive_url = github_archive_url(source, args.skeleton_ref)
    tmp = tempfile.TemporaryDirectory(prefix="springboot-kotlin-skeleton-")
    root = safe_extract_zip(fetch_bytes(archive_url), Path(tmp.name))
    return tmp, root


def replace_package(text: str, target_package: str) -> str:
    return text.replace(SOURCE_PACKAGE, target_package).replace("SampleStatus", "Status")


def copy_text_file(source: Path, destination: Path, target_package: str) -> None:
    write_text(destination, replace_package(read_text(source), target_package))


def copy_tree(source: Path, destination: Path, target_package: str, exclude) -> list[Path]:
    copied: list[Path] = []
    for path in source.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(source)
        if exclude(rel, path):
            continue
        target = destination / rel
        copy_text_file(path, target, target_package)
        copied.append(target)
    return copied


def exclude_sample(rel: Path, path: Path) -> bool:
    text = str(rel)
    name = path.name
    return (
        "/sample/" in f"/{text}/"
        or text.startswith("sample/")
        or name.startswith("Sample")
        or name in {"SampleErrorCode.kt", "SampleNotFoundException.kt"}
    )


def strip_error_properties(source: Path, destination: Path) -> None:
    lines: list[str] = []
    for line in read_text(source).splitlines():
        if line.strip() == "# Sample Error":
            break
        if line.startswith("sample."):
            continue
        lines.append(line)
    write_text(destination, "\n".join(lines).rstrip() + "\n")


def write_resource_placeholders(project_root: Path, artifact: str) -> None:
    write_text(project_root / "src/main/resources/enums/enum.properties", "# Enum labels\n")
    write_text(project_root / "src/main/resources/db/schema.sql", "-- Add DDL statements here.\n")
    write_text(
        project_root / "src/main/resources/application.yaml",
        "\n".join(
            [
                "server:",
                "  port: 18080",
                "",
                "spring:",
                "  application:",
                f"    name: {artifact}",
                "  messages:",
                "    basename: messages/message,validations/validation,enums/enum,errors/error",
                "    fallback-to-system-locale: false",
                "  web:",
                "    locale: ko_KR",
                "",
                "  datasource:",
                "    write:",
                "      hikari:",
                "        pool-name: write-hikari-pool",
                "        jdbc-url: jdbc:h2:mem:app-write;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE;INIT=RUNSCRIPT FROM 'classpath:db/schema.sql'",
                "        username: sa",
                "        password:",
                "        driver-class-name: org.h2.Driver",
                "        minimum-idle: 5",
                "        maximum-pool-size: 20",
                "    read:",
                "      hikari:",
                "        pool-name: read-hikari-pool",
                "        jdbc-url: jdbc:h2:mem:app-read;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE;INIT=RUNSCRIPT FROM 'classpath:db/schema.sql'",
                "        username: sa",
                "        password:",
                "        driver-class-name: org.h2.Driver",
                "        minimum-idle: 5",
                "        maximum-pool-size: 20",
                "",
                "management:",
                "  endpoints:",
                "    web:",
                "      exposure:",
                '        include: "*"',
                "",
                "logging:",
                "  pattern:",
                '    level: "%5p [traceId:%X{traceId:-}]"',
                "  level:",
                "    org.springframework: ERROR",
                "    org.springframework.web.reactive.function.client: DEBUG",
                "    org.springframework.transaction: DEBUG",
                "",
            ]
        ),
    )


def write_buildsrc(project_root: Path, skeleton_root: Path, versions: dict[str, str | None], config: dict[str, str]) -> None:
    write_buildsrc_version_management(project_root, versions, config, skeleton_root)


def adapt_for_java_version(project_root: Path, config: dict[str, str]) -> None:
    try:
        java_version = int(config["java_effective"])
    except ValueError:
        return
    if java_version >= 21:
        return

    database_config = project_root / "src/main/kotlin" / package_path(config["package"]) / "adapter/output/persistence/config/DatabasePersistenceConfiguration.kt"
    if database_config.exists():
        text = read_text(database_config)
        text = text.replace(
            "Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()",
            "Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors().coerceAtLeast(2)).asCoroutineDispatcher()",
        )
        write_text(database_config, text)

    transaction_adapter = project_root / "src/main/kotlin" / package_path(config["package"]) / "adapter/output/transaction/TransactionalExecutorAdapter.kt"
    if transaction_adapter.exists():
        text = read_text(transaction_adapter)
        text = text.replace("Thread.currentThread().isVirtual", "false")
        write_text(transaction_adapter, text)


def ensure_imports(text: str) -> str:
    imports = [
        "import dev.detekt.gradle.Detekt",
        "import dev.detekt.gradle.DetektCreateBaselineTask",
        "import org.jetbrains.kotlin.gradle.dsl.JvmTarget",
    ]
    existing = [line for line in imports if line in text]
    missing = [line for line in imports if line not in existing]
    if not missing:
        return text
    return "\n".join(missing) + "\n" + text


def ensure_line_in_block(text: str, block_name: str, marker: str, line: str) -> str:
    pattern = re.compile(rf"^{re.escape(block_name)}\s*\{{", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return text
    start = match.end()
    depth = 1
    index = start
    while index < len(text) and depth:
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        index += 1
    block = text[match.start():index]
    if marker in block:
        return text
    insert_at = text.find("\n", match.start()) + 1
    return text[:insert_at] + line + "\n" + text[insert_at:]


def ensure_dependency(text: str, configuration: str, coordinate: str) -> str:
    exact = f'{configuration}("{coordinate}")'
    if exact in text:
        return text
    return ensure_line_in_block(text, "dependencies", exact, f'\t{configuration}("{coordinate}")')


def dependency_line_for_scope(scope: str | None) -> str:
    return {
        "compile": "implementation",
        "runtime": "runtimeOnly",
        "annotationProcessor": "annotationProcessor",
        "testCompile": "testImplementation",
        "testRuntime": "testRuntimeOnly",
    }.get(scope or "compile", "implementation")


def patch_build_gradle(project_root: Path, config: dict[str, str], dependencies: list[str]) -> None:
    path = project_root / "build.gradle.kts"
    text = read_text(path)
    versions = extract_build_versions(text)

    text = ensure_imports(text)
    text = re.sub(r'kotlin\("jvm"\)\s+version\s+"[^"]+"', 'kotlin("jvm") version PluginVersions.KOTLIN', text)
    text = re.sub(r'kotlin\("plugin\.spring"\)\s+version\s+"[^"]+"', 'kotlin("plugin.spring") version PluginVersions.KOTLIN', text)
    text = re.sub(r'id\("org\.springframework\.boot"\)\s+version\s+"[^"]+"', 'id("org.springframework.boot") version PluginVersions.SPRING_BOOT', text)
    text = re.sub(r'id\("io\.spring\.dependency-management"\)\s+version\s+"[^"]+"', 'id("io.spring.dependency-management") version PluginVersions.SPRING_DEPENDENCY_MANAGEMENT', text)
    text = ensure_line_in_block(text, "plugins", 'id("dev.detekt")', '\tid("dev.detekt") version PluginVersions.DETEKT')
    text = ensure_line_in_block(text, "plugins", 'id("org.jooq.jooq-codegen-gradle")', '\tid("org.jooq.jooq-codegen-gradle") version PluginVersions.JOOQ')
    text = re.sub(r"JavaLanguageVersion\.of\(\d+\)", "JavaLanguageVersion.of(BuildVersions.JAVA.majorVersion.toInt())", text)

    if "configurations {" not in text:
        text += """

configurations {
    compileOnly {
        extendsFrom(configurations.annotationProcessor.get())
    }
}
"""

    resolved = fetch_json("dependencies", {"bootVersion": config["boot_effective"]}).get("dependencies", {})
    required_ids = ["actuator", "webflux", "validation", "jooq", "configuration-processor", "h2", "spring-webclient"]
    for dep_id in sorted(set(required_ids + dependencies)):
        dep = resolved.get(dep_id)
        if not dep:
            print(f"WARN: Initializr dependency is not available for Boot {config['boot_effective']}: {dep_id}")
            continue
        coordinate = f"{dep['groupId']}:{dep['artifactId']}"
        text = ensure_dependency(text, dependency_line_for_scope(dep.get("scope")), coordinate)

    for configuration, coordinate in [
        ("implementation", "io.micrometer:context-propagation"),
        ("implementation", "io.projectreactor.kotlin:reactor-kotlin-extensions"),
        ("implementation", "org.jetbrains.kotlinx:kotlinx-coroutines-reactor"),
        ("implementation", "tools.jackson.module:jackson-module-kotlin"),
        ("jooqCodegen", "com.h2database:h2"),
        ("jooqCodegen", "org.jooq:jooq-meta-extensions"),
    ]:
        text = ensure_dependency(text, configuration, coordinate)

    if "val jooqGeneratedDir" not in text:
        text += '\nval jooqGeneratedDir = layout.buildDirectory.dir("generated-src/jooq/main")\n'
    if "jooq {" not in text:
        text += f"""

jooq {{
    configuration {{
        generator {{
            name = "org.jooq.codegen.KotlinGenerator"
            database {{
                name = "org.jooq.meta.extensions.ddl.DDLDatabase"
                properties {{
                    property {{
                        key = "scripts"
                        value = "src/main/resources/db/schema.sql"
                    }}
                    property {{
                        key = "defaultNameCase"
                        value = "lower"
                    }}
                    property {{
                        key = "unqualifiedSchema"
                        value = "none"
                    }}
                }}
            }}
            generate {{
                isDeprecated = false
                isRecords = true
                isPojos = false
                isDaos = false
                isKotlinNotNullPojoAttributes = true
                isKotlinNotNullRecordAttributes = false
            }}
            target {{
                packageName = "{config['package']}.jooq.generated"
                directory = jooqGeneratedDir.get().asFile.absolutePath
            }}
        }}
    }}
}}
"""
    if 'kotlin.srcDir(jooqGeneratedDir)' not in text:
        text += """

kotlin {
    jvmToolchain(BuildVersions.JAVA.majorVersion.toInt())
    sourceSets.named("main") {
        kotlin.srcDir(jooqGeneratedDir)
    }
    compilerOptions {
        jvmTarget = JvmTarget.fromTarget(BuildVersions.JAVA.majorVersion)
    }
}
"""
    if "detekt {" not in text:
        text += """

detekt {
    toolVersion = PluginVersions.DETEKT
    config.setFrom(files("$projectDir/config/detekt/detekt.yml"))
    buildUponDefaultConfig = true
    parallel = true
    basePath = projectDir
}
"""
    if "tasks.withType<Detekt>()" not in text:
        text += """

tasks.withType<Detekt>().configureEach {
    jvmTarget = BuildVersions.JAVA.majorVersion
    exclude("**/build/**", "**/generated-src/**")
}

tasks.withType<DetektCreateBaselineTask>().configureEach {
    exclude("**/build/**", "**/generated-src/**")
}
"""
    if 'dependsOn(tasks.named("jooqCodegen"))' not in text:
        text += """

tasks.named("compileKotlin") {
    dependsOn(tasks.named("jooqCodegen"))
}
"""
    write_text(path, text)
    return versions


def scan_for_leftovers(project_root: Path) -> list[str]:
    leftovers: list[str] = []
    for path in (project_root / "src/main/kotlin").rglob("*.kt"):
        text = read_text(path)
        if SOURCE_PACKAGE in text or "/sample/" in str(path) or "Sample" in path.name:
            leftovers.append(str(path.relative_to(project_root)))
    return leftovers


def main() -> int:
    parser = argparse.ArgumentParser(description="사용자가 지정한 skeleton source의 공통 구조를 생성 프로젝트에 적용합니다.")
    parser.add_argument("--selection-json", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--skeleton-source", help="GitHub repository/archive URL 또는 local directory. 없으면 overlay를 건너뜁니다.")
    parser.add_argument("--skeleton-ref", default="main", help="GitHub repository URL일 때 사용할 branch/tag")
    args = parser.parse_args()

    selection = read_json(args.selection_json)
    config = selection["config"]
    target_package = config["package"]
    project_root = args.project_root.resolve()

    if not args.skeleton_source or args.skeleton_source.strip().lower() in {"none", "no", "skip", "initializr-only"}:
        print("Skeleton source가 제공되지 않아 skeleton overlay를 건너뜁니다.")
        print("Spring Initializr 프로젝트 생성과 buildSrc 기반 Gradle 버전 관리는 완료된 상태로 종료합니다.")
        print("안내: 이 프로젝트에는 skeleton의 common/config/resources/transaction/persistence 구조가 적용되지 않았습니다.")
        print("나중에 적용하려면 --skeleton-source에 GitHub repo URL 또는 local directory를 지정해 이 스크립트를 다시 실행하세요.")
        return 0

    tmp, skeleton_root = load_skeleton(args)
    try:
        source_base = skeleton_root / "src/main/kotlin" / package_path(SOURCE_PACKAGE)
        target_base = project_root / "src/main/kotlin" / package_path(target_package)

        copied: list[Path] = []
        copied += copy_tree(source_base / "common", target_base / "common", target_package, exclude_sample)
        copied += copy_tree(source_base / "adapter/output/transaction", target_base / "adapter/output/transaction", target_package, exclude_sample)
        copied += copy_tree(source_base / "adapter/output/persistence/config", target_base / "adapter/output/persistence/config", target_package, exclude_sample)
        copied += copy_tree(source_base / "application/port/output/transaction", target_base / "application/port/output/transaction", target_package, exclude_sample)

        if (skeleton_root / "config/detekt").exists():
            shutil.copytree(skeleton_root / "config/detekt", project_root / "config/detekt", dirs_exist_ok=True)

        resources = skeleton_root / "src/main/resources"
        strip_error_properties(resources / "errors/error.properties", project_root / "src/main/resources/errors/error.properties")
        copy_text_file(resources / "validations/validation.properties", project_root / "src/main/resources/validations/validation.properties", target_package)
        copy_text_file(resources / "messages/message.properties", project_root / "src/main/resources/messages/message.properties", target_package)
        write_resource_placeholders(project_root, config["artifact"])
        adapt_for_java_version(project_root, config)

        build_versions = extract_build_versions(read_text(project_root / "build.gradle.kts"))
        write_buildsrc(project_root, skeleton_root, build_versions, config)
        patch_build_gradle(project_root, config, selection.get("dependencies", []))

        leftovers = scan_for_leftovers(project_root)
        print(f"Applied skeleton overlay to {project_root}")
        print(f"Copied {len(copied)} Kotlin files")
        if leftovers:
            print("WARN: possible sample/source package leftovers:")
            for item in leftovers:
                print(f"  - {item}")
        return 0
    finally:
        if tmp:
            tmp.cleanup()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InitializrError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
