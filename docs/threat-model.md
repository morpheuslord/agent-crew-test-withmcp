# Threat Model: Taskboard (whole system)

> **Author:** Claude Code session (arm A), from sec-review perform_threat_model context  
> **Created:** 2026-10-18T06:20:22Z  

## What Are We Building?

Internal team task tracker: a FastAPI API (only component touching PostgreSQL, Redis and attachment storage) behind a Node.js Express UI server that renders pages and authenticates browser users. Features: email/password accounts with reset links, admin user management, teams, projects with outbound status-change webhooks, tasks with Markdown, comments, attachments up to 10 MB, search with client-chosen sort, CSV export, activity feeds.

## What Data Does It Touch?

- User credentials: email, Argon2id password hash (users table)
- Opaque session tokens: SHA-256 hash in sessions table, raw value only in the browser's HttpOnly cookie and in UI-to-API Authorization headers
- Password reset tokens: SHA-256 hash in password_reset_tokens, raw value in outbox rows and API log (dev mailer)
- Personal data: display names and emails of users, visible to teammates and admins
- Task content, Markdown descriptions and comments, labels, due dates
- Attachment bytes (local volume or S3) and original filenames
- Project webhook URLs and outbound webhook payloads
- Service secrets: UI-to-API service token, cookie/CSRF secret, DB password, Redis auth token

## Technologies

Python 3.13, FastAPI, SQLAlchemy 2, PostgreSQL 16, Redis 7, Node.js 24, Express 5, EJS, Docker, Terraform, AWS EC2/ALB/RDS/ElastiCache/S3

## What Can Go Wrong?

### TM-1: A member of team A changes the task, project, comment or attachment id in a URL and reads or edits team B's data, because a handler loads the object by id without checking team membership.

- **Impact:** Cross-team data disclosure and tampering.
- **Likelihood:** high
- **Data Affected:** tasks, comments, attachments, projects, team membership
- **Status:** in_progress

**Mitigation:** A single AccessPolicy service resolves every object to its team and checks membership (or admin) before any read or write; non-members get 404. Search and list queries join on team_members for the caller. Integration tests cover cross-team access for every resource type.

**Evidence:**

- [artifact] `brief section 4.2-4.4, data_flows` — All task/comment/attachment endpoints take bare UUIDs; team membership is the only boundary
  ```
  GET /api/v1/tasks/{task_id}
  ```

### TM-2: A member calls PATCH /api/v1/admin/users/{id} or creates/archives a project directly against the API (or via a crafted form post to the UI) because only the UI hides the buttons.

- **Impact:** Privilege escalation to admin; unauthorised project changes.
- **Likelihood:** medium
- **Data Affected:** user roles, projects
- **Status:** in_progress

**Mitigation:** Role and ownership checks live in services (AdminService requires admin; ProjectService requires team owner or admin). Request schemas use extra='forbid' so role cannot be set at registration or profile update.

**Evidence:**

- [artifact] `brief section 4.1, 4.3` — Admin-only and owner-only operations exist alongside member operations

### TM-3: An attacker sets a project's webhook URL to http://169.254.169.254/latest/meta-data/ or an internal service (api:8000, redis, RDS) and the API's background sender POSTs to it, or a public hostname that later resolves (DNS rebinding) or redirects to an internal address.

- **Impact:** SSRF into the VPC; on EC2 with IMDSv1 this could leak instance role credentials.
- **Likelihood:** medium
- **Data Affected:** instance credentials, internal services
- **Status:** in_progress

**Mitigation:** Validate scheme (https only unless explicitly allowed in dev), resolve the host at send time, reject loopback/private/link-local/multicast/reserved/CGNAT/metadata addresses, connect to the validated IP with the original Host header and SNI, never follow redirects, short connect/read timeouts, cap response read. Enforce IMDSv2 with hop limit 1 on EC2.

**Evidence:**

- [artifact] `data_flows` — API sends webhook POSTs from a background thread to user-configured URLs

### TM-4: A teammate writes a task description or comment containing <script>, an <img onerror>, or a [link](javascript:...) and every viewer of the task runs it in the UI origin, where it can submit forms as the victim.

- **Impact:** Account actions performed as other users, including admins.
- **Likelihood:** high
- **Data Affected:** sessions (indirectly), all data the victim can reach
- **Status:** in_progress

