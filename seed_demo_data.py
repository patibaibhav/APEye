"""Demo data seeder for APEye security monitoring prototype (Owner: Anvi).

Populates PostgreSQL database with realistic sample traffic, alerts, notes,
and investigations for demonstration and testing.
"""

from datetime import datetime, timedelta, timezone
import os
import sys
import uuid

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.auth.security import hash_password  # noqa: E402
from app.db.models import Alert, AlertNote, ApiRequestLog, IpInvestigation, User  # noqa: E402
from app.db.repositories import user_repository  # noqa: E402
from app.db.session import session_scope  # noqa: E402


def seed_demo_data() -> None:
    now = datetime.now(timezone.utc)

    with session_scope() as session:
        print("[*] Seeding demo users...")
        # 1. Users
        admin_pwd = hash_password(os.getenv("ADMIN_PASSWORD", "AdminPass123!"))
        analyst_pwd = hash_password("AnalystPass123!")

        admin = user_repository.get_user_by_username(session, "admin")
        if not admin:
            admin = user_repository.create_user(session, "admin", admin_pwd, "ADMIN")
            print("    Created user: admin (ADMIN)")
        else:
            print("    User admin already exists")

        analyst = user_repository.get_user_by_username(session, "analyst")
        if not analyst:
            analyst = user_repository.create_user(session, "analyst", analyst_pwd, "ANALYST")
            print("    Created user: analyst (ANALYST)")
        else:
            print("    User analyst already exists")

        session.flush()

        print("[*] Seeding API request logs...")
        # 2. API Request Logs
        # Normal traffic over the last 2 hours
        endpoints = [
            ("/api/dashboard/summary", "GET", 200, 45, "AUTHENTICATED", analyst.id),
            ("/api/logs", "GET", 200, 110, "AUTHENTICATED", analyst.id),
            ("/api/alerts", "GET", 200, 85, "AUTHENTICATED", analyst.id),
            ("/api/health", "GET", 200, 12, "NONE", None),
            ("/api/sandbox/ping", "GET", 200, 18, "NONE", None),
        ]

        normal_ip = "192.168.1.105"
        for i in range(40):
            offset_mins = 120 - (i * 3)
            log_time = now - timedelta(minutes=offset_mins)
            path, method, status_code, resp_time, auth_outcome, user_id = endpoints[i % len(endpoints)]
            log = ApiRequestLog(
                request_id=str(uuid.uuid4()),
                occurred_at=log_time,
                source_ip=normal_ip,
                path=path,
                normalized_path=path,
                method=method,
                status_code=status_code,
                response_time_ms=resp_time,
                auth_outcome=auth_outcome,
                user_id=user_id,
            )
            session.add(log)

        # Brute force attack logs from 198.51.100.22
        attacker_bf_ip = "198.51.100.22"
        for i in range(15):
            log_time = now - timedelta(minutes=25 - i)
            log = ApiRequestLog(
                request_id=str(uuid.uuid4()),
                occurred_at=log_time,
                source_ip=attacker_bf_ip,
                path="/api/auth/login",
                normalized_path="/api/auth/login",
                method="POST",
                status_code=401,
                response_time_ms=65,
                auth_outcome="LOGIN_FAILED",
                user_id=None,
            )
            session.add(log)

        # Reconnaissance scan logs from 203.0.113.88
        attacker_recon_ip = "203.0.113.88"
        recon_paths = [
            "/admin",
            "/.env",
            "/.git/config",
            "/wp-login.php",
            "/config.json",
            "/backup.sql",
            "/actuator/health",
            "/phpmyadmin/index.php",
            "/api/v1/users",
            "/debug",
            "/shell.php",
            "/api/test",
            "/console",
            "/server-status",
            "/swagger-ui.html",
        ]
        for idx, recon_path in enumerate(recon_paths):
            log_time = now - timedelta(minutes=45 - idx)
            log = ApiRequestLog(
                request_id=str(uuid.uuid4()),
                occurred_at=log_time,
                source_ip=attacker_recon_ip,
                path=recon_path,
                normalized_path=recon_path,
                method="GET",
                status_code=404,
                response_time_ms=25,
                auth_outcome="NONE",
                user_id=None,
            )
            session.add(log)

        session.flush()

        print("[*] Seeding alerts...")
        # 3. Alerts
        # Alert 1: Active brute force
        bf_alert = Alert(
            category="BRUTE_FORCE",
            severity="HIGH",
            status="ACTIVE",
            source_ip=attacker_bf_ip,
            user_id=None,
            dedup_key=f"BRUTE_FORCE:{attacker_bf_ip}:/api/auth/login",
            endpoints=["/api/auth/login"],
            evidence={"failed_count": 15, "window_seconds": 300, "threshold": 10},
            request_count=15,
            window_seconds=300,
            threshold=10,
            event_count=2,
            first_detected_at=now - timedelta(minutes=25),
            last_detected_at=now - timedelta(minutes=11),
        )
        session.add(bf_alert)
        session.flush()

        # Alert note for brute force
        session.add(
            AlertNote(
                alert_id=bf_alert.id,
                author_id=None,  # system note
                note="System triggered BRUTE_FORCE detection. Threshold 10 exceeded with 15 failed logins.",
                created_at=now - timedelta(minutes=25),
            )
        )

        # Alert 2: Investigating reconnaissance
        recon_alert = Alert(
            category="RECONNAISSANCE",
            severity="MEDIUM",
            status="INVESTIGATING",
            source_ip=attacker_recon_ip,
            user_id=None,
            dedup_key=f"RECONNAISSANCE:{attacker_recon_ip}",
            endpoints=recon_paths[:8],
            evidence={"distinct_endpoints": 15, "total_requests": 15, "error_ratio": 1.0},
            request_count=15,
            window_seconds=120,
            threshold=15,
            event_count=1,
            first_detected_at=now - timedelta(minutes=45),
            last_detected_at=now - timedelta(minutes=31),
            updated_by=analyst.id,
        )
        session.add(recon_alert)
        session.flush()

        session.add(
            AlertNote(
                alert_id=recon_alert.id,
                author_id=analyst.id,
                note="Triage started. Source IP appears to be scanning for common admin/debug endpoints.",
                created_at=now - timedelta(minutes=30),
            )
        )

        # Alert 3: Resolved rate limit
        rate_alert = Alert(
            category="EXCESSIVE_REQUESTS",
            severity="LOW",
            status="RESOLVED",
            source_ip="192.0.2.14",
            user_id=None,
            dedup_key="EXCESSIVE_REQUESTS:192.0.2.14",
            endpoints=["/api/logs"],
            evidence={"request_count": 120, "window_seconds": 60, "threshold": 100},
            request_count=120,
            window_seconds=60,
            threshold=100,
            event_count=1,
            first_detected_at=now - timedelta(hours=3),
            last_detected_at=now - timedelta(hours=3),
            resolved_at=now - timedelta(hours=2, minutes=30),
            updated_by=admin.id,
        )
        session.add(rate_alert)

        print("[*] Seeding IP investigations...")
        # 4. IP investigations
        session.merge(
            IpInvestigation(
                source_ip=attacker_bf_ip,
                status="INVESTIGATING",
                note="High volume of login failures targeting admin accounts.",
                updated_by=analyst.id,
                updated_at=now - timedelta(minutes=20),
            )
        )
        session.merge(
            IpInvestigation(
                source_ip=attacker_recon_ip,
                status="NEW",
                note=None,
                updated_by=None,
                updated_at=now - timedelta(minutes=40),
            )
        )
        session.merge(
            IpInvestigation(
                source_ip="192.0.2.14",
                status="RESOLVED",
                note="Burst traffic verified as automated integration test script.",
                updated_by=admin.id,
                updated_at=now - timedelta(hours=2, minutes=30),
            )
        )

        print("[OK] Demo data successfully seeded!")


def main() -> None:
    try:
        seed_demo_data()
    except Exception as e:
        print(f"[ERROR] Failed to seed demo data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
