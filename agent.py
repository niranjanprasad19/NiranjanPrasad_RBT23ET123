from __future__ import annotations

import re

from .analytics import (
    apply_filters,
    below_threshold,
    overview,
    student_summaries,
    table_from_summaries,
)
from .store import AttendanceStore

SUBJECT_MAP = {
    "math": "Mathematics",
    "mathematics": "Mathematics",
    "physics": "Physics",
    "english": "English",
    "computer science": "Computer Science",
    "cs": "Computer Science",
}


def extract_threshold(text: str) -> float | None:
    match = re.search(
        r"(?:below|under|less than|underperforming|<)\s*(\d{1,3})\s*%?", text, re.I
    )
    if match:
        return float(match.group(1))
    match = re.search(r"(\d{1,3})\s*%", text)
    if match and re.search(r"below|under|threshold|defaulter|at risk|less", text, re.I):
        return float(match.group(1))
    return None


def extract_section(text: str) -> str | None:
    match = re.search(r"section\s*([a-z0-9])", text, re.I)
    if match:
        return match.group(1).upper()
    return None


def extract_subject(text: str) -> str | None:
    lower = text.lower()
    for key in sorted(SUBJECT_MAP, key=len, reverse=True):
        if re.search(rf"\b{re.escape(key)}\b", lower):
            return SUBJECT_MAP[key]
    return None


def find_student(df, text: str) -> tuple[str, str] | None:
    names = df[["student_id", "name"]].drop_duplicates()
    lower = text.lower()
    for _, row in names.iterrows():
        name = str(row["name"])
        sid = str(row["student_id"])
        if name.lower() in lower or sid.lower() in lower:
            return sid, name
        first = name.split()[0].lower()
        if re.search(rf"\b{re.escape(first)}\b", lower):
            return sid, name
    return None


