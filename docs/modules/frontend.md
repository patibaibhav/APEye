# Frontend Architecture & Implementation Documentation

Owner: Lava  
Stack: React 18, Vite 5, Tailwind CSS 3.4, Recharts 2.x, Axios 1.x, React Router 6, Vitest & Testing Library.

## 1. Overview and Design Philosophy

The APEye frontend is an educational API-security monitoring and threat detection Single Page Application (SPA).
The interface is engineered around a **minimal, matte dark theme** with a **curated pastel palette**:
- **Backgrounds**: Pure matte dark surfaces (`#0f0f12`, `#121216`, `#16161b`). No bluish background tints or unnecessary cyanish glows.
- **Accents & Badges**: Soft pastel tones:
  - *Rose / Coral* (`#f87171`): High Severity, 5xx failures, error states.
  - *Amber / Peach* (`#fbbf24`): Medium Severity, 4xx warnings, active alerts, triage states.
  - *Mint / Sage* (`#4ade80`): Low Severity, 2xx success, operational health.
  - *Lavender / Violet* (`#b4a2f8`): Primary CTA, brand highlights, active navigation.
  - *Slate / Stone* (`#94a3b8`): Neutral / 3xx / resolved items.
- **Typography**: Crisp typographic hierarchy using system sans-serif and mono fonts with high contrast ratios for maximum legibility.

## 2. Directory Structure

```
frontend/
├── package.json, package-lock.json, vite.config.js, tailwind.config.js,
│   postcss.config.js, eslint.config.js, index.html, .env.example, .gitignore
└── src/
    ├── main.jsx, App.jsx, index.css, setupTests.js
    ├── routes/ AppRoutes.jsx, ProtectedRoute.jsx, RoleRoute.jsx
    ├── context/ AuthContext.jsx
    ├── hooks/ useApiQuery.js, useDebouncedValue.js
    ├── utils/ formatters.js, constants.js, queryParams.js
    ├── api/ client.js, authApi.js, usersApi.js, dashboardApi.js, logsApi.js, alertsApi.js, ipsApi.js, reportsApi.js
    ├── mocks/ mockAdapter.js, fixtures/*.json
    ├── pages/ LoginPage.jsx, DashboardPage.jsx, LogsPage.jsx, AlertsPage.jsx, AlertDetailPage.jsx, SuspiciousIpsPage.jsx, ReportsPage.jsx, UsersPage.jsx, ForbiddenPage.jsx, NotFoundPage.jsx
    ├── components/layout/ AppLayout.jsx, Sidebar.jsx, Topbar.jsx
    ├── components/common/ LoadingState.jsx, ErrorState.jsx, EmptyState.jsx, Pagination.jsx, DataTable.jsx, StatCard.jsx, SeverityBadge.jsx, StatusBadge.jsx, DateRangeFilter.jsx
    ├── components/charts/ TrafficTrendChart.jsx, StatusDistributionChart.jsx, TopEndpointsChart.jsx, ResponseTimeChart.jsx, SeverityDistributionChart.jsx
    ├── components/logs/ LogFilters.jsx, LogsTable.jsx, LogDetailDrawer.jsx
    ├── components/alerts/ AlertFilters.jsx, AlertsTable.jsx, AlertEvidencePanel.jsx, AlertStatusSelect.jsx, AlertNotes.jsx
    ├── components/ips/ SuspiciousIpTable.jsx, IpInvestigationForm.jsx
    └── __tests__/ routing.test.jsx, apiClient.test.js, LoginPage.test.jsx, ProtectedRoute.test.jsx, DashboardPage.test.jsx, charts.test.jsx, LogsPage.test.jsx, AlertsPage.test.jsx, SuspiciousIpsPage.test.jsx, states.test.jsx, layout.test.jsx
```

## 3. Four Universal Page States

In accordance with the engineering contract, every page view supports four discrete lifecycle states:
1. **Loading State**: Skeleton loader or spinner during asynchronous network retrieval.
2. **Error State**: Displays human-readable error messages, correlation `request_id`, and a retry action button.
3. **Empty State**: Explanatory message when no data matches query or date filter criteria.
4. **Success State**: Rich data tables, metric cards, and charts populated directly from backend contract responses.

## 4. Contract Adherence & Session Management

- **API Access**: All API interaction occurs strictly via `src/api/*`. Direct calls using `fetch` or Axios elsewhere are prohibited.
- **Client Base URL**: `import.meta.env.VITE_API_BASE_URL || '/api'`.
- **Error Mapping**: Backend `{ error: { code, message, details, request_id } }` envelopes are converted into typed `ApiError` instances.
- **Session Expiry**: When a `401` response with code `TOKEN_EXPIRED` or `TOKEN_INVALID` occurs, client credentials are cleared from memory and `sessionStorage`, and navigation redirects to `/login?reason=expired`.
- **Role Enforcement**:
  - `ADMIN` & `ANALYST`: Dashboard, Request Logs, Security Alerts, Suspicious IPs, Reports Summary & Download.
  - `ADMIN` Only: User Management (`/users`), Report Archival Trigger (`POST /api/reports/archive`).

## 5. Development & Testing Commands

```bash
# Navigate to frontend directory
cd frontend

# Install pinned dependencies
npm ci

# Start local development server (proxies /api to localhost:8000)
npm run dev

# Run full Vitest test suite
npm run test

# Run ESLint validation
npm run lint

# Compile production bundle
npm run build
```
