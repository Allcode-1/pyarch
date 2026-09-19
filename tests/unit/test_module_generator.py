import pytest

from pyarch.generators.module.layered import (
    normalize_module_name,
    pluralize_identifier,
    to_pascal_case,
)


@pytest.mark.parametrize(
    ("raw_name", "normalized_name"),
    (
        ("tasks", "tasks"),
        ("  blog-posts  ", "blog_posts"),
        ("v2_tasks", "v2_tasks"),
    ),
)
def test_normalize_module_name(raw_name: str, normalized_name: str) -> None:
    assert normalize_module_name(raw_name) == normalized_name


@pytest.mark.parametrize("raw_name", ("", "2tasks", "user name", "class"))
def test_normalize_module_name_rejects_invalid_identifiers(raw_name: str) -> None:
    with pytest.raises(ValueError):
        normalize_module_name(raw_name)


@pytest.mark.parametrize(
    ("module_name", "expected_model", "expected_resource"),
    (
        ("task", "Task", "tasks"),
        ("category", "Category", "categories"),
        ("blog_post", "BlogPost", "blog_posts"),
        ("box", "Box", "boxes"),
    ),
)
def test_module_name_derivations(
    module_name: str,
    expected_model: str,
    expected_resource: str,
) -> None:
    assert to_pascal_case(module_name) == expected_model
    assert pluralize_identifier(module_name) == expected_resource
