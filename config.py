import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    database_url: str = Field(
        default=os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://smartnic:smartnic@localhost:3306/smartnic_dashboard",
        )
    )
    udp_host: str = Field(default=os.getenv("UDP_HOST", "0.0.0.0"))
    udp_port: int = Field(default=int(os.getenv("UDP_PORT", 5005)))
    api_prefix: str = Field(default="/api")
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    auto_create_tables: bool = Field(default=bool(int(os.getenv("AUTO_CREATE_TABLES", 1))))


settings = Settings()
