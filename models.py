import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from db import Base


class DecisionEnum(str, enum.Enum):
    BENIGN = "BENIGN"
    SUSPICIOUS = "SUSPICIOUS"
    BLOCKED = "BLOCKED"


class BlockStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    UNBLOCKED = "UNBLOCKED"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_ip = Column(String(45), index=True)
    destination_ip = Column(String(45), index=True)
    attack_type = Column(String(50), index=True)
    decision = Column(Enum(DecisionEnum), index=True)
    packet_count = Column(Integer, default=0)
    details = Column(Text, nullable=True)


class BlockedIP(Base):
    __tablename__ = "blocked_ips"
    __table_args__ = (UniqueConstraint("ip_address", name="uq_blocked_ip_address"),)

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    attack_type = Column(String(50))
    status = Column(Enum(BlockStatusEnum), default=BlockStatusEnum.ACTIVE, index=True)
    notes = Column(Text, nullable=True)


class ConfigEntry(Base):
    __tablename__ = "config"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ConfigEntry {self.key}={self.value}>"
