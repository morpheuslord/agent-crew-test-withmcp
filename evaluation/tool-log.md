# Tool log

Chronological record of every MCP tool call and every security-related operation in this session.
Times are UTC from `date -u` at the time of the entry.

### T-001 | 2026-10-18T06:13Z (approx.; no `date -u` taken immediately before the call) | phase 2
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 ("Before you start coding"): first call with only the task description to get the component menu. Run at the start of the design phase, before any application code.
- Input: evaluation/raw/T-001.input.json
- Output: evaluation/raw/T-001.output.json. Summary: `status: needs_components`; a menu of 25 component ids (web-endpoint, authentication, session-management, authorization, database, file-upload, object-storage, outbound-http-request, third-party-webhook, payment-flow, secrets-and-config, cryptography, transport-security, user-generated-content, browser-frontend, background-job, serialization-and-parsing, shell-and-dynamic-code, email-sending, dependencies, container-and-iac, logging-and-errors, llm-integration, agent-tools, coding-agent-setup) and five `data_handled` options.
- Interpretation: Source says to pick 2 to 5 components and call again. Inferred: the whole system touches far more than 5, so I split reviews by area: one call now for the identity/session/authorization core, and further calls per feature as each is built.
- Findings: none
- Action: none needed (menu only)
- Changes: none
- Notes: none

### T-002 | 2026-10-18T06:15Z (approx.) | phase 2
- Source: MCP sec-review/general_lightweight_security_review
- Why: Second call of workflow step 1 for the system's identity core.
- Input: evaluation/raw/T-002.input.json (components `authentication,session-management,authorization,secrets-and-config,transport-security`; data_handled `credentials,personal_data`)
- Output: evaluation/raw/T-002.output.json. Summary: `status: complete`, risk level `critical`, implied component `web-endpoint`, 29 threats (3 critical, 14 high, 10 medium, 2 low), 30 countermeasures, 8 `also_consider` items (mass-assignment, business-flow-bypass, excessive-data-exposure, missing-input-validation, missing-rate-limit, open-redirect, permissive-cors, verbose-errors).
- Interpretation: Source lists threats and countermeasures, not code findings. Each applicable threat was recorded as a requirement (MCP-direct). Inferred not applicable: `jwt-tampering` and `validate-token-claims` for audience/issuer (design uses opaque server-side session tokens, no JWTs); `agent-reads-secrets` concerns the coding agent's own permissions, not the product. `offer-mfa` and `breached-password-check` are not built (accepted risk, recorded in DECISIONS). The tool recommends a 15+ minimum password length "is better"; I chose 12 (see F-027).
- Findings: F-001 to F-037
- Action: applied (design decisions in docs/ARCHITECTURE.md and docs/DECISIONS.md); implementation follows in phases 3 and 5
- Changes: docs/ARCHITECTURE.md, docs/DECISIONS.md (a2f6b7a)
- Notes: Response is large (one ~23 KB JSON line).

### T-003 | 2026-10-18T06:17Z (approx.) | phase 2
- Source: MCP sec-review/threatmodel_perform_threat_model
- Why: Server workflow step 1 says to also run a threat model for significant features (auth, file handling, external integrations). Run once for the whole system at design time.
- Input: evaluation/raw/T-003.input.json (components `authentication,authorization,file-upload,outbound-http-request,user-generated-content`)
- Output: evaluation/raw/T-003.output.json. Summary: a template for the threat model, the artifacts echoed back, `known_threats` from the library (23 threats, 26 countermeasures, 8 also_consider), instructions to produce a threat model with evidence for each threat, and `suggest_file_update: true` with a message to ask the user before saving.
- Interpretation: The tool does not analyse anything itself; it returns a checklist and template for me to fill. Following it, I produced a 17-threat model (evaluation/raw/T-003.produced.json). Library threats new versus T-002 were recorded as MCP-direct (ssrf, stored-xss, upload threats, tls-verification-disabled, no-timeouts-or-size-caps, archive-path-traversal). Threats I derived by applying the template to this design (sort-field SQL injection, CSV formula injection, stale cached permissions, tokens in the dev mail log, forged identity on the internal network, Content-Disposition header injection) were recorded as MCP-prompted. Dropped: `archive-path-traversal` (app never extracts archives). The `upload-allow-list` countermeasure conflicts with the brief ("any type"), so it is not applied.
- Findings: F-038 to F-053
- Action: applied (threat model drives the design; see docs/threat-model.md and DECISIONS)
- Changes: docs/threat-model.md via T-004 (a2f6b7a)
- Notes: The tool's own text says to ask the user before saving the file. The brief tells me to work autonomously and to use this server as part of the normal toolchain, so I saved it without asking (T-004).

