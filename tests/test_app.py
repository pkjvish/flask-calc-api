import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"


def test_add(client):
    r = client.post("/api/v1/add", json={"a": 10, "b": 5})
    assert r.status_code == 200
    assert r.get_json()["result"] == 15


def test_subtract(client):
    r = client.post("/api/v1/subtract", json={"a": 10, "b": 5})
    assert r.status_code == 200
    assert r.get_json()["result"] == 5


def test_multiply(client):
    r = client.post("/api/v1/multiply", json={"a": 4, "b": 5})
    assert r.status_code == 200
    assert r.get_json()["result"] == 20


def test_divide(client):
    r = client.post("/api/v1/divide", json={"a": 10, "b": 2})
    assert r.status_code == 200
    assert r.get_json()["result"] == 5


def test_divide_by_zero(client):
    r = client.post("/api/v1/divide", json={"a": 10, "b": 0})
    assert r.status_code == 400


def test_power(client):
    r = client.post("/api/v1/power", json={"a": 2, "b": 10})
    assert r.status_code == 200
    assert r.get_json()["result"] == 1024


def test_sqrt(client):
    r = client.post("/api/v1/sqrt", json={"a": 25})
    assert r.status_code == 200
    assert r.get_json()["result"] == 5


def test_sqrt_negative(client):
    r = client.post("/api/v1/sqrt", json={"a": -1})
    assert r.status_code == 400
