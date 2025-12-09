from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models import Decision, BlockStatus


class EventCreate(BaseModel):
    timestamp: Optional[datetime]
    source_ip: str
    destination_ip: str
    attack_type: str
    decision: Decision
    packet_count: int = 0
    details: Optional[str] = None


class EventRead(EventCreate):
    id: int

    class Config:
        orm_mode = True


class BlockedIPRead(BaseModel):
    id: int
    ip_address: str
    first_seen: datetime
    last_seen: datetime
    attack_type: Optional[str]
    status: BlockStatus
    notes: Optional[str]

    class Config:
        orm_mode = True


class ConfigEntryRead(BaseModel):
    key: str
    value: str

    class Config:
        orm_mode = True


class ConfigUpdate(BaseModel):
    syn_threshold: Optional[int] = Field(None, alias="syn_threshold")
    udp_threshold: Optional[int] = Field(None, alias="udp_threshold")
    ml_enabled: Optional[bool] = Field(None, alias="ml_enabled")

    class Config:
        allow_population_by_field_name = True


class UnblockRequest(BaseModel):
    ip: str
