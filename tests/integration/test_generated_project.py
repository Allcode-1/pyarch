import os
import subprocess
from pathlib import Path

import pytest

from pyarch.config.manifest import load_manifest
from pyarch.config.models import DatabaseEngine
from pyarch.services.add_integration import add_integration
from pyarch.services.create_module import create_module
from pyarch.services.create_project import create_project


def test_generated_project_supports_module_and_auth_workflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    project_dir = create_project("demo", DatabaseEngine.SQLITE)

    _, module_files = create_module("tasks", start=project_dir)
    _, auth_files = add_integration("auth", start=project_dir)
    _, protected_module_files = create_module(
        "notes",
        start=project_dir,
        protected=True,
    )

    manifest = load_manifest(project_dir)

    assert all(file_path.is_file() for file_path in module_files)
    assert all(file_path.is_file() for file_path in auth_files)
    assert all(file_path.is_file() for file_path in protected_module_files)
    assert manifest.state.modules == ["tasks", "notes"]
    assert manifest.state.integrations == ["auth"]
    assert "tests_db:" not in (project_dir / "docker-compose.yml").read_text(
        encoding="utf-8"
    )
    assert "get_current_active_user" in (
        project_dir / "app" / "api" / "v1" / "notes.py"
    ).read_text(encoding="utf-8")

    environment = {
        **os.environ,
        "DATABASE_URL": "sqlite:///./app.db",
        "TEST_DATABASE_URL": "sqlite:///./app_test.db",
    }
    environment.pop("VIRTUAL_ENV", None)
    result = subprocess.run(
        ("uv", "run", "pytest"),
        cwd=project_dir,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