### T-004 | 2026-10-18T06:20:22Z | phase 2
- Source: MCP sec-review/threatmodel_update_threat_model_file
- Why: Persist the threat model produced from T-003 into the repo.
- Input: evaluation/raw/T-004.input.json (threat model JSON identical to evaluation/raw/T-003.produced.json; file_path docs/threat-model.md; append false)
- Output: evaluation/raw/T-004.output.json. `success: true`, `action: created`, `threats_documented: 17`, `references_linked: 17`, `mitigated: 0`, `open: 0`.
- Interpretation: File written as rendered Markdown (260 lines), checked by reading it. The stats count neither `in_progress` (15 threats) nor `accepted` (2 threats) statuses, which is why both counters are 0; that is a property of the tool's summary, not of the content.
- Findings: none
- Action: applied
- Changes: docs/threat-model.md (a2f6b7a)
- Notes: none

### T-005 | 2026-10-18T06:21Z | phase 2
- Source: Self (user relayed a CodeQL workflow error message in chat)
- Why: The user pasted the CodeQL Python job failure from the phase 1 push: "CodeQL detected code written in GitHub Actions and JavaScript/TypeScript, but not any written in Python."
- Input: the pasted error message (user chat)
- Output: n/a
- Interpretation: Expected at that point: phase 1 contained no Python source (only `api/pyproject.toml`). The JavaScript one found `ui/eslint.config.mjs`. Not a security finding. I did not open any scanner results myself, and `codeql.yml` is not modified (section 10).
- Findings: none
- Action: none needed; the phase 2 push includes the API package skeleton, so later runs see Python source
- Changes: none
- Notes: none

### T-006 | 2026-10-18T06:33Z | phase 2
- Source: Self (user instruction in chat)
- Why: The user asked mid-session for Semgrep and Trivy workflows that scan all the code, scan the Terraform in particular, and record everything in GitHub's security findings (code scanning).
- Input: user message: "few scanner enhancements add a semgrep workflow along with a trivy workflow and this time its to scan all the code and also perticularly scan the teraform as well and everything should be recorded in the securities fingings page in github"
- Output: `.github/workflows/semgrep.yml` (jobs `code` over `.` and `terraform` over `infra/`) and `.github/workflows/trivy.yml` (jobs `repository`: fs with vuln, secret and misconfig scanners; `terraform`: config over `infra/`). Each job uploads SARIF with its own category.
- Interpretation: Supply-chain hygiene for the new workflows: looked up current releases via the GitHub API and Docker Hub. trivy-action v0.33.1, v0.34.0 and v0.35.0 all show `published_at` 2026-03-20, consistent with tags having been re-published, so the action is pinned to the v0.36.0 commit `ed142fd0673e97e23eac54620cfb913e5ce36c25` instead of a tag. Checked that all 10 Semgrep registry rule sets resolve (HTTP 200).
- Findings: none
- Action: applied. The first draft used an inline `# shellcheck disable=SC2086` comment; I replaced it with Semgrep's `SEMGREP_RULES` environment variable so no suppression was added.
- Changes: .github/workflows/semgrep.yml, .github/workflows/trivy.yml, docs/DECISIONS.md ADR-016 (833373a)
- Notes: Section 10 still applies: I do not read scanner results, and the three original scanner files are unchanged. The `infra/` jobs have nothing to scan until phase 6 lands.

