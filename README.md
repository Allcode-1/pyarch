# PyArch

[![PyPI](https://img.shields.io/pypi/v/PyArch-CLI)](https://pypi.org/project/PyArch-CLI/)
![Python](https://img.shields.io/badge/Python-3.13%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-green)
![Typer](https://img.shields.io/badge/Typer-CLI-purple)
![Jinja2](https://img.shields.io/badge/Jinja2-templates-orange)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-v0.2.0-blue)

PyArch is a CLI for creating and extending Layered FastAPI projects. It sets up
the application structure, database, tests and Alembic, then lets you add CRUD
modules and integrations without wiring every file by hand.

Unlike a one-time project template, PyArch keeps a small manifest in the
generated project. Later commands use it to understand the project and update
the right files.

<p align="center">
  <img src="./assets/pyarch-demo.gif" alt="PyArch CLI demo" width="900">
</p>

## Why PyArch?

PyArch removes repetitive setup while keeping the generated code readable and
ready to change.

- Layered FastAPI project structure
- PostgreSQL and SQLite support
- Complete CRUD modules with models, schemas, repositories, services and routes
- Automatic model and router registration
- JWT auth integration with generated RSA keys
- Protected CRUD routes
- Alembic setup for relational databases
- Tests and dependency setup through `uv`
- Project-aware generation through `pyarch.toml`
- Atomic project creation and rollback for failed extensions

## v0.2.0 Highlights

- Atomic project creation through a staging directory, with cleanup on failure
- Rollback for failed module and auth generation
- Database-specific Docker Compose files for PostgreSQL and SQLite
- Refresh-token rotation protected against concurrent reuse on PostgreSQL
- Self-tests for PyArch and an end-to-end generated-project workflow

## Quick Start

PyArch requires Python 3.13 or newer and
[`uv`](https://docs.astral.sh/uv/).

Install the latest release from PyPI:

```bash
pip install pyarch-cli
```

Create a project and move into it:

```bash
pyarch init my_project --database postgres
cd my_project
```

Copy `.env.example` to `.env` and set the database connection values. The
generated Compose file matches the selected database: PostgreSQL projects get
database services; SQLite projects get only migration and API services.

Start the generated application:

```bash
docker compose up -d
```

After adding a generated module or integration that changes the database
schema, create a revision with
`uv run alembic revision --autogenerate -m "describe schema change"`. Then
apply it with `uv run alembic upgrade head`.
PyArch never autogenerates revisions during container startup: migration files
are source code and should be reviewed and committed.

## Safe Generation

`pyarch init` builds the project in a staging directory and publishes it only
after all generation steps complete. If setup fails, the staging directory is
removed. `generate module` and `add integration` track every affected file and
restore the previous state if a generation step fails, including the manifest
and dependency files.

Open `http://127.0.0.1:8000/docs` to use the generated Swagger UI.

You can now extend the project:

```bash
pyarch generate module users
pyarch add integration auth
pyarch generate module tasks --protected
pyarch info
```

## What Gets Generated

A new project includes the application layers, database configuration, test
setup and the files needed to run FastAPI:

```text
my_project/
├── app/
│   ├── api/v1/
│   ├── core/
│   ├── db/
│   ├── dependencies/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── alembic/          # PostgreSQL and SQLite only
├── .env.example
├── pyarch.toml
└── pyproject.toml
```

Each generated CRUD module adds:

- a database model;
- create, update and response schemas;
- repository and service classes;
- list, get, create, update and delete routes;
- CRUD tests;
- model and router registration in the existing application.

## Commands

| Command                                     | Description                                      |
| ------------------------------------------- | ------------------------------------------------ |
| `pyarch init <name>`                        | Create a Layered FastAPI project                 |
| `pyarch init <name> --database <engine>`    | Select PostgreSQL or SQLite                      |
| `pyarch generate module <name>`             | Add a CRUD module to the current project         |
| `pyarch add integration auth`               | Add JWT authentication and user management       |
| `pyarch generate module <name> --protected` | Generate CRUD routes that require authentication |
| `pyarch info`                               | Show the current project configuration           |
| `pyarch --help`                             | Show CLI help                                    |

Generation commands must be run inside a project created by PyArch.

## Databases and Current Limitations

| Database   | CRUD modules | Alembic | Auth integration | Protected modules |
| ---------- | ------------ | ------- | ---------------- | ----------------- |
| PostgreSQL | Yes          | Yes     | Yes              | Yes               |
| SQLite     | Yes          | Yes     | Yes              | Yes               |

Current limitations:

- only Layered Architecture is supported;
- generated applications use synchronous database access;
- generated projects are starter scaffolds and still require
  application-specific configuration and code;
- the manifest format may change before a stable release.

## Project Manifest

Every generated project contains `pyarch.toml`. It records the selected
architecture and database, generated modules, enabled integrations and known
project paths.

Commands such as `generate module`, `add integration` and `info` read this file
instead of trying to infer project state from the directory structure. PyArch
updates the manifest after a successful generation step.

## Development

Clone the repository and install the development environment:

```bash
git clone https://github.com/Allcode-1/PyArch.git
cd PyArch
uv sync --group dev
```

Run the CLI from the checkout:

```bash
uv run pyarch --help
```

Or install the current checkout as an editable CLI tool:

```bash
uv tool install --editable .
```

Run the project checks before opening a pull request or releasing a version:

```bash
uv run pytest
uv run ruff check src tests
uv run mypy src tests
uv build
```

## Architecture and Design

<details>
<summary>How PyArch is structured</summary>

```text
Typer CLI
    ↓
Application services
    ↓
Generators
    ↓
Jinja2 templates
    ↓
Generated FastAPI project
    ↑
pyarch.toml
```

The CLI handles user input and delegates work to application services.
Generators render Jinja2 templates and update files at explicit registration
markers. The manifest provides the project context needed by later commands.

</details>

<details>
<summary>Why use a manifest?</summary>

Scanning the filesystem shows which files exist, but not which project choices
produced them. The manifest stores those choices directly, so later commands do
not have to guess the architecture, database or enabled features.

</details>

<details>
<summary>Why marker-based registration?</summary>

PyArch modifies files it generated itself. Explicit markers provide stable and
readable insertion points for model and router imports without requiring a full
AST rewriting pipeline.

</details>

<details>
<summary>Why Jinja2?</summary>

Templates stay close to the Python code users receive and can edit. Jinja2 is
used with `StrictUndefined`, so missing template context fails during generation
instead of producing incomplete files.

</details>

## Roadmap

### v0.2.0 (current)

- atomic project creation and cleanup on failure;
- rollback for failed module and auth generation;
- PostgreSQL- and SQLite-specific Compose templates;
- self-test suite and generated-project integration coverage.

### v0.3

- Redis integration foundation;
- opt-in cache-aside generation for CRUD modules;
- dry-run mode.

### Later

- scheduler integration;
- more architectures;
- plugin system;
- asynchronous database access.

## Status

PyArch v0.2.0 is an early alpha release. The main workflow is usable, but
commands, templates, generated code and the manifest may still change before a
stable release.
