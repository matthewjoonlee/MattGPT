"""Shared authenticated-GET-with-retry helper for the Health and Calendar clients."""

from typing import Any

import requests
from google.oauth2.credentials import Credentials
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class TransientAPIError(Exception):
    pass


@retry(
    retry=retry_if_exception_type(TransientAPIError),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
def get_json(creds: Credentials, url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {creds.token}"},
        params=params,
        timeout=30,
    )
    if response.status_code in _RETRYABLE_STATUS_CODES:
        raise TransientAPIError(f"{response.status_code} from {url}")
    response.raise_for_status()
    return response.json()
