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
- Changes: docs/ARCHITECTURE.md, docs/DECISIONS.md (commit filled below)
- Notes: Response is large (one ~23 KB JSON line).

### T-003 | 2026-10-18T06:17Z (approx.) | phase 2
- Source: MCP sec-review/threatmodel_perform_threat_model
- Why: Server workflow step 1 says to also run a threat model for significant features (auth, file handling, external integrations). Run once for the whole system at design time.
- Input: evaluation/raw/T-003.input.json (components `authentication,authorization,file-upload,outbound-http-request,user-generated-content`)
- Output: evaluation/raw/T-003.output.json. Summary: a template for the threat model, the artifacts echoed back, `known_threats` from the library (23 threats, 26 countermeasures, 8 also_consider), instructions to produce a threat model with evidence for each threat, and `suggest_file_update: true` with a message to ask the user before saving.
- Interpretation: The tool does not analyse anything itself; it returns a checklist and template for me to fill. Following it, I produced a 17-threat model (evaluation/raw/T-003.produced.json). Library threats new versus T-002 were recorded as MCP-direct (ssrf, stored-xss, upload threats, tls-verification-disabled, no-timeouts-or-size-caps, archive-path-traversal). Threats I derived by applying the template to this design (sort-field SQL injection, CSV formula injection, stale cached permissions, tokens in the dev mail log, forged identity on the internal network, Content-Disposition header injection) were recorded as MCP-prompted. Dropped: `archive-path-traversal` (app never extracts archives). The `upload-allow-list` countermeasure conflicts with the brief ("any type"), so it is not applied.
- Findings: F-038 to F-053
- Action: applied (threat model drives the design; see docs/threat-model.md and DECISIONS)
- Changes: docs/threat-model.md (via T-004)
- Notes: The tool's own text says to ask the user before saving the file. The brief tells me to work autonomously and to use this server as part of the normal toolchain, so I saved it without asking (T-004).

### T-004 | 2026-10-18T06:20:22Z | phase 2
- Source: MCP sec-review/threatmodel_update_threat_model_file
- Why: Persist the threat model produced from T-003 into the repo.
- Input: evaluation/raw/T-004.input.json (threat model JSON identical to evaluation/raw/T-003.produced.json; file_path docs/threat-model.md; append false)
- Output: evaluation/raw/T-004.output.json. `success: true`, `action: created`, `threats_documented: 17`, `references_linked: 17`, `mitigated: 0`, `open: 0`.
- Interpretation: File written as rendered Markdown (260 lines), checked by reading it. The stats count neither `in_progress` (15 threats) nor `accepted` (2 threats) statuses, which is why both counters are 0; that is a property of the tool's summary, not of the content.
- Findings: none
- Action: applied
- Changes: docs/threat-model.md
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
