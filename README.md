# Attendance Analysis Agent

Web app that answers natural language questions about student attendance and lists students below a threshold.

## Run

```bash
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## What you can ask

- Who is below 75% attendance?
- What is Priya Sharma's attendance?
- Class average in Physics
- Best attendance in section A
- Students with the most absences

Upload a CSV with columns: `student_id`, `name`, `section`, `subject`, `date`, `status` (`Present`, `Absent`, or `Late`). Late counts as attended.

## Backend API

The UI talks to `/api`:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/overview` | Class totals |
| GET | `/api/students` | Student summaries (`threshold`, `subject`, `section`) |
| GET | `/api/students/<id>` | One student, by subject |
| GET | `/api/at-risk?threshold=75` | Students below a cutoff |
| POST | `/api/ask` | `{ "question": "...", "threshold": 75 }` |
| POST | `/api/upload` | CSV file field `file` |
| POST | `/api/reset` | Reload sample data |
