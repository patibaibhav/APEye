"""Request Log schemas (Owner: Anvi).

Follows Blueprint Section 4 & 5 and API Contract Section 8.2:
- GET /api/logs
- GET /api/logs/{id}
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ApiRequestLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str
    occurred_at: datetime
    source_ip: str
    path: str
    method: str
    status_code: int
    response_time_ms: int
    auth_outcome: str
    user_id: Optional[int] = None
