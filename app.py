# app.py
import os
from flask import Flask, request, render_template, jsonify
import psycopg2
import psycopg2.extras

from indexer import ensure_schema, build_index

app = Flask(__name__)

# Environment variables:
# - DATABASE_URL: provided by Render Postgres (we'll wire this in render.yaml)
# - ADMIN_TOKEN: set in Render env to protect the /admin/reindex endpoint
DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. Ensure your Render Postgres is linked.")
    return psycopg2.connect(DATABASE_URL)

# Ensure schema exists when the app starts
with app.app_context():
    try:
        ensure_schema()
    except Exception as e:
        # Don't crash the app on cold start; show in logs instead.
        print(f"[boot] ensure_schema error: {e}")

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/search")
def search():
    q = request.args.get("q", "").strip()
    rows = []
    if q:
        sql = """
          SELECT id, name, address, phone, source_url, page
          FROM records
          WHERE fts @@ plainto_tsquery('english', %(q)s)
          ORDER BY ts_rank(fts, plainto_tsquery('english', %(q)s)) DESC
          LIMIT 50;
        """
        try:
            with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, {"q": q})
                rows = cur.fetchall()
        except Exception as e:
            # Render a minimal error for visibility; you can improve this later.
            return render_template("results.html", q=q, rows=[], error=str(e)), 500
    return render_template("results.html", q=q, rows=rows)

@app.post("/admin/reindex")
def reindex():
    if not ADMIN_TOKEN or request.headers.get("X-Admin-Token") != ADMIN_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    try:
        build_index()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Optional: health check for Render (not strictly required)
@app.get("/_health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    # For local testing only. On Render we use gunicorn via start command.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
