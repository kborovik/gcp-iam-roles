from pathlib import Path

SCRIPT_NAME = "gcp-iam-roles"
DB_FILE: Path = Path.home().joinpath(".local", "share", SCRIPT_NAME, "gcp_roles.db")
