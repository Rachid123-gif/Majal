"""Background generation: RQ worker (docker compose service « worker »), or a thread."""

import threading

from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.db import get_engine
from app.services.reports.generate import run_report
from app.settings import get_settings

QUEUE = "reports"


def generate_job(report_id: int, code: str) -> None:
    with Session(get_engine()) as session:
        run_report(session, report_id, code)


def enqueue(report_id: int, code: str) -> str:
    settings = get_settings()
    if not settings.reports_inline:
        try:
            connection = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
            connection.ping()
            Queue(QUEUE, connection=connection).enqueue(
                generate_job, report_id, code, job_timeout=1800, result_ttl=3600
            )
            return "worker"
        except Exception:  # Redis unavailable: fall back to a thread, the report still gets done
            pass
    threading.Thread(target=generate_job, args=(report_id, code), daemon=True).start()
    return "thread"
