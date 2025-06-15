import sys

import google.auth
from google.auth.credentials import Credentials
from rich.console import Console

console = Console()


def get_google_credentials() -> tuple[Credentials, str]:
    try:
        credentials, project_id = google.auth.default()
        credentials.refresh(google.auth.transport.requests.Request())
        return credentials, project_id
    except google.auth.exceptions.DefaultCredentialsError as error:
        console.print(f"[red]Authentication failed: {error}[/red]")
        sys.exit(1)
    except google.auth.exceptions.RefreshError:
        console.print(
            "[red]Token has been expired or revoked. Run `gcloud auth login --update-adc` to authenticate.[/red]"
        )
        sys.exit(1)
