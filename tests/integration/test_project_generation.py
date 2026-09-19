from pathlib import Path

import pytest

import pyarch.services.create_project as create_project_service
from pyarch.config.models import DatabaseEngine


def test_create_project_removes_staging_directory_after_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def create_base_dir(
        project_dir: Path,
        project_name: str,
        database: DatabaseEngine,
    ) -> Path:
        project_dir.mkdir()
        return project_dir

    def fail_to_create_layered_project(*_args: object) -> None:
        raise RuntimeError("dependency installation failed")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(create_project_service, "create_base_dir", create_base_dir)
    monkeypatch.setattr(
        create_project_service,
        "create_layered_project",
        fail_to_create_layered_project,
    )

    with pytest.raises(RuntimeError, match="dependency installation failed"):
        create_project_service.create_project("demo")

    assert not (tmp_path / "demo").exists()
    assert not list(tmp_path.glob(".demo.pyarch-*"))


def test_create_project_publishes_completed_staging_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def create_base_dir(
        project_dir: Path,
        project_name: str,
        database: DatabaseEngine,
    ) -> Path:
        project_dir.mkdir()
        return project_dir

    def create_layered_project(project_dir: Path, _database: DatabaseEngine) -> None:
        (project_dir / "app").mkdir()
        (project_dir / "app" / "main.py").touch()
        (project_dir / "alembic").mkdir()
        (project_dir / "alembic" / "env.py").touch()

    def create_readme_file(
        project_dir: Path,
        _project_name: str,
        _database: str,
    ) -> None:
        (project_dir / "README.md").touch()

    def create_manifest(
        project_dir: Path,
        _project_name: str,
        _database: DatabaseEngine,
    ) -> None:
        (project_dir / "pyarch.toml").touch()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(create_project_service, "create_base_dir", create_base_dir)
    monkeypatch.setattr(
        create_project_service,
        "create_layered_project",
        create_layered_project,
    )
    monkeypatch.setattr(
        create_project_service,
        "create_readme_file",
        create_readme_file,
    )
    monkeypatch.setattr(create_project_service, "create_manifest", create_manifest)
    monkeypatch.setattr(create_project_service, "run_command", lambda *_args, **_kwargs: None)

    project_dir = create_project_service.create_project(
        "demo",
        DatabaseEngine.SQLITE,
    )

    assert project_dir == tmp_path / "demo"
    assert (project_dir / "pyarch.toml").is_file()
    assert (project_dir / "app" / "main.py").is_file()
    assert (project_dir / "alembic" / "env.py").is_file()
    assert not list(tmp_path.glob(".demo.pyarch-*"))
