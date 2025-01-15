# AI of FGs pictures

Find yourself among the pictures taken at Studentersamfundet i Trondheim!

Live:
[https://hakonw.github.io/fg-ai/](https://hakonw.github.io/fg-ai/)

## Why

I wanted the funcitonality

## Run locally

For the frontend, in `frontend-svelte`, run `npm run dev`

For the packend, in functions, run `python main.py`

To use the local backend, in `frontend-sevelte/src/main.ts` switch out the server to `http://localhost:8080`

NOTE  functions_framework --target recognize


The backend needs 2 files files that are not commited. One is a pre-calculated cache for every face in the picture, and one is a metadata-cache to find information of the image.

Sadly, the metadata-cache is curreny `O(p*m)` (TODO combine both caches).

## Deploy

Frontend is deployed at github pages with `npm run deploy`

Backend is deployed with the command specified in the backend readme

## License

Ping me if one is required

## The code

Its a mess. Please don't judge me too hasty
