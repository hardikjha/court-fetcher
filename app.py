from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from db.db import init_db, SessionLocal
from db.models import QueryRecord
from scraper.ecourts_scraper import fetch_page_with_xhr, parse_causelist_simple
import asyncio
import json
from datetime import date, timedelta
from pathlib import Path

app = Flask(__name__)
init_db()
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        case_type = request.form.get("case_type")
        case_number = request.form.get("case_number")
        year = request.form.get("year")
        # For MVP: we'll search by hitting ecourts home and capturing content as a first pass
        # (Later: map case_type -> court-specific URL)
        # Save initial query
        session = SessionLocal()
        record = QueryRecord(case_type=case_type, case_number=case_number, year=year)
        session.add(record); session.commit()
        session.refresh(record)
        session.close()
        return redirect(url_for("search_result", record_id=record.id))
    return render_template("index.html")

@app.route("/result/<int:record_id>")
def search_result(record_id):
    session = SessionLocal()
    record = session.query(QueryRecord).get(record_id)
    session.close()
    return render_template("result.html", record=record)

@app.route("/api/fetch_page", methods=["POST"])
def api_fetch_page():
    # Accept JSON { "url": "..." }
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error":"missing url"}), 400
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    html, xhrs = loop.run_until_complete(fetch_page_with_xhr(url))
    parsed = parse_causelist_simple(html)
    # save to DB
    session = SessionLocal()
    rec = QueryRecord(case_type="", case_number="", year="", raw_response=html, parsed_json=json.dumps(parsed))
    session.add(rec); session.commit()
    rid = rec.id
    session.close()
    return jsonify({"record_id": rid, "xhrs": xhrs, "parsed_preview": parsed}), 200

@app.route("/download/html/<int:record_id>")
def download_html(record_id):
    session = SessionLocal()
    rec = session.query(QueryRecord).get(record_id)
    session.close()
    if not rec or not rec.raw_response:
        return "Not found", 404
    path = OUT_DIR / f"record_{record_id}.html"
    path.write_text(rec.raw_response, encoding="utf-8")
    return send_file(str(path), as_attachment=True)

# quick search for case in DB (by partial match in parsed_json/text) for tomorrow
@app.route("/api/search_case", methods=["GET"])
def api_search_case():
    q = request.args.get("q","").strip()
    if not q:
        return jsonify({"error":"missing query"}), 400
    session = SessionLocal()
    tomorrow = (date.today() + timedelta(days=1))
    # naive: search parsed_json text
    results = []
    for rec in session.query(QueryRecord).all():
        p = rec.parsed_json or ""
        if q.lower() in p.lower():
            results.append({"id": rec.id, "case_type": rec.case_type, "case_number": rec.case_number})
    session.close()
    return jsonify({"matches": results})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
