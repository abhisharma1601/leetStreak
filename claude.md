# LeetStreak — Project Guide for Claude Code

This is the single source of truth for the LeetStreak project. Read this entire file before generating any code. Every design decision below is intentional — do not second-guess them or "improve" them without asking the user first.

---

## 1. What we're building

A personal accountability tool for solving LeetCode questions daily.

**The pain it solves:** the user keeps breaking their LeetCode streak because nothing reminds them.

**The mechanism:**
- Backend stores ~150 curated LeetCode questions (NeetCode 150).
- Every day at 21:00 IST, backend sends ONE email containing today's question + the user's streak/stats + guilt-trip copy + two magic-link buttons (Done / Skip).
- User clicks "Done" → confirmation page → POST → streak +1.
- User clicks "Skip" or ignores email until midnight IST → streak resets to 0.

That's it. No app, no web UI beyond two confirmation pages, no signup, no LeetCode API verification.

---

## 2. Scope — exactly what's in and what's out

### In scope (MVP)
- One hardcoded user (the developer themselves), `user_id = 1`.
- One scheduled job at 21:00 IST that sends the daily email.
- One streak-reset job at 00:00 IST that resets streak if no DONE response.
- Magic-link JWT tokens encoding `{user_id, assignment_id, action}`.
- Two endpoints:
  - `GET /confirm/done?token=...` — renders confirmation page with POST form.
  - `GET /confirm/skip?token=...` — renders confirmation page with POST form.
- One endpoint `POST /respond` — processes the actual done/skip action.
- SQLite database (file: `leetstreak.db`).
- Gmail SMTP via app password (free, sending to self only).
- Jinja2 templates: 1 email template + 2 web pages (confirm + result).
- Question seed: NeetCode 150 loaded from JSON on first boot.

### Explicitly OUT of scope — do not build these
- Signup / login / multi-user UI.
- User settings table (timezone, send times are all hardcoded).
- LeetCode submission verification via GraphQL.
- Multiple emails per day (evening reminder, last-chance). Only ONE email at 21:00 IST.
- Web UI for stats — stats are EMBEDDED IN THE EMAIL only.
- Bounce/complaint handling (not needed for sending to self).
- Unsubscribe link (single-user, not needed yet).
- Mobile app, Flutter, React Native, anything frontend beyond two Jinja2 pages.
- AWS SES — Gmail SMTP only for MVP.
- Domain / HTTPS / production deployment — local development only for now.
- Question lists other than NeetCode 150.
- Premium LeetCode questions.

### Future roadmap (DO NOT IMPLEMENT, just keep schema compatible)
- Multi-user with magic-link signup → that's why we have `app_user` table even though there's only one row.
- User-configurable send times and timezones.
- Multiple question lists (Blind 75, Grind 75, etc.).
- LeetCode verification.
- Deployment to EC2 + SES + custom domain.

---

## 3. The hard rules (do not change without asking)

### Streak semantics
- **DONE** before midnight IST → `current_streak += 1`, `total_solved += 1`, `total_points += base × multiplier`.
- **SKIP** at any time → `current_streak = 0`. Skip counts as a streak break.
- **No response** by midnight IST → `current_streak = 0`. Same as skip.
- `longest_streak = max(longest_streak, current_streak)` is updated whenever current_streak changes.
- Skipped questions go BACK into the pool — they may be re-assigned in the future. They are NOT marked done.
- A DONE question never reappears.

### Points and levels
```
Base points:   EASY = 1,   MEDIUM = 3,   HARD = 6
Streak multiplier (applied at solve time):
   streak >= 7   → x1.2
   streak >= 30  → x1.5
   streak >= 100 → x2.0
   else          → x1.0

Levels (computed from total_points, not stored):
    0       Script Kiddie 🐣
    50      Code Monkey 🐒
    150     Algorithm Apprentice 📚
    400     DP Disciple 🧠
    800     Graph Wizard 🧙
    1500    Big-O Sensei 🥋
```
Level is a **pure function** of total_points. Never store it in the DB. Compute on read.

### Question picker algorithm
1. Pool = questions where there is NO `daily_assignment` row for this user with `response = 'DONE'` and that question.
2. Apply difficulty weighting: 25% EASY, 60% MEDIUM, 15% HARD.
3. Within the chosen difficulty, exclude questions whose topics appear in the user's last 3 daily assignments (topic rotation). If this empties the pool, ignore topic rotation.
4. Pick uniformly at random from what remains.
5. If pool is somehow empty (user finished all 150), email them a celebration message instead and stop.

