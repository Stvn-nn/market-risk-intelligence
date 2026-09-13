from fastapi.testclient import TestClient
from market_risk.api import app


def test_read_only_api_demo():
    client=TestClient(app)
    assert client.get('/health').json()=={'status':'ok'}
    response=client.get('/analysis/AAPL')
    assert response.status_code==200
    assert response.json()['provenance']['synthetic'] is True
    assert 0<=response.json()['risk_index']['score']<=100
    assert client.get('/analysis/TSLA').status_code==422
