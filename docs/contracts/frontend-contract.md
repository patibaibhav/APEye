# Frontend Contract (frozen)

Owner: Lava. Public `/login`; authenticated ANY: `/dashboard`, `/logs`, `/alerts`, `/alerts/:id`, `/suspicious-ips`, `/reports`; ADMIN `/users`; `/` redirects dashboard; `/forbidden` and `*` render forbidden/not-found.

Axios base URL is `VITE_API_BASE_URL || '/api'`; request interceptor adds Bearer token. Every client function returns parsed body and throws `ApiError {status,code,message,details}`. TOKEN_EXPIRED/TOKEN_INVALID clears session and redirects `/login?reason=expired`. Tokens are memory plus sessionStorage; logout POSTs then clears. No direct API access outside `src/api`.

Chart props: TrafficTrend `points`; StatusDistribution `classes`; TopEndpoints `items`; ResponseTime `points`; SeverityDistribution `items`. Every page supplies loading, error (request ID/retry), empty, success states. Mocks use the canonical contract examples unchanged.