### Pre-fetch defense (critical, do not skip)
Email contains links like `https://yourhost/confirm/done?token=...`. Gmail and corporate scanners will hit these URLs on email delivery, BEFORE the user clicks.

Defense:
- `GET /confirm/done` and `GET /confirm/skip` ONLY render an HTML page with a confirmation button. They do NOT mutate state.
- The actual mutation happens on `POST /respond`, triggered when the user clicks the in-page button. Pre-fetchers don't click buttons.
- Token verification happens on both GET (to show the right page) and POST (to actually act). Single use: once a token is consumed, store its hash in a `consumed_token` table — replay returns "already responded".

### Idempotency
- `daily_assignment` has `UNIQUE(user_id, assigned_date)` — sending twice on the same day is a no-op.
- `POST /respond` checks `responded_at IS NULL` before mutating — double-clicking the button doesn't double-credit.

### Timezone handling
- All `TIMESTAMP` columns stored as UTC (SQLAlchemy default).
- "Today" for the user is always computed as the current date in `Asia/Kolkata`.
- The scheduler cron is configured with `timezone='Asia/Kolkata'`.
- JWT `exp` claim is set to "tomorrow 09:00 IST" converted to UTC epoch.

---

## 4. Tech stack (exact versions)

```
Python 3.11+
FastAPI                  0.115.x
Uvicorn                  0.32.x  (with [standard] extras)
SQLAlchemy               2.0.x   (use the 2.0 style, not legacy)
Alembic                  1.13.x  (for migrations)
APScheduler              3.10.x  (for the daily cron)
PyJWT                    2.9.x   (HS256 signing)
Jinja2                   3.1.x   (FastAPI uses it for both email and web templates)
pydantic-settings        2.x     (env var management)
python-dotenv            1.x
```

Use `smtplib` and `email.message.EmailMessage` from the standard library — no need for `fastapi-mail` or similar.

Use SQLite directly via SQLAlchemy. No async driver — keep it sync, simpler. APScheduler's `BackgroundScheduler` runs alongside FastAPI's event loop fine.

---

## 5. Project structure

```
leetstreak/
├── CLAUDE.md                       (this file)
├── README.md                       (setup instructions for the human)
├── .env.example                    (template for env vars, committed)
├── .env                            (real values, gitignored)
├── .gitignore
├── pyproject.toml                  (or requirements.txt, dev's call)
├── leetstreak.db                   (SQLite file, gitignored)
├── alembic.ini
├── migrations/
│   └── versions/                   (alembic auto-generated)
├── seed_data/
│   └── neetcode_150.json           (committed, source of truth for questions)
└── app/
    ├── __init__.py
    ├── main.py                     (FastAPI app, lifespan, includes routers)
    ├── config.py                   (pydantic-settings, loads .env)
    ├── database.py                 (SQLAlchemy engine, SessionLocal, Base)
    ├── models/
    │   ├── __init__.py
    │   ├── user.py                 (AppUser)
    │   ├── question.py             (Question)
    │   ├── assignment.py           (DailyAssignment)
    │   └── consumed_token.py       (ConsumedToken)
    ├── schemas/                    (pydantic models for request/response)
    │   ├── __init__.py
    │   └── responses.py
    ├── services/
    │   ├── __init__.py
    │   ├── question_picker.py      (weighted random + topic rotation)
    │   ├── streak_service.py       (apply done/skip, update streak/points)
    │   ├── level_service.py        (pure function: points → level)
    │   ├── magic_link_service.py   (JWT encode/decode, single-use check)
    │   ├── email_service.py        (build + send via smtplib)
    │   ├── email_content_builder.py (assembles Jinja context: stats, guilt text)
    │   └── guilt_message_service.py (picks message intensity by streak length)
    ├── scheduler/
    │   ├── __init__.py
    │   ├── scheduler.py            (APScheduler setup, registered jobs)
    │   ├── daily_email_job.py      (21:00 IST job)
    │   └── streak_reset_job.py     (00:00 IST job)
    ├── routes/
    │   ├── __init__.py
    │   ├── confirm.py              (GET /confirm/done, GET /confirm/skip)
    │   ├── respond.py              (POST /respond)
    │   └── admin.py                (POST /admin/test-email, GET /admin/health)
    ├── seed/
    │   ├── __init__.py
    │   └── seed_questions.py       (loads neetcode_150.json on first boot)
    └── templates/
        ├── emails/
        │   └── daily.html          (Jinja2: the one daily email)
        └── web/
            ├── confirm.html        (GET /confirm/done|skip lands here)
            ├── responded.html      (success: streak updated)
            ├── already_done.html   (replay protection)
            └── all_done.html       (user finished all 150 questions)
```

