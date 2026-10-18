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
  non-public ranges and the connection pinned to the checked address. Bodies are HMAC-signed.
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

- **Decision:** All endpoints from brief 4.7 are kept as written. Added `GET /api/v1/admin/cache/stats`. The OpenAPI
  document is served at `/api/v1/openapi.json`. Interactive docs appear only when `ENABLE_DOCS=true`.
- **Reason:** Keeps the contract stable and versioned, with no debug surfaces by default.
- **Driven by:** Brief 4.7; sec-review T-002 (`disable-debug-in-prod`).

## ADR-015: Docker via rootless Podman in this environment

- **Decision:** Local container checks run through the user's rootless Podman socket using the Docker CLI
  (`DOCKER_HOST=unix:///run/user/1000/podman/podman.sock`). The Compose file and Makefile use plain `docker compose`.
- **Reason:** The build session cannot access the host Docker socket. Nothing in the repo depends on Podman.
- **Driven by:** Environment constraint.
