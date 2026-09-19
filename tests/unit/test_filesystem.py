from pathlib import Path

import pytest

from pyarch.generators.common.filesystem import rollback_file_changes


def test_rollback_file_changes_restores_files_and_removes_new_directories(
    tmp_path: Path,
) -> None:
    existing_file = tmp_path / "existing.txt"
    existing_file.write_text("before", encoding="utf-8")
    created_directory = tmp_path / "created"
    created_file = created_directory / "new.txt"

    with pytest.raises(RuntimeError, match="generation failed"), rollback_file_changes(
        (existing_file, created_file),
        (created_directory,),
    ):
        existing_file.write_text("after", encoding="utf-8")
        created_directory.mkdir()
        created_file.write_text("new", encoding="utf-8")
        raise RuntimeError("generation failed")

    assert existing_file.read_text(encoding="utf-8") == "before"
    assert not created_file.exists()
    assert not created_directory.exists()
