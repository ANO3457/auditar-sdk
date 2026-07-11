"""Batch inference session context manager."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Iterable, List, Optional

from auditar_sdk.client import AuditarClient
from auditar_sdk.models import BatchRequest, DecisionRecord

LOG = logging.getLogger(__name__)


class InferenceSession:
    """Context manager that batches emitted decisions."""

    def __init__(self, client: AuditarClient, use_case: Optional[str] = None) -> None:
        self.client = client
        self.use_case = use_case or client.default_use_case
        self._records: List[DecisionRecord] = []
        self._original_emit = client.emit

    def emit(self, decision: DecisionRecord) -> None:
        if decision.use_case is None and self.use_case is not None:
            object.__setattr__(decision, "use_case", self.use_case)
        self._records.append(decision)

    def __enter__(self) -> "InferenceSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            LOG.debug("InferenceSession exiting with exception; dropping %d buffered records", len(self._records))
            return
        if not self._records:
            return
        try:
            for record in self._records:
                self._original_emit(record)
        except Exception:
            LOG.exception("Failed to emit session batch")
