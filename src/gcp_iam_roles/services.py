import sqlite3
import sys
import time
from dataclasses import dataclass

from google.cloud import service_usage_v1
from rich.console import Console
from rich.table import Table

console = Console()

from . import DB_FILE


@dataclass
class Service:
    name: str
    title: str


def sync_services() -> list[Service]:
    """Retrieves a list of all Google Cloud services."""
    from . import ensure_authenticated

    services = []
    page_size = 10
    delay = 5.0

    console.print(
        "[blue]Searching for Google Cloud Services. Not all Cloud Services provided by Google. This may take a while...[/blue]"
    )

    _, project_id = ensure_authenticated()

    client = service_usage_v1.ServiceUsageClient()
    request = service_usage_v1.ListServicesRequest(
        parent=f"projects/{project_id}", page_size=page_size
    )

    try:
        for page in client.list_services(request=request).pages:
            batch = [
                Service(name=svc.config.name, title=svc.config.title)
                for svc in page.services
                if svc.config.name.endswith("googleapis.com")
            ]
            console.print(
                f"[blue]Found {len(batch)} Google Cloud Services. Total: {len(services) + len(batch)}[/blue]"
            )
            if batch:
                services.extend(batch)
                store_services(batch)
            time.sleep(delay)
    except Exception as error:
        console.print(f"[red]Error getting Google Cloud Services: {error}[/red]")
        raise
    except KeyboardInterrupt:
        console.print("[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)

    return services


def store_services(services: list[Service]) -> None:
    """Inserts a list of Google Cloud services into a SQLite database table."""

    conn = sqlite3.connect(DB_FILE)

    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO services (service, title) VALUES (?, ?)",
            [(service.name, service.title) for service in services],
        )
        conn.commit()
        console.print(f"[green]Saved {len(services)} Google Cloud Services in database[/green]")
    except sqlite3.IntegrityError:
        console.print("[yellow]Duplicate Google Cloud Services in database[/yellow]")
    except sqlite3.Error as error:
        console.print(f"[red]SQLite Error: {error}[/red]")
    except KeyboardInterrupt:
        console.print("[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)

    conn.close()


def search_services(service_name: str) -> None:
    """Searches for a Google Cloud Services in the SQLite database table."""
    from contextlib import suppress

    conn = sqlite3.connect(DB_FILE)

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT service,title FROM services WHERE service LIKE ? OR title LIKE ? ORDER BY service;",
            (f"%{service_name}%", f"%{service_name}%"),
        )
        rows = cursor.fetchall()
        table = Table(title="[bold green]GCP Services[/bold green]")
        table.add_column("Service", justify="left", max_width=80, style="blue")
        table.add_column("Title", justify="left", max_width=80, style="green")
        for row in rows:
            table.add_row(str(row[0]), str(row[1]))
    except sqlite3.Error as error:
        console.print(f"[red]SQLite Error: {error}[/red]")

    with suppress(BrokenPipeError):
        console.print(table)

    conn.close()


if __name__ == "__main__":
    sync_services()
