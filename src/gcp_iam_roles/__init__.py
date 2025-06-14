from importlib.metadata import metadata
from pathlib import Path

package_name = metadata(__package__).get("name")

DB_FILE: Path = Path.home().joinpath(".local", "share", package_name, f"{package_name}.db")
DB_FILE.parent.mkdir(parents=True, exist_ok=True)


import typer
from rich.console import Console

from .auth import get_google_credentials
from .db import clear_db, create_db, status_db
from .permissions import search_permissions, sync_permissions
from .roles import search_roles, sync_roles
from .services import search_services, sync_services

create_db()

console = Console()

app = typer.Typer(
    name="gcp-iam-roles",
    help="Search Google Cloud IAM roles and permissions",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Search Google Cloud IAM roles and permissions."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


# Cache credentials to avoid multiple authentication calls
def ensure_authenticated() -> object:
    """Ensure Google Cloud credentials are available, caching the result."""
    if not hasattr(ensure_authenticated, "_cache"):
        ensure_authenticated._cache = get_google_credentials()
    return ensure_authenticated._cache


@app.command()
def role(
    ctx: typer.Context,
    search: str | None = typer.Option(
        None,
        "--search",
        help="Search for roles by name pattern (searches role names, titles, and descriptions)",
    ),
    sync: bool = typer.Option(
        False, "--sync", help="Sync predefined IAM roles and permissions from Google Cloud APIs"
    ),
) -> None:
    """
    Manage GCP IAM roles.

    Search for existing roles or sync the latest roles from Google Cloud.

    Examples:

      gcp-iam-roles role --search viewer
      gcp-iam-roles role --search compute
      gcp-iam-roles role --sync

    Notes:

      • Search is case-insensitive and matches role names, titles, and descriptions
      • Sync requires authentication: gcloud auth login --update-adc
      • Role names displayed without 'roles/' prefix for cleaner output
      • Sync operation may take several minutes to complete
    """
    if search:
        search_roles(search)
    elif sync:
        ensure_authenticated()
        create_db()
        sync_roles()
        sync_permissions()
    else:
        # Show help when no options are provided
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command()
def permission(
    ctx: typer.Context,
    search: str | None = typer.Option(
        None, "--search", help="Search for permissions by name pattern"
    ),
) -> None:
    """Manage GCP IAM permissions."""
    if search:
        search_permissions(search)
    else:
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command()
def service(
    ctx: typer.Context,
    search: str | None = typer.Option(None, "--search", help="Search for services by name pattern"),
    sync: bool = typer.Option(False, "--sync", help="Sync Google Cloud services"),
) -> None:
    """Manage GCP services."""
    if search:
        search_services(search)
    elif sync:
        ensure_authenticated()
        create_db()
        sync_services()
    else:
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command()
def status() -> None:
    """Show roles and permissions count."""
    status_db()


@app.command("clear-db")
def clear_database() -> None:
    """Drop database tables."""
    clear_db()


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
