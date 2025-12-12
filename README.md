# Samfundet Face Search

A decoupled architecture for scraping, indexing, and searching faces from Samfundet's archive.

## Structure

*   `samfundet-admin`: Runs on your laptop. Used to queue images.
*   `samfundet-worker`: Runs on your Gaming PC (GPU). Used to process images.
*   `samfundet-frontend`: Deploys to Hugging Face Spaces. The public UI.

## Using with `uv`

Since you are using `uv`, you can run these projects extremely fast without managing complex virtualenvs manually.

### 1. Setup Database
Run the contents of `setup.sql` in your Supabase SQL Editor.

### 2. Admin Dashboard (Queueing)

```bash
cd admin
cp .env.example .env
# Edit .env with Supabase keys
uv run app.py
```

### 3. Worker (Processing)

```bash
cd worker
cp .env.example .env
# Edit .env with Supabase, Qdrant, and Samfundet credentials
uv run worker.py
```

### 4. Frontend (Testing Locally)

```bash
cd frontend
cp ../worker/.env .env # You can reuse the worker env for local testing
uv run app.py
```
