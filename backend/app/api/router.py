"""Central API router mounting all route modules (Owner: Baibhav).

Follows Blueprint Section 4 & 5 conflict-prevention design:
Contains router mounts for all modules. If an owner's route file is not yet
implemented, an empty APIRouter() stub is mounted so routes can land independently.
"""

from fastapi import APIRouter

# Base /api router
api_router = APIRouter()

# 1. Health router (Baibhav)
try:
    from app.api.routes.health import router as health_router
    api_router.include_router(health_router)
except ImportError:
    pass

# 2. Sandbox router (Baibhav)
try:
    from app.api.routes.sandbox import router as sandbox_router
    api_router.include_router(sandbox_router, prefix="/sandbox")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/sandbox", tags=["sandbox-stub"])

# 3. Alerts router (Baibhav)
try:
    from app.api.routes.alerts import router as alerts_router
    api_router.include_router(alerts_router, prefix="/alerts")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/alerts", tags=["alerts-stub"])

# 4. Suspicious IPs router (Baibhav)
try:
    from app.api.routes.suspicious_ips import router as suspicious_ips_router
    api_router.include_router(suspicious_ips_router, prefix="/suspicious-ips")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/suspicious-ips", tags=["suspicious-ips-stub"])

# 5. Auth router (Anvi stub)
try:
    from app.api.routes.auth import router as auth_router
    api_router.include_router(auth_router, prefix="/auth")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/auth", tags=["auth-stub"])

# 6. Users router (Anvi stub)
try:
    from app.api.routes.users import router as users_router
    api_router.include_router(users_router, prefix="/users")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/users", tags=["users-stub"])

# 7. Logs router (Anvi stub)
try:
    from app.api.routes.logs import router as logs_router
    api_router.include_router(logs_router, prefix="/logs")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/logs", tags=["logs-stub"])

# 8. Dashboard router (Anvi stub)
try:
    from app.api.routes.dashboard import router as dashboard_router
    api_router.include_router(dashboard_router, prefix="/dashboard")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/dashboard", tags=["dashboard-stub"])

# 9. Exports router (Anvi stub)
try:
    from app.api.routes.exports import router as exports_router
    api_router.include_router(exports_router, prefix="/exports")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/exports", tags=["exports-stub"])

# 10. Reports router (Anvi stub)
try:
    from app.api.routes.reports import router as reports_router
    api_router.include_router(reports_router, prefix="/reports")
except ImportError:
    api_router.include_router(APIRouter(), prefix="/reports", tags=["reports-stub"])
