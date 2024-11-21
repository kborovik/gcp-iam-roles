import sqlite3
import sys
from dataclasses import dataclass
from typing import List

from google.cloud import iam_admin_v1
from loguru import logger
from prettytable import from_db_cursor

from .config import DB_FILE


@dataclass
class RolePermissions:
    role: str
    permissions: List[str]


def get_permissions(role_name: str) -> RolePermissions:
    """
    Retrieves a list of all permissions associated with a given IAM role.
    """
    logger.info(f"Getting permissions for role: {role_name}")

    client = iam_admin_v1.IAMClient()
    request = iam_admin_v1.GetRoleRequest(name=role_name)
    role = client.get_role(request=request)

    included_permissions = []

    for item in role.included_permissions:
        included_permissions.append(item)

    role_permissions = RolePermissions(role=role.name, permissions=included_permissions)

    logger.success(
        f"Received {len(role_permissions.permissions)} permissions for role: {role_name}"
    )

    return role_permissions


def store_permissions() -> None:
    """
    Inserts a list of Google Cloud IAM predefined roles into a SQLite database table.
    """
    conn = sqlite3.connect(DB_FILE.as_uri())
    # Get all roles from the database
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM roles ORDER BY role;")
        roles_in_db = cursor.fetchall()
    except sqlite3.Error as error:
        logger.error("SQLite Error: ", error)
    # Get all permissions from the database
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT role FROM permissions ORDER BY role;")
        permissions_in_db = cursor.fetchall()
    except sqlite3.Error as error:
        logger.error("SQLite Error: ", error)
    # Check what role-permission pairs are missing in 'permissions' table
    db_role_names = {role[0] for role in roles_in_db}
    db_permission_names = {permission[0] for permission in permissions_in_db}
    roles_without_permissions = list(db_role_names - db_permission_names)
    # Insert missing role-permission pairs into 'permissions' table
    for role_name in roles_without_permissions:
        role_permissions = get_permissions(role_name)
        for permission in role_permissions.permissions:
            try:
                cursor.execute(
                    "INSERT INTO permissions (permission, role) VALUES (?, ?)",
                    (permission, role_name),
                )
                conn.commit()
            except sqlite3.IntegrityError as error:
                logger.warning("SQLite IntegrityError: ", error)
                continue
            except sqlite3.Error as error:
                logger.error("SQLite Error: ", error)
            except KeyboardInterrupt:
                logger.warning("Operation cancelled by user")
                sys.exit(130)

        logger.success(
            f"Saved {len(role_permissions.permissions)} permissions for role: {role_name}"
        )

    conn.close()


def search_permissions(permission_name: str) -> None:
    """
    Searches for a Google Cloud IAM predefined permission in the SQLite database table.
    """
    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role,permission FROM permissions WHERE permission LIKE ? ORDER BY permission, role;",
            (f"%{permission_name}%",),
        )
        table = from_db_cursor(cursor)
        table.align = "l"
        print(table)
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")

    conn.close()
