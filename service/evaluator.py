from __future__ import annotations

import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from threading import Event
from typing import Callable

import yaml

from service.logging_utils import append_submission_progress, env_path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger("sundai.evaluator")

NANOFOLD_REPO = env_path("NANOFOLD_REPO", "/root/nanoFold-Competition")
NANOFOLD_PYTHON = Path(os.environ.get("NANOFOLD_PYTHON", sys.executable))
NANOFOLD_FEATURES_DIR = env_path("NANOFOLD_FEATURES_DIR", str(NANOFOLD_REPO / "data" / "processed_features"))
NANOFOLD_LABELS_DIR = env_path("NANOFOLD_LABELS_DIR", str(NANOFOLD_REPO / "data" / "processed_labels"))
NANOFOLD_HIDDEN_MANIFEST = os.environ.get("NANOFOLD_HIDDEN_MANIFEST", "")
NANOFOLD_HIDDEN_FEATURES_DIR = os.environ.get("NANOFOLD_HIDDEN_FEATURES_DIR", "")
NANOFOLD_HIDDEN_LABELS_DIR = os.environ.get("NANOFOLD_HIDDEN_LABELS_DIR", "")


class SubmissionCancelledError(RuntimeError):
    pass


def evaluator_assets_ready() -> tuple[bool, list[str]]:
    required = [
        NANOFOLD_REPO / "train.py",
        NANOFOLD_REPO / "eval.py",
        NANOFOLD_REPO / "score.py",
        NANOFOLD_FEATURES_DIR,
        NANOFOLD_LABELS_DIR,
        NANOFOLD_REPO / "data" / "manifests" / "train.txt",
        NANOFOLD_REPO / "data" / "manifests" / "val.txt",
    ]
    missing = [str(p) for p in required if not Path(p).exists()]
    LOGGER.info(
        "evaluator assets check ready=%s nanofold_repo=%s missing=%s",
        len(missing) == 0,
        NANOFOLD_REPO,
        missing,
    )
    return len(missing) == 0, missing


def hidden_assets_available() -> bool:
    return bool(NANOFOLD_HIDDEN_MANIFEST and NANOFOLD_HIDDEN_FEATURES_DIR and NANOFOLD_HIDDEN_LABELS_DIR)


def _extract_submission(upload_path: Path, workspace_dir: Path) -> tuple[Path, Path]:
    extract_dir = workspace_dir / "submission_src"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(upload_path) as archive:
        archive.extractall(extract_dir)

    config_path = extract_dir / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError("uploaded zip must contain config.yaml")
    if not list(extract_dir.glob("*.py")):
        raise FileNotFoundError("uploaded zip must contain at least one .py submission file")

    LOGGER.info("submission extracted upload_path=%s workspace_dir=%s", upload_path, workspace_dir)
    return extract_dir, config_path


def _build_patched_config(extract_dir: Path, run_name: str, workspace_dir: Path, track: str) -> Path:
    raw_config = extract_dir / "config.yaml"
    with raw_config.open("r") as f:
        config = yaml.safe_load(f) or {}

    config["run_name"] = run_name
    config["track"] = track
    config.setdefault("data", {})
    config["data"]["processed_features_dir"] = str(NANOFOLD_FEATURES_DIR)
    config["data"]["processed_labels_dir"] = str(NANOFOLD_LABELS_DIR)
    config["data"]["train_manifest"] = str(NANOFOLD_REPO / "data" / "manifests" / "train.txt")
    config["data"]["val_manifest"] = str(NANOFOLD_REPO / "data" / "manifests" / "val.txt")

    patched_path = workspace_dir / "runtime_config.yaml"
    with patched_path.open("w") as f:
        yaml.dump(config, f, default_flow_style=False)

    LOGGER.info("patched config written run_name=%s track=%s path=%s", run_name, track, patched_path)
    return patched_path


def _place_submission(extract_dir: Path, run_name: str) -> Path:
    submission_dest = NANOFOLD_REPO / "submissions" / run_name
    if submission_dest.exists():
        shutil.rmtree(submission_dest)
    shutil.copytree(extract_dir, submission_dest)
    LOGGER.info("submission placed at %s", submission_dest)
    return submission_dest


