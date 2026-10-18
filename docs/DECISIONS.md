# Design decisions

Short ADR-style records. "Driven by" says where the decision came from: the brief, my own judgment, or a tool's output
(with the tool-log entry id from `evaluation/tool-log.md`).

## ADR-001: Opaque server-side session tokens, held by the UI in an HttpOnly cookie

- **Decision:** The API issues a random 256-bit token at login and stores only its SHA-256 hash with an expiry. The UI
  keeps the raw token in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` and `__Host-` prefix when `COOKIE_SECURE=true`)
  and forwards it as `Authorization: Bearer`. No JWTs.
- **Reason:** The UI has no database of its own, so the session must be carried by the browser. Opaque tokens can be
  revoked immediately on logout, password change or deactivation, and there is no signature or algorithm handling to
  get wrong.
- **Driven by:** Brief section 2 (my design decision to make); sec-review T-002 (`proper-logout-and-expiry`,
  `new-session-on-login`, `secure-cookie-attributes`, `no-sensitive-data-in-browser-storage`).

## ADR-002: UI-to-API service token

- **Decision:** All API routes except `/healthz` and `/readyz` require `X-Service-Token` equal to a shared secret,
  compared in constant time.
- **Reason:** Network isolation already keeps the API private. The token adds a second check, so other internal
  workloads cannot call it, and it makes the `X-Client-IP` header trustworthy for rate limiting.
- **Driven by:** My judgment, applying the sec-review threat model template (T-003, TM-10).

## ADR-003: CSRF protection with an HMAC-bound token

- **Decision:** A random `tb_csrf` cookie per browser, plus `HMAC-SHA256(COOKIE_SECRET, cookie)` embedded in every
  form and checked on every POST.
- **Reason:** It needs no server-side store, and an attacker cannot forge the form value without the secret.
- **Driven by:** sec-review T-002 (`csrf-protection`).

## ADR-004: Password policy, hashing and limits

- **Decision:** Argon2id via `argon2-cffi`. Passwords 12 to 128 characters with no composition rules. Login is limited
  per email (5 failures per 15 minutes) and per client IP (20 attempts per 15 minutes). Forgot-password and register
  are limited per IP. The limiter uses Redis and falls back to in-process counters.
- **Reason:** The tool suggested 15 or more characters "is better". I chose 12 as a balance for an internal tool and
  stayed above the ASVS minimum.
- **Driven by:** sec-review T-002 (`slow-password-hashing`, `sensible-password-rules`, `login-attempt-limits`); my
  judgment for the exact numbers.

## ADR-005: No MFA and no breached-password check

- **Decision:** Not implemented.
- **Reason:** Neither is in the brief's functional scope. A breached-password check would need an outbound call to a
  third-party API from the API tier. Both are recorded as accepted risks (F-021, and the `breached-password-check`
  countermeasure noted in T-002).
- **Driven by:** Brief scope; sec-review T-002 raised both.

## ADR-006: Authorization in one AccessPolicy, 404 for foreign objects

- **Decision:** Services call `AccessPolicy` to resolve an object to its team and check membership, ownership or the
  admin role. Non-members get `404`. List and search queries take the caller's team set as a mandatory filter.
  Admins have member-level access to every team.
- **Reason:** One place to get right, and it does not leak which ids exist. Admins need team access to create and
  archive projects (brief 4.3).
- **Driven by:** sec-review T-002 (`check-permissions-server-side`, `per-object-authorization`,
  `scope-queries-to-tenant`); brief 4.3.

## ADR-007: Domain entities as frozen dataclasses, repositories behind Protocols

- **Decision:** Repositories return frozen dataclasses from `taskboard.domain`, never ORM objects. Services depend on
  `typing.Protocol` repository interfaces, with SQLAlchemy implementations wired in `composition.py`. A unit of work
  commits explicitly in services, and cache invalidation and webhook dispatch happen after the commit.
- **Reason:** Unit tests use in-memory fakes without a database. Values are easy to cache as JSON. Side effects after
  the commit avoid caching or announcing data that is then rolled back.
- **Driven by:** Brief section 8; my judgment.

## ADR-008: Versioned keys for task-list cache invalidation

- **Decision:** Task-list keys include a per-project version number. Any task write in the project increments the
  version, which makes every older page and filter combination unreachable. Scalar keys are deleted directly.
- **Reason:** The brief caches lists "per page and filter combination". Enumerating those keys to delete them would
  need `SCAN` or a set per project. A version bump is O(1) and atomic.
- **Driven by:** Brief section 5; my judgment.

## ADR-009: Cache stats endpoint location

- **Decision:** `GET /api/v1/admin/cache/stats`, admin only, in addition to debug-level hit/miss log lines.
- **Reason:** The brief allows "logs or an internal stats endpoint". Putting it under the admin router reuses the
  existing role check instead of adding an unauthenticated internal route.
- **Driven by:** Brief section 5.

## ADR-010: Webhook delivery on a thread pool with SSRF guards

- **Decision:** `HttpWebhookNotifier` submits deliveries to a bounded `ThreadPoolExecutor`: 3 attempts, 3-second
  timeouts, no redirects, TLS verified. Only `https` targets, with every resolved address checked against
  non-public ranges and the connection pinned to the checked address. Bodies are HMAC-signed with a per-project key
  derived from `WEBHOOK_SIGNING_SECRET` and shown only to the project's owner and admins (F-077). At most 500
  deliveries are pending (F-072), and each attempt has an overall deadline (F-073).
- **Reason:** The brief requires asynchronous, best-effort delivery with a short retry. A thread pool needs no extra
  infrastructure. Project owners choose the URLs, so the API must not become an SSRF proxy into the VPC or to the
  EC2 metadata service.
- **Driven by:** Brief 4.3; sec-review T-003 (`ssrf-allow-list`, `no-redirect-following`, `validate-tls-certificates`,
  `timeouts-and-size-caps`).

## ADR-011: Attachments may be any type, served only as downloads

- **Decision:** No file-type allow-list. Downloads are always `application/octet-stream` with
  `Content-Disposition: attachment`, `nosniff` and `CSP: sandbox`. Storage keys are server-generated.
- **Reason:** The brief says "any type". The tool's `upload-allow-list` countermeasure conflicts with that, so the risk
  from active content is handled at serving time instead.
- **Driven by:** Brief 4.4; sec-review T-003 (`serve-uploads-safely`, `upload-rename-and-isolate`; `upload-allow-list`
  not applied, F-047).

## ADR-012: Markdown rendered in the UI, sanitized with an allow-list

- **Decision:** The API stores raw Markdown. The UI renders it with `marked`, then `sanitize-html` with a strict
  allow-list. No images, and only `http`, `https` and `mailto` links.
- **Reason:** Rendering is presentation, which belongs in the UI. Sanitizing after rendering covers raw HTML embedded in
  the Markdown.
- **Driven by:** Brief 4.4; sec-review T-003 (`sanitize-html`, `output-encoding`).

## ADR-013: Dev mailer writes reset links to the log

- **Decision:** `LogOutboxMailer` writes each email, including reset links, to the API log at INFO and to the `outbox`
  table.
- **Reason:** Required by brief 4.1. This is an accepted risk (F-051). A production mailer would implement the same
  `Mailer` interface and not log bodies.
- **Driven by:** Brief 4.1; sec-review T-003 prompted the risk analysis.

## ADR-014: API naming adjustments

- **Decision:** All endpoints from brief 4.7 are kept as written. Added `GET /api/v1/projects` (the caller's projects
  for the dashboard; the brief's list only has per-team project lists) and `GET /api/v1/admin/cache/stats`. The OpenAPI
  document is served at `/api/v1/openapi.json`, behind the service token like every other `/api/v1` route (F-071).
  There is no interactive docs UI.
- **Reason:** Keeps the contract stable and versioned, with no debug surfaces by default.
- **Driven by:** Brief 4.7; sec-review T-002 (`disable-debug-in-prod`).

## ADR-015: Docker via rootless Podman in this environment

- **Decision:** Local container checks run through the user's rootless Podman socket using the Docker CLI
  (`DOCKER_HOST=unix:///run/user/1000/podman/podman.sock`). The Compose file and Makefile use plain `docker compose`.
