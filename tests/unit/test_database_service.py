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
    monkeypatch.setattr(database, "schema_changes_pending", lambda _root: False)

    assert database.upgrade_database("add task priority", project_root) == (
        project_root,
        False,
    )
    assert calls == [
        ("docker", "compose", "down"),
        ("docker", "compose", "up", "-d", "--wait", "db"),
        ("docker", "compose", "up", "-d", "--build"),
    ]


def test_upgrade_restarts_compose_only_after_schema_change(
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
    monkeypatch.setattr(database, "schema_changes_pending", lambda _root: True)

    assert database.upgrade_database("add task priority", project_root) == (
        project_root,
        True,
    )
    assert calls == [
        ("docker", "compose", "down"),
        ("docker", "compose", "up", "-d", "--wait", "db"),
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
        ("docker", "compose", "up", "-d", "--build"),
    ]


def test_schema_changes_pending_uses_alembic_marker_not_windows_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = subprocess.CompletedProcess(
        args=("uv", "run", "alembic", "check"),
        returncode=4294967295,
        stderr="FAILED: New upgrade operations detected: [('add_table', 'tasks')]",
        stdout="",
    )
    monkeypatch.setattr(database.subprocess, "run", lambda *args, **kwargs: result)

    assert database.schema_changes_pending(tmp_path) is True


def test_schema_changes_pending_reports_an_actual_alembic_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = subprocess.CompletedProcess(
        args=("uv", "run", "alembic", "check"),
        returncode=255,
        stderr="ERROR: invalid database URL",
        stdout="",
    )
    monkeypatch.setattr(database.subprocess, "run", lambda *args, **kwargs: result)

    with pytest.raises(ValueError, match="invalid database URL"):
        database.schema_changes_pending(tmp_path)


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
