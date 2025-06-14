import sqlite3
import sys
from dataclasses import dataclass

from google.cloud import iam_admin_v1
from rich.console import Console
from rich.table import Table

console = Console()

from . import DB_FILE


@dataclass
class RolePermissions:
    role: str
    permissions: list[str]


def get_permissions(role_name: str) -> RolePermissions | None:
    """Retrieves a list of all permissions associated with a given IAM role."""

    console.print(f"[blue]Getting permissions for role: {role_name}[/blue]")

    client = iam_admin_v1.IAMClient()
    role = client.get_role(request=iam_admin_v1.GetRoleRequest(name=role_name))

    role_permissions = RolePermissions(role=role.name, permissions=list(role.included_permissions))

    if role_permissions.permissions:
        console.print(
            f"[green]Received {len(role_permissions.permissions)} permissions for role: {role_name}[/green]"
        )
        return role_permissions
    else:
        console.print(f"[yellow]No permissions found for role: {role_name}[/yellow]")
        return None


def sync_permissions() -> None:
    """Inserts a list of Google Cloud IAM predefined roles into a SQLite database table."""

    conn = sqlite3.connect(DB_FILE)
    # Get roles without permissions from the database
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.role
            FROM roles r
            LEFT JOIN permissions p ON r.role = p.role
            WHERE p.role IS NULL
            ORDER BY r.role
        """)
        roles_without_permissions = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as error:
        console.print(f"[red]SQLite Error: {error}[/red]")

    # Insert missing role-permission pairs into 'permissions' table
    for role_name in roles_without_permissions:
        role_permissions = get_permissions(role_name)
        if not role_permissions:
            continue
        # Create batch inserts instead of individual ones
        permission_values = [(permission, role_name) for permission in role_permissions.permissions]
        try:
            cursor.executemany(
                "INSERT INTO permissions (permission, role) VALUES (?, ?)", permission_values
            )
        except sqlite3.IntegrityError as error:
            console.print(f"[yellow]SQLite IntegrityError: {error}[/yellow]")
        except sqlite3.Error as error:
            console.print(f"[red]SQLite Error: {error}[/red]")
        except KeyboardInterrupt:
            console.print("[yellow]Operation cancelled by user[/yellow]")
            sys.exit(130)

        conn.commit()
        console.print(
            f"[green]Saved {len(role_permissions.permissions)} permissions for role: {role_name}[/green]"
        )

    conn.close()


def search_permissions(permission_name: str) -> None:
    """Searches for a Google Cloud IAM predefined permission in the SQLite database table."""

    from contextlib import suppress

    conn = sqlite3.connect(DB_FILE)

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT role, permission
            FROM permissions
            WHERE permission LIKE ?
            ORDER BY permission, role;
            """,
            (f"%{permission_name}%",),
        )
        rows = cursor.fetchall()
        table = Table(title="[bold yellow]GCP IAM Permissions[/bold yellow]")
        table.add_column("Role", justify="left", max_width=80, style="blue")
        table.add_column("Permission", justify="left", max_width=80, style="green")
        for row in rows:
            table.add_row(str(row[0]), str(row[1]))
    except sqlite3.Error as error:
        console.print(f"[red]SQLite Error: {error}[/red]")

    with suppress(BrokenPipeError):
        console.print(table)

    conn.close()


if __name__ == "__main__":
    sync_permissions()
