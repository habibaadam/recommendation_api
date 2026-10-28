import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import build_snapshot, clean


client = TestClient(app)

def test_known_user_gets_model_recommendations():
    r = client.get("/recommend/u5?k=3").json()
    assert r["source"] == "model"
    assert len(r["items"]) == 3


def test_unknown_user_gets_popular_fallback():
    r = client.get("/recommend/nobody").json()
    assert r["source"] == "fallback_popular"
    assert r["items"]

def test_slow_model_times_out_to_fallback(monkeypatch):
    monkeypatch.setenv("MODEL_DELAY_MS", "1500")
    r = client.get("/recommend/u5").json()
    assert r["source"] == "fallback_timeout"
    assert r["latency_ms"] < 1000

