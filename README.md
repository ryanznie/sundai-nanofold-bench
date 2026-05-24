# Sundai Protein Folding Bench

`sundai-protein-folding-bench` is a Kaggle-style benchmark scaffold for
budget-constrained SimpleFold adaptation and inference.

The repo now includes four concrete pieces:

- a real SimpleFold-backed starter path that calls the public `simplefold` CLI
- a bundle builder that packages FASTA files, baselines, and train/val tokenization
- a structure-based scorer for public-dev bundles
- a minimal FastAPI + Docker worker stack for production orchestration

## Runtime Contract

The benchmark runner mounts a bundle at `/input` and expects predictions at:

```text
/output/predictions/<target_id>_sampled_0.cif
```

The starter backend enforces these runtime rules:

- `backend` is forced to `torch`
- `nsample_per_protein` is forced to `1`
- each FASTA input in `test/manifest.json` must produce exactly one CIF at
  `/output/predictions/<target_id>_sampled_0.cif`

The default starter reads `sequence_fasta_path` from `test/manifest.json`
or uses cached bundle features when available, runs SimpleFold once per target,
and writes one CIF per FASTA input into that filename contract.

## Bundle Layout

```text
/input/
  manifest.json
  train/
    manifest.json
    fastas/
    baselines/
    processed/
    samples/
  val/
    manifest.json
    fastas/
    baselines/
    processed/
    samples/
  test/
    manifest.json
    fastas/
    baselines/            # public-dev only
  checkpoints/
    simplefold_100M.ckpt
```

`train` and `val` can include tokenized artifacts produced by the public
SimpleFold preprocessing scripts. `test` must include per-target FASTA files and
may include baseline structures only for public-dev scoring.

## Local Flow

1. Prepare a raw dataset with `train/`, `val/`, and `test/` FASTA files.
2. Build a bundle:

```bash
python3 tools/build_simplefold_bundle.py \
  --raw_dir /path/to/raw_targets \
  --output_dir data/public_dev \
  --checkpoint_path /path/to/simplefold_100M.ckpt \
  --simplefold_repo /path/to/ml-simplefold
```

3. Install the public `simplefold` CLI in the benchmark runtime.
4. Run:

```bash
bash benchmark.sh
```

## Public-Dev Scoring

The scorer validates that each prediction exists, is non-empty, and contains a
parseable CA trace. It then computes:

- `tm_score`
- `lddt`
- `rmsd`
- `ca_rmsd`
- `gdt_ts_like`

The default ranking remains:

1. `mean_tm_score` descending
2. `runtime_sec` ascending

## Production Pieces

- `service/`: FastAPI starter and leaderboard API with a SQL schema
- `service/web/`: static frontend for leaderboard and starter registration
- `worker/`: Docker-based worker callback flow
- `docker/`: API and worker Dockerfiles plus a runtime spec

See [docs/ARCHITECTURE.md](/Users/ryanznie/Desktop/Important/Work/Sundai/sundai-protein-folding-bench/docs/ARCHITECTURE.md),
[docs/DEPLOYMENT.md](/Users/ryanznie/Desktop/Important/Work/Sundai/sundai-protein-folding-bench/docs/DEPLOYMENT.md), and
[docs/SUBMISSION_SPEC.md](/Users/ryanznie/Desktop/Important/Work/Sundai/sundai-protein-folding-bench/docs/SUBMISSION_SPEC.md).

## Local Service Submission Flow

The local FastAPI service exposes the leaderboard and upload UI from `service/web/`. After uploading a submission, the page polls the active run for up to five minutes. If the run is still active after that window, refresh the page to continue checking status and logs.

Checkpoint files are local runtime artifacts and should stay outside git; the bundle builder copies or links them into the runtime bundle as needed.

## Local Service Env

Use the repo-local `uv` environment:

```bash
uv sync
uv run uvicorn service.app:app --reload
```
