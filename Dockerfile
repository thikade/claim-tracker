FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY claim_tracker/ ./claim_tracker/
COPY main.py .

ARG GIT_COMMIT=dev
ENV GIT_COMMIT=$GIT_COMMIT

ARG BUILD_DATE=
ENV BUILD_DATE=$BUILD_DATE

VOLUME ["/app/data"]

EXPOSE 8080

CMD ["python", "main.py"]