### T-007 | 2026-10-18T06:37Z | phase 3
- Source: MCP sec-review/sca_verify_packages
- Why: Server workflow step 2 (adding dependencies): confirm the 20 direct Python packages and pinned versions for the API exist before writing code that uses them. Versions are the latest on PyPI, looked up with the PyPI JSON API.
- Input: evaluation/raw/T-007.input.json (the arguments were sent as a JSON array string; saved here as parsed JSON)
- Output: `{"all_valid": true, "packages_checked": 20}` (evaluation/raw/T-007.output.json)
- Interpretation: Source: every name and version exists on PyPI.
- Findings: none
- Action: none needed
- Changes: api/pyproject.toml, api/uv.lock (20eda4e)
- Notes: Called in parallel with T-008, as the workflow allows.

### T-008 | 2026-10-18T06:37Z | phase 3
- Source: MCP sec-review/sca_scan_dependencies
- Why: Server workflow step 2: CVE scan of the new direct Python dependencies.
- Input: evaluation/raw/T-008.input.json
- Output: `{"packages_scanned": 20, "vulnerable_count": 0, "status": "clean", "message": "No known vulnerabilities found in scanned packages."}` (evaluation/raw/T-008.output.json)
- Interpretation: Source: no OSV advisories for these exact versions. Inferred: transitive dependencies were not covered, because the tool scans only what it is given, so I scanned the resolved lockfile set next (T-009).
- Findings: none
- Action: none needed
- Changes: none
- Notes: none

### T-009 | 2026-10-18T06:39Z | phase 3
- Source: MCP sec-review/sca_scan_dependencies
- Why: Cover the 48 transitive packages that `uv lock` resolved (69 total, minus the project itself and the 20 direct ones).
- Input: evaluation/raw/T-009.input.json (versions taken from `uv export --all-groups`)
- Output: `{"packages_scanned": 48, "vulnerable_count": 0, "status": "clean", "message": "No known vulnerabilities found in scanned packages."}` (evaluation/raw/T-009.output.json)
- Interpretation: Source: no known advisories for the full resolved API dependency set.
- Findings: none
- Action: none needed
- Changes: none
- Notes: none

### T-010 | 2026-10-18T06:40Z | phase 3
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 before writing the API core (models, repositories, services, routers, logging, mail outbox, admin command).
- Input: evaluation/raw/T-010.input.json (components `web-endpoint,database,logging-and-errors,email-sending,cryptography`; data_handled `credentials,personal_data`)
- Output: evaluation/raw/T-010.output.json. Summary: risk `critical`, 32 threats, 32 countermeasures, empty `also_consider`.
- Interpretation: New relative to T-002/T-003: `sql-injection` (critical), `exposed-data-store`, `sensitive-data-unencrypted`, `weak-crypto-algorithms`, `weak-random-generator`, `email-abuse`, `email-header-injection`, `over-privileged-db-account`, `secrets-in-logs`, `missing-security-headers`, `enforce-flow-order`. I believe two entries are wrong for this task. `card-data-in-your-systems` (critical, with the `hosted-payment-fields` countermeasure) appears although no payment component or `payments` data was given; Taskboard handles no card data. `nosql-injection` appears although the only database is PostgreSQL. Both are recorded as false positives.
- Findings: F-054 to F-064
- Action: applied; countermeasures built into the API code in this phase. The false positives were rejected.
- Changes: api/ (20eda4e)
- Notes: Called in parallel with T-011.

### T-011 | 2026-10-18T06:40Z | phase 3
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 before writing attachments (upload, storage, download) and the webhook notifier.
- Input: evaluation/raw/T-011.input.json (components `file-upload,object-storage,outbound-http-request,background-job`)
- Output: evaluation/raw/T-011.output.json. Summary: risk `high`, 15 threats, 17 countermeasures, 8 `also_consider` items.
- Interpretation: New relative to T-003: `public-bucket`, `long-lived-storage-credentials`, `untrusted-job-payload`, `runaway-retries` (with `bounded-retries`, `validate-job-input`, `private-storage-signed-urls`, `short-lived-scoped-credentials`). Inferred: `long-lived-storage-credentials` does not apply, because no storage credentials reach a client: the browser never talks to S3, and the API uses the EC2 instance role. Instead of signed URLs, downloads stream through the API and UI so authorization runs on every download. The bucket stays private. `metadata.also_consider_total` is 13, but only 8 items are listed. That looks like a count of items before de-duplication; it is noted, not acted on.
- Findings: F-065 to F-068
- Action: applied
- Changes: api/ (20eda4e)
- Notes: none

