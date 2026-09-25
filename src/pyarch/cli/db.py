from typing import Annotated

import typer

from pyarch.cli.common import console, execute_or_exit
from pyarch.services.database import initialize_database, upgrade_database

app = typer.Typer(no_args_is_help=True)


@app.command("init")
def initialize_database_command() -> None:
    """Create and apply the initial database revision without starting the app."""

    project_root = execute_or_exit(initialize_database)
    console.print(
        f"[green]Database initialized[/green] in [bold]{project_root}[/bold]. "
        "The application was not started."
    )


@app.command("upgrade")
def upgrade_database_command(
    message: Annotated[
        str | None,
        typer.Option("--message", "-m", help="Message for the Alembic revision."),
    ] = None,
) -> None:
    """Generate, apply, and restart the application with a schema revision."""

    migration_message = message
    if migration_message is None:
        migration_message = typer.prompt("Migration message")

    project_root, schema_changed = execute_or_exit(
        lambda: upgrade_database(migration_message)
    )
    if not schema_changed:
        console.print(
            "[yellow]No schema changes detected; Compose was restarted without a migration.[/yellow]"
        )
        return

    console.print(
        f"[green]Database upgraded and Compose restarted[/green] in "
        f"[bold]{project_root}[/bold]"
    )
