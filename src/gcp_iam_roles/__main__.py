import argparse
import sys
from pathlib import Path

import argcomplete
from loguru import logger

from .auth import get_google_credentials
from .db import clear_db, create_db, status_db
from .permissions import search_permissions, store_permissions
from .roles import get_roles, search_roles, store_roles
from .services import get_services, search_services, store_services


def main() -> None:
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
        "-s",
        "--service",
        nargs=1,
        help="Search for Services",
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

    if args.role:
        search_roles(args.role[0])

    elif args.permission:
        search_permissions(args.permission[0])

    elif args.service:
        search_services(args.service[0])

    elif args.status:
        status_db()

    elif args.bash_completion:
        completion_dir = Path.home().joinpath(
            ".local", "share", "bash-completion", "completions"
        )
        completion_dir.mkdir(parents=True, exist_ok=True)
        completion_file = completion_dir.joinpath("gcp-iam-roles")
        completion_file.write_text(
            '#!/usr/bin/env bash\neval "$(register-python-argcomplete gcp-iam-roles)"'
        )
        logger.info(f"Bash completion installed to {completion_file}")
        sys.exit(0)

    elif args.init_db:
        credential, project_id = get_google_credentials()
        create_db()
        store_roles(get_roles())
        store_permissions()
        store_services(get_services(project_id=project_id))

    elif args.clear_db:
        clear_db()

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
