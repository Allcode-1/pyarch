from pathlib import Path

from pyarch.config.manifest import find_project_root, load_manifest, save_manifest
from pyarch.generators.common.filesystem import rollback_file_changes
from pyarch.generators.integration.auth import (
    AUTH_INTEGRATION_NAME,
    create_auth_integration,
)


def add_integration(
    integration_name: str,
    start: Path | None = None,
) -> tuple[Path, tuple[Path, ...]]:
    project_root = find_project_root(start)
    manifest = load_manifest(project_root)
    normalized_name = integration_name.strip().lower().replace("-", "_")

    if not normalized_name:
        raise ValueError("Integration name cannot be empty")

    if normalized_name in manifest.state.integrations:
        raise FileExistsError(f"Integration {normalized_name!r} is already registered")

    if normalized_name != AUTH_INTEGRATION_NAME:
        raise NotImplementedError(
            f"Integration {normalized_name!r} does not have a generator yet"
        )

    app_path = project_root / manifest.paths.application
    auth_path = app_path / "auth"
    certs_path = project_root / "certs"
    tracked_files = (
        auth_path / "__init__.py",
        auth_path / "dependencies.py",
        auth_path / "routes.py",
        auth_path / "schemas.py",
        auth_path / "service.py",
        auth_path / "tokens.py",
        auth_path / "utils.py",
        app_path / "models" / "user.py",
        app_path / "models" / "refresh_session.py",
        project_root / manifest.paths.tests / "helpers.py",
        project_root / manifest.paths.tests / "test_auth.py",
        app_path / "core" / "config.py",
        certs_path / "private.pem",
        certs_path / "public.pem",
        app_path / "models" / "__init__.py",
        app_path / "api" / "v1" / "router.py",
        project_root / ".env.example",
        project_root / ".gitignore",
        project_root / "pyproject.toml",
        project_root / "uv.lock",
        project_root / "pyarch.toml",
    )

    with rollback_file_changes(tracked_files, (auth_path, certs_path)):
        created_files = create_auth_integration(
            project_root,
            manifest.database.engine,
        )
        manifest.state.integrations.append(normalized_name)
        save_manifest(project_root, manifest)

    return project_root, created_files
