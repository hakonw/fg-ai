
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    ffmpeg libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Pre-download DeepFace model files
RUN mkdir -p /root/.deepface/weights/ && \
    curl -L https://github.com/serengil/deepface_models/releases/download/v1.0/facenet512_weights.h5 -o /root/.deepface/weights/facenet512_weights.h5 && \
    curl -L https://github.com/serengil/deepface_models/releases/download/v1.0/retinaface.h5 -o /root/.deepface/weights/retinaface.h5


COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]