"""
Create a base for any project.
"""

from pathlib import Path

from pyarch.config.models import DatabaseEngine
from pyarch.generators.common.commands import run_command
from pyarch.generators.common.filesystem import create_empty_dir, create_empty_file
from pyarch.generators.common.gitignore import (
    BASE_GITIGNORE_ENTRIES,
    ensure_gitignore_entries,
)
from pyarch.generators.common.renderer import create_file_from_template


def create_base_dir(
    project_dir: Path,
    project_name: str,
    database: DatabaseEngine,
) -> Path:

    project_dir.mkdir(parents=True, exist_ok=False)

    # creating base uv app
    run_command(
        "uv",
        "init",
        "--name",
        project_name,
        "--no-workspace",
        ".",
        cwd=project_dir,
    )

    # .gitignote
    ensure_gitignore_entries(project_dir, "base", BASE_GITIGNORE_ENTRIES)

    # docker 
    create_dockerfile(project_dir)
    create_docker_compose(project_dir, database)

    # docs
    create_docs_dir(project_dir)

    return project_dir


def create_dockerfile(project_dir: Path) -> None:
    create_file_from_template(
        template_name="project/base/Dockerfile.j2",
        output_path=project_dir / "Dockerfile"
    )


def create_docker_compose(project_dir: Path, database: DatabaseEngine) -> None:
    template_name = (
        "project/base/docker-compose.postgres.yml.j2"
        if database is DatabaseEngine.POSTGRES
        else "project/base/docker-compose.sqlite.yml.j2"
    )

    create_file_from_template(
        template_name=template_name,
        output_path=project_dir / "docker-compose.yml",
    )


def create_docs_dir(project_dir: Path) -> None:
    docs_dir = create_empty_dir(project_dir / "docs")
    create_empty_file(docs_dir / "RBAC.md")
    create_empty_file(docs_dir / "ARCHITECTURE.md")


def create_readme_file(
    project_dir: Path,
    project_name: str,
    database: str,
) -> None:
    create_file_from_template(
        template_name="project/base/README.md.j2",
        output_path=project_dir / "README.md",
        project_name=project_name,
        database=database,
    )
