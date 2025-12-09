import json
import logging
import socket
import threading
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import BlockStatus, BlockedIP, Decision, Event

logger = logging.getLogger(__name__)


class FPGAListener:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        logger.info("FPGA listener thread started on %s:%s", self.host, self.port)

    def stop(self):
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=1)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))
        sock.settimeout(1.0)

        while not self._stop_event.is_set():
            try:
                data, _ = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except Exception as exc:  # pragma: no cover - defensive path
                logger.exception("Listener error: %s", exc)
                continue

            if not data:
                continue

            line = data.decode().strip()
            try:
                event = self.parse_event_line(line)
            except Exception:
                logger.warning("Invalid event line: %s", line)
                continue

            if event:
                self.save_event(event)

    def parse_event_line(self, line: str):
        # Accept JSON or CSV (6 fields)
        if line.startswith("{"):
            payload = json.loads(line)
            timestamp_str = payload.get("timestamp")
            timestamp = (
                datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if timestamp_str
                else datetime.utcnow()
            )
            return {
                "timestamp": timestamp,
                "source_ip": payload.get("source_ip", ""),
                "destination_ip": payload.get("destination_ip", ""),
                "attack_type": payload.get("attack_type", "UNKNOWN"),
                "decision": payload.get("decision", "BENIGN"),
                "packet_count": int(payload.get("packet_count", 0)),
                "details": payload.get("details"),
            }

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            raise ValueError("Invalid CSV event line")

        timestamp = datetime.fromisoformat(parts[0].replace("Z", "+00:00"))
        return {
            "timestamp": timestamp,
            "source_ip": parts[1],
            "destination_ip": parts[2],
            "attack_type": parts[3],
            "decision": parts[4],
            "packet_count": int(parts[5]),
            "details": None,
        }

    def save_event(self, event_data: dict):
        session: Session = SessionLocal()
        try:
            decision = Decision(event_data.get("decision", "BENIGN"))
            event = Event(
                timestamp=event_data.get("timestamp", datetime.utcnow()),
                source_ip=event_data.get("source_ip", ""),
                destination_ip=event_data.get("destination_ip", ""),
                attack_type=event_data.get("attack_type", "UNKNOWN"),
                decision=decision,
                packet_count=event_data.get("packet_count", 0),
                details=event_data.get("details"),
            )
            session.add(event)
            session.flush()

            if decision == Decision.BLOCKED:
                self._upsert_blocked_ip(session, event)

            session.commit()
        except Exception:  # pragma: no cover - logging path
            session.rollback()
            logger.exception("Failed to persist event")
        finally:
            session.close()

    def _upsert_blocked_ip(self, session: Session, event: Event):
        blocked = session.query(BlockedIP).filter_by(ip_address=event.source_ip).first()
        now = datetime.utcnow()
        if blocked:
            blocked.last_seen = now
            blocked.attack_type = event.attack_type
            blocked.status = BlockStatus.ACTIVE
        else:
            blocked = BlockedIP(
                ip_address=event.source_ip,
                first_seen=event.timestamp or now,
                last_seen=event.timestamp or now,
                attack_type=event.attack_type,
                status=BlockStatus.ACTIVE,
            )
            session.add(blocked)
        session.flush()
