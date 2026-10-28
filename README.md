# Lite Recommendation API

A small FastAPI service that recommends items from a precomputed purchase-history snapshot. It uses item co-purchase counts to rank items a user has not already purchased, with popular-item and timeout fallbacks.

The repository includes sample purchase data; generated snapshot files are ignored by Git. This is a lightweight demo service; its recommendation data and in-memory metrics are not a production data store.

## Features

- Item-to-item recommendations based on shared user purchase histories
- Popular-item fallback for users without useful co-purchase scores
- Timeout fallback to popular items if recommendation work takes too long
- User purchase features and a health endpoint
- Optional SMS-formatted recommendation text (formatting only; no SMS provider integration)

## Requirements

- Python 3.12 recommended (the Docker image uses Python 3.12)
- pip

## Run locally

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app.pipeline 2026-08-15
uvicorn app.main:app --reload
```

Generate the snapshot before launching the API; snapshot JSON files are ignored by Git and are not included in a fresh checkout. The command above creates the default snapshot from the included sample CSV. The service listens at <http://127.0.0.1:8000>. Interactive API documentation is available at <http://127.0.0.1:8000/docs>.

The default snapshot path is `artifacts/snapshot_2026-08-15.json`. To use another snapshot, set `SNAPSHOT_PATH` before starting the service:

```bash
SNAPSHOT_PATH=artifacts/snapshot_2026-09-15.json uvicorn app.main:app --reload
```

## API

### `GET /health`

Returns the service status and the date represented by the loaded snapshot.

```bash
curl http://127.0.0.1:8000/health
```

### `GET /recommend/{user_id}`

Returns recommendations for a user.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `k` | integer | `5` | Maximum number of items to return |
| `channel` | string | `api` | Set to `sms` to include a short `sms` message in the response |

```bash
curl 'http://127.0.0.1:8000/recommend/u5?k=3'
curl 'http://127.0.0.1:8000/recommend/u5?k=3&channel=sms'
```

The response includes `user_id`, `items`, `source`, and `latency_ms`. The `source` is `model`, `fallback_popular`, or `fallback_timeout`. For example:

```json
{
  "user_id": "u5",
  "items": ["item12", "item21", "item24"],
  "source": "model",
  "latency_ms": 1.2
}
```

Recommendation results depend on the selected snapshot, so item names and latency will vary. When `channel=sms`, the response also includes an `sms` string truncated to 160 characters.

### `GET /features/{user_id}`

Returns the user's snapshot date and features: `purchases_30d`, `distinct_items`, and `days_since_last`. Returns HTTP `404` for an unknown user.

```bash
curl http://127.0.0.1:8000/features/u5
```

### `GET /metrics`

Returns process-local request count, fallback rate, and average latency since the service started. These in-memory metrics reset on restart.

```bash
curl http://127.0.0.1:8000/metrics
```

## Data and snapshots

`data/purchases.csv` contains the sample purchase history with columns `user_id`, `item_id`, and `date`. The pipeline cleans invalid rows, removes duplicates, filters purchases after a cutoff date, and writes a JSON snapshot containing popular items, user purchase histories, co-purchase counts, and user features.

Build a snapshot from the included CSV:

```bash
python -m app.pipeline 2026-09-15
```

The cutoff date is optional; when omitted, it defaults to `2026-09-15`. The output is written to `artifacts/snapshot_<date>.json`. Point `SNAPSHOT_PATH` at that file when starting the API. Snapshot artifacts are ignored by Git, so regenerate them if they are not present in your checkout.

The sample data can be regenerated with:

```bash
python scripts/generate_sample_data.py
```

This overwrites `data/purchases.csv`.

## Configuration

| Environment variable | Default | Description |
| --- | --- | --- |
| `SNAPSHOT_PATH` | `artifacts/snapshot_2026-08-15.json` | Snapshot JSON file loaded when the app starts |
| `MODEL_TIMEOUT_S` | `0.8` | Maximum time, in seconds, to wait for recommendation work before using the timeout fallback |
| `MODEL_DELAY_MS` | `0` | Optional artificial model delay in milliseconds, useful for demonstrating the timeout fallback |

For example, to exercise the timeout fallback:

```bash
MODEL_DELAY_MS=1500 uvicorn app.main:app --reload
```

## Tests

Run the test suite from the repository root:

```bash
pytest
```

## Docker

Build and run the API from the repository root:

```bash
python -m app.pipeline 2026-08-15
docker build -t kola-lite .
docker run --rm -p 8000:8000 kola-lite
```

Generate the snapshot before building the image; the Dockerfile copies the `artifacts` directory into the container. The container listens on port `8000`. To override its snapshot or timeout settings, pass environment variables with `-e`, for example:

```bash
docker run --rm -p 8000:8000 \
  -e MODEL_TIMEOUT_S=1.2 \
  kola-lite
```
