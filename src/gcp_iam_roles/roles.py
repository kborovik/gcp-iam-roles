import sqlite3
import sys
from dataclasses import dataclass

from google.cloud import iam_admin_v1
from loguru import logger
from prettytable import from_db_cursor

from . import DB_FILE


@dataclass
class Role:
    name: str
    title: str
    description: str
    stage: str


def get_roles() -> list[Role]:
    """Retrieves a list of all predefined IAM roles in the current Google Cloud project."""
    from .auth import get_google_credentials

    get_google_credentials()

    roles: list[Role] = []

    logger.info("Getting Google Cloud Predefined Roles...")

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

    logger.success("Received {} Google Cloud Predefined Roles", len(roles))

    return roles


def sync_roles() -> None:
    """Inserts a list of Google Cloud IAM predefined roles into a SQLite database table."""

    conn = sqlite3.connect(DB_FILE)

    roles = get_roles()

    new_roles = []
    old_roles = []

    logger.info("Storing roles in database...")

    try:
        cursor = conn.cursor()
        for role in roles:
            try:
                cursor.execute(
                    "INSERT INTO roles (role, title, description, stage) VALUES (?, ?, ?, ?)",
                    (role.name, role.title, role.description, role.stage),
                )
                new_roles.append(role)
            except sqlite3.IntegrityError:
                old_roles.append(role)
                continue
        conn.commit()
    except sqlite3.Error as error:
        logger.error(f"SQLite Error: {error}")
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        sys.exit(130)

    conn.close()

    logger.success("New roles: {}, Existing roles: {}", len(new_roles), len(old_roles))


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
        table = from_db_cursor(cursor)
        table.align = "l"
        table.max_width = 160
    except sqlite3.Error as error:
        logger.error(f"SQLite Error: {error}")

    with suppress(BrokenPipeError):
        print(table)

    conn.close()


if __name__ == "__main__":
    sync_roles()
