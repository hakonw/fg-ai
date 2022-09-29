from animcogn/face_recognition:cpu-nightly
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8080

# ENTRYPOINT ["python"]
# CMD ["main.py"]
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app