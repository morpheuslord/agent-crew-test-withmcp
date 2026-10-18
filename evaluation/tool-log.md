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
- Changes: api/pyproject.toml, api/uv.lock (commit filled in at end of phase)
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

### T-012 | 2026-10-18T06:45Z | phase 3
- Source: Self (user relayed a Semgrep workflow failure in chat)
- Why: The user pasted the Semgrep `terraform` job log: `semgrep scan --metrics off --sarif --output semgrep.sarif "$SEMGREP_PATH"` with `SEMGREP_PATH: infra`, `Error: Process completed with exit code 2.`
- Input: the pasted log excerpt (user chat)
- Output: n/a
- Interpretation: Semgrep exit code 2 is a fatal error. Inferred cause: `infra/` does not exist until phase 6, so the scan target is missing. The Trivy `terraform` job (`scan-ref: infra`) has the same problem.
- Findings: none
- Action: applied. Both workflows now check that the target directory exists, skip the scan and the SARIF upload with a `::notice::` if it does not, and run normally once it does.
- Changes: .github/workflows/semgrep.yml, .github/workflows/trivy.yml (commit filled in below)
- Notes: The fix is based on the job log the user shared. I did not read any scan results.
