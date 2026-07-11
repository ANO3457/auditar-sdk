"""auditar-sdk exceptions."""

from __future__ import annotations


class AuditarError(Exception):
    """Base exception for auditar-sdk."""


class TransportError(AuditarError):
    """Raised when the HTTP transport encounters a terminal failure."""


class QueueFullError(AuditarError):
    """Raised when the local SQLite queue is at capacity."""


class ModelNotRegisteredError(AuditarError):
    """Raised when a decorator is applied without a registered model."""


class ClientNotConfiguredError(AuditarError):
    """Raised when the client is used without an endpoint or workspace."""
