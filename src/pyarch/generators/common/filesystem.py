from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def create_empty_dir(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_empty_file(file: Path) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.touch(exist_ok=True)
    return file


def init_py_module(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    init = directory / "__init__.py"
    init.touch(exist_ok=True)
    return init


def create_module_path(directory: Path) -> Path:
    create_empty_dir(directory)
    init_py_module(directory)
    return directory


def insert_line_before_marker(
    file_path: Path,
    marker: str,
    line: str,
) -> bool:
    content = file_path.read_text(encoding="utf-8")

    if line in content.splitlines():
        return False

    if marker not in content:
        raise ValueError(f"Marker {marker!r} was not found in {file_path}")

    updated_content = content.replace(marker, f"{line}\n{marker}", 1)
    file_path.write_text(updated_content, encoding="utf-8")
    return True


def append_text_once(file_path: Path, marker: str, text: str) -> bool:
    content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""

    if marker in content:
        return False

    separator = "" if not content or content.endswith("\n") else "\n"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(f"{content}{separator}{text}", encoding="utf-8")
    return True


@contextmanager
def rollback_file_changes(
    files: tuple[Path, ...],
    directories: tuple[Path, ...] = (),
) -> Iterator[None]:
    """Restore tracked files if a generation step fails."""

    snapshots = {
        file_path: file_path.read_bytes() if file_path.is_file() else None
        for file_path in files
    }
    created_directories = tuple(
        directory for directory in directories if not directory.exists()
    )

    try:
        yield
    except BaseException:
        for file_path, content in snapshots.items():
            if content is None:
                file_path.unlink(missing_ok=True)
            else:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(content)

        for directory in sorted(created_directories, key=lambda path: len(path.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass

        raise
