# Docker

## Docker Compose (recommended)

Build and start:

```bash
docker compose up -d
```

Stop:

```bash
docker compose down
```

Data is stored in a named Docker volume (`claims-data`). To remove it along with the container:

```bash
docker compose down -v
```

---

## Manual docker commands

### Build

```bash
docker build -t claims-tracker .
```

### Run

```bash
docker run -d \
  --name claims-tracker \
  -p 8080:8080 \
  -v /your/host/data:/app/data \
  claims-tracker
```

Replace `/your/host/data` with the absolute path on the host where the SQLite database and attachments should be persisted.

### Stop / remove

```bash
docker stop claims-tracker
docker rm claims-tracker
```

---

The app will be available at http://localhost:8080.

## Development mode

To enable hot-reload and auto-open the browser (local dev only, not inside a container):

```bash
CLAIMS_DEV=1 python main.py
```
