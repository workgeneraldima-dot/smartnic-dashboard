import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SmartNIC DDoS Dashboard"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./data.db",
    )
    udp_host: str = os.getenv("FPGA_UDP_HOST", "0.0.0.0")
    udp_port: int = int(os.getenv("FPGA_UDP_PORT", "5005"))
    listener_enabled: bool = os.getenv("LISTENER_ENABLED", "true").lower() == "true"


settings = Settings()
