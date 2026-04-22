from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from initializr_common import (  # noqa: E402
    extract_build_versions,
    patch_initializr_build_gradle_version_refs,
    write_buildsrc_version_management,
)


INITIALIZR_BUILD = """plugins {
\tkotlin("jvm") version "2.2.21"
\tkotlin("plugin.spring") version "2.2.21"
\tid("org.springframework.boot") version "4.0.5"
\tid("io.spring.dependency-management") version "1.1.7"
}

group = "com.example"
version = "0.0.1-SNAPSHOT"

java {
\ttoolchain {
\t\tlanguageVersion = JavaLanguageVersion.of(25)
\t}
}

repositories {
\tmavenCentral()
}

dependencies {
\timplementation("org.springframework.boot:spring-boot-starter")
\ttestImplementation("org.springframework.boot:spring-boot-starter-test")
}
"""


class BuildSrcVersionManagementTests(unittest.TestCase):
    def test_initializr_only_project_gets_skeleton_style_buildsrc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            build_gradle = project_root / "build.gradle.kts"
            build_gradle.write_text(INITIALIZR_BUILD, encoding="utf-8")

            versions = extract_build_versions(INITIALIZR_BUILD)
            config = {
                "kotlin_request": "default",
                "boot_effective": "4.0.5",
                "java_effective": "25",
            }

            write_buildsrc_version_management(project_root, versions, config)
            patch_initializr_build_gradle_version_refs(project_root)

            self.assertEqual(
                (project_root / "buildSrc/build.gradle.kts").read_text(encoding="utf-8"),
                """plugins {
    `kotlin-dsl`
}

repositories {
    mavenCentral()
}
""",
            )
            self.assertIn(
                "val JAVA = JavaVersion.VERSION_25",
                (project_root / "buildSrc/src/main/kotlin/BuildVersions.kt").read_text(encoding="utf-8"),
            )
            plugin_versions = (project_root / "buildSrc/src/main/kotlin/PluginVersions.kt").read_text(encoding="utf-8")
            self.assertIn('const val KOTLIN = "2.2.21"', plugin_versions)
            self.assertIn('const val SPRING_BOOT = "4.0.5"', plugin_versions)
            self.assertIn('const val SPRING_DEPENDENCY_MANAGEMENT = "1.1.7"', plugin_versions)
            self.assertIn('const val DETEKT = "2.0.0-alpha.2"', plugin_versions)
            self.assertIn('const val JOOQ = "3.19.31"', plugin_versions)
            self.assertIn('const val JIB = "3.5.2"', plugin_versions)

            dependency_versions = (
                project_root / "buildSrc/src/main/kotlin/DependencyVersions.kt"
            ).read_text(encoding="utf-8")
            self.assertIn('const val SPRING_RESTDOCS_WEBTESTCLIENT = "4.0.0"', dependency_versions)
            self.assertIn('const val MOCKK = "1.14.9"', dependency_versions)

            patched_build = build_gradle.read_text(encoding="utf-8")
            self.assertIn('kotlin("jvm") version PluginVersions.KOTLIN', patched_build)
            self.assertIn('kotlin("plugin.spring") version PluginVersions.KOTLIN', patched_build)
            self.assertIn('id("org.springframework.boot") version PluginVersions.SPRING_BOOT', patched_build)
            self.assertIn(
                'id("io.spring.dependency-management") version PluginVersions.SPRING_DEPENDENCY_MANAGEMENT',
                patched_build,
            )
            self.assertIn("JavaLanguageVersion.of(BuildVersions.JAVA.majorVersion.toInt())", patched_build)
            self.assertNotIn('version "2.2.21"', patched_build)
            self.assertNotIn('version "4.0.5"', patched_build)


if __name__ == "__main__":
    unittest.main()
