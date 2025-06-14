from importlib.metadata import metadata
from pathlib import Path

package_name = metadata(__package__).get("name")

DB_FILE: Path = Path.home().joinpath(".local", "share", package_name, f"{package_name}.db")
DB_FILE.parent.mkdir(parents=True, exist_ok=True)


import typer
from rich.console import Console

from .auth import get_google_credentials
from .db import clear_db, create_db, status_db
from .permissions import list_permissions, search_permissions, sync_permissions
from .roles import diff_roles, list_roles, search_roles, sync_roles
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
    diff: list[str] = typer.Option(
        [], "--diff", help="Compare permissions between two roles (use --diff role1 --diff role2)"
    ),
) -> None:
    """
    Manage GCP IAM roles.

    Examples:

      > gcp-iam-roles role --search compute.

      > gcp-iam-roles role --diff compute.osAdminLogin --diff compute.osLogin

      > gcp-iam-roles role --sync

    """
    if search:
        search_roles(search)
    elif sync:
        ensure_authenticated()
        create_db()
        sync_roles()
        sync_permissions()
    elif diff:
        diff_size = 2
        if len(diff) != diff_size:
            console.print("[red]Error: --diff requires exactly two role names[/red]")
            console.print("Example: gcp-iam-roles role --diff compute.viewer --diff storage.viewer")
            raise typer.Exit(1)
        diff_roles(diff[0], diff[1])
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
    list_role: str | None = typer.Option(
        None, "--list", help="List all permissions for a given role"
    ),
) -> None:
    """
    Manage GCP IAM permissions.

    Examples:

    > gcp-iam-roles permission --search compute.instances.osLogin

    > gcp-iam-roles permission --list compute.admin

    """
    if search:
        search_permissions(search)
    elif list_role:
        list_permissions(list_role)
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


@app.command("_list-roles", hidden=True)
def _list_roles_completion() -> None:
    """List roles for shell completion."""
    list_roles()


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