**Mitigation:** Render Markdown with marked, then sanitize-html with a strict tag/attribute allow-list and http/https/mailto-only links; EJS auto-escaping everywhere else (no <%- except sanitized HTML); strict CSP without inline script.

**Evidence:**

- [artifact] `data_flows` — UI renders Markdown to sanitized HTML

### TM-5: A user uploads an .html or .svg attachment; another user opens it and it renders inline in the UI origin, running script.

- **Impact:** Stored XSS through attachments.
- **Likelihood:** medium
- **Data Affected:** sessions (indirectly)
- **Status:** in_progress

**Mitigation:** Downloads are always Content-Disposition: attachment with Content-Type application/octet-stream and X-Content-Type-Options: nosniff, plus a sandbox CSP on the download response. Any file type is allowed by the brief, so no type allow-list.

**Evidence:**

- [artifact] `brief section 4.4` — Attachments are any type and downloadable with their original filename

### TM-6: An uploaded filename like ../../etc/passwd or a name with CR/LF or quotes is used in a storage path or echoed into the Content-Disposition header.

- **Impact:** File overwrite on the API host; response header injection.
- **Likelihood:** medium
- **Data Affected:** attachment storage, API host files
- **Status:** in_progress

**Mitigation:** Storage keys are server-generated UUIDs; the local storage resolves paths and checks they stay under the root. Original filename is stored only as metadata, reduced to its basename, stripped of control characters, and emitted with RFC 6266/5987 filename* encoding.

**Evidence:**

- [artifact] `data_flows` — stores attachment bytes on a local volume or S3 under random keys

### TM-7: A client uploads many multi-gigabyte bodies or a slow stream to exhaust disk or memory on the UI or API.

- **Impact:** Denial of service.
- **Likelihood:** medium
- **Data Affected:** 
- **Status:** in_progress

**Mitigation:** UI multer limit of 10 MB and one file; API rejects Content-Length over limit and counts bytes while streaming, aborting past 10 MB.

**Evidence:**

- [artifact] `brief section 4.4` — up to 10 MB each

### TM-8: Attackers run credential stuffing against /auth/login, or hammer /auth/password/forgot to spam the outbox.

- **Impact:** Account takeover; resource abuse.
- **Likelihood:** medium
- **Data Affected:** credentials
- **Status:** in_progress

**Mitigation:** Per-email and per-client-IP fixed-window rate limits on login and forgot-password (Redis-backed, in-memory fallback), Argon2id hashing, minimum 12-character passwords with a 128 limit, generic error text.

**Evidence:**

- [artifact] `data_flows` — UI forwards X-Client-IP so the API can rate-limit per client

### TM-9: Reset tokens are guessable, reusable, long-lived, or the reset link points at an attacker host because it was built from the Host header; or forgot-password reveals which emails exist.

- **Impact:** Account takeover; user enumeration.
- **Likelihood:** medium
- **Data Affected:** credentials, emails
- **Status:** in_progress

**Mitigation:** secrets.token_urlsafe(32) tokens stored as SHA-256, 30-minute expiry, single use, all sessions revoked on reset, link built from configured PUBLIC_BASE_URL, forgot always returns 202 with the same body.

**Evidence:**

- [artifact] `brief section 4.1` — Forgot password: request a reset link by email, then set a new password using the link

### TM-10: Any process on the internal network (or a compromised container) calls the API directly with forged identity headers, or a stolen session token keeps working after logout, password change or deactivation.

- **Impact:** Impersonation of any user.
- **Likelihood:** low
- **Data Affected:** all
- **Status:** in_progress

**Mitigation:** Identity is never taken from a header: the API resolves the Bearer session token against the sessions table on every request and checks the user is active. The UI must also present X-Service-Token, compared in constant time. Logout deletes the session; password change/reset and deactivation delete all of the user's sessions.

**Evidence:**

- [artifact] `data_flows` — Authorization: Bearer <session token>, X-Service-Token

### TM-11: Another website auto-submits a form to the UI (e.g. remove member, change password) using the victim's cookie.

- **Impact:** Unwanted state changes.
- **Likelihood:** medium
- **Data Affected:** teams, tasks, credentials
- **Status:** in_progress

