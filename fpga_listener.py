import json
import logging
import socket
import threading
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.exc import SQLAlchemyError

from config import settings
from db import SessionLocal
from models import BlockStatusEnum, BlockedIP, DecisionEnum, Event

logger = logging.getLogger(__name__)


class FpgaUdpListener:
    """Simple UDP listener that parses FPGA alerts and stores them in the database."""

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        self.host = host or settings.udp_host
        self.port = port or settings.udp_port
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.info("FPGA listener already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="fpga-udp-listener", daemon=True)
        self._thread.start()
        logger.info("Started FPGA UDP listener on %s:%s", self.host, self.port)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
            logger.info("Stopped FPGA UDP listener")

    def _run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((self.host, self.port))
            sock.settimeout(1.0)
            while not self._stop_event.is_set():
                try:
                    data, _ = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                except OSError as exc:
                    logger.error("Socket error: %s", exc)
                    continue

                line = data.decode().strip()
                if not line:
                    continue
                try:
                    payload = parse_event_line(line)
                except ValueError as exc:
                    logger.warning("Invalid FPGA payload '%s': %s", line, exc)
                    continue

                try:
                    self._persist_event(payload)
                except SQLAlchemyError as exc:
                    logger.exception("Database error while storing FPGA event: %s", exc)

    def _persist_event(self, payload: Dict[str, str | int]) -> None:
        session = SessionLocal()
        try:
            event = Event(
                timestamp=payload["timestamp"],
                source_ip=payload["source_ip"],
                destination_ip=payload["destination_ip"],
                attack_type=payload["attack_type"],
                decision=DecisionEnum(payload["decision"]),
                packet_count=int(payload.get("packet_count", 0)),
                details=payload.get("details"),
            )
            session.add(event)
            if payload["decision"] == DecisionEnum.BLOCKED.value:
                blocked = (
                    session.query(BlockedIP)
                    .filter(BlockedIP.ip_address == payload["source_ip"])
                    .one_or_none()
                )
                now = datetime.utcnow()
                if blocked:
                    blocked.last_seen = now
                    blocked.attack_type = payload["attack_type"]
                    blocked.status = BlockStatusEnum.ACTIVE
                else:
                    blocked = BlockedIP(
                        ip_address=payload["source_ip"],
                        attack_type=payload["attack_type"],
                        first_seen=now,
                        last_seen=now,
                        status=BlockStatusEnum.ACTIVE,
                    )
                    session.add(blocked)
            session.commit()
        finally:
            session.close()


def parse_event_line(line: str) -> Dict[str, str | int | datetime]:
    """Parse CSV or JSON line from FPGA into a payload dict."""
    try:
        if line.startswith("{"):
            data = json.loads(line)
            timestamp_str = data.get("timestamp")
            packet_count = int(data.get("packet_count") or data.get("count") or 0)
            return {
                "timestamp": datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")),
                "source_ip": data["source_ip"],
                "destination_ip": data["destination_ip"],
                "attack_type": data["attack_type"],
                "decision": data["decision"],
                "packet_count": packet_count,
                "details": data.get("details"),
            }
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 6:
            raise ValueError("CSV payload must have at least 6 fields")
        timestamp_str, source_ip, destination_ip, attack_type, decision, packet_count = parts[:6]
        return {
            "timestamp": datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")),
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "attack_type": attack_type,
            "decision": decision,
            "packet_count": int(packet_count),
        }
    except (ValueError, json.JSONDecodeError, KeyError) as exc:
        raise ValueError(str(exc)) from exc
