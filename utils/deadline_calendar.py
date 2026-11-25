"""Turn extracted deadlines into real dates and an .ics calendar file."""
from datetime import date, datetime, timedelta, timezone
from typing import Optional


def schedule(deadlines: list[dict], start: date, end: Optional[date] = None, today: Optional[date] = None) -> list[dict]:
    """Add `due_date` (ISO string or None) and `status` to each deadline."""
    today = today or date.today()
    rows = []
    for d in deadlines:
        days, anchor = d.get("days"), (d.get("anchor") or "event").lower()
        due = None
        if isinstance(days, (int, float)):
            if anchor == "start":
                due = start + timedelta(days=int(days))
            elif anchor == "end" and end:
                due = end - timedelta(days=int(days))
        if due is None:
            status = "Event-based" if anchor == "event" else "Needs end date"
        elif due < today:
            status = "Passed"
        elif (due - today).days <= 30:
            status = "Due within 30 days"
        else:
            status = "Upcoming"
        rows.append({**d, "due_date": due.isoformat() if due else None, "status": status})
    rows.sort(key=lambda r: (r["due_date"] is None, r["due_date"] or ""))
    return rows


def _esc(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def build_ics(rows: list[dict], contract: str = "Contract") -> str:
    """An iCalendar file (opens in Google Calendar, Outlook, Apple Calendar) with a
    reminder 3 days before each dated deadline."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Tata AI Legal//Deadlines//EN", "CALSCALE:GREGORIAN"]
    for i, r in enumerate(x for x in rows if x.get("due_date")):
        day = r["due_date"].replace("-", "")
        nxt = (date.fromisoformat(r["due_date"]) + timedelta(days=1)).strftime("%Y%m%d")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{day}-{i}@tata-ai-legal",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{day}",
            f"DTEND;VALUE=DATE:{nxt}",
            f"SUMMARY:{_esc(contract)}: {_esc(r.get('term', 'Deadline'))}",
            f"DESCRIPTION:{_esc(r.get('description', ''))} [{_esc(r.get('source', ''))}]",
            "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Contract deadline", "TRIGGER:-P3D", "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
