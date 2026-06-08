import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    DB_PROVIDER: str = os.getenv("DB_PROVIDER", "sqlite")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: str = os.getenv("DB_PORT", "")
    DB_NAME: str = os.getenv("DB_NAME", "entropy.db")

    @property
    def database_url(self) -> str:
        provider = self.DB_PROVIDER
        if provider == "sqlite":
            db_path = BASE_DIR / self.DB_NAME
            return f"sqlite:///{db_path}"

        driver_map = {
            "mysql": "pymysql",
            "mariadb": "pymysql",
            "postgresql": "psycopg2",
            "postgres": "psycopg2",
            "psql": "psycopg2",
        }
        driver = driver_map.get(provider)
        if driver:
            provider = f"{provider}+{driver}"
        return f"{provider}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    DATA_DIR: str = os.getenv("DATA_DIR", "data")

    CATEGORIZER_MODEL: str = os.getenv("CATEGORIZER_MODEL", "all-MiniLM-L6-v2")
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.20"))
    GAP_THRESHOLD: float = float(os.getenv("GAP_THRESHOLD", "0.03"))
    EFF_THRESHOLD: float = float(os.getenv("EFF_THRESHOLD", "0.38"))


settings = Settings()
