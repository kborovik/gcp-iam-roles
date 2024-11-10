import argparse
import os
import sqlite3
import sys
from pathlib import Path

import argcomplete
from google.cloud import iam_admin_v1
from google.cloud.iam_admin_v1.services.iam.pagers import ListRolesPager
from google.cloud.iam_admin_v1.types.iam import Role
from prettytable import PrettyTable, from_db_cursor

PROJECT_SCRIPT = "gcp-iam-roles"
DB_FILE: Path = Path.home().joinpath(".local", "share", PROJECT_SCRIPT, "gcp_roles.db")
BASH_COMPLETION_DIR = Path.home().joinpath(
    ".local", "share", "bash-completion", "completions"
)


def is_authenticated() -> None:
    from google.auth import default

    credentials, project_id = default()

    if credentials and project_id:
        print(f"Authenticated to Google Cloud with project ID: {project_id}")
    else:
        print("Not authenticated to Google Cloud")
        sys.exit(1)


def get_roles() -> ListRolesPager:
    """
    Retrieves a list of all predefined IAM roles in the current Google Cloud project.

    Returns:
        google.cloud.iam_admin_v1.services.iam.pagers.ListRolesPager: A pager object that can be used to iterate over the list of predefined IAM roles.
    """
    print("Getting Google Cloud IAM predefined roles...")
    client = iam_admin_v1.IAMClient()
    request = iam_admin_v1.ListRolesRequest()
    roles = client.list_roles(request=request)

    return roles


def get_permissions(role_name: str) -> Role:
    """
    Retrieves a list of all permissions associated with a given IAM role.
    """
    client = iam_admin_v1.IAMClient()
    request = iam_admin_v1.GetRoleRequest(name=role_name)
    role = client.get_role(request=request)

    return role


def create_db() -> None:
    """
    Creates a SQLite database table to store Google Cloud IAM predefined roles.
    """
    os.makedirs(DB_FILE.parent, exist_ok=True)

    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS roles (role TEXT PRIMARY KEY, title TEXT, stage TEXT);"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS permissions (permission TEXT, role TEXT, FOREIGN KEY (role) REFERENCES roles (role), UNIQUE (permission, role));"
        )
        print("Created tables: roles, permissions")
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Error creating table: {e}")
    finally:
        conn.close()


def clear_db() -> None:
    """
    Drops the SQLite database table that stores Google Cloud IAM predefined roles.
    """
    prompt = input(
        "**WARRNING!** This will delete all data in the database. Continue? (y/N): "
    )
    if prompt.lower() != "y":
        print("Aborting...")
        sys.exit(0)

    conn = sqlite3.connect(DB_FILE.as_uri())
    try:
        conn.execute("DROP TABLE IF EXISTS permissions;")
        conn.execute("DROP TABLE IF EXISTS roles;")
        conn.commit()
        print("Dropped tables: roles, permissions")
    except sqlite3.OperationalError as e:
        print(f"SQLite Error: {e}")
    finally:
        conn.close()


def store_roles(roles: ListRolesPager) -> None:
    """
    Inserts a list of Google Cloud IAM predefined roles into a SQLite database table.
    """
    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        cursor = conn.cursor()
        for role in roles:
            try:
                cursor.execute(
                    "INSERT INTO roles (role, title, stage) VALUES (?, ?, ?)",
                    (role.name, role.title, role.stage.name),
                )
                print(f"New: {role.name}")
            except sqlite3.IntegrityError:
                print(f"Duplicate: {role.name}")
                continue
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    finally:
        conn.close()


def store_permissions() -> None:
    """
    Inserts a list of Google Cloud IAM predefined roles into a SQLite database table.
    """
    conn = sqlite3.connect(DB_FILE.as_uri())
    # Get all roles from the database
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM roles;")
        roles = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    # Get all permissions for each role and insert them into the database
    try:
        for role in roles:
            role_data = get_permissions(role[0])
            for permission in role_data.included_permissions:
                try:
                    cursor.execute(
                        "INSERT INTO permissions (permission, role) VALUES (?, ?)",
                        (permission, role[0]),
                    )
                    print(f"New: {role[0]} => {permission}")
                except sqlite3.IntegrityError:
                    print(f"Duplicate: {role[0]} => {permission}")
                    continue
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    finally:
        conn.close()


def search_roles(role_name: str) -> None:
    """
    Searches for a Google Cloud IAM predefined role in the SQLite database table.
    """
    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role,title,stage FROM roles WHERE role LIKE ? OR title LIKE ? ORDER BY role;",
            (f"%{role_name}%", f"%{role_name}%"),
        )
        table = from_db_cursor(cursor)
        table.align = "l"
        print(table)
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    finally:
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
    finally:
        conn.close()


def status_db() -> None:
    """
    Prints the number of roles and permissions in the SQLite database table.
    """
    conn = sqlite3.connect(DB_FILE.as_uri())

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM roles;")
        roles = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT permission) FROM permissions;")
        permissions = cursor.fetchone()[0]
        table = PrettyTable()
        table.field_names = ["Type", "Count"]
        table.add_row(["GCP IAM Roles", roles])
        table.add_row(["GCP IAM Permissions", permissions])
        table.align = "l"
        print(table)
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search Google Cloud IAM roles and permissions"
    )

    parser.add_argument(
        "-r",
        "--role",
        nargs=1,
        help="Search for Roles",
    )

    parser.add_argument(
        "-p",
        "--permission",
        nargs=1,
        help="Search for Permissions",
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show Roles and Permissions count",
    )

    parser.add_argument(
        "--bash-completion",
        action="store_true",
        help="Generate bash completion",
    )

    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Populate database with Google Cloud IAM roles",
    )

    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="Drop database tables",
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    if args.role:
        search_roles(args.role[0])

    if args.permission:
        search_permissions(args.permission[0])

    if args.status:
        status_db()

    if args.bash_completion:
        completion_dir = BASH_COMPLETION_DIR
        completion_dir.mkdir(parents=True, exist_ok=True)
        completion_file = completion_dir.joinpath("gcp-iam-roles")
        with open(completion_file, "w") as f:
            f.write(
                '#!/usr/bin/env bash\neval "$(register-python-argcomplete gcp-iam-roles)"'
            )
        print(f"Bash completion installed to {completion_file}")
        sys.exit(0)

    if args.init_db:
        is_authenticated()
        create_db()
        store_roles(get_roles())
        store_permissions()

    if args.clear_db:
        clear_db()


if __name__ == "__main__":
    main()
