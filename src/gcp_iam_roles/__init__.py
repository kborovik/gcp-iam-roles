from importlib.metadata import metadata
from pathlib import Path

package_name = metadata(__package__).get("name")

DB_FILE: Path = Path.home().joinpath(".local", "share", package_name, f"{package_name}.db")
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

import argparse
import sys

import argcomplete
from loguru import logger

from .db import clear_db, create_db, status_db
from .permissions import search_permissions, sync_permissions
from .roles import search_roles, sync_roles
from .services import search_services, sync_services

create_db()


def cli() -> None:
    logger.remove()
    logger.level("ERROR", color="<red>")
    logger.level("WARNING", color="<yellow>")
    logger.level("INFO", color="<blue>")
    logger.level("SUCCESS", color="<green>")
    logger.level("DEBUG", color="<cyan>")
    logger.add(
        sink=sys.stdout,
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level: <7}</level> | <level>{message}</level>",
    )

    parser = argparse.ArgumentParser(description="Search Google Cloud IAM roles and permissions")

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
        "-s",
        "--service",
        nargs=1,
        help="Search for Services",
    )

    parser.add_argument(
        "--sync-roles",
        action="store_true",
        help="Sync Predefined AIM Roles and Permissions",
    )

    parser.add_argument(
        "--sync-services",
        action="store_true",
        help="Sync Google Cloud Services",
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
        "--clear-db",
        action="store_true",
        help="Drop database tables",
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.role:
        search_roles(args.role[0])

    elif args.permission:
        search_permissions(args.permission[0])

    elif args.service:
        search_services(args.service[0])

    elif args.sync_roles:
        create_db()
        sync_roles()
        sync_permissions()

    elif args.sync_services:
        create_db()
        sync_services()

    elif args.status:
        status_db()

    elif args.bash_completion:
        completion_dir = Path.home().joinpath(".local", "share", "bash-completion", "completions")
        completion_dir.mkdir(parents=True, exist_ok=True)
        completion_file = completion_dir.joinpath(package_name)
        completion_file.write_text(
            f'#!/usr/bin/env bash\neval "$(register-python-argcomplete {package_name})"'
        )
        logger.info(f"Bash completion installed to {completion_file}")
        sys.exit(0)

    elif args.clear_db:
        clear_db()

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    cli()