- **Reason:** The build session cannot access the host Docker socket. Nothing in the repo depends on Podman.
- **Driven by:** Environment constraint.

## ADR-016: Additional Semgrep and Trivy code scanning workflows

- **Decision:** Added `.github/workflows/semgrep.yml` and `.github/workflows/trivy.yml`. Both run on push to `main`
  and upload SARIF to GitHub code scanning. Each has two jobs. Semgrep scans the whole repo with the registry rule sets
  `p/default`, `p/python`, `p/typescript`, `p/javascript`, `p/nodejs`, `p/dockerfile`, `p/github-actions`,
  `p/secrets` and `p/owasp-top-ten` (category `semgrep-code`), and scans `infra/` with `p/terraform`
  (`semgrep-terraform`). Trivy runs `fs` over the repo with the vuln, secret and misconfig scanners
  (`trivy-repository`) and `config` over `infra/` (`trivy-terraform`). Findings never fail the job. The original
  `codeql.yml`, `codacy.yml` and `.codacy.yml` are unchanged.
- **Reason:** Requested by the user mid-session. `aquasecurity/trivy-action` is pinned by commit SHA
  (`ed142fd…`, tag v0.36.0) because several of its older release tags were re-published in March 2026. Trivy itself is
  pinned to v0.76.0, and Semgrep runs from the version-tagged `semgrep/semgrep:1.181.0` image with metrics off.
