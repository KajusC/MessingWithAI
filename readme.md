# Start

`uv` is optional, but faster than just pip.
Python 3.12 is required.

```bash
uv venv
uv pip install -r requirements.txt
```

## pgvector database

```
docker stop PostgreSQL
docker rm PostgreSQL
docker run -d --name PostgreSQL -e POSTGRES_PASSWORD=supperPassword -e POSTGRES_USER=postgres -p 5432:5432 -v "<PathToImagesSoItIsntDeleted>db_data:/var/lib/postgresql/data" pgvector/pgvector:pg14
```

## fast api (not needed now)

```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
