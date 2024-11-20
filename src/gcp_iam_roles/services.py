import sqlite3
import time
from dataclasses import dataclass
from typing import List

from google.cloud import service_usage_v1
from loguru import logger
from prettytable import from_db_cursor

from .config import DB_FILE


@dataclass
class Service:
    name: str
    title: str


def get_services(project_id: str) -> List[Service]:
    """
    Retrieves a list of all Google Cloud services.
    """

    page_size = 10
    delay = 2
    services: List[Service] = []

    logger.info("Getting Google Cloud Services...")

    client = service_usage_v1.ServiceUsageClient()
    request = service_usage_v1.ListServicesRequest(
        parent=f"projects/{project_id}", page_size=page_size
    )
    try:
        page_results = client.list_services(request=request)
        for page in page_results.pages:
            for service in page.services:
                if service.config.name.endswith("googleapis.com"):
                    services.append(
                        Service(
                            name=service.config.name,
                            title=service.config.title,
                        )
                    )
                    logger.info(
                        f"Received Google Cloud Services: {service.config.name}"
                    )
            time.sleep(delay)
    except Exception as error:
        logger.error(f"Error getting Google Cloud Services: {error}")
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")

    return services


def store_services(services: Service) -> None:
    """
    Inserts a list of Google Cloud services into a SQLite database table.
    """
    db_service_stored = []

    conn = sqlite3.connect(DB_FILE.as_uri())

    logger.info("Storing Google Cloud Services in database...")

    try:
        cursor = conn.cursor()
        for service in services:
            cursor.execute(
                "INSERT INTO services (service, title) VALUES (?, ?)",
                (
                    service.name,
                    service.title,
                ),
            )
        conn.commit()
        db_service_stored.append(service.name)
    except sqlite3.IntegrityError:
        pass
    except sqlite3.Error as error:
        logger.error(f"SQLite Error: {error}")

    conn.close()

    logger.success(f"{len(db_service_stored)} Google Cloud Services stored in database")


def search_services(service_name: str) -> None:
    """
    Searches for a Google Cloud Services in the SQLite database table.
    """
    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT service,title FROM services WHERE service LIKE ? OR title LIKE ? ORDER BY service;",
            (f"%{service_name}%", f"%{service_name}%"),
        )
        table = from_db_cursor(cursor)
        table.align = "l"
        print(table)
    except sqlite3.Error as error:
        logger.error("SQLite Error: ", error)

    conn.close()
