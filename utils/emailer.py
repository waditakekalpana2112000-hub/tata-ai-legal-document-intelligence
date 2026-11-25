"""Send deadline reminder emails through any SMTP server (optional feature)."""
import smtplib
from email.message import EmailMessage

from config import SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def email_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def reminder_body(contract: str, rows: list[dict]) -> str:
    lines = [f"Upcoming deadlines for {contract}:", ""]
    for r in rows:
        when = r.get("due_date") or r.get("status", "event-based")
        lines.append(f"- {when}: {r.get('term', '')}. {r.get('description', '')} [{r.get('source', '')}]")
    lines += ["", "Sent by Tata AI Legal Document Intelligence System."]
    return "\n".join(lines)


def send_reminder(to: str, contract: str, rows: list[dict]) -> None:
    if not email_configured():
        raise RuntimeError("Email is not set up. Add SMTP_HOST, SMTP_USER and SMTP_PASSWORD to .env.")
    msg = EmailMessage()
    msg["Subject"] = f"Contract deadlines: {contract}"
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg.set_content(reminder_body(contract, rows))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
