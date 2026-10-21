"""Ingestion Service (Owner: Baibhav).

Coordinates request log persistence followed by detection evaluation and alert creation.
Guarantees transaction isolation: detection failures never roll back persisted request logs.
"""

from typing import Any, Callable, Optional

from app.core.config import Settings, get_settings
from app.core.logging_config import get_ops_logger
from app.detection.engine import DetectionEngine
from app.schemas.detection import RequestEvent
from app.services import alert_service


class IngestionService:
    """Service handling asynchronous request event ingestion, log storage, and detection pipeline."""

    def __init__(
        self,
        session_factory: Callable,
        engine: DetectionEngine,
        settings: Optional[Settings] = None,
        log_repo: Any = None,
        alert_repo: Any = None,
        counter_factory: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self.session_factory = session_factory
        self.engine = engine
        self.settings = settings or get_settings()
        self.log_repo = log_repo
        self.alert_repo = alert_repo
        self.counter_factory = counter_factory

    def _resolve_log_repo(self) -> Any:
        if self.log_repo is not None:
            return self.log_repo
        try:
            from app.db.repositories import log_repository
            return log_repository
        except ImportError:
            return None

    def _resolve_counter(self, session: Any) -> Any:
        if self.counter_factory is not None:
            return self.counter_factory(session)
        try:
            from app.db.repositories.window_repository import SqlWindowCounter
            return SqlWindowCounter(session)
        except ImportError:
            return None

    def ingest(self, event: RequestEvent) -> None:
        """Persists the request event, then triggers detection if IP is not ignored."""
        ops_logger = get_ops_logger()
        session = self.session_factory()

        # Step 1: Persist the Request Log
        try:
            repo = self._resolve_log_repo()
            if repo and hasattr(repo, "create_request_log"):
                repo.create_request_log(session, event)
            elif hasattr(session, "create_request_log"):
                session.create_request_log(event)

            session.commit()
        except Exception as exc:
            try:
                session.rollback()
            except Exception:
                pass
            ops_logger.error(
                "request_log_write_failure",
                extra={
                    "extra_fields": {
                        "request_id": event.request_id,
                        "metric": "RequestLogWriteFailures",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                },
            )
            # Failure in log writing terminates ingestion without running detection
            try:
                session.close()
            except Exception:
                pass
            return

        # Step 2: Skip detection if IP is configured in DETECTION_IGNORE_IPS
        if event.source_ip in self.settings.detection.ignore_ips:
            try:
                session.close()
            except Exception:
                pass
            return

        # Step 3: Run Detection Engine and Alert Processing in an isolated transaction
        try:
            counter = self._resolve_counter(session)
            if counter is not None:
                results = self.engine.evaluate(event, counter)
                if results:
                    cooldown = self.settings.detection.alert_cooldown_seconds
                    alert_service.process_results(
                        session=session,
                        results=results,
                        cooldown_seconds=cooldown,
                        alert_repo=self.alert_repo,
                    )
            session.commit()
        except Exception as det_exc:
            try:
                session.rollback()
            except Exception:
                pass
            ops_logger.error(
                "detection_engine_failure",
                extra={
                    "extra_fields": {
                        "request_id": event.request_id,
                        "metric": "DetectionErrors",
                        "error": f"{type(det_exc).__name__}: {det_exc}",
                    }
                },
            )
        finally:
            try:
                session.close()
            except Exception:
                pass
