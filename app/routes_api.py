from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BlockStatus, BlockedIP, ConfigEntry, Decision, Event
from app.schemas import BlockedIPRead, ConfigEntryRead, ConfigUpdate, EventRead, UnblockRequest

router = APIRouter(prefix="/api")


@router.get("/events", response_model=List[EventRead])
def get_events(limit: int = 100, db: Session = Depends(get_db)):
    events = (
        db.query(Event)
        .order_by(Event.timestamp.desc())
        .limit(min(limit, 500))
        .all()
    )
    return list(reversed(events))


@router.get("/events/stats")
def get_event_stats(minutes: int = 60, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(minutes=minutes)
    attacks_by_type = (
        db.query(Event.attack_type, func.count(Event.id))
        .filter(Event.timestamp >= since)
        .group_by(Event.attack_type)
        .all()
    )

    decision_counts = (
        db.query(Event.decision, func.count(Event.id))
        .filter(Event.timestamp >= since)
        .group_by(Event.decision)
        .all()
    )

    blocked_total = db.query(BlockedIP).filter(BlockedIP.status == BlockStatus.ACTIVE).count()

    return {
        "attacks_by_type": {name: count for name, count in attacks_by_type},
        "decision_counts": {decision.value: count for decision, count in decision_counts},
        "blocked_total": blocked_total,
    }


@router.get("/blocked_ips", response_model=List[BlockedIPRead])
def get_blocked_ips(db: Session = Depends(get_db)):
    return (
        db.query(BlockedIP)
        .filter(BlockedIP.status == BlockStatus.ACTIVE)
        .order_by(BlockedIP.last_seen.desc())
        .all()
    )


@router.post("/blocked_ips/unblock")
def unblock_ip(request: UnblockRequest, db: Session = Depends(get_db)):
    blocked = db.query(BlockedIP).filter_by(ip_address=request.ip).first()
    if not blocked:
        raise HTTPException(status_code=404, detail="IP not found")

    blocked.status = BlockStatus.UNBLOCKED
    blocked.last_seen = datetime.utcnow()
    db.commit()
    return {"status": "unblocked", "ip": request.ip}


@router.get("/config", response_model=List[ConfigEntryRead])
def get_config(db: Session = Depends(get_db)):
    configs = db.query(ConfigEntry).all()
    return configs


@router.post("/config")
def update_config(payload: ConfigUpdate, db: Session = Depends(get_db)):
    updates = {
        "syn_threshold": payload.syn_threshold,
        "udp_threshold": payload.udp_threshold,
        "ml_enabled": str(payload.ml_enabled) if payload.ml_enabled is not None else None,
    }
    changed = []
    for key, value in updates.items():
        if value is None:
            continue
        entry = db.query(ConfigEntry).filter_by(key=key).first()
        if not entry:
            entry = ConfigEntry(key=key, value=str(value))
            db.add(entry)
        else:
            entry.value = str(value)
        changed.append(key)
    db.commit()
    return {"updated": changed}
