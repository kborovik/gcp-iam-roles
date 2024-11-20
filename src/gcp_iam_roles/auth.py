import sys
from typing import Tuple

import google.auth
from google.auth.credentials import Credentials
from loguru import logger


def get_google_credentials() -> Tuple[Credentials, str]:
    try:
        credentials, project_id = google.auth.default()
        credentials.refresh(google.auth.transport.requests.Request())
        return credentials, project_id
    except google.auth.exceptions.DefaultCredentialsError as error:
        logger.error("Authentication failed: ", error)
        sys.exit(1)
    except google.auth.exceptions.RefreshError:
        logger.error(
            "Token has been expired or revoked. Run `gcloud auth login --update-adc` to authenticate."
        )
        sys.exit(1)
