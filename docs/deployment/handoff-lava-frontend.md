# Frontend Production Handoff Checklist

**Deliverable**: Production-ready Single Page Application (SPA) Build Bundle  
**Owner / Author**: Lava  
**Recipient / Deployment Lead**: Baibhav  
**Status**: Ready for Integration and Deployment  

---

## 1. Handoff Verification Checklist

- [x] **Tooling and Dependency Verification**
  - Clean `npm ci` completes with zero dependency resolution errors.
  - Node version: `20.x` / `24.x`.
  - Pinned runtime dependencies: React 18, React Router 6, Recharts 2.x, Axios 1.x, Tailwind CSS 3.4.

- [x] **Contract and Response Shape Compliance**
  - All endpoints under `/api` invoked exclusively via `src/api/*`.
  - Zero modifications to backend response envelopes (`{ error: { code, message, details, request_id } }`).
  - No secrets, tokens, or credentials stored in local repositories or logged to browser console.
  - Token expiry (`401` `TOKEN_EXPIRED` / `TOKEN_INVALID`) tested: cleans session and routes cleanly to `/login?reason=expired`.

- [x] **Page State and Feature Coverage**
  - [x] Login page (`/login`)
  - [x] Security Dashboard (`/dashboard`) with 6 KPI stat cards and 5 dynamic Recharts charts
  - [x] Request Logs Explorer (`/logs`) with 5 filter criteria, pagination, detail drawer, and CSV export
  - [x] Threat Alerts (`/alerts`) with severity/status filters, pagination, CSV export, and detail view
  - [x] Alert Detail (`/alerts/:id`) with rule evidence inspection, notes thread, and allowed status transitions
  - [x] Suspicious IP Directory (`/suspicious-ips`) with investigation triage status modal
  - [x] Security Reports (`/reports`) with summary brief, archive triggers (ADMIN-gated), and download links
  - [x] User Management (`/users`) with ADMIN-only role protection, creation modal (min 12-char password check), and self-deactivation safeguards
  - [x] Error / Access handling (`/forbidden`, `404`)
  - [x] Universal Four States implemented across every page: Loading (skeleton/spinner), Error (with correlation request_id and retry), Empty, and Success.

- [x] **Visual and Aesthetic Standards**
  - Minimal, matte dark theme (`#0f0f12`, `#16161b`).
  - Strict absence of neon blues, harsh contrasts, or unnecessary cyanish glows.
  - Curated matte pastel palette for severities, status badges, and chart metrics (Rose, Amber, Mint, Lavender, Slate).

- [x] **Test Suite & CI Status**
  - Full Vitest suite (`npm run test`) passing with green results across 11 test suites.
  - Linting (`npm run lint`) clean with zero errors.
  - GitHub Actions workflow defined at `.github/workflows/frontend-ci.yml`.

---

## 2. Production Build Artifact Instructions

To compile the production distribution bundle for serving via FastAPI static file mounting:

```bash
cd frontend
npm ci
npm run build
```

This compiles static assets into `frontend/dist/`.
Baibhav's `scripts/build_release.sh` copies `frontend/dist/*` into `backend/app/static/` to serve the SPA from the root origin with SPA fallback to `index.html`.

---

## 3. Sign-off

- **Frontend Lead**: Lava (Completed & Verified)
- **Deployment Lead**: Baibhav (Receipt & Acceptance)
