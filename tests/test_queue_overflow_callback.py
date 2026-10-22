import pytest

from auditar_sdk.exceptions import QueueFullError
from auditar_sdk.models import DecisionRecord
from auditar_sdk.transport import LocalTransport


def test_callback_observes_overflow_error_and_existing_queue(tmp_path):
    observed = []
    transport = LocalTransport(
        tmp_path / "queue.db",
        on_queue_full=lambda error: observed.append((error, transport.pending_count())),
    )
    transport.max_rows = 1
    accepted = DecisionRecord(model_name="accepted")
    rejected = DecisionRecord(model_name="rejected")
    transport.enqueue(accepted)
    assert observed == []
    with pytest.raises(QueueFullError, match="Queue is full at 1 records") as caught:
        transport.enqueue(rejected)
    assert observed == [(caught.value, 1)]
    assert transport.drain() == [accepted]
    transport.enqueue(rejected)
    assert transport.drain() == [rejected]
    assert len(observed) == 1


def test_callback_failure_does_not_replace_queue_full_error(tmp_path, caplog):
    def broken_callback(error):
        raise RuntimeError("notification unavailable")

    transport = LocalTransport(tmp_path / "queue.db", on_queue_full=broken_callback)
    transport.max_rows = 0
    with pytest.raises(QueueFullError):
        transport.enqueue(DecisionRecord(model_name="rejected"))
    assert transport.pending_count() == 0
    assert "notification unavailable" in caplog.text
    assert "rejected" not in caplog.text


def test_default_overflow_still_raises_without_callback(tmp_path):
    transport = LocalTransport(tmp_path / "queue.db")
    transport.max_rows = 0
    with pytest.raises(QueueFullError):
        transport.enqueue(DecisionRecord(model_name="rejected"))
    assert transport.pending_count() == 0
