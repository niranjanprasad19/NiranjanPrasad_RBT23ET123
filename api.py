from __future__ import annotations

import pandas as pd
from flask import Blueprint, current_app, jsonify, request

from .agent import answer_question
from .analytics import (
    apply_filters,
    below_threshold,
    overview,
    student_detail,
    student_summaries,
    table_from_summaries,
)
from .store import AttendanceStore

api_bp = Blueprint("api", __name__)


def store() -> AttendanceStore:
    return current_app.config["ATTENDANCE_STORE"]


@api_bp.get("/overview")
def api_overview():
    return jsonify(overview(store().df))


@api_bp.get("/students")
def api_students():
    threshold = request.args.get("threshold", type=float)
    subject = request.args.get("subject") or None
    section = request.args.get("section") or None
    rows = student_summaries(apply_filters(store().df, subject, section))
    if threshold is not None:
        rows = rows[rows["attendance_pct"] < threshold]
    return jsonify(table_from_summaries(rows.to_dict(orient="records")))


@api_bp.get("/students/<student_id>")
def api_student(student_id: str):
    detail = student_detail(store().df, student_id)
    if detail is None:
        return jsonify({"error": f"Student {student_id} was not found."}), 404
    return jsonify(detail)


@api_bp.get("/at-risk")
def api_at_risk():
    threshold = request.args.get("threshold", default=75.0, type=float)
    subject = request.args.get("subject") or None
    section = request.args.get("section") or None
    rows = below_threshold(store().df, threshold, subject, section)
    return jsonify(
        {
            "threshold": threshold,
            "count": len(rows),
            "students": table_from_summaries(rows),
        }
    )


@api_bp.post("/ask")
def api_ask():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", ""))
    threshold = float(payload.get("threshold", 75))
    return jsonify(answer_question(store(), question, threshold))


@api_bp.post("/upload")
def api_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "Choose a CSV file to upload."}), 400
    try:
        store().load_frame(pd.read_csv(file))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True, "overview": overview(store().df)})


@api_bp.post("/reset")
def api_reset():
    store().reset()
    return jsonify({"ok": True, "overview": overview(store().df)})
