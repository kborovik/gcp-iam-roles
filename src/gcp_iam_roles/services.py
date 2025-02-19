import sqlite3
import sys
import time
from dataclasses import dataclass

from google.cloud import service_usage_v1
from loguru import logger
from prettytable import from_db_cursor

from . import DB_FILE


@dataclass
class Service:
    name: str
    title: str


def sync_services() -> list[Service]:
    """Retrieves a list of all Google Cloud services."""

    from .auth import get_google_credentials

    services = []
    page_size = 10
    delay = 5.0

    logger.info(
        "Searching for Google Cloud Services. Not all Cloud Services provided by Google. This may take a while..."
    )

    _, project_id = get_google_credentials()

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
            logger.info(
                f"Found {len(batch)} Google Cloud Services. Total: {len(services) + len(batch)}"
            )
            if batch:
                services.extend(batch)
                store_services(batch)
            time.sleep(delay)
    except Exception as error:
        logger.error(f"Error getting Google Cloud Services: {error}")
        raise
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        sys.exit(130)

    return services


def store_services(services: list[Service]) -> None:
    """Inserts a list of Google Cloud services into a SQLite database table."""

    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO services (service, title) VALUES (?, ?)",
            [(service.name, service.title) for service in services],
        )
        conn.commit()
        logger.success(f"Saved {len(services)} Google Cloud Services in database")
    except sqlite3.IntegrityError:
        logger.warning("Duplicate Google Cloud Services in database")
    except sqlite3.Error as error:
        logger.error(f"SQLite Error: {error}")
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        sys.exit(130)

    conn.close()


def search_services(service_name: str) -> None:
    """Searches for a Google Cloud Services in the SQLite database table."""
    from contextlib import suppress

    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT service,title FROM services WHERE service LIKE ? OR title LIKE ? ORDER BY service;",
            (f"%{service_name}%", f"%{service_name}%"),
        )
        table = from_db_cursor(cursor)
        table.align = "l"
    except sqlite3.Error as error:
        logger.error(f"SQLite Error: {error}")

    with suppress(BrokenPipeError):
        print(table)

    conn.close()


if __name__ == "__main__":
    sync_services()
