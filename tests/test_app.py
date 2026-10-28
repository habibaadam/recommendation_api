import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import build_snapshot, clean
from app.messaging import format_sms


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

def test_cleaning_drops_bad_rows():
    df = pd.DataFrame({
        "user_id": ["a", "a", "", "b"],
        "item_id": ["x", "x", "y", "z"],
        "date": ["2026-08-01", "2026-08-01", "2026-08-01", "bad"],
    })
    assert len(clean(df)) == 1

def test_snapshot_ignores_rows_after_cutoff():
    df = clean(pd.DataFrame({
        "user_id": ["a", "a"],
        "item_id": ["x", "y"],
        "date": ["2026-08-01", "2026-09-30"],
    }))
    snap = build_snapshot(df, "2026-08-15")
    assert snap["rows_used"] == 1
    assert snap["user_items"]["a"] == ["x"]

def test_metrics_report_fallback_rate():
    client.get("/recommend/nobody")
    m = client.get("/metrics").json()
    assert m["requests"] >= 1 and 0 <= m["fallback_rate"] <= 1

def test_sms_fits_limit():
    assert len(format_sms("u1", [f"item{i}" for i in range(50)])) <= 160