---

## 6. Database schema

Use Alembic for migrations. Initial migration creates all four tables.

```sql
-- app_user: one row for MVP (user_id = 1)
CREATE TABLE app_user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,
    current_streak  INTEGER NOT NULL DEFAULT 0,
    longest_streak  INTEGER NOT NULL DEFAULT 0,
    total_solved    INTEGER NOT NULL DEFAULT 0,
    total_points    INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- question: seeded from neetcode_150.json
CREATE TABLE question (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    leetcode_slug   TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    difficulty      TEXT NOT NULL,                   -- EASY | MEDIUM | HARD
    url             TEXT NOT NULL,
    topics          TEXT NOT NULL                    -- comma-separated, e.g. "array,hash-table"
);

-- daily_assignment: one row per (user, day)
CREATE TABLE daily_assignment (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES app_user(id),
    question_id     INTEGER NOT NULL REFERENCES question(id),
    assigned_date   DATE NOT NULL,                   -- date in Asia/Kolkata
    sent_at         TIMESTAMP,
    response        TEXT,                            -- NULL | DONE | SKIP
    responded_at    TIMESTAMP,
    UNIQUE(user_id, assigned_date)
);
CREATE INDEX idx_assignment_user_date ON daily_assignment(user_id, assigned_date);
CREATE INDEX idx_assignment_user_response ON daily_assignment(user_id, response);

-- consumed_token: single-use enforcement for magic links
CREATE TABLE consumed_token (
    token_hash      TEXT PRIMARY KEY,                -- SHA256 hex of the JWT
    consumed_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Notes:
- Use SQLAlchemy `DateTime(timezone=True)` for the `TIMESTAMP` columns; store UTC.
- `assigned_date` is a plain `Date` representing the date in `Asia/Kolkata`.
- A question is "done" if it has any `daily_assignment` row with `response = 'DONE'`. There is no separate `user_progress` table for the MVP.

---

## 7. Environment variables

Create `.env.example` (committed) and `.env` (gitignored).

```bash
# Application
APP_BASE_URL=http://localhost:8000          # used in magic-link URLs in emails
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./leetstreak.db

# User (single-user MVP)
USER_EMAIL=your.email@gmail.com             # who gets the daily emails
USER_DISPLAY_NAME=Mister Chief

# Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com          # the Gmail account sending emails
SMTP_APP_PASSWORD=xxxxxxxxxxxxxxxx          # 16-char Gmail app password
SMTP_FROM_NAME=LeetStreak

# JWT
JWT_SECRET=change-me-to-a-long-random-string-at-least-32-chars
JWT_ALGORITHM=HS256

# Scheduling (hardcoded in code for MVP but referenced here for clarity)
# Daily email: 21:00 Asia/Kolkata
# Streak reset: 00:00 Asia/Kolkata
```

Load these via `pydantic-settings` in `app/config.py`. Never read `os.environ` directly anywhere else.

---

## 8. The daily flow (concrete sequence)

### 21:00 IST — `daily_email_job`
```
1. Open DB session.
2. Get user (id=1). If no user, abort with log warning ("seed user first").
3. Compute today_ist = current date in Asia/Kolkata.
4. Check if a daily_assignment already exists for (user.id, today_ist).
   - If yes → log "already sent today" and return.
5. Call question_picker_service.pick_next(user) → returns Question or None.
   - If None → render and send "all done" celebration email, return.
6. Insert daily_assignment row with sent_at=NULL, response=NULL.
7. Commit so we have assignment.id.
8. Generate two JWTs:
   - DONE: payload {sub: user.id, aid: assignment.id, act: "DONE",
                    exp: tomorrow 09:00 IST as UTC epoch}
   - SKIP: same with act="SKIP"
9. Build email context via email_content_builder:
   - user (streak, points, level info)
   - question (title, difficulty, url, topics)
   - done_url = f"{APP_BASE_URL}/confirm/done?token={done_jwt}"
   - skip_url = f"{APP_BASE_URL}/confirm/skip?token={skip_jwt}"
   - guilt_text = guilt_message_service.pick(current_streak)
   - progress_text = f"{total_solved}/{total_questions} done"
   - level_progress = (current_points, next_level_threshold, next_level_name)
