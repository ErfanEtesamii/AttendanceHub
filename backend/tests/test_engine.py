from uuid import uuid4

from app.engine import MockEngineClient


def test_mock_engine_is_explicitly_not_connected() -> None:
    client = MockEngineClient(); company_id = uuid4()
    health = client.health(company_id)
    assert health.status == "not_connected"
    assert health.provider == "mock"
    assert client.provision_company(company_id).status == "not_connected"
    assert client.sync_policy(company_id).status == "not_connected"
    assert client.sync_members(company_id).status == "not_connected"
