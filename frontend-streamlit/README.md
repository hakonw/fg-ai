# Frontend

## Setup
Using `UV`

```bash
uv init
source .venv/Scripts/activate
uv pip install --requirements requirements.txt

streamlit run app.py

```

## Deploy
Dockerfile  

Docker compose

### GCP cloud run
```bash
gcloud init
gcloud config set project fg-ai-363622

gcloud run deploy fg-ai-frontend-streamlit \
--source . \
--min-instances 0 \
--max-instances 4 \
--allow-unauthenticated \
--region europe-west1 \
--timeout 100 \
--memory 1Gi \
--concurrency 10 \
--env-vars-file=env.yaml
```
