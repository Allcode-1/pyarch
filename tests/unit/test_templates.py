from pathlib import Path

from pyarch.generators.common.renderer import render_template
from pyarch.generators.project.base import (
    create_ci_workflow,
    create_docker_compose,
    create_dockerignore,
    create_ruff_config,
)


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
    assert "alembic revision" not in postgres_compose
    assert "alembic upgrade" not in postgres_compose
    assert "migrate:" not in postgres_compose
    assert "service_completed_successfully" not in postgres_compose
    assert "image: backend:dev" not in postgres_compose
    assert "tests_db:" not in postgres_compose
    assert "postgres_data:" in postgres_compose


def test_postgres_compose_and_dockerignore_are_generated(
    tmp_path: Path,
) -> None:
    postgres_dir = tmp_path / "postgres"
    postgres_dir.mkdir()

    create_docker_compose(postgres_dir)
    create_dockerignore(postgres_dir)
    create_ruff_config(postgres_dir)

    postgres_compose = (postgres_dir / "docker-compose.yml").read_text(encoding="utf-8")
    dockerignore = (postgres_dir / ".dockerignore").read_text(encoding="utf-8")
    ruff_config = (postgres_dir / "ruff.toml").read_text(encoding="utf-8")

    assert "tests_db:" not in postgres_compose
    assert ".env" in dockerignore
    assert ".venv/" in dockerignore
    assert "alembic/versions" in ruff_config


def test_generated_ci_runs_only_lint_and_tests(tmp_path: Path) -> None:
    create_ci_workflow(tmp_path)

    workflow = (tmp_path / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert "uv run ruff check app tests" in workflow
    assert "uv run pytest" in workflow
    assert "mypy" not in workflow
    assert "uv build" not in workflow
