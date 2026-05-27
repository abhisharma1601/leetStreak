from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_base_url: str = "http://34.197.110.168:8000"
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./leetstreak.db"

    # User
    user_email: str
    user_display_name: str = "Mister Chief"

    # Gmail SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str
    smtp_app_password: str
    smtp_from_name: str = "LeetStreak"

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"


settings = Settings()
