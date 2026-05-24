# Deployment Plan

## Image

The repo includes `docker/api/Dockerfile` for the FastAPI service.

## Data

Use the official nanoFold competition repository for data, manifests, preprocessing, and participant training instructions:

https://github.com/ChrisHayduk/nanoFold-Competition/tree/main

Downloading and preprocessing the official data can take hours. Reuse an existing local clone/data checkout when available.

## Local API Bring-Up

Set `NANOFOLD_REPO_ROOT` to the local nanoFold checkout before starting Docker Compose:

```bash
export NANOFOLD_REPO_ROOT=/path/to/nanoFold-Competition
docker compose up -d --build api
docker compose logs -f api
```

The API container expects these mounts:

- `${NANOFOLD_REPO_ROOT}` -> `/opt/sundai/nanofold-competition` as a read-only nanoFold checkout
- a writable Docker volume at `/data` for the SQLite DB, uploads, and per-submission logs

Or, in the repo-local environment:

```bash
uv sync
uv run uvicorn service.app:app --reload
```

## Evaluation Flow

1. `POST /submissions/upload`
2. Store uploaded zip under the configured upload root
3. Queue the upload through the in-process evaluator
4. The service runs nanoFold `predict.py` and `score.py`
5. The service persists results and logs
6. Leaderboard reads scored submissions

## Production Constraints

- keep downloaded nanoFold data outside git
- mount official nanoFold data read-only where possible
- keep uploads, logs, and SQLite DB on persistent storage
- run one evaluation at a time unless GPU capacity and isolation are explicitly changed
