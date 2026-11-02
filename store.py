from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ["student_id", "name", "section", "subject", "date", "status"]
VALID_STATUS = {"Present", "Absent", "Late"}
BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_PATH = BASE_DIR / "data" / "attendance.csv"


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(missing)}")
    out = df[REQUIRED_COLUMNS].copy()
    out["student_id"] = out["student_id"].astype(str).str.strip()
    out["name"] = out["name"].astype(str).str.strip()
    out["section"] = out["section"].astype(str).str.strip()
    out["subject"] = out["subject"].astype(str).str.strip()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out["status"] = out["status"].astype(str).str.strip().str.title()
    out.loc[~out["status"].isin(VALID_STATUS), "status"] = "Absent"
    return out.reset_index(drop=True)


class AttendanceStore:
    def __init__(self, sample_path: Path | None = None) -> None:
        self.sample_path = sample_path or SAMPLE_PATH
        self.df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        self.reset()

    def reset(self) -> pd.DataFrame:
        self.df = normalize_dataframe(pd.read_csv(self.sample_path))
        return self.df

    def load_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        self.df = normalize_dataframe(df)
        return self.df
