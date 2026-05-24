# Local Service Handoff

This document is the shortest path to wiring the benchmark into a separate local leaderboard service.

## Pin These Inputs

### Benchmark Repo

Use a pinned commit SHA from this repository. Do not integrate against a moving `main` branch reference for production evaluations.

### Data Repo

Use the official nanoFold competition repository for data, manifests, preprocessing, and submission-contract documentation:

```text
https://github.com/ChrisHayduk/nanoFold-Competition/tree/main
```

The dataset is intentionally not vendored here. Downloading and preprocessing the official data can take hours, so reuse an existing local checkout when one is already available.

## Runtime Contract

The worker should mount:

- `/input` -> read-only official nanoFold data or prepared evaluation bundle
- `/output` -> writable run output directory

The runner should execute the pinned benchmark command with:

```text
INPUT_DIR=/input
OUTPUT_DIR=/output
TIMEOUT_SEC=600
```

## Submission Contract

Submissions should follow the nanoFold competition API contract documented in the data repo, including the `build_model`, `build_optimizer`, and `run_batch` entrypoints used by official tracks.

The benchmark service owns:

- upload validation
- worker launch
- service-side scoring integration
- final score extraction
- leaderboard persistence

## Recommended Worker Behavior

1. Unpack submission into a workspace.
2. Mount the local nanoFold data checkout or prepared bundle at `/input`.
3. Mount an empty output directory at `/output`.
4. Run the pinned benchmark command.
5. Read result artifacts from `/output`.
6. Persist logs and scores.

## Suggested Metadata To Store

- `benchmark_repo`
- `benchmark_commit_sha`
- `data_repo`
- `data_commit_sha`
- `data_root`
- `track`
- `runtime_sec`
- `valid`
- per-target metrics

## Recommended Defaults

- official nanoFold public data only
- one GPU unless a track says otherwise
- no internet during execution
- final ranking by the configured nanoFold track metric
