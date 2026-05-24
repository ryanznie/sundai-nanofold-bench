# Sundai NanoFold Bench

`sundai-nanofold-bench` is the local service and submission scaffold for the Sundai nanoFold leaderboard. It provides the FastAPI service, static leaderboard UI, Docker worker flow, scorer integration, and example submission wiring used to run and evaluate competition submissions.

## Data Source

Use the official nanoFold competition repository for data, manifests, preprocessing, and participant-facing training instructions:

https://github.com/ChrisHayduk/nanoFold-Competition/tree/main

The nanoFold repo describes itself as a data-efficiency competition for protein structure prediction and includes the official train set, sample budget, hidden evaluation path, track policy, manifests, and submission API documentation.

Important: downloading and preprocessing the official data can take hours. If you already have a local clone with the data prepared, reuse that local copy rather than downloading it again. New users should start the download early and expect a long first setup.

## Runtime Contract

Submissions are evaluated through the nanoFold contract rather than the removed SimpleFold/public_lb bundles. A submission should follow the API and tensor formats documented in the nanoFold competition repo, especially the `build_model`, `build_optimizer`, and `run_batch` contract used by the official tracks.

The local service in this repository handles upload, queueing, worker execution, status reporting, and leaderboard display. The competition data itself should be mounted or referenced from your local nanoFold data checkout.

## Production Pieces

- `service/`: FastAPI service and leaderboard API with a SQL schema
- `service/web/`: static frontend for leaderboard, submission upload, run status, and metrics
- `worker/`: Docker-based worker callback flow
- `docker/`: API and worker Dockerfiles plus a runtime spec
- `sdk/`: lightweight client helpers for service interaction

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), and [docs/SUBMISSION_SPEC.md](docs/SUBMISSION_SPEC.md).

## Local Service Submission Flow

The local FastAPI service exposes the leaderboard and upload UI from `service/web/`. After uploading a submission, the page polls the active run for up to five minutes. If the run is still active after that window, refresh the page to continue checking status and logs.

Runtime artifacts, downloaded datasets, checkpoints, and generated bundles should stay outside git. Keep large local data in your nanoFold checkout or another local data directory and point your training/evaluation commands at that location.

## Local Service Env

Use the repo-local `uv` environment:

```bash
uv sync
uv run uvicorn service.app:app --reload
```
