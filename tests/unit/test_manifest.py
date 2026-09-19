from pathlib import Path

from pyarch.config.manifest import (
    create_manifest,
    find_project_root,
    load_manifest,
    save_manifest,
)
from pyarch.config.models import DatabaseEngine


def test_manifest_round_trip_and_project_root_discovery(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    manifest = create_manifest(project_dir, "project", DatabaseEngine.SQLITE)
    manifest.state.modules.append("tasks")
    manifest.state.integrations.append("auth")
    save_manifest(project_dir, manifest)

    nested_dir = project_dir / "app" / "api" / "v1"
    nested_dir.mkdir(parents=True)

    loaded_manifest = load_manifest(project_dir)

    assert find_project_root(nested_dir) == project_dir
    assert loaded_manifest.project.name == "project"
    assert loaded_manifest.database.engine is DatabaseEngine.SQLITE
    assert loaded_manifest.state.modules == ["tasks"]
    assert loaded_manifest.state.integrations == ["auth"]