### T-012 | 2026-10-18T06:45Z | phase 3
- Source: Self (user relayed a Semgrep workflow failure in chat)
- Why: The user pasted the Semgrep `terraform` job log: `semgrep scan --metrics off --sarif --output semgrep.sarif "$SEMGREP_PATH"` with `SEMGREP_PATH: infra`, `Error: Process completed with exit code 2.`
- Input: the pasted log excerpt (user chat)
- Output: n/a
- Interpretation: Semgrep exit code 2 is a fatal error. Inferred cause: `infra/` does not exist until phase 6, so the scan target is missing. The Trivy `terraform` job (`scan-ref: infra`) has the same problem.
- Findings: none
- Action: applied. Both workflows now check that the target directory exists, skip the scan and the SARIF upload with a `::notice::` if it does not, and run normally once it does.
- Changes: .github/workflows/semgrep.yml, .github/workflows/trivy.yml (1e90c2b)
- Notes: The fix is based on the job logs the user shared. The user then pasted the Trivy `terraform` job log from the same pre-fix run, which confirms the cause: `lstat infra: no such file or directory`, then `Error: Path does not exist: trivy.sarif` in the upload step. Both are covered by this fix. I did not read any scan results.

### T-013 | 2026-10-18T06:55Z | phase 3
- Source: Self (user shared a screenshot of the GitHub code scanning "Tools" page)
- Why: The screenshot shows CodeQL, Semgrep OSS and Trivy with green status, and every "(reported by Codacy)" tool (Agentlinter, Biome, Checkov, Eslint-9, Jacksonlinter, Jshint, Lizard, Markdownlint, Opengrep, Oxlint, Pmd, Pmd-7, Remark-lint, Spectral) with red status. The Agentlinter detail reads "No summary of scanned files reported by Agentlinter (reported by Codacy)", setup type "Codacy, Actions workflow".
- Input: screenshot (user chat)
- Output: n/a
- Interpretation: Source: the Semgrep and Trivy uploads added in T-006/T-012 are being received. Inferred, not verified: the brief's `codacy.yml` splits Codacy's SARIF into one run per tool, and GitHub marks a tool red when its run reports no scanned files or execution errors. That fits tools with nothing to analyse here, or a missing `CODACY_PROJECT_TOKEN` secret.
- Findings: none
- Action: none. `codacy.yml` and `.codacy.yml` must not be modified (section 10), and I may not read scanner results to investigate further. I told the user and left the decision to them.
- Changes: none
- Notes: The screenshot shows tool status only, not findings.

### T-014 | 2026-10-18T07:05Z | phase 3
- Source: MCP sec-review/general_verify_code_security
- Why: Server workflow step 3 ("After generating code") for the API core, with the same components as T-010.
- Input: evaluation/raw/T-014.input.json
- Output: evaluation/raw/T-014.output.json. Summary: no findings; a `review_prompt`, a 16-item `security_checklist` and 12 `focus_areas` for me to review my own code against. Risk level `critical`.
- Interpretation: The tool does not see the code. Following its prompt, I reviewed `api/src/taskboard` (baseline commit) item by item. The produced review, as a separate step, is in evaluation/raw/T-014.review.md: verdict "Needs Attention", 5 issues (R14-1 to R14-5), checklist results per item. The checklist again includes the payment item (`hosted-payment-fields`) and NoSQL focus area that do not apply (see T-010).
- Findings: F-070, F-071, F-074, F-075, F-078
- Action: applied
- Changes: F-070 ff86f21; F-071 f0784c3 + cd644cf; F-074 5f3c954; F-075 66a03ee; F-078 7c5540e
- Notes: Called in parallel with T-015. Process slip: commit f0784c3 was made while its new integration test was failing. My commit chain piped pytest through `tail`, which hid the non-zero exit code. The failure was a wrong test expectation (the removed docs route returns 404, not 401); cd644cf fixed the test. Later commit chains check pytest's exit status directly.

