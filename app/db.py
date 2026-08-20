import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "phi.db"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sarah_johnson.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    notes TEXT DEFAULT '',
    category TEXT DEFAULT 'personal',
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    due_date TEXT,
    completed_at TEXT
);
"""


def connect():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    conn = connect()
    conn.executescript(SCHEMA)
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        seed(conn)
    conn.commit()
    conn.close()


def seed(conn=None, reset=False):
    own = conn is None
    if own:
        conn = connect()
        conn.executescript(SCHEMA)
    if reset:
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")
    fixture = json.loads(FIXTURE.read_text())
    now = datetime.now()
    for i, t in enumerate(fixture["tasks"]):
        created = now - timedelta(days=t["days_ago"], hours=(i * 37) % 22, minutes=(i * 13) % 60)
        due = None
        if t.get("due_in_days") is not None:
            due = (now + timedelta(days=t["due_in_days"])).date().isoformat()
        completed = None
        if t.get("completed_days_ago") is not None:
            completed = (now - timedelta(days=t["completed_days_ago"])).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO tasks (title, notes, category, priority, status, created_at, updated_at, due_date, completed_at)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (t["title"], t.get("notes", ""), t["category"], t["priority"], t["status"],
             created.isoformat(timespec="seconds"), created.isoformat(timespec="seconds"), due, completed),
        )
    conn.commit()
    if own:
        conn.close()


def profile():
    return json.loads(FIXTURE.read_text())["profile"]


def list_tasks(status=None, limit=25, oldest_first=False):
    conn = connect()
    order = "ASC" if oldest_first else "DESC"
    if status:
        rows = conn.execute(
            f"SELECT * FROM tasks WHERE status=? ORDER BY created_at {order} LIMIT ?", (status, limit)
        ).fetchall()
    else:
        rows = conn.execute(f"SELECT * FROM tasks ORDER BY created_at {order} LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_task(task_id):
    conn = connect()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_task(fields):
    now = datetime.now().isoformat(timespec="seconds")
    conn = connect()
    cur = conn.execute(
        "INSERT INTO tasks (title, notes, category, priority, status, created_at, updated_at, due_date)"
        " VALUES (?,?,?,?,'active',?,?,?)",
        (fields["title"], fields.get("notes", ""), fields.get("category", "personal"),
         fields.get("priority", "medium"), now, now, fields.get("due_date")),
    )
    conn.commit()
    task = dict(conn.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone())
    conn.close()
    return task


def update_task(task_id, fields):
    if not fields:
        return
    fields = dict(fields)
    fields["updated_at"] = datetime.now().isoformat(timespec="seconds")
    if fields.get("status") == "completed":
        fields["completed_at"] = datetime.now().isoformat(timespec="seconds")
    cols = ", ".join(f"{k}=?" for k in fields)
    conn = connect()
    conn.execute(f"UPDATE tasks SET {cols} WHERE id=?", (*fields.values(), task_id))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = connect()
    cur = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def stats():
    conn = connect()
    row = conn.execute(
        "SELECT COUNT(*) AS total,"
        " SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) AS active,"
        " SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed"
        " FROM tasks"
    ).fetchone()
    conn.close()
    return dict(row)
