from pathlib import Path
from typing import Any

from tomlkit import document, dumps, load, table

from pyarch import __version__
from pyarch.config.models import (
    Architecture,
    DatabaseAccess,
    DatabaseEngine,
    DatabaseSettings,
    ProjectManifest,
    ProjectPaths,
    ProjectSettings,
    ProjectState,
)

MANIFEST_NAME = "pyarch.toml"
SCHEMA_VERSION = 1


class ManifestError(ValueError):
    pass


def load_current_manifest():
    project_root = find_project_root()
    return project_root, load_manifest(project_root)


def create_manifest(
    project_dir: Path,
    project_name: str,
    database: DatabaseEngine,
) -> ProjectManifest:
    manifest = ProjectManifest(
        schema_version=SCHEMA_VERSION,
        pyarch_version=__version__,
        project=ProjectSettings(name=project_name),
        database=DatabaseSettings(engine=database),
        paths=ProjectPaths(),
    )
    save_manifest(project_dir, manifest)
    return manifest


def find_project_root(start: Path | None = None) -> Path:

    current = (start or Path.cwd()).resolve()

    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        if (directory / MANIFEST_NAME).is_file():
            return directory

    raise FileNotFoundError(
        f"{MANIFEST_NAME} was not found in {current} or its parent directories"
    )


def load_manifest(project_dir: Path) -> ProjectManifest:

    manifest_path = project_dir / MANIFEST_NAME

    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest does not exist: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        raw = load(manifest_file).unwrap()

    try:
        schema_version = int(raw["schema_version"])
        if schema_version != SCHEMA_VERSION:
            raise ManifestError(
                f"Unsupported manifest schema version: {schema_version}"
            )

        project_data = require_table(raw, "project")
        database_data = require_table(raw, "database")
        paths_data = require_table(raw, "paths")
        state_data = require_table(raw, "state")

        return ProjectManifest(
            schema_version=schema_version,
            pyarch_version=str(raw["pyarch_version"]),
            project=ProjectSettings(
                name=str(project_data["name"]),
                architecture=Architecture(str(project_data["architecture"])),
            ),
            database=DatabaseSettings(
                engine=DatabaseEngine(str(database_data["engine"])),
                access=DatabaseAccess(str(database_data["access"])),
            ),
            paths=ProjectPaths(
                application=str(paths_data["application"]),
                tests=str(paths_data["tests"]),
                migrations=(
                    str(paths_data["migrations"])
                    if "migrations" in paths_data
                    else None
                ),
            ),
            state=ProjectState(
                modules=require_string_list(state_data, "modules"),
                integrations=require_string_list(state_data, "integrations"),
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, ManifestError):
            raise
        raise ManifestError(f"Invalid {MANIFEST_NAME}: {error}") from error


def save_manifest(project_dir: Path, manifest: ProjectManifest) -> Path:

    manifest_path = project_dir / MANIFEST_NAME
    temporary_path = manifest_path.with_suffix(".toml.tmp")

    doc = document()
    doc.add("schema_version", manifest.schema_version)
    doc.add("pyarch_version", __version__)

    project = table()
    project.add("name", manifest.project.name)
    project.add("architecture", manifest.project.architecture.value)
    doc.add("project", project)

    database = table()
    database.add("engine", manifest.database.engine.value)
    database.add("access", manifest.database.access.value)
    doc.add("database", database)

    paths = table()
    paths.add("application", manifest.paths.application)
    paths.add("tests", manifest.paths.tests)
    if manifest.paths.migrations is not None:
        paths.add("migrations", manifest.paths.migrations)
    doc.add("paths", paths)

    state = table()
    state.add("modules", manifest.state.modules)
    state.add("integrations", manifest.state.integrations)
    doc.add("state", state)

    temporary_path.write_text(dumps(doc), encoding="utf-8")
    temporary_path.replace(manifest_path)
    manifest.pyarch_version = __version__
    return manifest_path


def require_table(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw[key]
    if not isinstance(value, dict):
        raise ManifestError(f"{key!r} must be a TOML table")
    return value


def require_string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ManifestError(f"{key!r} must be an array of strings")
    return list(value)
