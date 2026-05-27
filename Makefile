.PHONY: run migrate test test-email trigger db-stats lint

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

migrate:
	alembic upgrade head

test:
	pytest -v

test-email:
	curl -s -X POST http://localhost:8000/admin/test-email | python -m json.tool

trigger:
	curl -s -X POST http://localhost:8000/admin/trigger-daily-job | python -m json.tool

db-stats:
	sqlite3 leetstreak.db "SELECT email, current_streak, longest_streak, total_solved, total_points FROM app_user;"
	sqlite3 leetstreak.db "SELECT difficulty, COUNT(*) FROM question GROUP BY difficulty;"
	sqlite3 leetstreak.db "SELECT da.assigned_date, q.title, q.difficulty, da.response, da.responded_at FROM daily_assignment da JOIN question q ON q.id = da.question_id ORDER BY da.id DESC LIMIT 10;"