def _stream_process(
    args: list[str],
    *,
    cwd: Path,
    cancel_event: Event | None,
    submission_log_path: Path | None,
    process_started: Callable[[subprocess.Popen[str]], None] | None = None,
    label: str = "process",
) -> tuple[str, int]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(NANOFOLD_REPO)
    env["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        args,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
        env=env,
    )
    if process_started is not None:
        process_started(process)

    lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        if cancel_event and cancel_event.is_set():
            LOGGER.info("%s cancellation requested pid=%s", label, process.pid)
            terminate_process_tree(process)
        stripped = line.rstrip()
        lines.append(line)
        if submission_log_path and stripped.startswith("[progress]"):
            append_submission_progress(submission_log_path, stripped.removeprefix("[progress]").strip())
        LOGGER.info("%s stream %s", label, stripped)

    returncode = process.wait()
    return "".join(lines), returncode


def _find_checkpoints(run_name: str) -> list[Path]:
    ckpt_dir = NANOFOLD_REPO / "runs" / run_name / "checkpoints"
    if not ckpt_dir.exists():
        return []
    ckpts = sorted(ckpt_dir.glob("ckpt_step_*.pt"), key=lambda p: int(p.stem.split("_")[-1]))
    last = ckpt_dir / "ckpt_last.pt"
    if last.exists() and last not in ckpts:
        ckpts.append(last)
    return ckpts


def _run_eval(
    *,
    config_path: Path,
    run_name: str,
    split: str,
    workspace_dir: Path,
    features_dir: Path | str,
    labels_dir: Path | str,
    manifest: str,
    cancel_event: Event | None,
    submission_log_path: Path | None,
) -> Path:
    ckpts = _find_checkpoints(run_name)
    if not ckpts:
        raise RuntimeError(f"no checkpoints found for run_name={run_name}")

    predict_out = workspace_dir / f"predict_summary_{split}.json"
    args = [
        str(NANOFOLD_PYTHON),
        str(NANOFOLD_REPO / "eval.py"),
        "--config", str(config_path),
        "--ckpt-list", ",".join(str(c) for c in ckpts),
        "--split", split,
        "--features-dir", str(features_dir),
        "--labels-dir", str(labels_dir),
        "--save", str(predict_out),
    ]
    if manifest:
        args += ["--manifest", manifest]
    LOGGER.info("starting eval command=%s", args)
    stdout, returncode = _stream_process(
        args,
        cwd=NANOFOLD_REPO,
        cancel_event=cancel_event,
        submission_log_path=submission_log_path,
        label=f"eval_{split}",
    )
    if returncode != 0:
        raise RuntimeError(f"eval.py failed for split={split}\nstdout:\n{stdout}")
    return predict_out


def _run_score(
    *,
    predict_summary: Path,
    features_dir: Path | str,
    labels_dir: Path | str,
    workspace_dir: Path,
    label: str,
    cancel_event: Event | None,
    submission_log_path: Path | None,
) -> dict:
    score_out = workspace_dir / f"score_{label}.json"
    args = [
        str(NANOFOLD_PYTHON),
        str(NANOFOLD_REPO / "score.py"),
        "--prediction-summary", str(predict_summary),
        "--features-dir", str(features_dir),
        "--labels-dir", str(labels_dir),
        "--save", str(score_out),
    ]
    LOGGER.info("starting score command=%s", args)
    stdout, returncode = _stream_process(
        args,
        cwd=NANOFOLD_REPO,
        cancel_event=cancel_event,
        submission_log_path=submission_log_path,
        label=f"score_{label}",
    )
    if returncode != 0:
        raise RuntimeError(f"score.py failed for {label}\nstdout:\n{stdout}")
    return json.loads(score_out.read_text())


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except Exception:
        process.terminate()


