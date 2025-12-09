import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from db import Base, create_database_if_missing, engine
from fpga_listener import FpgaUdpListener
from routes_api import router as api_router
from routes_web import router as web_router

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(title="FPGA Smart NIC DDoS Dashboard", version="0.1.0")
listener = FpgaUdpListener()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(web_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup_event():
    if settings.auto_create_tables:
        create_database_if_missing()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured")
    listener.start()


@app.on_event("shutdown")
def shutdown_event():
    listener.stop()


@app.get("/health")
def health():
    return {"status": "ok"}
