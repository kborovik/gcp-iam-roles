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


def _get_role_permissions(cursor: sqlite3.Cursor, role_name: str) -> set[str]:
    """Get permissions for a role from the database."""
    cursor.execute(
        "SELECT permission FROM permissions WHERE role = ? ORDER BY permission", (role_name,)
    )
    return {row[0] for row in cursor.fetchall()}


def _validate_roles_exist(
    role1: str, role2: str, role1_perms: set[str], role2_perms: set[str]
) -> bool:
    """Validate that both roles exist in the database."""
    if not role1_perms and not role2_perms:
        console.print(f"[red]Neither role '{role1}' nor '{role2}' found in database[/red]")
        return False
    elif not role1_perms:
        console.print(f"[red]Role '{role1}' not found in database[/red]")
        return False
    elif not role2_perms:
        console.print(f"[red]Role '{role2}' not found in database[/red]")
        return False
    return True


def diff_roles(role1: str, role2: str) -> None:
    """Compares permissions between two GCP IAM roles and displays the differences."""
    from contextlib import suppress

    conn = sqlite3.connect(DB_FILE)

    try:
        cursor = conn.cursor()

        role1_permissions = _get_role_permissions(cursor, role1)
        role2_permissions = _get_role_permissions(cursor, role2)

        if not _validate_roles_exist(role1, role2, role1_permissions, role2_permissions):
            return

        # Calculate differences
        only_in_role1 = role1_permissions - role2_permissions
        only_in_role2 = role2_permissions - role1_permissions
        common_permissions = role1_permissions & role2_permissions

        # Create summary table
        summary_table = Table(title=f"[bold cyan]Role Comparison: {role1} vs {role2}[/bold cyan]")
        summary_table.add_column("Category", justify="left", style="yellow")
        summary_table.add_column("Count", justify="right", style="green")

        summary_table.add_row("Common Permissions", str(len(common_permissions)))
        summary_table.add_row(f"Only in {role1}", str(len(only_in_role1)))
        summary_table.add_row(f"Only in {role2}", str(len(only_in_role2)))
        summary_table.add_row(
            "Total Unique Permissions", str(len(role1_permissions | role2_permissions))
        )

        console.print(summary_table)
        console.print()

        # Show permissions only in role1
        if only_in_role1:
            role1_table = Table(
                title=f"[bold red]Permissions only in '{role1}' ({len(only_in_role1)} permissions)[/bold red]"
            )
            role1_table.add_column("Permission", justify="left", style="red", max_width=80)
            for permission in sorted(only_in_role1):
                role1_table.add_row(permission)
            console.print(role1_table)
            console.print()

        # Show permissions only in role2
        if only_in_role2:
            role2_table = Table(
                title=f"[bold blue]Permissions only in '{role2}' ({len(only_in_role2)} permissions)[/bold blue]"
            )
            role2_table.add_column("Permission", justify="left", style="blue", max_width=80)
            for permission in sorted(only_in_role2):
                role2_table.add_row(permission)
            console.print(role2_table)
            console.print()

        # Show common permissions if there are any
        if common_permissions:
            common_table = Table(
                title=f"[bold green]Common Permissions ({len(common_permissions)} permissions)[/bold green]"
            )
            common_table.add_column("Permission", justify="left", style="green", max_width=80)
            for permission in sorted(common_permissions):
                common_table.add_row(permission)
            console.print(common_table)

    except sqlite3.Error as error:
        console.print(f"[red]SQLite Error: {error}[/red]")

    with suppress(BrokenPipeError):
        pass

    conn.close()


if __name__ == "__main__":
    sync_roles()
