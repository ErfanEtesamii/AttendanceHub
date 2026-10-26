from uuid import uuid4

from app.engine import MockEngineClient


def test_mock_engine_is_explicitly_not_connected() -> None:
    health = MockEngineClient().health(uuid4())
    assert health.status == "not_connected"
    assert health.provider == "mock"
