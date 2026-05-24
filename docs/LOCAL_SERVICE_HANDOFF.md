# Local Service Handoff

This document is the shortest path to wiring the local leaderboard service to a prepared nanoFold checkout.

## Pin These Inputs

### Service Repo

Use a pinned commit SHA from this repository. Do not integrate against a moving `main` branch reference for production evaluations.

### Data Repo

Use the official nanoFold competition repository for data, manifests, preprocessing, and submission-contract documentation:

```text
https://github.com/ChrisHayduk/nanoFold-Competition/tree/main
```

Downloading and preprocessing the official data can take hours, so reuse an existing local checkout when one is already available.

## Evaluator Contract

The service expects:

- `NANOFOLD_REPO` -> local nanoFold competition checkout
- `NANOFOLD_FEATURES_DIR` -> public processed features
- `NANOFOLD_LABELS_DIR` -> public processed labels
- optional hidden manifest/features/labels environment variables for hidden scoring

Uploaded submissions are zip archives containing `config.yaml`, `submission.py`, and a `checkpoints/` directory with `ckpt_last.pt` or `ckpt_step_*.pt`.

## Service Responsibilities

- upload validation
- single-run queueing and cancellation
- config patching for local data paths
- nanoFold `predict.py` and `score.py` execution
- final score extraction
- leaderboard persistence

## Suggested Metadata To Store

- `service_repo`
- `service_commit_sha`
- `data_repo`
- `data_commit_sha`
- `data_root`
- `track`
- `runtime_sec`
- `valid`
- public and hidden score summaries

## Recommended Defaults

- official nanoFold public data only unless hidden data is configured
- one GPU unless a track says otherwise
- no internet during evaluation
- final ranking by the configured nanoFold track metric
