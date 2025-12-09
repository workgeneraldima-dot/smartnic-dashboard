from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
import enum

from app.db import Base


class Decision(str, enum.Enum):
    BENIGN = "BENIGN"
    SUSPICIOUS = "SUSPICIOUS"
    BLOCKED = "BLOCKED"


class BlockStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    UNBLOCKED = "UNBLOCKED"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_ip = Column(String(45), index=True, nullable=False)
    destination_ip = Column(String(45), nullable=False)
    attack_type = Column(String(50), nullable=False)
    decision = Column(Enum(Decision), nullable=False)
    packet_count = Column(Integer, default=0)
    details = Column(Text, nullable=True)


class BlockedIP(Base):
    __tablename__ = "blocked_ips"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, index=True, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    attack_type = Column(String(50), nullable=True)
    status = Column(Enum(BlockStatus), default=BlockStatus.ACTIVE, nullable=False)
    notes = Column(Text, nullable=True)


class ConfigEntry(Base):
    __tablename__ = "config"

    key = Column(String(50), primary_key=True)
    value = Column(String(255))
