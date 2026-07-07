install:
    pip install -r requirements.txt
    cd ui && npm install

run:
    start cmd /k "uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
    start cmd /k "cd ui && npm run dev"

reindex:
    python tools/synth_data.py
    python -c "from core.ingestor import ingest_all; ingest_all()"
    python -c "from core.embedder import embed_all; embed_all()"

eval:
    python tools/evaluate.py
