# Deployment Plan

## Images

The repo includes:

1. `docker/api/Dockerfile`
2. `docker/worker/Dockerfile`

The worker runtime contract is described in [docker/worker/runtime-spec.json](../docker/worker/runtime-spec.json).

## Data

This repository no longer ships `simplefold_hackathon_v1` or `public_lb_v1` data. Use the official nanoFold competition repository for data, manifests, preprocessing, and participant training instructions:

https://github.com/ChrisHayduk/nanoFold-Competition/tree/main

Downloading and preprocessing the official data can take hours. Reuse an existing local clone/data checkout when available.

## Local API Bring-Up

Set `NANOFOLD_DATA_ROOT` to the local nanoFold data checkout before starting Docker Compose:

```bash
export NANOFOLD_DATA_ROOT=/path/to/nanoFold-Competition/data
docker compose up -d --build api
docker compose logs -f api
```

The API container expects these mounts:

- `${NANOFOLD_DATA_ROOT}` -> `/opt/sundai/nanofold-data` as read-only competition data
- a writable Docker volume at `/data` for the SQLite DB, uploads, and per-submission logs

Or, in the repo-local environment:

```bash
uv sync
uv run uvicorn service.app:app --reload
```

## Worker Flow

1. `POST /submissions`
2. Store uploaded zip in object storage
3. Start `worker/run_submission.py`
4. Worker runs `docker run --gpus all --network none`
5. Worker posts results to `/internal/submissions/{id}/complete`
6. Leaderboard reads scored submissions

## Production Constraints

- disable egress in benchmark containers
- mount official nanoFold data read-only
- mount `/output` writable
- enforce GPU count and timeout from runtime spec
- mount a repo snapshot so the runner and submission contract stay pinned
