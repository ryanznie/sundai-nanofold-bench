# Submission Spec

Submissions are zip archives uploaded through the local service UI or `POST /submissions/upload`.

## Required Zip Contents

```text
config.yaml
submission.py
checkpoints/
  ckpt_last.pt
```

`checkpoints/ckpt_step_*.pt` is also accepted. When multiple step checkpoints are present, the evaluator uses the highest numbered checkpoint. If no `ckpt_step_*.pt` exists, it falls back to `checkpoints/ckpt_last.pt`.

The zip should place these files at the archive root, not under an extra parent directory.

## Runtime Contract

The service copies the uploaded submission into the local nanoFold checkout configured by `NANOFOLD_REPO`. It then patches `config.yaml` with the active data paths and runs the official nanoFold `predict.py` and `score.py` entrypoints.

Submissions should follow the contract documented in the official nanoFold competition repository:

https://github.com/ChrisHayduk/nanoFold-Competition/tree/main

That includes the model, optimizer, and batch entrypoints used by the official tracks, such as `build_model`, `build_optimizer`, and `run_batch`.

## Evaluator Environment

The service reads these environment variables:

- `NANOFOLD_REPO`: local nanoFold competition checkout; default `/root/nanoFold-Competition`
- `NANOFOLD_PYTHON`: Python executable used to run nanoFold scripts; default current interpreter
- `NANOFOLD_FEATURES_DIR`: public processed features directory
- `NANOFOLD_LABELS_DIR`: public processed labels directory
- `NANOFOLD_HIDDEN_MANIFEST`: optional hidden manifest path
- `NANOFOLD_HIDDEN_FEATURES_DIR`: optional hidden processed features directory
- `NANOFOLD_HIDDEN_LABELS_DIR`: optional hidden processed labels directory

Downloading and preprocessing the official data can take hours. Reuse an existing prepared local checkout when available.