**Mitigation:** SameSite=Lax HttpOnly cookies (Secure and __Host- prefix in production) plus a per-session HMAC CSRF token on every POST form, verified by middleware.

**Evidence:**

- [artifact] `data_flows` — session token in an HttpOnly SameSite cookie

### TM-12: The client-supplied sort field is interpolated into SQL (ORDER BY {field}), or free-text search builds LIKE patterns by string concatenation.

- **Impact:** SQL injection, full database read.
- **Likelihood:** medium
- **Data Affected:** all database contents
- **Status:** in_progress

**Mitigation:** Sort field is validated against an enum mapped to ORM column objects; direction is an enum; search uses bound parameters with LIKE wildcards escaped.

**Evidence:**

- [artifact] `brief section 4.5` — sort by any task field in either direction, with field and direction supplied by the client

### TM-13: A task title starting with =HYPERLINK(...) or =cmd|... is exported to CSV and executes when a teammate opens it in a spreadsheet.

- **Impact:** Code execution or data exfiltration on the victim's workstation.
- **Likelihood:** low
- **Data Affected:** exported task data
- **Status:** in_progress

**Mitigation:** Prefix cells beginning with = + - @ tab or CR with a single quote.

**Evidence:**

- [artifact] `brief section 4.5` — Export a project's tasks as CSV

### TM-14: A cached team or project list or task detail is served to a user who was removed from the team, or cached data keyed only by object id bypasses the membership check.

- **Impact:** Stale-permission data disclosure.
- **Likelihood:** medium
- **Data Affected:** tasks, projects
- **Status:** in_progress

**Mitigation:** Authorization runs against the database before any cache read; per-user list caches are invalidated on member add/remove; cache values are JSON, never pickle.

**Evidence:**

- [artifact] `data_flows` — uses Redis for cache-aside reads

### TM-15: Reset links and session tokens are written to logs, which are shipped to a log store readable by more people than the database.

- **Impact:** Token leakage via logs.
- **Likelihood:** medium
- **Data Affected:** reset tokens
- **Status:** accepted

**Mitigation:** Session tokens and passwords are never logged. The brief requires emails to be written to the API log, so the dev mailer logs the reset email; this is accepted for this build and documented, with a real mailer replacing it in production.

**Accepted Risk:** Required by the brief: there is no real email provider and emails must be readable from the API log in dev and tests.

**Evidence:**

- [artifact] `brief section 4.1` — write outgoing emails to the API log and to an outbox table

### TM-16: The first-admin management command ships a default password, or secrets are baked into images or committed in .env files.

- **Impact:** Trivial admin takeover.
- **Likelihood:** low
- **Data Affected:** admin account, service secrets
- **Status:** in_progress

**Mitigation:** Command reads email and password from env vars, refuses empty or short passwords, no defaults. Secrets only in env/SSM; .env git-ignored and .dockerignore'd; no build args for secrets.

**Evidence:**

- [artifact] `architecture_notes` — Secrets ... come from environment variables populated from AWS SSM Parameter Store at boot

### TM-17: Traffic between ALB and UI, UI and API, or API and RDS/ElastiCache is sniffed inside the VPC.

- **Impact:** Session token and credential disclosure to a network-positioned attacker.
- **Likelihood:** low
- **Data Affected:** session tokens, DB credentials
- **Status:** accepted

**Mitigation:** TLS 1.2+ policy on the ALB with HTTP->HTTPS redirect; RDS with forced SSL (rds.force_ssl) and sslmode=require; ElastiCache transit encryption with auth token. UI-to-API stays HTTP inside private subnets restricted by security groups; accepted for this build and documented.

**Accepted Risk:** UI-to-API hop is plain HTTP inside private subnets locked to the UI security group; adding internal TLS needs a private CA, out of scope for this build.

**Evidence:**

- [artifact] `data_flows` — ALB --HTTP--> UI server ... calls the API over the private network

## Summary

17 threats. Highest risk: cross-team object access (TM-1), stored XSS via Markdown (TM-4), and webhook SSRF (TM-3). Archive extraction threats from the library were dropped because the app never extracts uploaded archives. MFA and breached-password checks are not in scope for this internal tool and are noted as accepted gaps in DECISIONS.

---
*Generated by mcp-security-review threat modeling tool*
