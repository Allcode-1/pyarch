from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyarch.cli import db
from pyarch.cli.app import app

runner = CliRunner()


def test_db_init_calls_database_service(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(db, "initialize_database", lambda: tmp_path)

    result = runner.invoke(app, ["db", "init"])

    assert result.exit_code == 0
    assert "Database initialized" in result.stdout
    assert "not started" in result.stdout


def test_db_upgrade_prompts_for_message(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    received: list[str] = []

    def upgrade(message: str) -> tuple[Path, bool]:
        received.append(message)
        return tmp_path, True

    monkeypatch.setattr(db, "upgrade_database", upgrade)

    result = runner.invoke(app, ["db", "upgrade"], input="add priority\n")

    assert result.exit_code == 0
    assert received == ["add priority"]
    assert "Compose restarted" in result.stdout


def test_db_upgrade_accepts_message_option(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    received: list[str] = []

    def upgrade(message: str) -> tuple[Path, bool]:
        received.append(message)
        return tmp_path, False

    monkeypatch.setattr(db, "upgrade_database", upgrade)

    result = runner.invoke(app, ["db", "upgrade", "-m", "add priority"])

    assert result.exit_code == 0
    assert received == ["add priority"]
    assert "without a migration" in result.stdout
