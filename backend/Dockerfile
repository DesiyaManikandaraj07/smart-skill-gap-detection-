FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "psycopg2-binary==2.9.10" \
    && python -m spacy download en_core_web_sm || true

COPY . .

# Train heavy proxy model at image build (offline-capable demo)
RUN python ml/build_proxy_labels.py && python ml/train.py

ENV SSG_USE_SENTENCE_TRANSFORMERS=false
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