10. Render templates/emails/daily.html with that context.
11. Send via smtplib.
12. Update daily_assignment.sent_at = now(UTC).
13. Commit. Done.
```

### 00:00 IST — `streak_reset_job`
```
1. Open DB session.
2. Compute yesterday_ist = (now in IST - 1 day).date()
3. Find daily_assignment for (user_id=1, assigned_date=yesterday_ist).
4. If found AND response IS NULL:
     - user.current_streak = 0
     - commit
     - log "streak reset due to no response"
   (No action if response was DONE — streak already incremented at response time.)
   (No action if response was SKIP — streak already reset at skip time.)
```

### User clicks "Done" link in email → `GET /confirm/done?token=...`
```
1. Decode JWT (verify signature, exp, act=="DONE").
   - On failure → render web/responded.html with error="invalid or expired link".
2. Check consumed_token table for sha256(token).
   - If found → render web/already_done.html.
3. Load assignment by aid. Check responded_at IS NULL.
   - If already responded → render web/already_done.html.
4. Render web/confirm.html:
     - shows question title
     - shows current streak
     - POST form with hidden token field, action="/respond", method="POST"
     - button: "Yes, mark Done"
```

### User clicks the "Yes" button → `POST /respond`
```
Body: form-encoded { token: "...", action: "DONE" | "SKIP" }
   (the action in the body must match the JWT's act claim — if not, 400)

1. Re-verify JWT (signature, exp, act matches body action).
2. Re-check consumed_token. If found → render already_done.html.
3. Load assignment. Check responded_at IS NULL. If not → already_done.html.
4. In a transaction:
     a. assignment.response = action
     b. assignment.responded_at = now(UTC)
     c. If action == DONE:
          user.total_solved += 1
          multiplier = streak_multiplier(user.current_streak + 1)
          base = base_points(question.difficulty)
          user.total_points += round(base * multiplier)
          user.current_streak += 1
          user.longest_streak = max(user.longest_streak, user.current_streak)
        If action == SKIP:
          user.current_streak = 0
     d. Insert consumed_token (sha256(token), now())
     e. Commit
5. Render web/responded.html with success state:
     - "🔥 Streak: {current_streak} days" (or "💔 Streak broken" for skip)
     - new level if changed
     - progress
```

The `GET /confirm/skip` and SKIP variant of `/respond` follow the same pattern.

---

## 9. Magic link token spec

JWT, HS256, `JWT_SECRET` from env.

Payload:
```json
{
  "sub": 1,              // user_id
  "aid": 42,             // daily_assignment.id
  "act": "DONE",         // or "SKIP"
  "iat": 1735689600,     // issued at, UTC epoch seconds
  "exp": 1735776000      // expires at: tomorrow 09:00 IST as UTC epoch
}
```

`magic_link_service.py`:
- `generate(user_id, assignment_id, action) -> str` — encodes the JWT.
- `verify(token: str) -> dict` — decodes, raises on bad signature / expired / malformed.
- `mark_consumed(token: str, db_session)` — inserts sha256(token) into `consumed_token`.
- `is_consumed(token: str, db_session) -> bool` — checks the table.

Use `hashlib.sha256(token.encode()).hexdigest()` for the storage key. Never store the raw token.

---

## 10. Email template — what it must contain

`templates/emails/daily.html` is the ONLY user-facing surface besides two confirmation pages. It must include:

1. Greeting with display name.
2. Question block:
   - Title (large, bold)
   - Difficulty badge (color-coded: green/orange/red)
   - Topics (small, light)
   - Big "Open in LeetCode" link to the question URL
3. Stats block:
   - 🔥 Current streak: N days
   - 🏆 Longest streak: N days
   - 📊 Solved: X / 150
   - 🎖 Level: {level_name}
   - 📈 Points: {points} (needs {delta} more for {next_level_name})
4. Guilt text paragraph (from guilt_message_service, varies by streak length).
5. Two big buttons: ✅ "I solved it" and ⏭ "Skip today"
   - These are styled `<a>` tags, not real buttons (broader email-client compatibility).
   - Link to `done_url` and `skip_url` respectively.
6. Footer: small text noting the deadline ("Streak dies at midnight IST. Tokens expire at 9 AM tomorrow.").

Use inline CSS only. Email clients strip `<style>` blocks. Test rendering in Gmail's iOS app.

---

## 11. Guilt message logic

`guilt_message_service.pick(current_streak)` picks one message at random from a tier based on streak length. Tone escalates with stakes.

Tiers:
- **streak == 0** → encouraging start: "Fresh start today. Just one question stands between you and a new streak."
- **1 <= streak <= 6** → light nudge: "Day {n}. Don't kill the momentum."
- **7 <= streak <= 29** → real stakes: "You're {n} days in. The first {n} days were the hardest — coast on the discipline you've already built."
- **30 <= streak <= 99** → serious: "{n} days. That's not a streak anymore, that's a habit. Don't let one lazy evening reset it."
- **streak >= 100** → existential: "{n} days. You'd really watch it all burn over a single problem?"

Have 2–3 variations per tier so emails don't feel repetitive. Store as a dict-of-lists in the module.

---

## 12. Question seed data

Source: NeetCode 150. There are public GitHub repos with this as JSON. Recommended format for `seed_data/neetcode_150.json`:

```json
[
  {
    "leetcode_slug": "two-sum",
    "title": "Two Sum",
    "difficulty": "EASY",
    "url": "https://leetcode.com/problems/two-sum/",
    "topics": "array,hash-table"
  },
  ...
]
```

`app/seed/seed_questions.py`:
- On app startup, check if `question` table is empty.
- If empty, load the JSON and bulk-insert.
- Also check if `app_user` table is empty — if so, insert the single user using `USER_EMAIL` from settings.

Run both seeders inside FastAPI's `lifespan` startup event.

If you can't find a clean NeetCode 150 JSON online, scaffold with a small list of ~10 questions for now and leave a TODO in the README for the human to populate the rest.

---

## 13. Build order — implement in this sequence

Each step should be runnable and testable before moving to the next. Do not jump ahead.

### Step 1: Project skeleton
- `pyproject.toml` with deps pinned.
- `.env.example`, `.gitignore`.
- `app/config.py` with `Settings` class.
- `app/main.py` with a FastAPI app + a `GET /health` endpoint that returns `{"status": "ok"}`.
- `uvicorn app.main:app --reload` should work.

### Step 2: Database + models
- `app/database.py` with engine, SessionLocal, Base, `get_db` dependency.
- All 4 SQLAlchemy models in `app/models/`.
- Alembic init + first migration.
- `alembic upgrade head` should create `leetstreak.db` with all tables.

### Step 3: Seeders
- Put a small NeetCode JSON in `seed_data/` (10 questions is fine to start).
- `seed_questions.py` runs on startup, idempotent.
- Verify on first run: questions row count == JSON length, one app_user row exists.

### Step 4: Pure logic services (no DB writes)
- `level_service.py` — `level_for_points(points) -> (name, next_threshold, next_name)`. Add unit tests.
- `guilt_message_service.py` — `pick(streak) -> str`. Add unit tests.
- `magic_link_service.py` — generate/verify only (no DB yet). Add unit tests.

### Step 5: Question picker
- `question_picker.py` — `pick_next(user, db) -> Question | None`.
- Logic: build pool, apply difficulty weighting, apply topic rotation, random pick.
- Add unit tests using a temp SQLite DB with seeded data.

### Step 6: Email infrastructure
- `email_content_builder.py` — assembles a dict for Jinja.
- `templates/emails/daily.html` — designed but with placeholder values for now.
- `email_service.py` — sends an email via smtplib. Hardcode a test recipient initially.
- Add `POST /admin/test-email` endpoint that sends a sample email. Use it to verify Gmail setup works before continuing.

### Step 7: Daily email job
- `daily_email_job.py` ties everything together: pick question → insert assignment → generate JWTs → render template → send → update sent_at.
- `app/scheduler/scheduler.py` registers the job with APScheduler at cron `0 21 * * *` timezone `Asia/Kolkata`.
- Start scheduler in FastAPI lifespan.
- Test by temporarily changing cron to "every minute" and verifying email arrives.

### Step 8: Confirm + respond endpoints
- `routes/confirm.py` — GET handlers render `web/confirm.html`.
- `routes/respond.py` — POST handler applies the streak/points changes.
- `streak_service.py` encapsulates the mutation logic.
- Web templates: `confirm.html`, `responded.html`, `already_done.html`, `all_done.html`.
- End-to-end test: trigger daily job manually → check inbox → click button → confirm → see streak update in DB.

### Step 9: Streak reset job
- `streak_reset_job.py` cron `0 0 * * *` timezone `Asia/Kolkata`.
- Verify by setting up a test scenario: insert yesterday's assignment with response=NULL, run job manually, check current_streak == 0.

### Step 10: Polish + README
- Write `README.md` with: Gmail app password setup, .env setup, alembic commands, how to manually trigger a test email, how to view DB.
- Add a `Makefile` or `justfile` with common commands.

---

## 14. Gotchas — read carefully

1. **Gmail app password ≠ Gmail password.** User must enable 2FA on Google account, then generate a 16-char app password at https://myaccount.google.com/apppasswords. Document this in README.

2. **Gmail SMTP "Less secure apps" is gone.** Only app passwords work in 2026. Do not suggest enabling less-secure-app access — that option no longer exists.

3. **APScheduler in a FastAPI app:** start it in the `lifespan` async context manager. Use `BackgroundScheduler`, not `AsyncIOScheduler`, unless you want to convert all DB calls to async. Sync is simpler for this app.

4. **Don't use FastAPI `BackgroundTasks` for the daily cron.** Those are per-request. Use APScheduler.

5. **Pre-fetch defense is not optional.** If you make GET `/confirm/done` mutate state, Gmail will auto-complete every question the moment the email arrives. Render-only on GET, mutate only on POST.

6. **SQLite write concurrency:** the daily job + a user response can race in theory. SQLite handles this fine for one user, but use `with engine.begin()` blocks or `Session.commit()` explicitly. Don't rely on autocommit.

7. **Timezone math:** never use `datetime.now()` without a timezone. Always `datetime.now(ZoneInfo("Asia/Kolkata"))` or `datetime.now(timezone.utc)`. Store UTC in DB, convert at boundaries.

8. **JWT exp claim:** must be a UTC epoch integer, not an ISO string. PyJWT will reject otherwise.

9. **Idempotency:** the daily job MUST be safe to run twice on the same day. The UNIQUE constraint on (user_id, assigned_date) is your safety net — catch the IntegrityError and log a warning, don't crash.

10. **Email HTML quirks:** Gmail strips `<style>` blocks. Use inline `style=""` on every element. Don't use modern CSS (flexbox is fine, grid is risky). Use tables for layout if you want bulletproof rendering.

11. **Topic rotation edge case:** if the user has done every topic in the last 3 days, topic rotation will empty the pool. Handle this by falling back to "ignore rotation" rather than returning None.

12. **All-questions-done state:** when the user solves all 150, `question_picker.pick_next` returns None. The daily job should send a celebration email and stop. Future feature: loop back through SKIPped/old questions for review mode. Out of scope for MVP.

---

## 15. Testing approach

Pytest. No need for full coverage, but at minimum:
- `level_service`: 10 cases covering each level boundary.
- `magic_link_service`: encode → decode roundtrip, expired token rejection, tampered signature rejection.
- `guilt_message_service`: each tier returns a non-empty string.
- `question_picker`: pool excludes DONE questions, picks from correct difficulty distribution over 1000 trials (statistical test, allow ±10% tolerance).
- `streak_service.apply_done`: streak increments, points calculated correctly with multipliers, longest_streak updates.
- `streak_service.apply_skip`: streak resets to 0.

For integration tests, use a fixture that creates an in-memory SQLite, seeds 10 questions, and runs the full job.

---

## 16. Questions to ask the user before implementing

When uncertain, ask the user. Don't guess on:
- Specific guilt-message wording — propose 3 per tier, let user pick favorites.
- Exact email HTML styling — show a screenshot or HTML preview, ask for tweaks.
- Whether to start scheduler in test/dev environments (default: yes, but cron can be overridden via env var for testing).

---

## 17. Definition of done for the MVP

The user (Mister Chief) can:
1. `git clone`, set up `.env`, run `alembic upgrade head`, `uvicorn app.main:app`.
2. Hit `POST /admin/test-email` and immediately receive a sample email in their Gmail.
3. Let it run. At 21:00 IST, automatically receive an email with today's question.
4. Click "Done" → see a confirmation page → click Yes → see "Streak: 1 day".
5. Next day at 21:00 IST, receive a new question with updated streak shown.
6. If they ignore an email past midnight IST, the next day's email shows "Streak: 0 — Fresh start".

When all six work, ship.