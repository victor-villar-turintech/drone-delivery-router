from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://drone_user:drone_pass@localhost:5432/drone_delivery"
    database_url_sync: str = "postgresql://drone_user:drone_pass@localhost:5432/drone_delivery"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    sim_tick_seconds: float = 1.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
