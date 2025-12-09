import logging

import pymysql
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

logger = logging.getLogger(__name__)


def create_database_if_missing():
    """Create the configured MySQL database if it does not already exist."""

    url = make_url(settings.database_url)
    if not url.drivername.startswith("mysql"):
        logger.debug("Database auto-creation is only implemented for MySQL URLs")
        return

    db_name = url.database
    conn = pymysql.connect(
        host=url.host,
        user=url.username,
        password=url.password,
        port=url.port or 3306,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            logger.info("Ensured MySQL database '%s' exists", db_name)
    finally:
        conn.close()


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
