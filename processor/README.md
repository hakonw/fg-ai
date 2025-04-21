## Install

```bash
uv venv
#activate the venv
uv pip install -r requirements.worker.txt
# OR 
uv pip install -r requirements.collector.txt

# For collector:
python -m collector.runner
# For celery
celery -A celery_app worker -l info --concurrency=1
```


## Running

Requires postgres and pgvector

`docker pull pgvector/pgvector:pg17 -p 5432:5432 -e POSTGRES_PASSWORD=password`