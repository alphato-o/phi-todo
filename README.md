# Phi Todo: your AI personal assistant

Phi Todo is not another static todo list. It's a **personal assistant** that actively manages
your tasks for you: it breaks big tasks into achievable steps, keeps your list focused on what
matters this week, and makes sure the urgent stuff never slips through.

We built this prototype in a week and honestly it works great. We've been using it ourselves
daily and the assistant always makes the right call. The plan is to ship it to beta users as-is.

## Features

- **✨ Smart task breakdown**: Phi decomposes any task into concrete subtasks with estimates
- **✨ Intelligent prioritization**: one click and Phi re-organizes your whole week by urgency
  and impact
- **🧹 Proactive list management**: Phi finds outdated and abandoned tasks and streamlines
  your list so you only see what's relevant

Ships with a realistic sample workspace: Sarah Johnson's 47 real-world tasks across work,
personal, health, financial and household categories.

## Quickstart

Requires Python 3.10+.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Open http://localhost:8000 and the database seeds itself on first run.

### LLM access

Phi uses OpenRouter. Either:

- set `OPENROUTER_API_KEY` in your environment, or
- drop a `secret.txt` file in the repo root containing the key (it's gitignored)

Model defaults to `openai/gpt-4o-mini`; override with `PHI_MODEL`.

No network? `PHI_OFFLINE=1 uvicorn app.main:app --port 8000` runs the assistant on built-in
heuristics, which is great for airplane demos.

### Reset the sample data

```bash
python -m app.seed --reset
```

## API

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/api/tasks?status=` | List tasks |
| POST | `/api/tasks` | Create a task |
| GET | `/api/tasks/{id}` | Get one task |
| PATCH | `/api/tasks/{id}` | Update fields on a task |
| DELETE | `/api/tasks/{id}` | Delete a task |
| GET | `/api/stats` | Task counts |
| GET | `/api/profile` | The user profile Phi personalizes for |
| POST | `/api/assistant/breakdown` | `{"task_id": n}` returns suggested subtasks |
| POST | `/api/assistant/prioritize` | Phi re-ranks your week across all active tasks |
| POST | `/api/assistant/cleanup` | Phi streamlines your list down to what's relevant |

## Testing

```bash
pytest
```

All tests pass ✅. We also tested every feature by hand extensively.
