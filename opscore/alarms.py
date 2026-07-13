"""Alarm bus + ntfy sender (SPEC-03). Three topics, unguessable (the topic string is the only
auth on ntfy.sh — kept in Actions secrets / env, never in the repo). Steady state: the alarm
topic is ~silent; the alarm budget (>5 events/week sustained 2 weeks) auto-files a gate item
('fix the root cause or mute with a recorded decision'). Outbound send is behind an interface
and INERT until the BUILD-00 ntfy topics exist. Alarms must never crash their caller."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import date, timedelta

TOPIC_ENV = {"alarm": "NTFY_ALARM", "gate": "NTFY_GATE", "pulse": "NTFY_PULSE"}


def _parse(s: str):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


class NtfySender:
    def send(self, topic, title, message, priority="default"):  # pragma: no cover - interface
        raise NotImplementedError


class NullNtfySender(NtfySender):
    """Records sends without network I/O (pre-BUILD-00 default, and for tests)."""

    def __init__(self):
        self.sent = []

    def send(self, topic, title, message, priority="default"):
        self.sent.append({"topic": topic, "title": title, "message": message, "priority": priority})


class HttpNtfySender(NtfySender):
    def send(self, topic, title, message, priority="default"):
        if not topic:
            return  # inert if the topic is unset
        req = urllib.request.Request("https://ntfy.sh/" + topic, data=(message or "").encode("utf-8"),
                                     headers={"Title": title, "Priority": priority})
        try:
            urllib.request.urlopen(req, timeout=15)
        except Exception:
            pass  # an alarm failing to send must never crash the pipeline


class AlarmBus:
    def __init__(self, sender=None, topics=None, ledger_path=None):
        self.topics = topics if topics is not None else {k: os.environ.get(v, "") for k, v in TOPIC_ENV.items()}
        self.sender = sender or (HttpNtfySender() if any(self.topics.values()) else NullNtfySender())
        self.ledger_path = ledger_path

    def _emit(self, kind, title, message, priority, today=None):
        self.sender.send(self.topics.get(kind, ""), title, message, priority)
        if self.ledger_path:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"date": (today or date.today()).isoformat(), "kind": kind, "title": title}) + "\n")

    def alarm(self, title, message="", today=None):
        self._emit("alarm", title, message, "high", today)

    def gate(self, title, message="", today=None):
        self._emit("gate", title, message, "default", today)

    def pulse(self, title, message="", today=None):
        self._emit("pulse", title, message, "low", today)

    def _alarm_events(self):
        if not self.ledger_path or not os.path.exists(self.ledger_path):
            return []
        out = []
        for line in open(self.ledger_path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind") == "alarm":
                out.append(r)
        return out

    def weekly_alarm_counts(self, today):
        """Alarm events in each of the two most recent 7-day windows ending today."""
        evs = [d for d in (_parse(r.get("date")) for r in self._alarm_events()) if d]
        wk1 = sum(1 for d in evs if today - timedelta(days=6) <= d <= today)
        wk2 = sum(1 for d in evs if today - timedelta(days=13) <= d <= today - timedelta(days=7))
        return wk1, wk2

    def budget_breach(self, today, threshold=5):
        """>threshold alarm events/week sustained across BOTH recent weeks -> gate item (SPEC-03 §4)."""
        wk1, wk2 = self.weekly_alarm_counts(today)
        return {"breached": True, "week1": wk1, "week2": wk2} if (wk1 > threshold and wk2 > threshold) else None