- **Driven by:** User instruction in chat (2026-10-18), outside the original brief.

## ADR-017: Codacy workflow corrections

- **Decision:** `codacy.yml` keeps the Codacy CLI step unchanged. The post-processing step now gives each run a
  stable category (`codacy/<tool name>`, with the run index added only when two runs share a tool name). It removes
  Codacy's `partialFingerprints` so `upload-sarif` computes consistent ones, and splits the runs into files of at
  most 20 runs. Each file is uploaded with its own category (`codacy-part-0`, `-1`, `-2`), and the step fails loudly
  above 60 runs. `.codacy.yml` also excludes generated output and lockfiles.
- **Reason:** Code scanning rejected the upload with "rejecting SARIF, as there are more runs than allowed
  (24 > 20)". The upload log also warned about inconsistent fingerprints for Codacy results.
- **Follow-up:** after the split upload worked, the user asked to "reduce it to have only usable stuff". The prepare
  step now keeps only the Codacy tools that apply to this stack and run cleanly here, listed in `CODACY_TOOLS`:
  bandit, checkov, lizard, opengrep, prospector, pylint, pylintpython3, ruff, spectral. Dropped: agentlinter,
  biome, eslint-9, jacksonlinter, jshint, markdownlint, oxlint, pmd, pmd-7, remark-lint. These reported execution
  errors in code scanning. TypeScript is still linted (ESLint + typescript-eslint) and type-checked in `ci.yml`, and
  CodeQL, Semgrep and Trivy cover the JavaScript/TypeScript code.
- **Driven by:** User instructions in chat (2026-10-18) to correct the Codacy configuration and then to reduce it to
  usable tools, overriding the brief's rule that these files are never modified.

## ADR-018: TypeScript 6.0 instead of 7.0

- **Decision:** The UI uses TypeScript 6.0.3.
- **Reason:** TypeScript 7.0.2 is the latest release, but typescript-eslint 8.71.2 (required for ESLint with
  typescript-eslint) only supports `typescript >=4.8.4 <6.1.0`.
- **Driven by:** Brief section 3 (current stable releases; ESLint with typescript-eslint); npm peer dependency data.

## ADR-019: Internal ALB in the api module

- **Decision:** The `api` module creates an internal Application Load Balancer in the private app subnets, reachable
  only from the UI security group. The UI calls the API through it.
- **Reason:** The API runs as an Auto Scaling group of several instances, and the UI needs one stable address. The
  brief's module list has no separate internal load balancer module, so it lives with the service it fronts.
- **Driven by:** My judgment (brief section 6 module list).

## ADR-020: Least-privilege database role created by a migration command

- **Decision:** `taskboard-admin migrate` runs Alembic as the owner and maintains `taskboard_app` with DML-only grants.
  The API always connects as `taskboard_app`, locally and in AWS.
- **Reason:** A flaw in the API (for example SQL injection) cannot drop or alter tables, and cannot read the migration
  table.
- **Driven by:** sec-review T-010 and T-027/T-030 (`least-privilege-accounts`, F-062).

## ADR-021: No secrets reach the instances except through SSM at boot

- **Decision:** Terraform generates every runtime secret and stores it as an SSM SecureString under the service's
  path. user_data contains only parameter paths. Each instance role can decrypt only its own path (KMS encryption
  context). The RDS master password stays in RDS-managed Secrets Manager, readable by operators only.
- **Reason:** Keeps secrets out of code, tfvars, images and user_data, and isolates the UI from the API's database and
  cache credentials.
- **Driven by:** sec-review T-027 (`secrets-manager`, `least-privilege-iam`) and T-029 review finding F-090.

## ADR-022: Healthchecks declared in Compose as well as in the Dockerfiles

- **Decision:** `docker-compose.yml` declares the API and UI healthchecks itself.
- **Reason:** OCI-format image builds (Podman's default, which this build environment uses) drop the Dockerfile
  `HEALTHCHECK`, and Compose's `service_healthy` dependencies then fail. Declaring the healthchecks in Compose works with
  both Docker and Podman.
- **Driven by:** Environment constraint found while running `make up`.
