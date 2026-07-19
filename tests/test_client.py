from uuid import uuid4

import pytest

from auditar_sdk.client import AuditarClient
from auditar_sdk.context import InferenceSession
from auditar_sdk.decorators import trace_inference
from auditar_sdk.exceptions import ClientNotConfiguredError, QueueFullError
from auditar_sdk.http_client import HttpClient
from auditar_sdk.models import BatchRequest, BatchResponse, DecisionRecord, ModelRegistration
from auditar_sdk.transport import LocalTransport


class TestDecisionRecord:
    def test_defaults(self):
        rec = DecisionRecord(model_name="m")
        assert rec.decision_id is not None
        assert rec.model_name == "m"
        assert rec.latency_ms is None

    def test_json_roundtrip(self):
        rec = DecisionRecord(model_name="m", latency_ms=1.23)
        data = rec.model_dump_json()
        back = DecisionRecord.model_validate_json(data)
        assert back.model_name == "m"
        assert back.latency_ms == pytest.approx(1.23, abs=1e-3)


class TestModelRegistration:
    def test_defaults(self):
        reg = ModelRegistration(workspace="w", model_name="m")
        assert reg.workspace == "w"
        assert reg.model_version is None
        assert reg.use_case is None


class TestLocalTransport:
    def test_enqueue_and_drain(self, tmp_path):
        db = tmp_path / "queue.db"
        transport = LocalTransport(db_path=str(db))
        rec = DecisionRecord(model_name="m", use_case="u")
        transport.enqueue(rec)
        assert transport.pending_count() == 1
        drained = transport.drain()
        assert len(drained) == 1
        assert drained[0].model_name == "m"
        assert transport.pending_count() == 0

    def test_queue_full_raises(self, tmp_path):
        db = tmp_path / "queue.db"
        transport = LocalTransport(db_path=str(db))
        transport.max_rows = 2
        transport.enqueue(DecisionRecord(model_name="m1"))
        transport.enqueue(DecisionRecord(model_name="m2"))
        with pytest.raises(QueueFullError):
            transport.enqueue(DecisionRecord(model_name="m3"))


class TestAuditarClient:
    def test_emit_and_flush(self, tmp_path):
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
            transport=LocalTransport(db_path=str(tmp_path / "q.db")),
        )
        rec = DecisionRecord(model_name="m", use_case="u", latency_ms=0.5)
        client.emit(rec)
        assert client.pending_count() == 1
        resp = client.manual_flush()
        assert resp is not None
        assert client.pending_count() == 0
        client.close()

    def test_manual_flush_no_endpoint(self, tmp_path):
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
            transport=LocalTransport(db_path=str(tmp_path / "q2.db")),
        )
        if client.manual_flush() is not None:
            raise AssertionError("Expected empty flush to be non-blocking")
        client.close()

    def test_manual_flush_batch_semantics(self, tmp_path):
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
            batch_size=2,
            flush_interval=100.0,
            transport=LocalTransport(db_path=str(tmp_path / "q_batch.db")),
        )
        
        # Manually add 5 decisions to bypass the automatic flush in emit()
        decisions = [DecisionRecord(model_name=f"m{i}") for i in range(5)]
        with client._lock:
            client._pending.extend(decisions)
            
        assert client.pending_count() == 5
        
        # Mock send_batch
        sent_batches = []
        def mock_send_batch(batch):
            sent_batches.append(batch)
            return BatchResponse(batch_id=batch.batch_id, accepted=len(batch.decisions), failed=0, errors=[])
            
        client._http.send_batch = mock_send_batch
        
        # Perform manual flush
        resp = client.manual_flush()
        
        # It should only flush one batch of batch_size (2)
        assert resp is not None
        assert resp.accepted == 2
        assert len(sent_batches) == 1
        assert [d.model_name for d in sent_batches[0].decisions] == ["m0", "m1"]
        assert client.pending_count() == 3
        
        # Flush again
        resp2 = client.manual_flush()
        assert resp2 is not None
        assert resp2.accepted == 2
        assert len(sent_batches) == 2
        assert [d.model_name for d in sent_batches[1].decisions] == ["m2", "m3"]
        assert client.pending_count() == 1
        
        # Flush the remaining 1
        resp3 = client.manual_flush()
        assert resp3 is not None
        assert resp3.accepted == 1
        assert len(sent_batches) == 3
        assert [d.model_name for d in sent_batches[2].decisions] == ["m4"]
        assert client.pending_count() == 0
        
        # Flush empty
        resp4 = client.manual_flush()
        assert resp4 is None
        
        client.close()

    def test_sklearn_wrapper(self):
        pytest.importorskip("sklearn")
        from sklearn.dummy import DummyClassifier
        from sklearn.datasets import make_classification

        X, y = make_classification(n_samples=20, n_features=4, random_state=1)
        model = DummyClassifier(strategy="prior").fit(X, y)
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
        )

        @trace_inference(client, model_name="dummy", use_case="demo")
        def predict(features):
            return model.predict_proba([features])[0][1]

        prob = predict([0.1, 0.2, 0.3, 0.4])
        assert 0.0 <= prob <= 1.0
        assert client.pending_count() >= 1
        client.close()


class TestContextManager:
    def test_inference_session_emits(self, tmp_path):
        client = AuditarClient(
            workspace="w",
            endpoint="https://example.invalid",
            transport=LocalTransport(db_path=str(tmp_path / "q3.db")),
        )
        with InferenceSession(client, use_case="u") as session:
            session.emit(DecisionRecord(model_name="m", latency_ms=0.1))
        assert client.pending_count() >= 1
        client.close()
