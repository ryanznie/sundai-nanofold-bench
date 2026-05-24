# Running the Site on a Fresh Node

## 1. Clone the repo

```bash
git clone https://github.com/ryanznie/sundai-protein-folding-bench/
cd sundai-protein-folding-bench
```

## 2. Install uv

```bash
pip install uv
```

## 3. Install dependencies

```bash
uv sync
```

## 4. Start the server

```bash
nohup uv run uvicorn service.app:app --host 0.0.0.0 --port 8888 > /tmp/sundai.log 2>&1 &
```

Check it started:

```bash
cat /tmp/sundai.log
```

You should see `Uvicorn running on http://0.0.0.0:8888`.

## 5. Access the site

On RunPod, port 8888 is exposed as an HTTP port. Your URL is:

```
https://<your-pod-id>-8888.proxy.runpod.net
```

Find your pod ID in the RunPod dashboard — there's a clickable link next to the exposed HTTP port that goes directly to the site.
