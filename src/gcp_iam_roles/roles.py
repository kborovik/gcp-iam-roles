import sqlite3
import sys
from dataclasses import dataclass

from google.cloud import iam_admin_v1
from rich.console import Console
from rich.table import Table

console = Console()

from . import DB_FILE


@dataclass
class Role:
    name: str
    title: str
    description: str
    stage: str


def get_roles() -> list[Role]:
    """Retrieves a list of all predefined IAM roles in the current Google Cloud project."""

    roles: list[Role] = []

    console.print("[blue]Getting Google Cloud Predefined Roles...[/blue]")

    client = iam_admin_v1.IAMClient()
    request = iam_admin_v1.ListRolesRequest()
    data = client.list_roles(request=request)

    for role in data:
        roles.append(
            Role(
                name=role.name,
                title=role.title,
                description=role.description,
                stage=role.stage.name,
            )
        )

    console.print(f"[green]Received {len(roles)} Google Cloud Predefined Roles[/green]")

    return roles


def sync_roles() -> None:
    """Inserts a list of Google Cloud IAM predefined roles into a SQLite database table."""

    conn = sqlite3.connect(DB_FILE)

    roles = get_roles()

    new_roles = []
    old_roles = []

    console.print("[blue]Storing roles in database...[/blue]")

    try:
        cursor = conn.cursor()
        for role in roles:
            try:
                # Strip 'roles/' prefix from role name
                role_name_clean = role.name.removeprefix("roles/")
                cursor.execute(
                    "INSERT INTO roles (role, title, description, stage) VALUES (?, ?, ?, ?)",
                    (role_name_clean, role.title, role.description, role.stage),
                )
                new_roles.append(role)
            except sqlite3.IntegrityError:
                old_roles.append(role)
                continue
        conn.commit()
    except sqlite3.Error as error:
        console.print(f"[red]SQLite Error: {error}[/red]")
    except KeyboardInterrupt:
        console.print("[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)

    conn.close()

    console.print(f"[green]New roles: {len(new_roles)}, Existing roles: {len(old_roles)}[/green]")


def search_roles(role_name: str) -> None:
    """Searches for a Google Cloud IAM predefined role in the SQLite database table."""

    from contextlib import suppress

    conn = sqlite3.connect(DB_FILE)

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT role, title
            FROM roles
            WHERE role LIKE ? OR title LIKE ? OR description LIKE ?
            ORDER BY role;
            """,
            (f"%{role_name}%", f"%{role_name}%", f"%{role_name}%"),
        )
        rows = cursor.fetchall()
        table = Table(title="[bold magenta]GCP IAM Roles[/bold magenta]")
        table.add_column("Role", justify="left", max_width=80, style="blue")
        table.add_column("Title", justify="left", max_width=80, style="green")
        for row in rows:
            table.add_row(str(row[0]), str(row[1]))
    except sqlite3.Error as error:
        console.print(f"[red]SQLite Error: {error}[/red]")

    with suppress(BrokenPipeError):
        console.print(table)

    conn.close()


if __name__ == "__main__":
    sync_roles()
