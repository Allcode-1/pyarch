import subprocess
from collections.abc import Callable
from typing import Never

import typer
from rich.console import Console

console = Console()
def execute_or_exit[ResultT](action: Callable[[], ResultT]) -> ResultT:
    try:
        return action()
    except (
        FileExistsError,
        FileNotFoundError,
        NotImplementedError,
        subprocess.CalledProcessError,
        ValueError,
    ) as error:
        abort(str(error))


def abort(message: str) -> Never:
    console.print(f"[bold red]Error:[/bold red] {message}")
    raise typer.Exit(code=1)
