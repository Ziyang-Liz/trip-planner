"""Shared configuration; shell variables override backend/.env."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    pg_host: str = os.getenv("PG_HOST", "127.0.0.1")
    pg_port: int = int(os.getenv("PG_PORT", "5432"))
    pg_db: str = os.getenv("PG_DB", "trip_db")
    pg_user: str = os.getenv("PG_USER", "postgres")
    pg_password: str = os.getenv("PG_PASSWORD", "postgres")
    pg_connect_timeout: int = int(os.getenv("PG_CONNECT_TIMEOUT", "5"))
    opentripmap_api_key: str = os.getenv("OPENTRIPMAP_API_KEY", "")
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")

    def postgres_kwargs(self) -> dict:
        return {
            "host": self.pg_host,
            "port": self.pg_port,
            "dbname": self.pg_db,
            "user": self.pg_user,
            "password": self.pg_password,
            "connect_timeout": self.pg_connect_timeout,
        }


settings = Settings()
