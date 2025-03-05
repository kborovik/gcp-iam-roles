import sqlite3
import sys
from dataclasses import dataclass

from google.cloud import iam_admin_v1
from loguru import logger
from prettytable import from_db_cursor

from . import DB_FILE


@dataclass
class RolePermissions:
    role: str
    permissions: list[str]


def get_permissions(role_name: str) -> RolePermissions | None:
    """Retrieves a list of all permissions associated with a given IAM role."""
    from .auth import get_google_credentials

    get_google_credentials()

    logger.info(f"Getting permissions for role: {role_name}")

    client = iam_admin_v1.IAMClient()
    role = client.get_role(request=iam_admin_v1.GetRoleRequest(name=role_name))

    role_permissions = RolePermissions(role=role.name, permissions=list(role.included_permissions))

    if role_permissions.permissions:
        logger.success(
            f"Received {len(role_permissions.permissions)} permissions for role: {role_name}"
        )
        return role_permissions
    else:
        logger.warning(f"No permissions found for role: {role_name}")
        return None


def sync_permissions() -> None:
    """Inserts a list of Google Cloud IAM predefined roles into a SQLite database table."""

    conn = sqlite3.connect(DB_FILE.as_uri())
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
        logger.error(f"SQLite Error: {error}")

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
            logger.warning(f"SQLite IntegrityError: {error}")
        except sqlite3.Error as error:
            logger.error(f"SQLite Error: {error}")
        except KeyboardInterrupt:
            logger.warning("Operation cancelled by user")
            sys.exit(130)

        conn.commit()
        logger.success(
            f"Saved {len(role_permissions.permissions)} permissions for role: {role_name}"
        )

    conn.close()


def search_permissions(permission_name: str) -> None:
    """Searches for a Google Cloud IAM predefined permission in the SQLite database table."""

    from contextlib import suppress

    conn = sqlite3.connect(DB_FILE.as_uri())

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
        table = from_db_cursor(cursor)
        table.align = "l"
        table.max_width = 160
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")

    with suppress(BrokenPipeError):
        print(table)

    conn.close()


if __name__ == "__main__":
    sync_permissions()
