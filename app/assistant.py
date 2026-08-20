import os
from datetime import datetime

from . import db, llm

OFFLINE = lambda: bool(os.environ.get("PHI_OFFLINE"))


def _task_line(t):
    age = (datetime.now() - datetime.fromisoformat(t["created_at"])).days
    return {
        "id": t["id"],
        "title": t["title"],
        "notes": t["notes"],
        "category": t["category"],
        "priority": t["priority"],
        "status": t["status"],
        "days_old": age,
        "due_date": t["due_date"],
    }


def breakdown(task_id):
    task = db.get_task(task_id)
    if not task:
        return None
    if OFFLINE():
        subtasks = [
            {"title": f"Clarify scope for: {task['title']}", "estimate": "15m"},
            {"title": "Gather what you need to start", "estimate": "20m"},
            {"title": "Do the first concrete step", "estimate": "30m"},
            {"title": "Review and wrap up", "estimate": "15m"},
        ]
        return {"task_id": task_id, "subtasks": subtasks}
    profile = db.profile()
    out = llm.chat_json(
        "You are Phi, a personal productivity assistant. Respond ONLY with JSON:"
        ' {"subtasks": [{"title": str, "estimate": str}]}. 3-5 subtasks.',
        f"User profile: {profile}\nBreak this task into subtasks: {_task_line(task)}",
    )
    return {"task_id": task_id, "subtasks": out["subtasks"]}


def prioritize():
    tasks = db.list_tasks(status="active", limit=30)
    lines = [_task_line(t) for t in tasks]
    if OFFLINE():
        def score(t):
            overdue = t["due_date"] is not None and t["due_date"] <= datetime.now().date().isoformat()
            pr = {"high": 0, "medium": 1, "low": 2}[t["priority"]]
            return (0 if overdue else 1, pr, t["due_date"] or "9999")
        ranked = sorted(lines, key=score)
        ranking = [
            {"id": t["id"], "priority": "high" if i < 8 else ("medium" if i < 20 else "low"),
             "reason": "offline heuristic: due date + priority"}
            for i, t in enumerate(ranked)
        ]
    else:
        profile = db.profile()
        out = llm.chat_json(
            "You are Phi, a personal productivity assistant. The user wants their week organized."
            " Here are ALL of the user's active tasks. Re-rank them so the most urgent and impactful"
            " come first. Respond ONLY with JSON:"
            ' {"ranking": [{"id": int, "priority": "high"|"medium"|"low", "reason": str}]}.'
            " Include every task.",
            f"User profile: {profile}\nActive tasks: {lines}",
        )
        ranking = out["ranking"]
    for item in ranking:
        db.update_task(item["id"], {"priority": item["priority"]})
    return {"applied": len(ranking), "ranking": ranking}


def cleanup():
    tasks = db.list_tasks(limit=100)
    lines = [_task_line(t) for t in tasks]
    if OFFLINE():
        to_delete = [
            {"id": t["id"], "reason": "offline heuristic: stale"}
            for t in lines
            if (t["status"] == "completed" and t["days_old"] > 30)
            or (t["status"] == "active" and t["days_old"] > 90)
        ]
    else:
        profile = db.profile()
        out = llm.chat_json(
            "You are Phi, a personal productivity assistant. The user wants a streamlined, relevant"
            " task list. Identify tasks that are outdated, abandoned, or no longer relevant so they"
            " can be removed. Respond ONLY with JSON:"
            ' {"delete": [{"id": int, "reason": str}]}.',
            f"User profile: {profile}\nTasks: {lines}",
        )
        to_delete = out["delete"]
    deleted = []
    for item in to_delete:
        if db.delete_task(item["id"]):
            deleted.append(item)
    return {"deleted": deleted, "message": f"Cleaned up {len(deleted)} tasks. Your list is now streamlined!"}
