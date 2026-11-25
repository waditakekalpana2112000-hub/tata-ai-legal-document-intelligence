from sqlalchemy.orm import Session

from backend import models


def log_query(db: Session, task: str, source, question: str, answer: str) -> models.QueryLog:
    row = models.QueryLog(task=task, source=source, question=question, answer=answer)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_history(db: Session, limit: int = 20):
    return db.query(models.QueryLog).order_by(models.QueryLog.id.desc()).limit(limit).all()
