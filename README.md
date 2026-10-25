# APEye — API-Security Monitoring Prototype

An educational API-security monitoring prototype that records API request metadata, detects rule-based suspicious patterns in real-time, raises and manages security alerts, and presents operational analytics.

---

## Architecture & Technology Stack

- **Frontend**: React (Vite), JavaScript, Tailwind CSS, Recharts, Axios, React Router.
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, Psycopg 3.
- **Database**: PostgreSQL 16 (Docker Compose locally; RDS in AWS).
- **Storage & Telemetry**: Local filesystem or AWS S3 (for report archives) and AWS CloudWatch (operational metrics/logs).
- **Deployment Scope**: AWS EC2 rehearsal, AWS Elastic Beanstalk (single-instance), AWS RDS PostgreSQL, AWS S3, and AWS CloudWatch.

---

## Detection Capabilities

APEye implements four rule-based detection engines operating across sliding time windows:

1. **Brute Force (`BRUTE_FORCE`)**: Identifies repeated failed login attempts (`401` status / `LOGIN_FAILED`) targeting `/api/auth/login` from a source IP within a sliding window (default 10 failures in 300s). Dynamically elevates severity if subsequent login succeeds.
2. **Excessive Requests (`EXCESSIVE_REQUESTS`)**: Detects high-frequency volumetric traffic exceeding request rate thresholds from a single source IP (default 100 requests in 60s).
3. **Reconnaissance (`RECONNAISSANCE`)**: Triggers when an IP scans diverse endpoints resulting in high 4xx error rates (default 15 distinct endpoints, 20 requests, ≥50% error ratio in 120s), with priority boosts for sensitive administrative patterns (`/admin`, `/.env`, `/.git`, etc.).
4. **Unauthorized Access (`UNAUTHORIZED_ACCESS`)**: Flags repeated `401 Unauthorized` or `403 Forbidden` responses from an IP or user account (default 15 in 600s).

---

## Repository Structure

```text
APEye/
├── .github/
│   ├── CODEOWNERS               # Authoritative ownership matrix per AGENTS.md
│   └── workflows/
│       ├── backend-ci.yml       # Ruff linting, migrations, and pytest suite
│       └── frontend-ci.yml      # ESLint, Vitest, and Vite build
├── backend/
│   ├── alembic/                 # Migration scripts (0001_initial_schema.py)
│   ├── app/
│   │   ├── api/                 # FastAPI route endpoints
│   │   ├── auth/                # JWT and bcrypt authentication utilities
│   │   ├── core/                # Config, logging, and error envelopes
│   │   ├── db/                  # SQLAlchemy models and repositories
│   │   ├── detection/           # Sliding-window detection rules and engine
│   │   ├── integrations/        # S3 storage and CloudWatch telemetry
│   │   ├── middleware/          # Request logging and client IP resolution
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # Alert, ingestion, export, and report services
│   │   ├── static_site.py       # SPA static file mounting
│   │   └── main.py              # Application factory and ASGI entrypoint
│   └── tests/                   # Pytest unit, API, integration, and DB tests
├── deploy/
│   ├── eb/                      # Elastic Beanstalk Procfile, .ebextensions, nginx proxy
│   └── ec2/                     # EC2 rehearsal host setup script
├── docs/
│   └── contracts/               # Frozen architectural and API contracts
├── frontend/
│   ├── src/                     # React components, pages, charts, API client
│   └── dist/                    # Production frontend build
├── scripts/
│   └── build_release.sh         # Release packaging script
├── create_admin.py              # Initial admin user creation CLI
├── docker-compose.yml           # Local PostgreSQL 16 container
├── seed_demo_data.py            # Prototype demo traffic and alert seeder
└── README.md
```

---

## Local Development Quickstart

### 1. Prerequisites
- Python 3.10+ (Python 3.13 recommended)
- Node.js 20+ and npm
- Docker and Docker Compose

### 2. Start PostgreSQL
```bash
docker compose up -d
```
PostgreSQL will be accessible at `localhost:5432` with user `postgres`, password `postgres`, and database `apimonitor`.

### 3. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env

# Run database migrations
alembic upgrade head
```

### 4. Create Admin User & Seed Demo Data
```bash
# Return to project root
cd ..

# Create initial admin user
python create_admin.py --username admin --password change_this_admin_password_123

# Seed sample traffic, alerts, and investigations
python seed_demo_data.py
```

### 5. Start Backend Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
Backend API and OpenAPI docs will be available at:
- API Documentation: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/api/health`

### 6. Frontend Setup
```bash
cd frontend
npm ci
npm run dev
```
The React frontend dev server will launch at `http://localhost:5173`.

---

## Testing & Quality Assurance

### Run Backend Tests & Linting
```bash
# In backend/
ruff check backend/
pytest -v
```

### Run Frontend Tests & Linting
```bash
# In frontend/
npm run lint
npm run test
npm run build
```

---

## Production Build & AWS Deployment

### 1. Package Release Artifact
Run the packaging script to build the frontend, sync static files to `backend/app/static/`, and produce a deployment zip:
```bash
bash scripts/build_release.sh
```
Output: `dist/apeye-release.zip`

### 2. AWS Elastic Beanstalk Single Instance
1. Create a Python platform single-instance environment on AWS Elastic Beanstalk.
2. Deploy `dist/apeye-release.zip`.
3. Provide database credentials via EB Environment Properties (`DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`).
4. EB `.ebextensions` automatically runs `alembic upgrade head` on leader deployment.
5. In single instance behind Nginx, `TRUSTED_PROXY_COUNT=1` resolves client IPs safely.

---

## Engineering Standards & Constraints

- **Single Origin**: Production builds serve the React SPA directly from FastAPI (`backend/app/static`).
- **Standard Envelopes**: All API responses follow standardized JSON pagination and error envelopes per `docs/contracts/api-contract.md`.
- **Security-First**:
  - Passwords hashed using `bcrypt` with salt.
  - Stateless JWT authentication with role authorization (`ADMIN`, `ANALYST`).
  - Parameterized SQLAlchemy queries strictly prevent SQL injection.
  - CSV exports neutralize spreadsheet formula injection (`=`, `+`, `-`, `@`, `\t`, `\r`).
  - Presigned S3 URLs expire in 300 seconds; buckets are strictly private.
  - Operational logging (`get_ops_logger()`) strictly excludes request bodies, credentials, tokens, and authorization headers.
