# Functions!

TODO requirements.txt

To run locally, do:
`functions-framework --target recognize --debug`

- Required files
  - all images with all face encodings
  - mapping from image to metadata

## Deploy

### Googe cloud run

```
 gcloud run deploy fg-ai-backend \
--source . \
--min-instances 0 \
--max-instances 3 \
--allow-unauthenticated \
--region europe-west1 \
--timeout 20
```

### Via functions (but dlib isnt possiblt to install)

```
gcloud config set project fg-ai-363622

# https://cloud.google.com/functions/docs/locations
# https://cloud.google.com/sdk/gcloud/reference/functions/deploy
gcloud functions deploy recognize \
--allow-unauthenticated \
--runtime python310 \
--trigger-http \
--max-instances 10 \
--timeout 15 \
--region europe-west4 \
--gen2
```
