"""Project type detection and context awareness."""

from enum import Enum
from pathlib import Path


class ProjectType(str, Enum):
    """Supported project types."""

    PYTHON = "python"
    NODEJS = "nodejs"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    WEB = "web"
    UNKNOWN = "unknown"


class ProjectContext:
    """Project context information."""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.project_type = self._detect_project_type()
        self.package_manager = self._detect_package_manager()
        self.build_tool = self._detect_build_tool()
        self.test_framework = self._detect_test_framework()

    def _detect_project_type(self) -> ProjectType:
        """Detect the project type based on files in the root directory."""
        # Check for Python project
        if (self.root_dir / "pyproject.toml").exists() or (
            self.root_dir / "setup.py"
        ).exists():
            return ProjectType.PYTHON

        # Check for Node.js project
        if (self.root_dir / "package.json").exists():
            return ProjectType.NODEJS

        # Check for Rust project
        if (self.root_dir / "Cargo.toml").exists():
            return ProjectType.RUST

        # Check for Go project
        if (self.root_dir / "go.mod").exists():
            return ProjectType.GO

        # Check for Java project
        if (self.root_dir / "pom.xml").exists() or (
            self.root_dir / "build.gradle"
        ).exists():
            return ProjectType.JAVA

        # Check for general web project
        if (
            (self.root_dir / "index.html").exists()
            or (self.root_dir / "src" / "index.html").exists()
        ):
            return ProjectType.WEB

        return ProjectType.UNKNOWN

    def _detect_package_manager(self) -> str | None:
        """Detect the package manager used in the project."""
        if self.project_type == ProjectType.PYTHON:
            if (self.root_dir / "pyproject.toml").exists():
                # Check if using uv, poetry, or pip
                pyproject = self.root_dir / "pyproject.toml"
                content = pyproject.read_text()
                if "uv" in content or "tool.uv" in content:
                    return "uv"
                elif "poetry" in content or "tool.poetry" in content:
                    return "poetry"
            return "pip"

        elif self.project_type == ProjectType.NODEJS:
            if (self.root_dir / "pnpm-lock.yaml").exists():
                return "pnpm"
            elif (self.root_dir / "yarn.lock").exists():
                return "yarn"
            elif (self.root_dir / "package-lock.json").exists():
                return "npm"
            return "npm"  # Default to npm

        elif self.project_type == ProjectType.RUST:
            return "cargo"

        elif self.project_type == ProjectType.GO:
            return "go"

        return None

    def _detect_build_tool(self) -> str | None:
        """Detect the build tool used in the project."""
        if self.project_type == ProjectType.PYTHON:
            if (self.root_dir / "Makefile").exists():
                return "make"
            elif (self.root_dir / "pyproject.toml").exists():
                return "build"  # python -m build

        elif self.project_type == ProjectType.NODEJS:
            # Check package.json for build scripts
            package_json = self.root_dir / "package.json"
            if package_json.exists():
                return "npm scripts"

        elif self.project_type == ProjectType.RUST:
            return "cargo"

        elif self.project_type == ProjectType.GO:
            return "go build"

        elif self.project_type == ProjectType.JAVA:
            if (self.root_dir / "pom.xml").exists():
                return "maven"
            elif (self.root_dir / "build.gradle").exists():
                return "gradle"

        return None

    def _detect_test_framework(self) -> str | None:
        """Detect the test framework used in the project."""
        if self.project_type == ProjectType.PYTHON:
            if (self.root_dir / "pytest.ini").exists() or (
                self.root_dir / "pyproject.toml"
            ).exists():
                return "pytest"
            elif any(self.root_dir.rglob("test_*.py")) or any(
                self.root_dir.rglob("*_test.py")
            ):
                return "unittest/pytest"

        elif self.project_type == ProjectType.NODEJS:
            package_json = self.root_dir / "package.json"
            if package_json.exists():
                content = package_json.read_text()
                if "jest" in content:
                    return "jest"
                elif "vitest" in content:
                    return "vitest"
                elif "mocha" in content:
                    return "mocha"

        elif self.project_type == ProjectType.RUST:
            return "cargo test"

        elif self.project_type == ProjectType.GO:
            return "go test"

        return None

    def get_context_summary(self) -> str:
        """Get a summary of the project context."""
        lines = [
            f"Project Type: {self.project_type.value}",
        ]
        if self.package_manager:
            lines.append(f"Package Manager: {self.package_manager}")
        if self.build_tool:
            lines.append(f"Build Tool: {self.build_tool}")
        if self.test_framework:
            lines.append(f"Test Framework: {self.test_framework}")
        return "\n".join(lines)

    def get_recommended_commands(self) -> dict[str, str]:
        """Get recommended commands for common operations."""
        commands = {}

        if self.project_type == ProjectType.PYTHON:
            if self.package_manager == "uv":
                commands["install"] = "uv sync"
                commands["run"] = "uv run python -m <module>"
                commands["test"] = "uv run pytest"
            elif self.package_manager == "poetry":
                commands["install"] = "poetry install"
                commands["run"] = "poetry run python -m <module>"
                commands["test"] = "poetry run pytest"
            else:
                commands["install"] = "pip install -r requirements.txt"
                commands["run"] = "python -m <module>"
                commands["test"] = "pytest"

        elif self.project_type == ProjectType.NODEJS:
            pm = self.package_manager or "npm"
            commands["install"] = f"{pm} install"
            commands["run"] = f"{pm} run dev"
            commands["build"] = f"{pm} run build"
            commands["test"] = f"{pm} test"

        elif self.project_type == ProjectType.RUST:
            commands["build"] = "cargo build"
            commands["run"] = "cargo run"
            commands["test"] = "cargo test"

        elif self.project_type == ProjectType.GO:
            commands["build"] = "go build"
            commands["run"] = "go run ."
            commands["test"] = "go test ./..."

        return commands
