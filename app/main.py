import asyncio, logging, os, time

from fastapi import FastAPI, HTTPException

from app.messaging import format_sms
from app.recommender import Recommender

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("kola-lite")


SNAPSHOT = os.getenv("SNAPSHOT_PATH", "artifacts/snapshot_2026-08-15.json")
TIMEOUT_S = float(os.getenv("MODEL_TIMEOUT_S", "0.8"))

app = FastAPI(title="kola-lite")
model = Recommender.load(SNAPSHOT)
metrics = {"requests": 0, "fallbacks": 0, "latency_ms_total": 0.0}


@app.get("/health")
def health():
    return {"status": "ok", "snapshot_as_of": model.s["as_of"]}


@app.get("/recommend/{user_id}")
async def recommend(user_id: str, k: int = 5, channel: str = "api"):
    started = time.perf_counter()
    source = "model"
    try:
        items, source = await asyncio.wait_for(
            asyncio.to_thread(model.recommend, user_id, k), timeout=TIMEOUT_S
        )
    except asyncio.TimeoutError:
        items = [i for i in model.s["popular"] if i not in model.s["user_items"].get(user_id, [])][:k]
        source = "fallback_timeout"

    latency_ms = (time.perf_counter() - started) * 1000
    metrics["requests"] += 1
    metrics["latency_ms_total"] += latency_ms
    if source != "model":
        metrics["fallbacks"] += 1
    log.info('{"event":"recommend","user":"%s","source":"%s","latency_ms":%.1f}', user_id, source, latency_ms)

    body = {"user_id": user_id, "items": items, "source": source, "latency_ms": round(latency_ms, 1)}
    if channel == "sms":
        body["sms"] = format_sms(user_id, items)
    return body

@app.get("/features/{user_id}")
def features(user_id: str):
    f = model.features(user_id)
    if f is None:
        raise HTTPException(status_code=404, detail="unknown user")
    return {"user_id": user_id, "as_of": model.s["as_of"], **f}


@app.get("/metrics")
def get_metrics():
    n = metrics["requests"] or 1
    return {
        "requests": metrics["requests"],
        "fallback_rate": round(metrics["fallbacks"] / n, 3),
        "avg_latency_ms": round(metrics["latency_ms_total"] / n, 1),
    }
