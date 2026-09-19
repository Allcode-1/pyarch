import keyword
import re
from pathlib import Path

from pyarch.config.models import DatabaseEngine
from pyarch.generators.common.filesystem import insert_line_before_marker
from pyarch.generators.common.renderer import create_file_from_template

MODULE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def create_layered_module(
    project_dir: Path,
    module_name: str,
    database: DatabaseEngine | str = DatabaseEngine.POSTGRES,
    *,
    protected: bool = False,
) -> tuple[Path, ...]:
    
    database = DatabaseEngine(database)

    module_name = normalize_module_name(module_name)
    model_name = to_pascal_case(module_name)
    resource_name = pluralize_identifier(module_name)

    app_path = project_dir / "app"
    models_init = app_path / "models" / "__init__.py"
    main_router = app_path / "api" / "v1" / "router.py"

    ensure_layered_project(models_init, main_router)

    targets = (
        (
            "layered/module/module_model.py.j2",
            app_path / "models" / f"{module_name}.py",
        ),
        (
            "layered/module/module_schema.py.j2",
            app_path / "schemas" / f"{module_name}.py",
        ),
        (
            "layered/module/module_repo.py.j2",
            app_path / "repositories" / f"{module_name}.py",
        ),
        (
            "layered/module/module_service.py.j2",
            app_path / "services" / f"{module_name}.py",
        ),
        (
            (
                "layered/module/module_router_protected.py.j2"
                if protected
                else "layered/module/module_router.py.j2"
            ),
            app_path / "api" / "v1" / f"{module_name}.py",
        ),
        (
            (
                "layered/module/module_test_protected.py.j2"
                if protected
                else "layered/module/module_test.py.j2"
            ),
            project_dir / "tests" / f"test_{module_name}.py",
        ),
    )
    existing_targets = [path for _, path in targets if path.exists()]
    if existing_targets:
        existing = ", ".join(str(path) for path in existing_targets)
        raise FileExistsError(f"Module files already exist: {existing}")

    context = {
        "module_name": module_name,
        "model_name": model_name,
        "resource_name": resource_name,
        "table_name": resource_name,
        "id_type": "int",
    }

    created_files = tuple(
        create_file_from_template(template_name, output_path, **context)
        for template_name, output_path in targets
    )

    register_model(models_init, module_name, model_name)
    register_router(main_router, module_name, resource_name)
    return created_files


def normalize_module_name(module_name: str) -> str:
    normalized = module_name.strip().lower().replace("-", "_")

    if not MODULE_NAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Module name must start with a letter and contain only "
            "lowercase letters, numbers, and underscores"
        )

    if keyword.iskeyword(normalized):
        raise ValueError(f"Module name cannot be a Python keyword: {normalized}")

    return normalized


def to_pascal_case(module_name: str) -> str:
    return "".join(part.capitalize() for part in module_name.split("_"))


def pluralize_identifier(module_name: str) -> str:
    prefix, separator, word = module_name.rpartition("_")

    if word.endswith(("s", "x", "z", "ch", "sh")):
        plural = f"{word}es"
    elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        plural = f"{word[:-1]}ies"
    else:
        plural = f"{word}s"

    return f"{prefix}{separator}{plural}" if prefix else plural


def ensure_layered_project(models_init: Path, main_router: Path) -> None:
    required_markers = (
        (models_init, "# pyarch:model-imports"),
        (models_init, "# pyarch:model-exports"),
        (main_router, "# pyarch:router-imports"),
        (main_router, "# pyarch:router-includes"),
    )

    for file_path, marker in required_markers:
        if not file_path.is_file():
            raise FileNotFoundError(f"Required Layered file is missing: {file_path}")

        if marker not in file_path.read_text(encoding="utf-8"):
            raise ValueError(f"Marker {marker!r} was not found in {file_path}")


def register_model(
    models_init: Path,
    module_name: str,
    model_name: str,
) -> None:
    insert_line_before_marker(
        models_init,
        "# pyarch:model-imports",
        f"from app.models.{module_name} import {model_name}",
    )
    insert_line_before_marker(
        models_init,
        "    # pyarch:model-exports",
        f'    "{model_name}",',
    )


def register_router(main_router: Path, module_name: str, resource_name: str) -> None:
    insert_line_before_marker(
        main_router,
        "# pyarch:router-imports",
        f"from app.api.v1 import {module_name}",
    )
    insert_line_before_marker(
        main_router,
        "# pyarch:router-includes",
        (
            f"v1_router.include_router({module_name}.router, "
            f'prefix="/{resource_name}", tags=["{resource_name}"])'
        ),
    )