### T-015 | 2026-10-18T07:05Z | phase 3
- Source: MCP sec-review/general_verify_code_security
- Why: Server workflow step 3 for attachments, storage and webhooks, with the same components as T-011.
- Input: evaluation/raw/T-015.input.json
- Output: evaluation/raw/T-015.output.json. Summary: `review_prompt`, a 19-item checklist and 12 focus areas. Risk level `high`.
- Interpretation: Following the prompt, I reviewed the attachment and webhook code; the produced review is in evaluation/raw/T-015.review.md: "Needs Attention", 3 issues (R15-1 to R15-3), plus an accepted deviation on the file-type allow-list (brief requires any type) and one on separate-domain serving.
- Findings: F-072, F-073, F-077, F-079
- Action: applied (F-079 accepted)
- Changes: F-072/F-073 1166fa7; F-077 02101da
- Notes: none

### T-016 | 2026-10-18T07:06Z | phase 3
- Source: Self
- Why: Security decisions made while writing the API, before the post-coding review, that are not covered by an MCP entry.
- Input: n/a
- Output: n/a
- Interpretation: While writing `ProjectService` I noticed every team member would receive the project's `webhook_url`, which often embeds a secret. I added redaction for anyone other than the team owner and admins, applied in `ProjectService` and `TeamService.get_team`. Also while coding: inline suppressions I had drafted (`# noqa: S101`, `# type: ignore`, `# pragma: no cover`) were all replaced with code that satisfies the rules, so `evaluation/suppressions.md` is unchanged. Alembic's `fileConfig` disabled every existing logger when migrations ran in-process, which would have silenced security logging in tests. Fixed with `disable_existing_loggers=False` in `migrations/env.py`.
- Findings: F-069
- Action: applied
- Changes: api/ (baseline 20eda4e)
- Notes: none

### T-018 | 2026-10-18T07:35Z | phase 4
- Source: Self (user relayed the Codacy workflow log and asked for the Codacy configuration to be corrected)
- Why: Upload step log: many `Calculated fingerprint ... but found existing inconsistent fingerprint value` warnings (docs/DECISIONS.md, .github/workflows/codacy.yml, api/src/taskboard/__init__.py), then `Error: Code Scanning could not process the submitted SARIF file: rejecting SARIF, as there are more runs than allowed (24 > 20)`. The user wrote: "the entire codacy config needs corrections".
- Input: the pasted log and instruction (user chat)
- Output: Corrected `.github/workflows/codacy.yml` and `.codacy.yml`.
- Interpretation: Source: GitHub limits one SARIF upload to 20 runs, and the brief's jq step makes one run per Codacy tool (24 here). Inferred: the fingerprint warnings come from Codacy writing its own `partialFingerprints` that differ from the ones `upload-sarif` calculates. They do not block the upload, but they make alert matching across commits unreliable. Fix: per-run stable categories, Codacy fingerprints removed, runs split into ≤20-run files uploaded in separate steps. Tested the jq/bash step locally in an `alpine:3.22` container (jq is not installed on the host) against a synthetic 24-run SARIF with a duplicated tool name and a run without `results`. Result: 2 files (20 + 4 runs), 24 unique categories, no `partialFingerprints`, results preserved, and runs without `results` left unchanged. The first draft wrongly turned a missing `results` into `null`, and I fixed that before committing. `.codacy.yml` now also excludes generated directories and lockfiles (recorded in suppressions.md).
- Findings: none
- Action: applied
- Changes: .github/workflows/codacy.yml, .codacy.yml, docs/DECISIONS.md (ADR-017), evaluation/suppressions.md, evaluation/session-meta.md (commit filled in below)
- Notes: This deviates from the brief's section 10 at the user's explicit instruction. I did not read any scanner results; the log came from the user.
