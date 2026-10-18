# Taskboard

Taskboard is a small internal task tracker for teams. People sign up, create teams, add teammates, create projects
inside a team, and manage tasks with Markdown descriptions, comments and file attachments. Admins manage users and see
a global activity feed. Projects can notify an outbound webhook when a task changes status.

| Part | Technology | Directory |
| --- | --- | --- |
| API | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16, Redis 7 | [`api/`](api/) |
| UI server | Node.js 24, TypeScript, Express 5, EJS (server-rendered, no client JavaScript) | [`ui/`](ui/) |
| Infrastructure | Terraform modules for AWS (VPC, ALB, EC2, RDS, ElastiCache, S3, ECR, IAM) | [`infra/`](infra/) |

The browser only talks to the UI server; the UI server calls the API over an internal network; only the API touches
PostgreSQL, Redis and attachment storage. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/DECISIONS.md](docs/DECISIONS.md) and the
[threat model](docs/threat-model.md).

## Run it locally

Requirements: Docker with Compose v2 (or Podman with its Docker-compatible socket), GNU Make, curl.

```bash
make up
```

`make up` creates `.env` from [`.env.example`](.env.example) with freshly generated secrets on first run, builds both
images, runs the migrations and starts the stack. Open <http://localhost:3000> and register. Only the UI is published,
on 127.0.0.1; the API, PostgreSQL and Redis are on internal Compose networks.

Create the first admin by setting `ADMIN_EMAIL` and `ADMIN_PASSWORD` (12+ characters) in `.env`, then:

```bash
make admin
```

Password-reset emails are not sent anywhere: they are written to the API log and to the `outbox` table.

```bash
docker compose logs api | grep "outgoing email"
```

Stop the stack with `make down` (data volumes are kept; `docker compose down -v` removes them).

## Run the checks

Requirements for the checks: [uv](https://docs.astral.sh/uv/), Node.js 24 with npm, Terraform ≥ 1.9, and Docker for the
API integration tests.

| Command | What it does |
| --- | --- |
| `make lint` | ruff (lint and format check) for the API; ESLint and Prettier for the UI |
| `make typecheck` | `mypy --strict` for the API; `tsc --noEmit` for the UI |
| `make test` | API unit + integration tests against throwaway PostgreSQL/Redis containers, UI tests; both enforce ≥ 80 % line coverage |
| `make tf-check` | `terraform fmt -check -recursive`, then `init -backend=false` and `validate` for `infra/envs/dev` |
| `make smoke` | End-to-end test through the UI of the running stack (register → … → log out) |
| `make fmt` | Format everything |

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs the same lint, type, test and Terraform checks on every
push to `main`, with PostgreSQL and Redis service containers. CodeQL, Codacy, Semgrep and Trivy workflows upload their
results to GitHub code scanning.

## Repository layout

```
api/          FastAPI service: src/taskboard/{api,services,repositories,models,domain,infra}, migrations/, tests/
ui/           Express UI server: src/{api,controllers,http,security,viewmodels}, views/, public/, test/
infra/        Terraform: modules/{network,alb,ui,api,database,cache,storage,registry,iam}, envs/dev/
scripts/      gen-env.sh (local secrets), smoke.sh (end-to-end test)
docs/         Architecture, deployment, decisions, threat model
evaluation/   Build evaluation record
```
