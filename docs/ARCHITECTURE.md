# Architecture

## Service

The repo is centered on the local nanoFold leaderboard service.

[service/app.py](../service/app.py) accepts uploaded submission zips, records queue/running/completed status, stores scores in SQLite, serves the static frontend, and exposes leaderboard/status APIs.

[service/evaluator.py](../service/evaluator.py) is the active evaluator. It extracts each uploaded zip, copies it into the configured nanoFold checkout, patches `config.yaml` with local data paths, runs nanoFold `predict.py`, runs nanoFold `score.py`, and persists public/hidden score summaries.

## Data

Competition data is not stored in this repository. Use a local checkout of the official nanoFold competition repo:

```text
https://github.com/ChrisHayduk/nanoFold-Competition/tree/main
```

The evaluator is configured with `NANOFOLD_REPO`, `NANOFOLD_FEATURES_DIR`, `NANOFOLD_LABELS_DIR`, and optional hidden-eval environment variables.

## Frontend

`service/web/` contains the static leaderboard, upload form, metrics page, and submission status/log viewer. It talks directly to the FastAPI service.

## Runtime

The current local runtime is an in-process API evaluator with an exclusive job semaphore. Generated state lives outside git in the configured DB, upload, and log directories.
