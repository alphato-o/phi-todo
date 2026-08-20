from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import assistant, db

app = FastAPI(title="Phi Todo", version="0.1.0")

STATIC = Path(__file__).resolve().parent.parent / "static"


@app.on_event("startup")
def startup():
    db.init()


class TaskIn(BaseModel):
    title: str
    notes: str = ""
    category: str = "personal"
    priority: str = "medium"
    due_date: Optional[str] = None


class TaskPatch(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None


class BreakdownIn(BaseModel):
    task_id: int


def serialize(t):
    t = dict(t)
    t["overdue"] = bool(
        t["status"] == "active" and t["due_date"] and t["due_date"] <= date.today().isoformat()
    )
    return t


@app.get("/api/tasks")
def list_tasks(status: Optional[str] = None):
    return [serialize(t) for t in db.list_tasks(status)]


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(404, "task not found")
    return serialize(task)


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskIn):
    return serialize(db.create_task(task.dict()))


@app.patch("/api/tasks/{task_id}")
def patch_task(task_id: int, patch: TaskPatch):
    fields = {k: v for k, v in patch.dict().items() if v is not None}
    db.update_task(task_id, fields)
    return {"ok": True}


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if not db.delete_task(task_id):
        raise HTTPException(404, "task not found")


@app.get("/api/stats")
def stats():
    return db.stats()


@app.get("/api/profile")
def profile():
    return db.profile()


@app.post("/api/assistant/breakdown")
def assistant_breakdown(body: BreakdownIn):
    result = assistant.breakdown(body.task_id)
    if result is None:
        raise HTTPException(404, "task not found")
    return result


@app.post("/api/assistant/prioritize")
def assistant_prioritize():
    return assistant.prioritize()


@app.post("/api/assistant/cleanup")
def assistant_cleanup():
    return assistant.cleanup()


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
