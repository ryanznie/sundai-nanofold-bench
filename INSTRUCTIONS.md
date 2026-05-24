# Running the Site on a Fresh Node

## 1. Clone the repo

```bash
git clone https://github.com/ryanznie/sundai-nanofold-bench/
cd sundai-nanofold-bench
```

## 2. Prepare nanoFold data

Clone and prepare the official nanoFold competition repo:

```text
https://github.com/ChrisHayduk/nanoFold-Competition/tree/main
```

Downloading and preprocessing can take hours. Reuse an existing prepared local checkout when possible.

## 3. Install uv

```bash
pip install uv
```

## 4. Install dependencies

```bash
uv sync
```

## 5. Start the server

```bash
export NANOFOLD_REPO=/path/to/nanoFold-Competition
nohup uv run uvicorn service.app:app --host 0.0.0.0 --port 8888 > /tmp/sundai.log 2>&1 &
```

Check it started:

```bash
cat /tmp/sundai.log
```

You should see `Uvicorn running on http://0.0.0.0:8888`.

## 6. Access the site

On RunPod, port 8888 is exposed as an HTTP port. Your URL is:

```text
https://<your-pod-id>-8888.proxy.runpod.net
```

Find your pod ID in the RunPod dashboard. The exposed HTTP port usually has a direct clickable link.
