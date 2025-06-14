import sqlite3
import sys

from rich.console import Console
from rich.table import Table

console = Console()

from . import DB_FILE


def create_db() -> None:
    """Creates a SQLite database table to store Google Cloud IAM predefined roles."""

    conn = sqlite3.connect(DB_FILE)

    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
            role TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            stage TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS permissions (
            permission TEXT,
            role TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role) REFERENCES roles (role),
            UNIQUE (permission, role)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
            service TEXT PRIMARY KEY,
            title TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
    except sqlite3.OperationalError as error:
        console.print(f"[red]Error creating table: {error}[/red]")

    conn.close()


def clear_db() -> None:
    """Drops the SQLite database table that stores Google Cloud IAM predefined roles."""

    prompt = input("**WARNING!** This will delete all data in the database. Continue? (y/N): ")
    if prompt.lower() != "y":
        print("Aborting...")
        sys.exit(0)

    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("DROP TABLE IF EXISTS permissions;")
        conn.execute("DROP TABLE IF EXISTS roles;")
        conn.execute("DROP TABLE IF EXISTS services;")
        conn.commit()
        console.print("[green]Dropped tables: roles, permissions, services[/green]")
    except sqlite3.OperationalError as error:
        console.print(f"[red]SQLite Error: {error}[/red]")

    conn.close()


def status_db() -> None:
    """Prints the number of roles and permissions in the SQLite database table."""

    conn = sqlite3.connect(DB_FILE)

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(role) FROM roles;")
        roles = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT permission) FROM permissions;")
        permissions = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT service) FROM services;")
        services = cursor.fetchone()[0]
        table_count = Table(title="[bold blue]Database Status[/bold blue]")
        table_count.add_column("Type", justify="left", style="blue")
        table_count.add_column("Count", justify="right", style="green")
        table_count.add_row("GCP IAM Roles", str(roles))
        table_count.add_row("GCP IAM Permissions", str(permissions))
        table_count.add_row("GCP Services", str(services))
        console.print(table_count)
    except sqlite3.Error as error:
        console.print(f"[red]SQLite Error: {error}[/red]")

    conn.close()

    print(f"DB File: {DB_FILE.as_posix()}")
