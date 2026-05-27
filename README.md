# LeetStreak

A personal daily LeetCode accountability tool. Sends one email at 21:00 IST with a question, your streak stats, some guilt text, and two magic-link buttons — Done or Skip.

---

## Prerequisites

- Python 3.11+
- A Gmail account with 2FA enabled

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd leetstreak
python -m venv env
# Windows
env\Scripts\activate
# Mac / Linux
source env/bin/activate
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in every value. The critical ones:

| Variable | What to put |
|---|---|
| `USER_EMAIL` | Your Gmail address (this is where emails are sent) |
| `USER_DISPLAY_NAME` | Your name, used in email greeting |
| `SMTP_USERNAME` | The Gmail account that sends the emails (can be same as USER_EMAIL) |
| `SMTP_APP_PASSWORD` | A 16-character Gmail app password (see below) |
| `JWT_SECRET` | Any random string, at least 32 characters |
| `APP_BASE_URL` | `http://localhost:8000` for local dev |

### 4. Generate a Gmail App Password

> **Important:** Gmail App Passwords are different from your regular Gmail password. Do not put your real Gmail password in `.env` — it won't work.

1. Make sure 2-Step Verification is enabled on your Google Account:  
   https://myaccount.google.com/security

2. Go to App Passwords:  
   https://myaccount.google.com/apppasswords

3. Click **Create**, give it a name like "LeetStreak", and copy the 16-character password shown.

4. Paste it as `SMTP_APP_PASSWORD` in your `.env`.

### 5. Run database migrations

```bash
alembic upgrade head
```

This creates `leetstreak.db` with all four tables. The app seeds questions (365 total) and creates your user row on first startup.

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

On startup you'll see logs confirming questions were seeded and the scheduler started.

---

## Verifying the setup

### Send a test email immediately

```bash
curl -X POST http://localhost:8000/admin/test-email
```

Or open http://localhost:8000/admin/test-email in a browser (GET shows a form, POST sends).

Check your inbox. If it arrives, the full pipeline works.

### Manually trigger the daily job

```bash
curl -X POST http://localhost:8000/admin/trigger-daily-job
```

This runs the 21:00 job right now: picks a question, inserts a daily assignment, sends the real email with live magic links.

### Health check

```bash
curl http://localhost:8000/admin/health
```

---

## How the daily flow works

1. **21:00 IST** — scheduler sends an email with today's question.
2. You click **"I solved it"** → browser opens `/confirm/done?token=...` → shows a confirmation page.
3. You click **"Yes, mark Done"** → POST to `/respond` → streak increments, points awarded.
4. If you click **Skip** or ignore the email past **midnight IST** — streak resets to 0.

The Done/Skip links are single-use JWTs. Clicking Done twice (or Gmail pre-fetching the link) won't double-credit — GET endpoints only render a page; the actual mutation only happens on the POST form submit.

---

## Viewing the database

```bash
# Quick stats
sqlite3 leetstreak.db "SELECT email, current_streak, longest_streak, total_solved, total_points FROM app_user;"

# Today's assignment
sqlite3 leetstreak.db "SELECT da.assigned_date, q.title, q.difficulty, da.response FROM daily_assignment da JOIN question q ON q.id = da.question_id ORDER BY da.id DESC LIMIT 5;"

# All questions
sqlite3 leetstreak.db "SELECT difficulty, COUNT(*) FROM question GROUP BY difficulty;"
```

---

## Where the 21:00 schedule is configured

`app/scheduler/scheduler.py` — the two APScheduler jobs:

```python
scheduler.add_job(run_daily_email_job, trigger="cron", hour=21, minute=0, ...)
scheduler.add_job(run_streak_reset_job, trigger="cron", hour=0,  minute=0, ...)
```

Both run on `timezone="Asia/Kolkata"`. To change the time, edit those `hour`/`minute` values and restart.

---

## Running tests

```bash
pytest
pytest -v                  # verbose
pytest tests/test_streak_service.py   # single file
```

---

## Common commands (Makefile)

```bash
make run          # start the dev server
make migrate      # run alembic upgrade head
make test         # run pytest
make test-email   # POST to /admin/test-email
make trigger      # POST to /admin/trigger-daily-job
make db-stats     # show user stats from SQLite
```

---

## Project structure

```
app/
  main.py                  FastAPI app + lifespan (seed + scheduler)
  config.py                pydantic-settings, reads .env
  database.py              SQLAlchemy engine + SessionLocal
  models/                  SQLAlchemy ORM models
  services/
    question_picker.py     weighted random + topic rotation
    streak_service.py      apply_done / apply_skip mutations
    level_service.py       points → level name (pure function)
    magic_link_service.py  JWT encode/decode + consumed-token check
    email_service.py       smtplib STARTTLS send
    email_content_builder.py  builds Jinja context dict
    guilt_message_service.py  picks guilt text by streak tier
  scheduler/
    scheduler.py           APScheduler setup
    daily_email_job.py     21:00 IST job
    streak_reset_job.py    00:00 IST reset job
  routes/
    confirm.py             GET /confirm/done|skip (render only)
    respond.py             POST /respond (mutates streak/points)
    admin.py               health + test-email + trigger-daily-job
  templates/
    emails/daily.html      the one daily email (inline CSS)
    web/                   confirm, responded, already_done, all_done
seed_data/
  neetcode_150.json        365 questions (arrays → strings → ... → DP)
```
