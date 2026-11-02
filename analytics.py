from __future__ import annotations

import pandas as pd


def apply_filters(
    df: pd.DataFrame, subject: str | None = None, section: str | None = None
) -> pd.DataFrame:
    filtered = df
    if subject:
        filtered = filtered[filtered["subject"].str.lower() == subject.lower()]
    if section:
        filtered = filtered[filtered["section"].str.lower() == section.lower()]
    return filtered


def student_summaries(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "student_id",
        "name",
        "section",
        "sessions",
        "present",
        "late",
        "absent",
        "attendance_pct",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)
    grouped = df.groupby(["student_id", "name", "section"], as_index=False).agg(
        sessions=("status", "size"),
        present=("status", lambda s: int((s == "Present").sum())),
        late=("status", lambda s: int((s == "Late").sum())),
        absent=("status", lambda s: int((s == "Absent").sum())),
    )
    grouped["attendance_pct"] = (
        (grouped["present"] + grouped["late"]) / grouped["sessions"] * 100
    ).round(1)
    return grouped.sort_values("attendance_pct")


def overview(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "students": 0,
            "sessions": 0,
            "records": 0,
            "average_pct": 0,
            "present": 0,
            "late": 0,
            "absent": 0,
            "sections": [],
            "subjects": [],
            "date_range": None,
        }
    summaries = student_summaries(df)
    return {
        "students": int(summaries.shape[0]),
        "sessions": int(df["date"].nunique()),
        "records": int(len(df)),
        "average_pct": round(float(summaries["attendance_pct"].mean()), 1),
        "present": int((df["status"] == "Present").sum()),
        "late": int((df["status"] == "Late").sum()),
        "absent": int((df["status"] == "Absent").sum()),
        "sections": sorted(df["section"].unique().tolist()),
        "subjects": sorted(df["subject"].unique().tolist()),
        "date_range": {"from": str(df["date"].min()), "to": str(df["date"].max())},
    }


def below_threshold(
    df: pd.DataFrame,
    threshold: float,
    subject: str | None = None,
    section: str | None = None,
) -> list[dict]:
    rows = student_summaries(apply_filters(df, subject, section))
    return rows[rows["attendance_pct"] < threshold].to_dict(orient="records")


def table_from_summaries(rows: list[dict]) -> list[dict]:
    return [
        {
            "Name": r["name"],
            "ID": r["student_id"],
            "Section": r["section"],
            "Attendance %": r["attendance_pct"],
            "Present": r["present"],
            "Late": r["late"],
            "Absent": r["absent"],
        }
        for r in rows
    ]


def student_detail(df: pd.DataFrame, student_id: str) -> dict | None:
    person = df[df["student_id"].str.lower() == student_id.lower()]
    if person.empty:
        return None
    overall = student_summaries(person).iloc[0].to_dict()
    subject_rows = []
    for subject, part in person.groupby("subject"):
        summary = student_summaries(part).iloc[0].to_dict()
        subject_rows.append(
            {
                "subject": subject,
                "attendance_pct": summary["attendance_pct"],
                "present": int(summary["present"]),
                "late": int(summary["late"]),
                "absent": int(summary["absent"]),
                "sessions": int(summary["sessions"]),
            }
        )
    return {
        "student": {
            "student_id": overall["student_id"],
            "name": overall["name"],
            "section": overall["section"],
            "attendance_pct": overall["attendance_pct"],
            "present": int(overall["present"]),
            "late": int(overall["late"]),
            "absent": int(overall["absent"]),
            "sessions": int(overall["sessions"]),
        },
        "by_subject": sorted(subject_rows, key=lambda r: r["subject"]),
        "records": person.sort_values(["date", "subject"]).to_dict(orient="records"),
    }
