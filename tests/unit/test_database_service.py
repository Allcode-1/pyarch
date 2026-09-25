import subprocess
from pathlib import Path

import pytest

from pyarch.config.manifest import create_manifest
from pyarch.config.models import DatabaseEngine
from pyarch.services import database


def create_database_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "demo"
    project_root.mkdir()
    create_manifest(project_root, "demo", DatabaseEngine.POSTGRES)
    (project_root / ".env").touch()
    (project_root / "docker-compose.yml").touch()
    (project_root / "alembic.ini").touch()
    (project_root / "alembic" / "versions").mkdir(parents=True)
    (project_root / "alembic" / "env.py").touch()
    return project_root


def test_initialize_database_starts_only_db_and_creates_initial_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = create_database_project(tmp_path)
    calls: list[tuple[str, ...]] = []

    monkeypatch.setattr(
        database,
        "run_command",
        lambda *command, cwd: calls.append(command),
    )

    assert database.initialize_database(project_root) == project_root
    assert calls == [
        ("docker", "compose", "up", "-d", "--wait", "db"),
        (
            "uv",
            "run",
            "alembic",
            "revision",
            "--autogenerate",
            "-m",
            "db init",
        ),
        ("uv", "run", "alembic", "upgrade", "head"),
    ]


def test_upgrade_restarts_compose_without_creating_empty_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = create_database_project(tmp_path)
    calls: list[tuple[str, ...]] = []

    monkeypatch.setattr(
        database,
        "run_command",
        lambda *command, cwd: calls.append(command),
    )

    assert database.upgrade_database("add task priority", project_root) == (
        project_root,
        False,
    )
    assert calls == [
        ("docker", "compose", "down"),
        ("docker", "compose", "up", "-d", "--wait", "db"),
        ("uv", "run", "alembic", "check"),
        ("docker", "compose", "up", "-d"),
    ]


def test_upgrade_restarts_compose_only_after_schema_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = create_database_project(tmp_path)
    calls: list[tuple[str, ...]] = []

    def record(*command: str, cwd: Path) -> None:
        calls.append(command)
        if command == ("uv", "run", "alembic", "check"):
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(database, "run_command", record)

    assert database.upgrade_database("add task priority", project_root) == (
        project_root,
        True,
    )
    assert calls == [
        ("docker", "compose", "down"),
        ("docker", "compose", "up", "-d", "--wait", "db"),
        ("uv", "run", "alembic", "check"),
        (
            "uv",
            "run",
            "alembic",
            "revision",
            "--autogenerate",
            "-m",
            "add task priority",
        ),
        ("uv", "run", "alembic", "upgrade", "head"),
        ("docker", "compose", "up", "-d"),
    ]


def test_initialize_rejects_existing_revisions(tmp_path: Path) -> None:
    project_root = create_database_project(tmp_path)
    (project_root / "alembic" / "versions" / "existing.py").touch()

    with pytest.raises(FileExistsError, match="already has Alembic revisions"):
        database.initialize_database(project_root)


def test_database_commands_reject_sqlite_project(tmp_path: Path) -> None:
    project_root = tmp_path / "demo"
    project_root.mkdir()
    create_manifest(project_root, "demo", DatabaseEngine.SQLITE)

    with pytest.raises(NotImplementedError, match="PostgreSQL"):
        database.validate_database_project(project_root)


@pytest.mark.parametrize("message", ("", "   "))
def test_upgrade_rejects_blank_migration_message(message: str) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        database.validate_migration_message(message)
