"""Decorators and async wrappers for zero-knowledge inference tracing."""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar

from auditar_sdk.client import AuditarClient
from auditar_sdk.exceptions import ModelNotRegisteredError
from auditar_sdk.models import DecisionRecord, ModelRegistration

LOG = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def trace_inference(
    client: AuditarClient,
    model_name: str,
    model_version: Optional[str] = None,
    use_case: Optional[str] = None,
) -> Callable[[F], F]:
    """Wrap a sync ML function/callable and emit a zero-knowledge decision record."""
    reg = client._get_reg(model_name, use_case=use_case)

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            return _make_async_wrapper(client, reg, func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.perf_counter()
            result = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                raise
            finally:
                latency_ms = (time.perf_counter() - started) * 1000.0
                decision = DecisionRecord(
                    model_name=reg.model_name,
                    model_version=reg.model_version,
                    use_case=reg.use_case,
                    inputs=_safe_inputs(args, kwargs),
                    outputs=_safe_outputs(result),
                    latency_ms=latency_ms,
                )
                try:
                    client.emit(decision)
                except Exception as exc:
                    LOG.debug("Auditar emit failed: %s", exc)

        return wrapper  # type: ignore[return-value]

    return decorator


def trace_inference_async(
    client: AuditarClient,
    model_name: str,
    model_version: Optional[str] = None,
    use_case: Optional[str] = None,
) -> Callable[[F], F]:
    """Wrap an async ML function/callable and emit a zero-knowledge decision record."""
    reg = client._get_reg(model_name, use_case=use_case)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.perf_counter()
            result = None
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                raise
            finally:
                latency_ms = (time.perf_counter() - started) * 1000.0
                decision = DecisionRecord(
                    model_name=reg.model_name,
                    model_version=reg.model_version,
                    use_case=reg.use_case,
                    inputs=_safe_inputs(args, kwargs),
                    outputs=_safe_outputs(result),
                    latency_ms=latency_ms,
                )
                try:
                    client.emit(decision)
                except Exception as exc:
                    LOG.debug("Auditar emit failed: %s", exc)

        return wrapper  # type: ignore[return-value]

    return decorator


def _make_sync_wrapper(client: AuditarClient, reg: ModelRegistration, func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        result = None
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            raise
        finally:
            latency_ms = (time.perf_counter() - started) * 1000.0
            decision = DecisionRecord(
                model_name=reg.model_name,
                model_version=reg.model_version,
                use_case=reg.use_case,
                inputs=_safe_inputs(args, kwargs),
                outputs=_safe_outputs(result),
                latency_ms=latency_ms,
            )
            try:
                client.emit(decision)
            except Exception as exc:
                LOG.debug("Auditar emit failed: %s", exc)

    return wrapper


def _make_async_wrapper(client: AuditarClient, reg: ModelRegistration, func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        result = None
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception:
            raise
        finally:
            latency_ms = (time.perf_counter() - started) * 1000.0
            decision = DecisionRecord(
                model_name=reg.model_name,
                model_version=reg.model_version,
                use_case=reg.use_case,
                inputs=_safe_inputs(args, kwargs),
                outputs=_safe_outputs(result),
                latency_ms=latency_ms,
            )
            try:
                client.emit(decision)
            except Exception as exc:
                LOG.debug("Auditar emit failed: %s", exc)

    return wrapper


def _safe_inputs(args: tuple, kwargs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        return {"args": _safe(args), "kwargs": _safe(kwargs)}
    except Exception:
        return None


def _safe_outputs(result: Any) -> Optional[Dict[str, Any]]:
    try:
        value = _safe(result)
        if value is None or isinstance(value, dict):
            return value
        return {"value": value}
    except Exception:
        return None


def _safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    try:
        return str(value)
    except Exception:
        return None
