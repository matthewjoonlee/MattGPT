"""OAuth authorization for the Google Health API.

Manual, one-time setup (cannot be scripted -- requires an interactive Google
login) is documented in spec/data-ingestion.md. This module only handles the
code side: first-time interactive consent, caching the refresh token, and
silent refresh on subsequent runs. The token file is never logged.
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from mattgpt.config import settings
from mattgpt.ingest.bundles import all_scopes


def load_credentials() -> Credentials:
    """Return valid credentials, refreshing or running the interactive
    consent flow as needed. Caches the result at settings.google_token_path."""
    creds: Credentials | None = None
    token_path = settings.google_token_path

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), all_scopes())

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(settings.google_client_secret_path), all_scopes()
        )
        creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    return creds
