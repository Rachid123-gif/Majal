"""Background analysis of an imported consultation: RQ worker, or a thread without Redis."""

import threading

from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Consultation
from app.services.citizens.pipeline import run
from app.settings import get_settings

QUEUE = "reports"  # same worker as the reports


def analyse_job(consultation_id: int) -> None:
    with Session(get_engine()) as session:
        consultation = session.get(Consultation, consultation_id)
        if consultation is not None:
            run(session, consultation)


def enqueue(consultation_id: int) -> str:
    settings = get_settings()
    if not settings.reports_inline:
        try:
            connection = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
            connection.ping()
            Queue(QUEUE, connection=connection).enqueue(
                analyse_job, consultation_id, job_timeout=7200, result_ttl=3600
            )
            return "worker"
        except Exception:  # Redis unavailable: a thread does the work
            pass
    threading.Thread(target=analyse_job, args=(consultation_id,), daemon=True).start()
    return "thread"
