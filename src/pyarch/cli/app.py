import typer

from pyarch.cli.add import app as add_app
from pyarch.cli.db import app as db_app
from pyarch.cli.generate import app as generate_app
from pyarch.cli.info import show_info
from pyarch.cli.init import init_project

app = typer.Typer(
    name="pyarch",
    help="Generate and extend Layered FastAPI projects.",
    no_args_is_help=True,
)

app.command("init", help="Create a new Layered FastAPI project.")(init_project)
app.command("info", help="Show information from the current project's manifest.")(
    show_info
)

app.add_typer(
    generate_app,
    name="generate",
    help="Generate project components.",
)

app.add_typer(
    add_app,
    name="add",
    help="Add project integrations.",
)

app.add_typer(
    db_app,
    name="db",
    help="Create and apply database migrations.",
)
