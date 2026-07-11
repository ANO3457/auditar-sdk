import asyncio

import pytest

from auditar_sdk.client import AuditarClient
from auditar_sdk.decorators import trace_inference, trace_inference_async
from auditar_sdk.models import DecisionRecord


class TestSyncDecorator:
    def test_wraps_result(self):
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
        )

        @trace_inference(client, model_name="m", use_case="u")
        def add(a, b):
            return a + b

        assert add(1, 2) == 3
        assert client.pending_count() >= 1
        client.close()

    def test_passes_exception(self):
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
        )

        @trace_inference(client, model_name="m", use_case="u")
        def fail():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            fail()
        client.close()

    def test_exception_does_not_crash_emit(self):
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
        )

        @trace_inference(client, model_name="m", use_case="u")
        def fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            fail()
        client.close()


class TestAsyncDecorator:
    @pytest.mark.asyncio
    async def test_async_passthrough(self):
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
        )

        @trace_inference_async(client, model_name="m", use_case="u")
        async def mul(a, b):
            return a * b

        result = await mul(3, 4)
        assert result == 12
        assert client.pending_count() >= 1
        client.close()
