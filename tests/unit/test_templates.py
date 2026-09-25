from pathlib import Path

from pyarch.config.models import DatabaseEngine
from pyarch.generators.common.renderer import render_template
from pyarch.generators.project.base import create_docker_compose


def test_python_templates_render_to_valid_python() -> None:
    module_context = {
        "module_name": "tasks",
        "model_name": "Task",
        "resource_name": "tasks",
        "table_name": "tasks",
        "id_type": "int",
    }
    template_names = (
        "layered/module/module_model.py.j2",
        "layered/module/module_schema.py.j2",
        "layered/module/module_repo.py.j2",
        "layered/module/module_service.py.j2",
        "layered/module/module_router.py.j2",
        "layered/module/module_router_protected.py.j2",
        "layered/auth/service.py.j2",
        "layered/auth/routes.py.j2",
    )

    for template_name in template_names:
        source = render_template(template_name, **module_context)
        compile(source, template_name, "exec")


def test_compose_templates_do_not_manage_migrations() -> None:
    postgres_compose = render_template("project/base/docker-compose.postgres.yml.j2")
    sqlite_compose = render_template("project/base/docker-compose.sqlite.yml.j2")

    for compose in (postgres_compose, sqlite_compose):
        assert "alembic revision" not in compose
        assert "alembic upgrade" not in compose
        assert "migrate:" not in compose
        assert "service_completed_successfully" not in compose

    assert "tests_db:" in postgres_compose
    assert "postgres_data:" in postgres_compose
    assert "tests_db:" not in sqlite_compose
    assert "postgres_data:" not in sqlite_compose


def test_compose_generator_selects_template_for_database(
    tmp_path: Path,
) -> None:
    postgres_dir = tmp_path / "postgres"
    sqlite_dir = tmp_path / "sqlite"
    postgres_dir.mkdir()
    sqlite_dir.mkdir()

    create_docker_compose(postgres_dir, DatabaseEngine.POSTGRES)
    create_docker_compose(sqlite_dir, DatabaseEngine.SQLITE)

    postgres_compose = (postgres_dir / "docker-compose.yml").read_text(
        encoding="utf-8"
    )
    sqlite_compose = (sqlite_dir / "docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert "tests_db:" in postgres_compose
    assert "tests_db:" not in sqlite_compose
