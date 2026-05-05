# fg-ai Backend

## Run

This backend currently supports Python 3.11 to 3.13. Python 3.14 is not supported yet because `onnxruntime` 1.23.2 does not publish `cp314` wheels.

```bash
uv run python main.py
```

## Environment

Set these environment variables (for example in a `.env` file):

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `QDRANT_URL`
- `QDRANT_KEY`
- `QDRANT_COLLECTION` (optional, default: `samfundet_faces`)

```bash

gcloud run deploy fg-ai-backend-2 \
--source . \
--min-instances 0 \
--max-instances 1 \
--region europe-west1 \
--allow-unauthenticated \
--memory 2Gi \
--concurrency 10 \
--env-vars-file .env
```
