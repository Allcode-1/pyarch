import subprocess
from pathlib import Path

from pyarch.config.manifest import find_project_root, load_manifest
from pyarch.config.models import DatabaseEngine
from pyarch.generators.common.commands import run_command


def initialize_database(start: Path | None = None) -> Path:
    """Create and apply the initial Alembic revision for a PostgreSQL project."""

    project_root = validate_database_project(start)
    versions_path = project_root / "alembic" / "versions"
    if any(versions_path.glob("*.py")):
        raise FileExistsError(
            "The project already has Alembic revisions; use 'pyarch db upgrade' instead"
        )

    run_command("docker", "compose", "up", "-d", "--wait", "db", cwd=project_root)
    run_command(
        "uv",
        "run",
        "alembic",
        "revision",
        "--autogenerate",
        "-m",
        "db init",
        cwd=project_root,
    )
    run_command("uv", "run", "alembic", "upgrade", "head", cwd=project_root)
    return project_root


def upgrade_database(message: str, start: Path | None = None) -> tuple[Path, bool]:
    """Generate and apply a schema revision, restarting the Compose application."""

    project_root = validate_database_project(start)
    normalized_message = validate_migration_message(message)

    run_command("docker", "compose", "down", cwd=project_root)
    run_command("docker", "compose", "up", "-d", "--wait", "db", cwd=project_root)
    if not schema_changes_pending(project_root):
        run_command("docker", "compose", "up", "-d", "--build", cwd=project_root)
        return project_root, False

    run_command(
        "uv",
        "run",
        "alembic",
        "revision",
        "--autogenerate",
        "-m",
        normalized_message,
        cwd=project_root,
    )
    run_command("uv", "run", "alembic", "upgrade", "head", cwd=project_root)
    run_command("docker", "compose", "up", "-d", "--build", cwd=project_root)
    return project_root, True


def validate_database_project(start: Path | None = None) -> Path:
    project_root = find_project_root(start)
    manifest = load_manifest(project_root)

    if manifest.database.engine is not DatabaseEngine.POSTGRES:
        raise NotImplementedError(
            "Database lifecycle commands currently support PostgreSQL projects only"
        )

    required_paths = (
        project_root / ".env",
        project_root / "docker-compose.yml",
        project_root / "alembic.ini",
        project_root / "alembic" / "env.py",
        project_root / "alembic" / "versions",
    )
    missing_paths = [path.name for path in required_paths if not path.exists()]
    if missing_paths:
        raise FileNotFoundError(
            "Database project setup is incomplete; missing: " + ", ".join(missing_paths)
        )

    return project_root


def schema_changes_pending(project_root: Path) -> bool:
    command = ("uv", "run", "alembic", "check")
    result = subprocess.run(
        command,
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return False

    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if "New upgrade operations detected" in output:
        return True

    details = output.strip() or f"exit status {result.returncode}"
    raise ValueError(f"Alembic check failed: {details}")


def validate_migration_message(message: str) -> str:
    normalized_message = message.strip()
    if not normalized_message:
        raise ValueError("Migration message cannot be empty")
    return normalized_message
