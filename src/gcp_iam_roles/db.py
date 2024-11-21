import os
import sqlite3
import sys

from loguru import logger
from prettytable import PrettyTable

from .config import DB_FILE


def create_db() -> None:
    """
    Creates a SQLite database table to store Google Cloud IAM predefined roles.
    """
    os.makedirs(DB_FILE.parent, exist_ok=True)

    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
            role TEXT PRIMARY KEY,
            title TEXT,
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
        logger.success("Created tables: roles, permissions, services")
    except sqlite3.OperationalError as error:
        logger.error("Error creating table: ", error)

    conn.close()


def clear_db() -> None:
    """
    Drops the SQLite database table that stores Google Cloud IAM predefined roles.
    """
    prompt = input(
        "**WARNING!** This will delete all data in the database. Continue? (y/N): "
    )
    if prompt.lower() != "y":
        print("Aborting...")
        sys.exit(0)

    conn = sqlite3.connect(DB_FILE.as_uri())
    try:
        conn.execute("DROP TABLE IF EXISTS permissions;")
        conn.execute("DROP TABLE IF EXISTS roles;")
        conn.execute("DROP TABLE IF EXISTS services;")
        conn.commit()
        logger.success("Dropped tables: roles, permissions, services")
    except sqlite3.OperationalError as error:
        logger.error("SQLite Error: ", error)

    conn.close()


def status_db() -> None:
    """
    Prints the number of roles and permissions in the SQLite database table.
    """
    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(role) FROM roles;")
        roles = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT permission) FROM permissions;")
        permissions = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT service) FROM services;")
        services = cursor.fetchone()[0]
        table = PrettyTable()
        table.field_names = ["Type", "Count"]
        table.add_row(["GCP IAM Roles", roles])
        table.add_row(["GCP IAM Permissions", permissions])
        table.add_row(["GCP Services", services])
        table.align = "l"
        print(table)
    except sqlite3.Error as error:
        logger.error("SQLite Error: ", error)

    conn.close()
