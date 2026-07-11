"""AuditarClient — batch emit + flush."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from auditar_sdk.exceptions import ClientNotConfiguredError, ModelNotRegisteredError
from auditar_sdk.http_client import HttpClient
from auditar_sdk.models import BatchRequest, BatchResponse, DecisionRecord, ModelRegistration
from auditar_sdk.transport import LocalTransport

LOG = logging.getLogger(__name__)


class AuditarClient:
    """Core SDK client for emitting inference decisions."""

    def __init__(
        self,
        workspace: str,
        endpoint: str,
        token: Optional[str] = None,
        batch_size: int = 50,
        flush_interval: float = 2.0,
        transport: Optional[LocalTransport] = None,
        default_use_case: Optional[str] = None,
    ) -> None:
        if not endpoint:
            raise ClientNotConfiguredError("endpoint is required")
        self.workspace = workspace
        self.endpoint = endpoint
        self.token = token
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.default_use_case = default_use_case
        self._http = HttpClient(endpoint=endpoint, token=token)
        self._transport = transport or LocalTransport()
        self._regs: Dict[str, ModelRegistration] = {}
        self._pending: List[DecisionRecord] = []
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._ensure_flush_loop()

    def register_model(self, model_name: str, model_version: Optional[str] = None, use_case: Optional[str] = None) -> ModelRegistration:
        reg = ModelRegistration(
            workspace=self.workspace,
            model_name=model_name,
            model_version=model_version,
            use_case=use_case or self.default_use_case,
        )
        self._regs[model_name] = reg
        LOG.info("Registered model %s", model_name)
        return reg

    def _get_reg(self, model_name: str, use_case: Optional[str]) -> ModelRegistration:
        reg = self._regs.get(model_name)
        if reg is not None:
            return reg
        return self.register_model(
            model_name=model_name,
            use_case=use_case or self.default_use_case,
        )

    def emit(self, decision: DecisionRecord) -> None:
        with self._lock:
            self._pending.append(decision)
            if len(self._pending) >= self.batch_size:
                self._flush_locked()

    def manual_flush(self) -> Optional[BatchResponse]:
        with self._lock:
            return self._flush_locked()

    def _flush_locked(self) -> Optional[BatchResponse]:
        if not self._pending:
            return None
        batch = BatchRequest(batch_id=uuid4(), decisions=self._pending[: self.batch_size])
        self._pending = self._pending[self.batch_size :]
        try:
            response = self._http.send_batch(batch)
            if response.failed:
                LOG.warning("Partial batch failure: %s", response.errors)
            LOG.debug("Flushed batch %s", batch.batch_id)
            return response
        except Exception as exc:
            LOG.error("Flush failed, requeuing: %s", exc)
            self._transport.enqueue(batch.decisions[0])
            return BatchResponse(batch_id=batch.batch_id, accepted=0, failed=len(batch.decisions), errors=[str(exc)])

    def _ensure_flush_loop(self) -> None:
        def _tick() -> None:
            try:
                with self._lock:
                    self._flush_locked()
            finally:
                self._timer = threading.Timer(self.flush_interval, _tick)
                self._timer.daemon = True
                self._timer.start()

        self._timer = threading.Timer(self.flush_interval, _tick)
        self._timer.daemon = True
        self._timer.start()

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    def close(self) -> None:
        if self._timer:
            self._timer.cancel()
        self._http.close()

    def __enter__(self) -> "AuditarClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
