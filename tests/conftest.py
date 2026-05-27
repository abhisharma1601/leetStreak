import os

# Set required env vars before any app.* import triggers pydantic-settings
os.environ.setdefault("USER_EMAIL", "test@example.com")
os.environ.setdefault("SMTP_USERNAME", "test@example.com")
os.environ.setdefault("SMTP_APP_PASSWORD", "testapppassword1234")
os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-chars-long!!")
