# indexer.py
import os
import time
import requests
import psycopg2
from psycopg2.extras import execute_values
from parser import records_from_pdf_bytes

REQUEST_HEADERS = {"User-Agent": "BT-Phonebook-Lookup/1.0 (+https://github.com/your/repo)"}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS records (
  id SERIAL PRIMARY KEY,
  name TEXT,
  address TEXT,
  phone TEXT,
  source_url TEXT NOT NULL,
  page INT,
  raw_text TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uniq_record_idx
  ON records (phone, md5(coalesce(name,'') || '|' || coalesce(address,'') || '|' || coalesce(source_url,'')));

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uniq_record'
  ) THEN
    ALTER TABLE records
      ADD CONSTRAINT uniq_record UNIQUE USING INDEX uniq_record_idx;
  END IF;
END$$;

ALTER TABLE records
  ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(name,'') || ' ' ||
      coalesce(address,'') || ' ' ||
      coalesce(phone,'') || ' ' ||
      coalesce(raw_text,''))
  ) STORED;

CREATE INDEX IF NOT EXISTS records_fts_idx ON records USING GIN (fts);
"""

def get_conn():
    """
    Connect to Postgres using DATABASE_URL (Render will provide this env var).
    """
    db_url = os.environ["DATABASE_URL"]
    return psycopg2.connect(db_url)

def ensure_schema():
    """
    Create the schema & indexes if they don't exist yet.
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        conn.commit()

def load_pdf_urls_from_file(path="pdf_urls.txt"):
    """
    Read a newline-delimited list of .pdf URLs.
    Ignores blank lines and lines starting with '#'.
    Returns a sorted, de-duplicated list of URLs.
    """
    # If a custom file path is provided via env, use that.
    src = os.environ.get("PDF_URLS_SOURCE", f"file:{path}")
    text = ""

    # Allow remote lists via raw GitHub URLs (optional)
    if src.startswith("http://") or src.startswith("https://"):
        r = requests.get(src, headers=REQUEST_HEADERS, timeout=20)
        r.raise_for_status()
        text = r.text
    else:
        # Expect format file:<path> or just a relative file path
        file_path = src[5:] if src.startswith("file:") else src
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Could not find URL list at {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    urls = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().endswith(".pdf"):
            urls.append(line)

    return sorted(set(urls))

def fetch_pdf(url, timeout=60) -> bytes:
    """
    Download a PDF into memory (bytes). No filesystem writes.
    """
    with requests.get(url, headers=REQUEST_HEADERS, timeout=timeout, stream=True) as r:
        r.raise_for_status()
        return r.content

def upsert_records(conn, rows, source_url):
    """
    Insert records; ignore duplicates based on the uniq_record constraint.
    """
    if not rows:
        return 0
    values = []
    for r in rows:
        values.append((
            (r.get("name") or None),
            (r.get("address") or None),
            (r.get("phone") or None),
            source_url,
            r.get("page") or None,           # we don't detect pages with PyPDF2; stays NULL
            r.get("raw_text") or "",
        ))
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO records (name, address, phone, source_url, page, raw_text)
            VALUES %s
            ON CONFLICT ON CONSTRAINT uniq_record DO NOTHING
        """, values)
    conn.commit()
    return len(values)

def build_index():
    """
    Main index builder:
      1) ensure schema
      2) load URL list
      3) stream each PDF, parse in memory, upsert into Postgres
    """
    ensure_schema()

    pdf_urls = load_pdf_urls_from_file("pdf_urls.txt")
    print(f"Indexing {len(pdf_urls)} PDFs from list")

    total_inserted = 0
    with get_conn() as conn:
        for i, url in enumerate(pdf_urls, 1):
            print(f"[{i}/{len(pdf_urls)}] Fetching {url}")
            try:
                pdf_bytes = fetch_pdf(url)
                rows = records_from_pdf_bytes(pdf_bytes)
                added = upsert_records(conn, rows, url)
                total_inserted += added
                print(f"  -> Parsed {len(rows)} rows, inserted {added}")
                time.sleep(0.25)  # politeness delay to avoid hammering the host
            except Exception as e:
                print(f"  !! Error indexing {url}: {e}")

