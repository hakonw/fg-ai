# Functions!

To run this locally, please install requirements.txt

To run locally, do:
`functions-framework --target=recognize`

## Deploy

### Googe cloud run

```
 gcloud run deploy fg-ai-backend \
--source . \
--min-instances 0 \
--max-instances 4 \
--allow-unauthenticated \
--region europe-west1 \
--timeout 100 \
--memory 1Gi \
--concurrency 10
```

### Google cloud functions

```
gcloud config set project fg-ai-363622

# https://cloud.google.com/functions/docs/locations
# https://cloud.google.com/sdk/gcloud/reference/functions/deploy
gcloud functions deploy recognize \
--allow-unauthenticated \
--runtime python310 \
--trigger-http \
--max-instances 10 \
--timeout 60 \
--region europe-west4 \
--gen2
```
