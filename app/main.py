import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import routes_api, routes_web
from app.config import settings
from app.db import Base, engine
from app.fpga_listener import FPGAListener

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.include_router(routes_api.router)
app.include_router(routes_web.router)
app.mount("/static", StaticFiles(directory="static"), name="static")

listener = FPGAListener(settings.udp_host, settings.udp_port)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    if settings.listener_enabled:
        try:
            listener.start()
        except OSError as exc:  # pragma: no cover - environment specific
            logger.error("Could not start listener: %s", exc)


@app.on_event("shutdown")
def on_shutdown():
    listener.stop()
