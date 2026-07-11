import pytest
from uuid import uuid4

from auditar_sdk.exceptions import QueueFullError
from auditar_sdk.http_client import HttpClient
from auditar_sdk.models import BatchRequest, BatchResponse, DecisionRecord
from auditar_sdk.transport import LocalTransport


class TestTransport:
    def test_drain_ordered(self, tmp_path):
        db = tmp_path / "q.db"
        transport = LocalTransport(db_path=str(db))
        transport.enqueue(DecisionRecord(model_name="a"))
        transport.enqueue(DecisionRecord(model_name="b"))
        transport.enqueue(DecisionRecord(model_name="c"))
        drained = transport.drain(batch_size=2)
        assert [d.model_name for d in drained] == ["a", "b"]
        assert transport.pending_count() == 1
        rest = transport.drain()
        assert [d.model_name for d in rest] == ["c"]

    def test_max_rows(self, tmp_path):
        db = tmp_path / "q.db"
        transport = LocalTransport(db_path=str(db))
        transport.max_rows = 1
        transport.enqueue(DecisionRecord(model_name="a"))
        with pytest.raises(QueueFullError):
            transport.enqueue(DecisionRecord(model_name="b"))


class TestHttpClient:
    def test_send_batch_success(self):
        client = HttpClient(
            endpoint="https://example.invalid",
            token="tok",
        )

        def fake_post(*args, **kwargs):  # pragma: no cover
            class _Resp:
                status_code = 200
                def raise_for_status(self):
                    return None
                def json(self):
                    return {"accepted": 1, "failed": 0, "errors": []}
            return _Resp()

        client._client.post = fake_post  # type: ignore[assignment]
        response = client.send_batch(
            BatchRequest(batch_id=uuid4(), decisions=[DecisionRecord(model_name="m")])
        )
        assert isinstance(response, BatchResponse)
        assert response.accepted == 1
        client.close()