def run_uploaded_submission(
    upload_path: Path,
    *,
    track: str = "limited",
    cancel_event: Event | None = None,
    process_started: Callable[[subprocess.Popen[str]], None] | None = None,
    submission_log_path: Path | None = None,
) -> dict:
    ready, missing = evaluator_assets_ready()
    if not ready:
        raise FileNotFoundError(f"missing evaluator assets: {missing}")
    if cancel_event and cancel_event.is_set():
        raise SubmissionCancelledError("submission cancelled before benchmark start")

    started = time.perf_counter()
    run_name = upload_path.stem[:48].replace(" ", "_")
    submission_dest: Path | None = None
    combined_stdout = ""

    with tempfile.TemporaryDirectory(prefix="nanofold_eval_") as tmp_dir:
        workspace_dir = Path(tmp_dir)

        try:
            extract_dir, _ = _extract_submission(upload_path, workspace_dir)
            config_path = _build_patched_config(extract_dir, run_name, workspace_dir, track)
            submission_dest = _place_submission(extract_dir, run_name)

            if submission_log_path:
                append_submission_progress(submission_log_path, f"starting training track={track}")

            train_stdout, train_rc = _stream_process(
                [str(NANOFOLD_PYTHON), str(NANOFOLD_REPO / "train.py"), "--config", str(config_path), "--track", track, "--official"],
                cwd=NANOFOLD_REPO,
                cancel_event=cancel_event,
                submission_log_path=submission_log_path,
                process_started=process_started,
                label="train",
            )
            combined_stdout += train_stdout
            if train_rc != 0:
                return {"valid": False, "error": f"train.py failed (rc={train_rc})", "runtime_sec": time.perf_counter() - started, "stdout": combined_stdout}

            if cancel_event and cancel_event.is_set():
                raise SubmissionCancelledError("submission cancelled after training")

            if submission_log_path:
                append_submission_progress(submission_log_path, "training complete — evaluating on public val")

            predict_val = _run_eval(
                config_path=config_path,
                run_name=run_name,
                split="val",
                workspace_dir=workspace_dir,
                features_dir=NANOFOLD_FEATURES_DIR,
                labels_dir=NANOFOLD_LABELS_DIR,
                manifest="",
                cancel_event=cancel_event,
                submission_log_path=submission_log_path,
            )
            public_score = _run_score(
                predict_summary=predict_val,
                features_dir=NANOFOLD_FEATURES_DIR,
                labels_dir=NANOFOLD_LABELS_DIR,
                workspace_dir=workspace_dir,
                label="val",
                cancel_event=cancel_event,
                submission_log_path=submission_log_path,
            )

            hidden_score: dict | None = None
            if hidden_assets_available() and not (cancel_event and cancel_event.is_set()):
                if submission_log_path:
                    append_submission_progress(submission_log_path, "evaluating on hidden val")
                try:
                    predict_hidden = _run_eval(
                        config_path=config_path,
                        run_name=run_name,
                        split="hidden_val",
                        workspace_dir=workspace_dir,
                        features_dir=NANOFOLD_HIDDEN_FEATURES_DIR,
                        labels_dir=NANOFOLD_HIDDEN_LABELS_DIR,
                        manifest=NANOFOLD_HIDDEN_MANIFEST,
                        cancel_event=cancel_event,
                        submission_log_path=submission_log_path,
                    )
                    hidden_score = _run_score(
                        predict_summary=predict_hidden,
                        features_dir=NANOFOLD_HIDDEN_FEATURES_DIR,
                        labels_dir=NANOFOLD_HIDDEN_LABELS_DIR,
                        workspace_dir=workspace_dir,
                        label="hidden",
                        cancel_event=cancel_event,
                        submission_log_path=submission_log_path,
                    )
                except Exception as exc:
                    LOGGER.warning("hidden scoring failed: %s", exc)

            runtime_sec = time.perf_counter() - started
            LOGGER.info("nanofold eval finished track=%s runtime_sec=%.1f", track, runtime_sec)
            return {
                "valid": True,
                "runtime_sec": runtime_sec,
                "track": track,
                "public_score": public_score,
                "hidden_score": hidden_score,
                "stdout": combined_stdout,
            }

        finally:
            if submission_dest and submission_dest.exists():
                shutil.rmtree(submission_dest, ignore_errors=True)
            run_dir = NANOFOLD_REPO / "runs" / run_name
            if run_dir.exists():
                shutil.rmtree(run_dir, ignore_errors=True)
            LOGGER.info("cleaned up submission_dest and run_dir for run_name=%s", run_name)
