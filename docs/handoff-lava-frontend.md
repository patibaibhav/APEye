# Frontend Handoff Checklist — Lava

**Owner:** Lava  
**Date:** 2026-10-24  
**Recipient:** Baibhav (deployment)

---

## 1. Build Readiness

| Check | Status | Notes |
|-------|--------|-------|
| `npm run build` succeeds | ✅ | Produces `dist/` with `index.html`, JS bundle, CSS bundle |
| No TypeScript or ESLint blocking errors | ✅ | ESLint configured via `eslint.config.js` (flat config) |
| `npm test` (Vitest) all green | ✅ | 54 tests, 11 test files, all passing |
| Production bundle size acceptable | ✅ | ~757 kB JS (210 kB gzipped), ~26 kB CSS (5 kB gzipped) |

### Build command

```bash
cd frontend
npm ci
npm run build
```

Output goes to `frontend/dist/`. Copy contents to `backend/app/static/` for deployment via `scripts/build_release.sh`.

---

## 2. Environment Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `/api` | Base URL for all API calls. Use `/api` for same-origin production. |
| `VITE_USE_MOCKS` | `false` | Set `true` to enable the built-in mock adapter (no backend needed). |

### Files

- `.env` — live mode (`VITE_USE_MOCKS=false`)
- `.env.mock` — mock mode (`VITE_USE_MOCKS=true`)
- `.env.example` — template for reference

---

## 3. Architecture Overview

### Entry point

`src/main.jsx` → renders `<App />` which wraps `<BrowserRouter>` → `<AuthProvider>` → `<AppRoutes />`

### Routing (`src/routes/`)

| Route | Page | Access |
|-------|------|--------|
| `/login` | `LoginPage` | Public |
| `/dashboard` | `DashboardPage` | ANY authenticated |
| `/logs` | `LogsPage` | ANY authenticated |
| `/alerts` | `AlertsPage` | ANY authenticated |
| `/alerts/:id` | `AlertDetailPage` | ANY authenticated |
| `/suspicious-ips` | `SuspiciousIpsPage` | ANY authenticated |
| `/reports` | `ReportsPage` | ANY authenticated |
| `/users` | `UsersPage` | ADMIN only |
| `/forbidden` | `ForbiddenPage` | Public |
| `*` | `NotFoundPage` | Public |
| `/` | Redirects → `/dashboard` | — |

### Protected routes

- `ProtectedRoute.jsx` — redirects to `/login` if no token
- `RoleRoute.jsx` — redirects to `/forbidden` if role mismatch

### Authentication (`src/context/`)

- `AuthContext.jsx` — provides `login()`, `logout()`, `hasRole()`, `isAuthenticated`, `user`, `token`
- Token stored in memory + `sessionStorage` under keys `apeye_token` and `apeye_user`
- `useAuth()` hook for consuming auth state

### API client (`src/api/client.js`)

- Axios instance with base URL from `VITE_API_BASE_URL`
- Request interceptor: attaches `Bearer <token>` header
- Response interceptor: returns `response.data` directly (parsed body)
- Error interceptor: maps to `ApiError { status, code, message, details, requestId }`
- On 401 with `TOKEN_EXPIRED` or `TOKEN_INVALID`: clears session, redirects to `/login?reason=expired`
- Blob error responses (CSV exports): properly parsed from Blob → JSON before extracting error

### API modules (`src/api/`)

| Module | Endpoints covered |
|--------|-------------------|
| `authApi.js` | `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` |
| `dashboardApi.js` | `GET /dashboard/summary,traffic,status-distribution,top-endpoints,response-times,alert-severity` |
| `logsApi.js` | `GET /logs`, `GET /logs/:id` |
| `alertsApi.js` | `GET /alerts`, `GET /alerts/:id`, `PATCH /alerts/:id/status`, `POST /alerts/:id/notes` |
| `ipsApi.js` | `GET /suspicious-ips`, `GET /suspicious-ips/:ip`, `PATCH /suspicious-ips/:ip/investigation` |
| `reportsApi.js` | `GET /reports/summary`, `POST /reports/archive`, `GET /reports`, `GET /reports/:id/download`, `GET /exports/logs.csv`, `GET /exports/alerts.csv` |
| `usersApi.js` | `GET /users`, `POST /users`, `PATCH /users/:id` |

All functions return parsed response bodies and throw `ApiError` on failure. No direct API access exists outside `src/api/`.

---

## 4. Mock System

`src/mocks/mockAdapter.js` replaces the Axios adapter when `VITE_USE_MOCKS=true`. It routes all API calls to local JSON fixtures from `src/mocks/fixtures/`. Mock data uses the canonical contract examples unchanged.

Supports: login/logout, all dashboard endpoints, logs list/detail, alerts list/detail/status/notes, suspicious IPs list/detail/investigation, reports summary/archive/list/download, exports, users CRUD.

---

## 5. Component Inventory

### Layout (`src/components/layout/`)
- `AppLayout.jsx` — shell with sidebar + topbar + outlet
- `Sidebar.jsx` — navigation with role-aware links (ADMIN sees User Management)
- `Topbar.jsx` — username display, ADMIN badge, sign out

