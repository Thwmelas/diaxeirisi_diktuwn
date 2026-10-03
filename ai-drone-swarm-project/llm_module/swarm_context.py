"""
Swarm context memory.
Responsible: Member 3

Keeps the most recent messages received from the swarm so the LLM can reason
about what OTHER drones have seen, not just the current message. This is what
turns single-drone detection into collaborative awareness.
"""

import math
import time
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional, Tuple


def _parse_ts(value: Any) -> Optional[float]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def distance_m(loc_a: Any, loc_b: Any) -> Optional[float]:
    """Ground distance in metres between two [lat, lon, alt] locations."""
    try:
        lat1, lon1 = float(loc_a[0]), float(loc_a[1])
        lat2, lon2 = float(loc_b[0]), float(loc_b[1])
    except (TypeError, ValueError, IndexError):
        return None
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class SwarmContext:
    """Sliding window of recent swarm messages."""

    def __init__(self, max_messages: int = 50, max_age_s: float = 60.0):
        self.max_age_s = max_age_s
        self._items: Deque[Tuple[float, Dict[str, Any]]] = deque(maxlen=max_messages)

    def add(self, message: Dict[str, Any]) -> None:
        ts = _parse_ts(message.get("timestamp")) or time.time()
        self._items.append((ts, dict(message)))

    def recent(self, exclude_drone: Optional[str] = None, now: Optional[float] = None) -> List[Dict[str, Any]]:
        """Messages newer than max_age_s, from drones other than exclude_drone."""
        if now is None:
            now = max((ts for ts, _ in self._items), default=time.time())
        return [
            msg for ts, msg in self._items
            if now - ts <= self.max_age_s and msg.get("drone_id") != exclude_drone
        ]

    def summary(self, current: Dict[str, Any], limit: int = 8) -> str:
        """Short text summary for the prompt (most recent first)."""
        now = _parse_ts(current.get("timestamp"))
        others = self.recent(exclude_drone=current.get("drone_id"), now=now)[-limit:]
        if not others:
            return "No recent reports from other drones."

        lines = []
        for msg in reversed(others):
            line = (
                f"- {msg.get('drone_id', '?')}: {msg.get('object', 'unknown')} "
                f"at {msg.get('distance', '?')} m {msg.get('direction', '?')} "
                f"(confidence {msg.get('confidence', '?')})"
            )
            gap = distance_m(current.get("location"), msg.get("location"))
            if gap is not None:
                line += f", about {gap:.0f} m from this drone"
            lines.append(line)
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._items)
