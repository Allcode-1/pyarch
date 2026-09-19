import shutil
from pathlib import Path
from uuid import uuid4

from pyarch.config.manifest import create_manifest
from pyarch.config.models import DatabaseEngine
from pyarch.generators.common.commands import run_command
from pyarch.generators.project.base import create_base_dir, create_readme_file
from pyarch.generators.project.layered import create_layered_project


def create_project(
    project_name: str,
    database: DatabaseEngine | str = DatabaseEngine.POSTGRES,
) -> Path:
    database = DatabaseEngine(database)
    project_dir = (Path.cwd() / project_name).resolve()

    if project_dir.exists():
        raise FileExistsError(f"Project directory already exists: {project_dir}")

    staging_dir = project_dir.parent / f".{project_dir.name}.pyarch-{uuid4().hex}"
    published = False

    try:
        create_base_dir(staging_dir, project_dir.name, database)
        create_layered_project(staging_dir, database)
        create_readme_file(staging_dir, project_name, database.value)
        create_manifest(staging_dir, project_name, database)
        staging_dir.rename(project_dir)
        published = True
        run_command("uv", "sync", "--reinstall", cwd=project_dir)
    except BaseException:
        shutil.rmtree(project_dir if published else staging_dir, ignore_errors=True)
        raise

    return project_dir