def answer_question(
    store: AttendanceStore, question: str, threshold_default: float = 75.0
) -> dict:
    df = store.df
    text = question.strip()
    if not text:
        return {"text": "Ask a question about attendance.", "table": [], "intent": "empty"}
    if df.empty:
        return {
            "text": "No attendance data is loaded. Upload a CSV with student_id, name, section, subject, date, and status.",
            "table": [],
            "intent": "no_data",
        }

    lower = text.lower()
    subject = extract_subject(text)
    section = extract_section(text)
    filtered = apply_filters(df, subject, section)
    summaries = student_summaries(filtered)
    scope = []
    if subject:
        scope.append(subject)
    if section:
        scope.append(f"section {section}")
    scope_label = f" for {' / '.join(scope)}" if scope else ""

    if re.search(r"help|what can you|how do i", lower):
        return {
            "text": (
                "I can answer attendance questions in plain English. Try:\n"
                "• Who is below 75% attendance?\n"
                "• What is Priya Sharma's attendance?\n"
                "• Class average in Physics\n"
                "• Students with the most absences\n"
                "• Best attendance in section A"
            ),
            "table": [],
            "intent": "help",
        }

    threshold = extract_threshold(text)
    if threshold is not None or re.search(
        r"defaulter|at[- ]risk|short attendance|below threshold", lower
    ):
        cut = threshold if threshold is not None else threshold_default
        rows = below_threshold(df, cut, subject, section)
        if not rows:
            return {
                "text": f"No students are below {cut:.0f}% attendance{scope_label}.",
                "table": [],
                "intent": "below_threshold",
                "threshold": cut,
            }
        return {
            "text": f"{len(rows)} student(s) are below {cut:.0f}% attendance{scope_label}.",
            "table": table_from_summaries(rows),
            "intent": "below_threshold",
            "threshold": cut,
        }

    student = find_student(df, text)
    if student and re.search(
        r"attendance|absent|present|late|how is|how's|status", lower
    ):
        sid, name = student
        row = summaries[summaries["student_id"] == sid]
        if row.empty:
            person = df[df["student_id"] == sid]
            row = student_summaries(apply_filters(person, subject, section))
        if row.empty:
            return {
                "text": f"No matching records for {name}{scope_label}.",
                "table": [],
                "intent": "student",
            }
        rec = row.iloc[0].to_dict()
        return {
            "text": (
                f"{name} ({sid}) in section {rec['section']} has {rec['attendance_pct']}% attendance"
                f"{scope_label}: {int(rec['present'])} present, {int(rec['late'])} late, {int(rec['absent'])} absent "
                f"across {int(rec['sessions'])} sessions."
            ),
            "table": table_from_summaries([rec]),
            "intent": "student",
        }

    if re.search(r"average|overall|class attendance|summary|overview", lower):
        stats = overview(filtered)
        return {
            "text": (
                f"Class attendance{scope_label} averages {stats['average_pct']}% across "
                f"{stats['students']} students and {stats['records']} records "
                f"({stats['present']} present, {stats['late']} late, {stats['absent']} absent)."
            ),
            "table": table_from_summaries(
                summaries.sort_values("name").to_dict(orient="records")
            ),
            "intent": "average",
        }

    if re.search(r"best|highest|top|perfect", lower):
        ranked = summaries.sort_values(
            ["attendance_pct", "name"], ascending=[False, True]
        )
        if re.search(r"perfect", lower):
            ranked = ranked[ranked["attendance_pct"] >= 100]
            if ranked.empty:
                return {
                    "text": f"No students have perfect attendance{scope_label}.",
                    "table": [],
                    "intent": "best",
                }
            return {
                "text": f"{len(ranked)} student(s) have perfect attendance{scope_label}.",
                "table": table_from_summaries(ranked.to_dict(orient="records")),
                "intent": "best",
            }
        return {
            "text": f"Highest attendance{scope_label}:",
            "table": table_from_summaries(ranked.head(5).to_dict(orient="records")),
            "intent": "best",
        }

    if re.search(r"worst|lowest|least attendance|poor", lower):
        bottom = summaries.sort_values(["attendance_pct", "name"]).head(5)
        return {
            "text": f"Lowest attendance{scope_label}:",
            "table": table_from_summaries(bottom.to_dict(orient="records")),
            "intent": "worst",
        }

    if re.search(r"most absen|absent most|most missed", lower):
        ranked = summaries.sort_values(
            ["absent", "name"], ascending=[False, True]
        ).head(5)
        return {
            "text": f"Students with the most absences{scope_label}:",
            "table": table_from_summaries(ranked.to_dict(orient="records")),
            "intent": "absences",
        }

    if re.search(r"late", lower):
        ranked = summaries[summaries["late"] > 0].sort_values(
            ["late", "name"], ascending=[False, True]
        )
        if ranked.empty:
            return {
                "text": f"No late marks found{scope_label}.",
                "table": [],
                "intent": "late",
            }
        return {
            "text": f"Students marked late{scope_label}:",
            "table": table_from_summaries(ranked.to_dict(orient="records")),
            "intent": "late",
        }

    if re.search(r"list|all students|roster|who is in", lower):
        ranked = summaries.sort_values("name")
        return {
            "text": f"{len(ranked)} students{scope_label}:",
            "table": table_from_summaries(ranked.to_dict(orient="records")),
            "intent": "list",
        }

    if student:
        sid, name = student
        rec = summaries[summaries["student_id"] == sid]
        if rec.empty:
            return {
                "text": f"I found {name}, but there are no records{scope_label}.",
                "table": [],
                "intent": "student",
            }
        row = rec.iloc[0].to_dict()
        return {
            "text": f"{name} has {row['attendance_pct']}% attendance{scope_label}.",
            "table": table_from_summaries([row]),
            "intent": "student",
        }

    return {
        "text": (
            "I could not match that question. Try asking who is below a percentage, "
            "a student's attendance, class average, or the best/worst records."
        ),
        "table": [],
        "intent": "unknown",
    }
