from pathlib import Path

from pyarch.config.models import DatabaseEngine
from pyarch.generators.common.commands import run_command
from pyarch.generators.common.filesystem import create_module_path
from pyarch.generators.common.renderer import create_file_from_template

COMMON_RUNTIME_DEPENDENCIES = (
    "fastapi",
    "uvicorn",
    "python-dotenv",
    "pydantic-settings",
)

SQL_RUNTIME_DEPENDENCIES = (
    "sqlalchemy",
    "alembic",
)

DATABASE_RUNTIME_DEPENDENCIES = {
    DatabaseEngine.POSTGRES: ("psycopg[binary]",),
    DatabaseEngine.SQLITE: (),
}

COMMON_DEV_DEPENDENCIES = (
    "pytest",
    "httpx",
    "ruff",
    "mypy",
)


def create_layered_project(
    project_dir: Path,
    database: DatabaseEngine,
) -> Path:
    install_dependencies(project_dir, database)

    generated_main = project_dir / "main.py"
    if generated_main.exists():
        generated_main.unlink()

    app_path = create_module_path(project_dir / "app")
    create_layered_arch(app_path)
    create_database_setup(project_dir, app_path, database)
    create_test_setup(project_dir, database)

    initialize_alembic(project_dir)

    return app_path


def install_dependencies(
    project_dir: Path,
    database: DatabaseEngine,
) -> None:
    
    runtime_dependencies = list(COMMON_RUNTIME_DEPENDENCIES)
    runtime_dependencies.extend(SQL_RUNTIME_DEPENDENCIES)
    runtime_dependencies.extend(DATABASE_RUNTIME_DEPENDENCIES[database])

    run_command("uv", "add", *runtime_dependencies, cwd=project_dir)
    run_command("uv", "add", "--dev", *COMMON_DEV_DEPENDENCIES, cwd=project_dir)


def create_layered_arch(app_path: Path) -> None:

    """Create packages and shared files for a Layered application."""

    create_file_from_template(
        template_name="project/base/main.py.j2",
        output_path=app_path / "main.py",
    )

    base_layers = (
        "core",
        "db",
        "models",
        "schemas",
        "api",
        "services",
        "repositories",
        "dependencies",
    )

    for layer in base_layers:
        create_module_path(app_path / layer)

    create_module_path(app_path / "api" / "v1")

    create_file_from_template(
        template_name="layered/router.py.j2",
        output_path=app_path / "api" / "v1" / "router.py",
    )

    create_file_from_template(
        template_name="layered/errors.py.j2",
        output_path=app_path / "core" / "errors.py",
    )

    create_file_from_template(
        template_name="layered/exception_handlers.py.j2",
        output_path=app_path / "core" / "exception_handlers.py",
    )

    create_file_from_template(
        template_name="layered/pagination.py.j2",
        output_path=app_path / "dependencies" / "pagination.py",
    )

    create_file_from_template(
        template_name="layered/models_init.py.j2",
        output_path=app_path / "models" / "__init__.py",
    )


def create_database_setup(
    project_dir: Path,
    app_path: Path,
    database: DatabaseEngine,
) -> None:
    
    create_file_from_template(
        template_name="layered/config.py.j2",
        output_path=app_path / "core" / "config.py",
    )
    create_file_from_template(
        template_name="layered/session.py.j2",
        output_path=app_path / "db" / "session.py",
        database=database.value,
    )
    create_file_from_template(
        template_name="layered/env.example.j2",
        output_path=project_dir / ".env.example",
        database=database.value,
    )


def create_test_setup(
    project_dir: Path,
    database: DatabaseEngine,
) -> None:
    
    create_module_path(project_dir / "tests")

    create_file_from_template(
        template_name="project/base/conftest.py.j2",
        output_path=project_dir / "tests" / "conftest.py",
    )


def initialize_alembic(project_dir: Path) -> None:

    run_command("uv", "run", "alembic", "init", "alembic", cwd=project_dir)
    
    create_file_from_template(
        template_name="layered/alembic_env.py.j2",
        output_path=project_dir / "alembic" / "env.py",
    )
