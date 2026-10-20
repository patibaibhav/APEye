# AGENTS.md: Engineering Agreement

Read this fully before changing anything. This repository is an educational API-security monitoring prototype; it records API metadata, detects rule-based suspicious patterns, raises alerts, and presents analytics. It is not a production SIEM and does not guarantee prevention.

## Scope and stack

Frontend: React, JavaScript, Tailwind, Recharts, Axios, React Router, Vite. Backend: Python, FastAPI, SQLAlchemy, Pydantic, Alembic. PostgreSQL is local/RDS when deployed; tests use Pytest/Vitest; Docker Compose runs the database only. Modules cover request logging, four detection rules, alerts, ADMIN/ANALYST auth, analytics, logs, exports, S3 archival, and CloudWatch operational logging.

Only EC2, Elastic Beanstalk, RDS, S3, and CloudWatch are in AWS scope. Default locally to `STORAGE_BACKEND=local` and `CLOUDWATCH_ENABLED=false`. Do not add other AWS services, machine learning, PDF reports, or manual IP blocking. The React build is served by FastAPI from one origin.

## Fixed ownership

- Baibhav: backend entry architecture; request logging/client IP/detection/alerts; alerts, suspicious-IP, health and sandbox routes; backend integration tests; API/detection/config/deployment contracts; backend CI; final AWS deployment and deployment documentation.
- Anvi: database schema/models/repositories/sessions/migrations; auth; auth/users/logs/dashboard/exports/reports routes; reporting/CSV; S3/CloudWatch; related tests and documentation; AWS integration handoff. Anvi does not own final deployment.
- Lava: all `frontend/`: routing, UI, charts, pages, client/auth, mocks, tests, build and frontend handoff. Lava uses frozen API shapes and never changes them.

`frontend/**` belongs to Lava. `backend/app/db/**`, `backend/app/auth/**`, `backend/app/integrations/**`, `backend/alembic/**`, reporting/CSV services, Anvi routes/schemas/tests, `docker-compose.yml`, `create_admin.py`, and `seed_demo_data.py` belong to Anvi. Remaining backend, deploy, scripts, docs/root files and `.github` except frontend CI belong to Baibhav. Migrations belong only to Anvi.

## Ownership and contract changes

Every file has one owner; `.github/CODEOWNERS` and the architecture ownership matrix are authoritative once added. Do not edit another owner’s file without agreement. For cross-owner work: identify target/owner, describe need, reason and affected endpoints/signatures/schemas/tables/env vars; obtain written agreement; coordinate changes and merge order; request owner review. In a blocked-demo/main-breakage emergency after two working hours, make only the minimal fix, label `urgent-cross-owner`, notify immediately, and obtain review within one working day.

Contracts are frozen before parallel work. Changes require a contract PR approved by its owner and every consumer before dependent code. Follow all files in `docs/contracts/` exactly.

## Git and conflict workflow

Use protected `main`, no direct pushes. Branches: `<type>/<owner>-<topic>` with `feat`, `fix`, `docs`, `test`, or `chore`; Conventional Commits; short-lived branches; one topic/PR. Rebase latest main then squash merge. Each PR needs every touched-file owner’s approval and green CI. One active editor per source file. The owner resolves conflicts in their files; non-owners ask them. Never commit `.env`, secrets, credentials, node_modules, dist, virtual environments, `.local_storage`, or `backend/app/static/*` build output.

## Technical rules

- Python: PEP 8, public type hints, ruff; business logic in services, SQL only in repositories, HTTP only in routes.
- React: function components; API access only in `src/api`; no passwords or tokens in logs.
- API: JSON, standard pagination/error envelopes, ISO UTC `Z`, per `api-contract.md`.
- DB: snake_case plural tables, UTC TIMESTAMPTZ, explicitly named constraints/indexes, VARCHAR CHECK enums.
- Log only via `get_ops_logger()`; never bodies, passwords, tokens, authorization headers, or secrets.
- Every setting is env-based and registered in `config-contract.md`; no hardcoded hosts/credentials.
- Use bcrypt; role-check protected endpoints; parameterized SQLAlchemy queries; CSV formula neutralization; short-lived presigned downloads; never public S3 or database exposure; honor only configured trusted proxies.

## Tests and definition of done

Before merge: relevant unit/API/real-PostgreSQL repository and migration tests; frontend lint/Vitest/build; contract examples; integration tests for logging/detection/alerts; deployment smoke test for deploys. Report actual commands and results; never claim unrun tests pass.

Done means implementation and tests are complete, contracts remain compatible, documentation is updated, owners reviewed, no secrets are committed, integrated behavior works, and actual results/limitations are reported.

## AI coding-agent rules

Agents must inspect working state, preserve uncommitted work, identify requester ownership, modify only authorized/owned files, avoid unrelated churn, follow contracts, ask before changing shared interfaces/schema/manifest/entry points, update tests, and report changed files, real tests, assumptions, and risks. Never transfer Baibhav’s deployment ownership, Anvi’s S3/CloudWatch ownership, or Lava’s frontend ownership without explicit team approval.

Task template: requesting member; task ID/title; objective; exact authorized and prohibited files; required contracts/dependencies; observable behavior/edge cases; acceptance criteria; tests; final report of changes, real commands/results, contract impact, open questions, and handoffs.
