from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from models import DecisionEnum, BlockStatusEnum


class EventBase(BaseModel):
    timestamp: datetime
    source_ip: str
    destination_ip: str
    attack_type: str
    decision: DecisionEnum
    packet_count: int
    details: Optional[str] = None


class EventRead(EventBase):
    id: int

    class Config:
        orm_mode = True


class EventStats(BaseModel):
    total_events: int = 0
    attacks_today: int = 0
    blocked_count: int = 0
    attacks_by_type: dict = Field(default_factory=dict)
    attacks_over_time: List[dict] = Field(default_factory=list)


class BlockedIPBase(BaseModel):
    ip_address: str
    attack_type: str
    first_seen: datetime
    last_seen: datetime
    status: BlockStatusEnum
    notes: Optional[str] = None


class BlockedIPRead(BlockedIPBase):
    id: int

    class Config:
        orm_mode = True


class UnblockRequest(BaseModel):
    ip: str


class ConfigEntryRead(BaseModel):
    key: str
    value: str
    description: Optional[str]

    class Config:
        orm_mode = True


class ConfigUpdate(BaseModel):
    syn_threshold: Optional[int]
    udp_threshold: Optional[int]
    enable_ml: Optional[bool]
