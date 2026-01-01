# fg-ai Backend

## Run

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
--max-instances 4 \
--region europe-west1 \
--allow-unauthenticated \
--memory 4Gi \
--concurrency 10 \
--env-vars-file .env
```