### Common (`src/components/common/`)
- `DataTable.jsx` — generic sortable table wrapper
- `DateRangeFilter.jsx` — from/to picker with presets (1h, 6h, 24h, 7d, custom)
- `EmptyState.jsx` — zero-data state with optional action
- `ErrorState.jsx` — error display with request ID and retry button
- `LoadingState.jsx` — skeleton loading animation
- `Pagination.jsx` — page navigation with size selector
- `SeverityBadge.jsx` — LOW/MEDIUM/HIGH badge
- `StatCard.jsx` — dashboard stat card with icon and accent
- `StatusBadge.jsx` — alert status badge (ACTIVE/INVESTIGATING/RESOLVED)

### Charts (`src/components/charts/`)
- `TrafficTrendChart.jsx` — area chart (successful vs failed over time)
- `StatusDistributionChart.jsx` — donut chart (2xx/3xx/4xx/5xx)
- `TopEndpointsChart.jsx` — horizontal bar chart
- `ResponseTimeChart.jsx` — line chart (avg, p95, max)
- `SeverityDistributionChart.jsx` — donut chart (LOW/MEDIUM/HIGH)

### Alerts (`src/components/alerts/`)
- `AlertFilters.jsx` — severity/category/status/IP filters
- `AlertsTable.jsx` — alert list with navigation to detail
- `AlertStatusSelect.jsx` — status transition dropdown
- `AlertEvidencePanel.jsx` — evidence JSON viewer
- `AlertNotes.jsx` — notes list with add-note form

### Logs (`src/components/logs/`)
- `LogFilters.jsx` — IP/endpoint/method/status filters
- `LogsTable.jsx` — log records table
- `LogDetailDrawer.jsx` — slide-over detail panel

### IPs (`src/components/ips/`)
- `SuspiciousIpTable.jsx` — IP directory with categories and counts
- `IpInvestigationForm.jsx` — investigation status/note form

---

## 6. Page States

Every data page implements all four required states:

1. **Loading** — skeleton animation via `LoadingState`
2. **Error** — error message with request ID and retry button via `ErrorState`
3. **Empty** — descriptive zero-data state via `EmptyState`
4. **Success** — data rendered with tables, charts, and pagination

---

## 7. Test Coverage

| Test file | Tests | Coverage |
|-----------|-------|----------|
| `routing.test.jsx` | 6 | Route access, redirects, role gating |
| `apiClient.test.js` | 8 | Token injection, error mapping, TOKEN_EXPIRED redirect |
| `LoginPage.test.jsx` | 4 | Form render, validation, login flow, expired session |
| `ProtectedRoute.test.jsx` | 3 | Auth redirect, role check, forbidden route |
| `DashboardPage.test.jsx` | 3 | Summary cards, charts, loading state |
| `charts.test.jsx` | 5 | Each chart renders with contract data |
| `LogsPage.test.jsx` | 4 | Table render, pagination, filters, detail drawer |
| `AlertsPage.test.jsx` | 5 | Table, filters, status update, notes, evidence |
| `SuspiciousIpsPage.test.jsx` | 3 | Table, investigation modal, status update |
| `states.test.jsx` | 5 | LoadingState, ErrorState, EmptyState, StatCard, badges |
| `layout.test.jsx` | 3 | Sidebar links, role-aware nav, topbar |
| **Total** | **54** | All passing |

Run with: `npm test` (or `npx vitest run`)

---

## 8. Design System

- **Theme:** Dark matte with pastel accents — no blue/cyan glows
- **Font:** Inter (body), JetBrains Mono (code/mono)
- **Colors:** Defined in `tailwind.config.js` under `matte.*` and `pastel.*`
- **Component classes:** `matte-card`, `btn-primary`, `btn-secondary`, `btn-danger`, `input-matte` (defined in `src/index.css`)
- **Framework:** Tailwind CSS 3.4

---

## 9. Deployment Notes for Baibhav

1. Run `npm ci && npm run build` in `frontend/`
2. Copy `frontend/dist/*` → `backend/app/static/`
3. FastAPI serves static files with SPA fallback (all non-`/api` routes → `index.html`)
4. No CORS needed — same origin
5. The Vite dev proxy (`localhost:5173` → `localhost:8000`) is dev-only
6. All `VITE_*` vars are baked into the bundle at build time — changes require a rebuild
7. The `.env` file should have `VITE_USE_MOCKS=false` for production builds

---

## 10. Known Limitations

- Chart components emit Recharts warnings about zero-width containers in test environments (harmless in jsdom)
- `act(...)` warnings in `SuspiciousIpsPage.test.jsx` during async state updates (does not affect test correctness)
- Bundle size warning (~757 kB) — can be addressed with code splitting via dynamic `import()` if needed
- CSV exports use `responseType: 'blob'` — the Axios interceptor has special blob error parsing to handle server-side error responses correctly

---

## Signoff

- [ ] Baibhav confirms build integrates into `backend/app/static/`
- [ ] Baibhav confirms all pages render against live backend
- [ ] Baibhav confirms CSV exports download successfully
- [ ] Baibhav confirms deployment smoke test passes
