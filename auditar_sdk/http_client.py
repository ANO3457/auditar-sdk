"""HTTP client with tenacity retry logic."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from auditar_sdk.exceptions import TransportError
from auditar_sdk.models import BatchRequest, BatchResponse

LOG = logging.getLogger(__name__)


class HttpClient:
    """Retrying HTTP client for Auditar ingest."""

    def __init__(self, endpoint: str, token: Optional[str] = None) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self._client = httpx.Client(
            timeout=httpx.Timeout(10.0, connect=5.0)
        )

    def _headers(self) -> Dict[str, str]:
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
        }
        if self.token:
            headers["authorization"] = f"Bearer {self.token}"
        return headers

    @retry(
        retry=retry_if_exception(lambda exc: isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500),
        wait=wait_exponential(multiplier=0.3, min=0.5, max=4),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _post(self, path: str, payload: Dict) -> Dict:
        resp = self._client.post(
            f"{self.endpoint}{path}",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def send_batch(self, batch: BatchRequest) -> BatchResponse:
        try:
            data = self._post("/api/v1/ingest/batch", batch.model_dump())
            return BatchResponse(
                batch_id=batch.batch_id,
                accepted=data.get("accepted", 0),
                failed=data.get("failed", 0),
                errors=data.get("errors", []),
            )
        except RetryError as exc:
            LOG.error("HTTP transport failed after retries: %s", exc)
            raise TransportError("Auditar endpoint unreachable") from exc
        except httpx.HTTPStatusError as exc:
            LOG.error("HTTP transport error: %s", exc)
            raise TransportError(f"HTTP {exc.response.status_code}") from exc

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
