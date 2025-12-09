from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from db import SessionLocal
from models import BlockStatusEnum, BlockedIP, ConfigEntry, DecisionEnum, Event
from schemas import (
    BlockedIPRead,
    ConfigEntryRead,
    ConfigUpdate,
    EventRead,
    EventStats,
    UnblockRequest,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/events", response_model=List[EventRead])
def list_events(limit: int = 100, db: Session = Depends(get_db)):
    events = (
        db.query(Event)
        .order_by(Event.timestamp.desc())
        .limit(min(limit, 500))
        .all()
    )
    return events


@router.get("/events/stats", response_model=EventStats)
def events_stats(minutes: int = 60, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    since = now - timedelta(minutes=minutes)
    last_day = now - timedelta(hours=24)

    total_events = db.query(Event).filter(Event.timestamp >= last_day).count()
    attacks_today = (
        db.query(Event)
        .filter(Event.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
        .filter(Event.decision != DecisionEnum.BENIGN)
        .count()
    )
    blocked_count = db.query(BlockedIP).filter(BlockedIP.status == BlockStatusEnum.ACTIVE).count()

    attacks_by_type = dict(
        db.query(Event.attack_type, func.count(Event.id))
        .filter(Event.timestamp >= since)
        .group_by(Event.attack_type)
        .all()
    )

    buckets = (
        db.query(
            func.date_format(Event.timestamp, "%Y-%m-%d %H:%i:00").label("bucket"),
            func.count(Event.id),
        )
        .filter(Event.timestamp >= since)
        .filter(Event.decision != DecisionEnum.BENIGN)
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )

    attacks_over_time = [
        {"timestamp": bucket + "Z", "count": count}
        for bucket, count in buckets
    ]

    return EventStats(
        total_events=total_events,
        attacks_today=attacks_today,
        blocked_count=blocked_count,
        attacks_by_type=attacks_by_type,
        attacks_over_time=attacks_over_time,
    )


@router.get("/blocked_ips", response_model=List[BlockedIPRead])
def list_blocked_ips(db: Session = Depends(get_db)):
    return (
        db.query(BlockedIP)
        .filter(BlockedIP.status == BlockStatusEnum.ACTIVE)
        .order_by(BlockedIP.last_seen.desc())
        .all()
    )


@router.post("/blocked_ips/unblock")
def unblock_ip(request: UnblockRequest, db: Session = Depends(get_db)):
    blocked = (
        db.query(BlockedIP)
        .filter(BlockedIP.ip_address == request.ip)
        .filter(BlockedIP.status == BlockStatusEnum.ACTIVE)
        .one_or_none()
    )
    if not blocked:
        raise HTTPException(status_code=404, detail="IP not found or already unblocked")
    blocked.status = BlockStatusEnum.UNBLOCKED
    blocked.last_seen = datetime.utcnow()
    db.commit()
    return {"status": "ok", "ip": request.ip}


@router.get("/config", response_model=List[ConfigEntryRead])
def get_config(db: Session = Depends(get_db)):
    return db.query(ConfigEntry).order_by(ConfigEntry.key).all()


@router.post("/config")
def update_config(update: ConfigUpdate, db: Session = Depends(get_db)):
    updates = update.dict(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No configuration changes provided")

    for key, value in updates.items():
        entry = db.query(ConfigEntry).filter(ConfigEntry.key == key).one_or_none()
        if entry:
            entry.value = str(value)
        else:
            entry = ConfigEntry(key=key, value=str(value))
            db.add(entry)
    db.commit()
    return {"status": "ok", "updated": list(updates.keys())}
