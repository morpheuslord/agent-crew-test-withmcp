# Complete evaluation record (arm A, with ai-security-crew MCP)

This file puts every file under `evaluation/` together in one document, at the user's request after wrap-up. Nothing
has been edited. Markdown headings in the included files are moved down two levels. Each raw file is included
verbatim in a code block. The separate files under `evaluation/` are still the source of record.

## Contents

1. [`evaluation/summary.md`](#part-1-evaluationsummarymd)
2. [`evaluation/session-meta.md`](#part-2-evaluationsession-metamd)
3. [`evaluation/tool-log.md`](#part-3-evaluationtool-logmd)
4. [`evaluation/findings.md`](#part-4-evaluationfindingsmd)
5. [`evaluation/suppressions.md`](#part-5-evaluationsuppressionsmd)
6. [Raw tool inputs and outputs, `evaluation/raw/` (56 files)](#part-6-evaluationraw)

## Part 1: evaluation/summary.md

### Evaluation summary (arm A, with ai-security-crew MCP)

Written last, at wrap-up. The tables come from `tool-log.md` and `findings.md`; the commit counts come from `git log`.

#### Time

| | UTC |
| --- | --- |
| Start | 2026-10-18T06:11:07Z |
| End | 2026-10-18T08:18:52Z |
| Elapsed | 2 h 07 min 45 s |

#### Log entries (tool-log.md)

33 entries: 24 MCP tool calls and 9 self entries. No MCP call returned an error.

| Source | Entries |
| --- | --- |
| MCP `general_lightweight_security_review` | 8 |
| MCP `general_verify_code_security` | 6 |
| MCP `sca_scan_dependencies` | 5 |
| MCP `sca_verify_packages` | 2 |
| MCP `threatmodel_perform_threat_model` | 1 |
| MCP `threatmodel_update_threat_model_file` | 2 |
| Self: 8 prompted by the user in chat (CI and scanner logs or screenshots, scanner requests); T-016 records my own API design decisions | 9 (T-005, T-006, T-012, T-013, T-016, T-018, T-020, T-028, T-031) |
| test / CLI | 0 |

#### Findings (findings.md)

100 findings, F-001 to F-100, all with a disposition.

| Raised by | Count | fixed | mitigated | accepted risk | out of scope | false positive |
| --- | --- | --- | --- | --- | --- | --- |
| MCP-direct:lightweight_security_review | 60 | | | | | |
| MCP-direct:perform_threat_model | 10 | | | | | |
| **MCP-direct total** | **70** | 56 | 5 | 3 | 4 | 2 |
| MCP-prompted:verify_code_security | 11 | | | | | |
| MCP-prompted:perform_threat_model | 6 | | | | | |
| MCP-prompted:lightweight_security_review | 3 | | | | | |
| **MCP-prompted total** | **20** | 16 | 0 | 4 | 0 | 0 |
| **self** | **10** | 5 | 0 | 5 | 0 | 0 |
| test / CLI | 0 | | | | | |
| **All** | **100** | **77** | **5** | **12** | **4** | **2** |

For MCP-direct findings, the severity is the one the source gave: 6 critical, 31 high, 27 medium, 5 low, 1 none given.
Findings from MCP-prompted reviews and from me carry my own severity: 4 medium, 18 low, 8 none given.

The SCA tools (`sca_verify_packages` and `sca_scan_dependencies`) reported every package as valid and found no
vulnerabilities, so no findings came from them.

#### Commits

The repository has 40 commits before the wrap-up commit, all on `main`, with one author and no trailers.

- **Commits whose subject names a finding (dedicated fix commits): 12**
  - **MCP-prompted (9):**
    - ff86f21 F-070
    - f0784c3 and cd644cf F-071
    - 5f3c954 F-074
    - 66a03ee F-075
    - 1166fa7 F-072/F-073
    - 939a161 F-080
    - cab2611 F-090
    - d4a7faf F-095
  - **self (3):** 7c5540e F-078, 02101da F-077, 4ef53a7 F-087
  - **MCP-direct (0):** the direct findings were requirements returned before coding, so they were built into the
    feature commits instead.
- **Distinct commits named in the findings table's Commit column: 17**
  - MCP-direct findings point to 9 of them: 20eda4e, ff86f21, f0784c3, 01111f5, 72f10c3, c85a32c, cab2611, cad3a6b
    and 1166fa7.
  - MCP-prompted findings point to 13.
  - Self findings point to 6.
- **Scanner workflow commits driven by user reports (logged as self, not findings): 4**
  - 833373a: Semgrep/Trivy added
  - 1e90c2b: missing-target guard
  - 8e90f68: Codacy SARIF split
  - de661a6: Codacy tool allow-list

#### False positives

| ID | Source | Why it is a false positive |
| --- | --- | --- |
| F-055 | MCP-direct:lightweight_security_review | Raised `card-data-in-your-systems`, although no payment component and no payment data were given. Taskboard handles no card data. |
| F-056 | MCP-direct:lightweight_security_review | Raised `nosql-injection`. The only store queried with user input is PostgreSQL through SQLAlchemy. Redis keys are built from UUIDs and hashes, never from raw input. |

The 4 out-of-scope items are also off-target generic content:

- F-011 JWT tampering: the design uses opaque session tokens.
- F-018 agent reads secrets.
- F-046 archive path traversal: there is no archive extraction.
- F-066 long-lived storage credentials shipped to clients.

#### Suppressions

There are no inline suppression comments in the source (`noqa`, `type: ignore`, `eslint-disable`, `pragma`,
`nosec`, `shellcheck disable`). `suppressions.md` has 5 configuration-level rows:

- ruff S101, and S105/S106, for tests (2 rows)
- the typescript-eslint `disableTypeChecked` override for the ESLint config file
- the `.codacy.yml` exclusions for generated files and lockfiles
- the Codacy tool allow-list, added at the user's request

#### Final check status

- **Passed:**
  - `make up` and `make smoke`
  - `make lint` and `make typecheck`
  - `make test`: API 118 tests at 96.78 % coverage, UI 62 tests at 96.6 % lines
  - `make tf-check`
  - CI `ci.yml` run for 303d2ed: success (status only)
- **Skipped:** none. Docker ran through rootless Podman.
- **Not run, by rule:** `terraform plan`/`apply`, local CodeQL and Codacy CLI, and reading scanner results.

#### Observations on the MCP tooling

1. **The tools return checklists, not findings.**
   - `general_verify_code_security` never looks at code. It returns a checklist and a `review_prompt`, and every
     MCP-prompted finding came from my own review against that checklist.
   - `general_lightweight_security_review` returns generic threat and countermeasure catalogues for the chosen
     components.
   - These two tools still shaped the design. 60 of the 100 findings are their requirements, and they drove 9 of the
     12 dedicated fix commits.
2. **Off-target content.**
   - Payment, NoSQL, archive-extraction, XML and JWT items appeared without any matching component. These produced
     the 2 false positives and 4 out-of-scope items.
   - Some countermeasures conflicted with the brief:
     - an upload allow-list against "any file type" (F-047)
     - emails written to the log, which leaks reset tokens (F-051)
3. **Inconsistent counters.**
   - In two lightweight-review responses, `also_consider_total` is larger than the `also_consider` list: 9 against 8
     listed in T-002, and 13 against 8 in T-011. The list looks capped at 8 with no note.
   - `threatmodel_update_threat_model_file` reports only `mitigated` and `open`. Threats with status `accepted` or
     `in_progress` appear in neither count: T-033 reported 17 mitigated and 0 open for 19 threats, 2 of them accepted.
   - It reports `action: created` when it overwrites an existing file.
4. **Interface differences from the brief.**
   - The tool names carry a `general_`/`sca_`/`threatmodel_` prefix.
   - `assess_ticket_security` and `search_previous_threat_models` were not exposed, because no Jira or Confluence
     tools were registered.
   - The server instructions reached the model truncated at "## 4. Persisting thre… [truncated]", and no MCP
     resource holds the rest.
5. **SCA tools.** They covered the API's 20 direct and 48 locked Python packages and the UI's 24 direct and 127 locked
   npm packages. They found no invalid packages and no CVEs, so they changed no code.
6. **Session deviations, at the user's request.**
   - Semgrep and Trivy workflows were added.
   - `codacy.yml` and `.codacy.yml` were changed: SARIF split into uploads of at most 20 runs, and a tool allow-list.
   - `codeql.yml` is unchanged from the brief.
   - Ten stale Codacy tool configurations remain on GitHub's code scanning tool status page. Only the repository owner
     can delete them, in the GitHub UI.
7. **Timestamp correction.** I estimated tool-log times while working instead of running `date -u`. At wrap-up I
   corrected them from the modification times of the raw files and from the commit times (see the note at the top of
   `tool-log.md`).

## Part 2: evaluation/session-meta.md

### Session metadata

| Item | Value |
| --- | --- |
| Arm | A (with ai-security-crew MCP) |
| Model | Claude Opus 5.5 (`claude-opus-5-5`) |
| Claude Code version | `2.1.296 (Claude Code)` (output of `claude --version`) |
| Host surface | Claude desktop app, Code tab |
| Start time (UTC) | 2026-10-18T06:11:07Z (first `date -u` of the session) |
| End time (UTC) | 2026-10-18T08:18:52Z (`date -u` before the wrap-up commit) |

#### Git identity (recorded before the first commit)

```
$ git config user.name
morpheuslord
$ git config user.email
morpheuslord@protonmail.com
```

#### Environment notes

- System Node.js is v18.19.1. The brief fixes Node.js 24 LTS, so Node v24.22.0 was downloaded from
  `https://nodejs.org/dist/v24.22.0/node-v24.22.0-linux-x64.tar.xz`, its SHA-256 verified against the
  published `SHASUMS256.txt`, and unpacked to `~/.local/toolchains/node-v24.22.0-linux-x64` (outside the repo).
  All UI commands in this session use that toolchain.
- Python 3.13.13 and uv 0.11.21 are available. Terraform v1.15.8 is available.
- Docker CLI 29.7.2 and Docker Compose v5.5.0 are installed, but the session runs inside a toolbox
  container and `/var/run/docker.sock` returns `permission denied`. The user's rootless Podman 5.8.7 socket at
  `/run/user/1000/podman/podman.sock` speaks the Docker API, so Docker and Compose commands in this session run with
  `DOCKER_HOST=unix:///run/user/1000/podman/podman.sock`. Container checks were run this way, not skipped.
- A SessionStart hook injected instructions to use "superpowers" skills. Section 0 rule 7 of the brief forbids
  invoking skills, so no skill was invoked.

#### MCP servers and tools visible in this session

Server under test: `sec-review` (ai-security-crew). Tools exactly as they appear in the tool list:

- `mcp__sec-review__general_lightweight_security_review`
- `mcp__sec-review__general_verify_code_security`
- `mcp__sec-review__threatmodel_perform_threat_model`
- `mcp__sec-review__sca_scan_dependencies`
- `mcp__sec-review__sca_verify_packages`
- `mcp__sec-review__threatmodel_update_threat_model_file`

Differences from the list in the brief:

- The tool names carry a namespace prefix (`general_`, `sca_`, `threatmodel_`) after the `mcp__sec-review__` prefix.
- `assess_ticket_security` and `search_previous_threat_models` are **not** in the tool list (no Jira/Confluence tools
  were registered). They therefore cannot be called. `ListMcpResourcesTool` for `sec-review` returned
  `No resources found. MCP servers may still provide tools even if they have no resources.`

Other MCP servers present in the session (not used, per section 0 rule 7): `21st`, `claude-in-chrome`,
`Claude_Browser`, `visualize`, `terminal`, `scheduled-tasks`, `mcp-registry`, a Claude Docs connector, and several
`ccd_*` desktop-app servers. Several `plugin:*` servers were listed as needing authentication.

#### sec-review server instructions (verbatim, as shown to the model)

The harness displayed the instructions truncated at the point marked `… [truncated]`; the remainder was never shown to
the model and no resource exposes it.

```
## sec-review
# Security Review MCP — Agent Workflow

Follow this workflow whenever you write or modify code.

## 1. Before you start coding
Call `general_lightweight_security_review` with a description of what you're building. It returns a menu of components (file upload, database, login, and so on).
- Call it a second time with the same description and `components` set to the ids of the components this change adds or directly modifies, usually 2 to 5 (add `data_handled` for credentials, payments, or personal data). The second call returns the threats to guard against and the countermeasures to build in.
- Use this for any non-trivial coding task to identify risks upfront.
- If the task comes from a ticket or page link (Jira, Confluence, Linear, GitHub issues, Notion, and so on), fetch it first with the matching MCP server you have connected, then pass its summary, description, and acceptance criteria as the task description.
- For significant new features (auth, file handling, external integrations), also call `threatmodel_perform_threat_model` with the same `components`.

## 2. When adding or updating dependencies
Run both steps before writing any code that uses the new packages:
1. Call `sca_verify_packages` — confirms packages exist with valid versions. Fix any invalid packages before proceeding.
2. Call `sca_scan_dependencies` in parallel with step 3 — scans for CVEs. Each finding has a `reachability_check`; answer it from your own code:
   - affected symbols are used, or you cannot tell → upgrade to the fixed version or avoid the symbol before continuing.
   - symbols are not used → note it and continue; consider upgrading anyway.

## 3. After generating code
Call `general_verify_code_security` with the same `components`. Do not paste code: it returns a checklist, and you review the code you wrote against it.
- Run this after every non-trivial code generation before presenting results to the user.
- Follow the `review_prompt` in the response, check each item against your code, and report findings.

## 4. Persisting thre… [truncated]
```

#### Deviations from the brief requested by the user

- About 2026-10-18T06:25Z: the user asked in chat for Semgrep and Trivy code scanning workflows (whole repo plus a
  Terraform-specific scan, SARIF uploaded to GitHub code scanning). They were added as
  `.github/workflows/semgrep.yml` and `.github/workflows/trivy.yml` (DECISIONS ADR-016, tool-log T-006). Arm B may not
  have them, which matters when comparing scanner results between the two builds.
- About 2026-10-18T07:10Z: the user relayed the Codacy upload failure ("rejecting SARIF, as there are more runs than allowed
  (24 > 20)") and said "the entire codacy config needs corrections". This overrides section 10's rule that
  `.github/workflows/codacy.yml` and `.codacy.yml` are never modified. Both files were changed (DECISIONS ADR-017,
  tool-log T-018). `.github/workflows/codeql.yml` is still exactly as given in the brief.

#### Checks skipped

None of the definition-of-done checks were skipped. All of them ran locally in this session:

- `make up` and `make smoke` (`SMOKE PASSED`), with Docker commands sent to rootless Podman through `DOCKER_HOST` (see Environment notes).
- `make lint`, `make typecheck` and `make test` all exited 0. The API has 118 tests at 96.78 % coverage, including the integration tests against throwaway PostgreSQL 16 and Redis 7 containers. The UI has 62 tests at 96.6 % line coverage.
- `make tf-check` exited 0.

Not run, by rule of the brief:

- `terraform plan` / `apply` (no AWS account).
- CodeQL and the Codacy CLI locally.
- Any reading of scanner results.

For CI, only the run status of `ci.yml` was read; the run for 303d2ed completed with `success`. The CodeQL, Codacy, Semgrep and Trivy workflows were not waited on.

## Part 3: evaluation/tool-log.md

### Tool log

Chronological record of every MCP tool call and every security-related operation in this session.
Times are UTC. Corrected at wrap-up: while working, I estimated most entry times instead of running `date -u`, and from
T-006 on the estimates ran up to 100 minutes late. Each header now shows the modification time of the entry's raw output
file (written right after the call). Entries with no raw file use the time of their commit or the window between
neighbouring entries. T-004 is the only time taken from `date -u` at the moment of the call.

##### T-001 | 2026-10-18T06:15:51Z | phase 2
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 ("Before you start coding"): first call with only the task description to get the component menu. Run at the start of the design phase, before any application code.
- Input: evaluation/raw/T-001.input.json
- Output: evaluation/raw/T-001.output.json. Summary: `status: needs_components`; a menu of 25 component ids (web-endpoint, authentication, session-management, authorization, database, file-upload, object-storage, outbound-http-request, third-party-webhook, payment-flow, secrets-and-config, cryptography, transport-security, user-generated-content, browser-frontend, background-job, serialization-and-parsing, shell-and-dynamic-code, email-sending, dependencies, container-and-iac, logging-and-errors, llm-integration, agent-tools, coding-agent-setup) and five `data_handled` options.
- Interpretation: Source says to pick 2 to 5 components and call again. Inferred: the whole system touches far more than 5, so I split reviews by area: one call now for the identity/session/authorization core, and further calls per feature as each is built.
- Findings: none
- Action: none needed (menu only)
- Changes: none
- Notes: none

##### T-002 | 2026-10-18T06:16:56Z | phase 2
- Source: MCP sec-review/general_lightweight_security_review
- Why: Second call of workflow step 1 for the system's identity core.
- Input: evaluation/raw/T-002.input.json (components `authentication,session-management,authorization,secrets-and-config,transport-security`; data_handled `credentials,personal_data`)
- Output: evaluation/raw/T-002.output.json. Summary: `status: complete`, risk level `critical`, implied component `web-endpoint`, 29 threats (3 critical, 14 high, 10 medium, 2 low), 30 countermeasures, 8 `also_consider` items (mass-assignment, business-flow-bypass, excessive-data-exposure, missing-input-validation, missing-rate-limit, open-redirect, permissive-cors, verbose-errors).
- Interpretation: Source lists threats and countermeasures, not code findings. Each applicable threat was recorded as a requirement (MCP-direct). Inferred not applicable: `jwt-tampering` and `validate-token-claims` for audience/issuer (design uses opaque server-side session tokens, no JWTs); `agent-reads-secrets` concerns the coding agent's own permissions, not the product. `offer-mfa` and `breached-password-check` are not built (accepted risk, recorded in DECISIONS). The tool recommends a 15+ minimum password length "is better"; I chose 12 (see F-027).
- Findings: F-001 to F-037
- Action: applied (design decisions in docs/ARCHITECTURE.md and docs/DECISIONS.md); implementation follows in phases 3 and 5
- Changes: docs/ARCHITECTURE.md, docs/DECISIONS.md (a2f6b7a)
- Notes: Response is large (one ~23 KB JSON line).

##### T-003 | 2026-10-18T06:18:27Z | phase 2
- Source: MCP sec-review/threatmodel_perform_threat_model
- Why: Server workflow step 1 says to also run a threat model for significant features (auth, file handling, external integrations). Run once for the whole system at design time.
- Input: evaluation/raw/T-003.input.json (components `authentication,authorization,file-upload,outbound-http-request,user-generated-content`)
- Output: evaluation/raw/T-003.output.json. Summary: a template for the threat model, the artifacts echoed back, `known_threats` from the library (23 threats, 26 countermeasures, 8 also_consider), instructions to produce a threat model with evidence for each threat, and `suggest_file_update: true` with a message to ask the user before saving.
- Interpretation: The tool does not analyse anything itself; it returns a checklist and template for me to fill. Following it, I produced a 17-threat model (evaluation/raw/T-003.produced.json). Library threats new versus T-002 were recorded as MCP-direct (ssrf, stored-xss, upload threats, tls-verification-disabled, no-timeouts-or-size-caps, archive-path-traversal). Threats I derived by applying the template to this design (sort-field SQL injection, CSV formula injection, stale cached permissions, tokens in the dev mail log, forged identity on the internal network, Content-Disposition header injection) were recorded as MCP-prompted. Dropped: `archive-path-traversal` (app never extracts archives). The `upload-allow-list` countermeasure conflicts with the brief ("any type"), so it is not applied.
- Findings: F-038 to F-053
- Action: applied (threat model drives the design; see docs/threat-model.md and DECISIONS)
- Changes: docs/threat-model.md via T-004 (a2f6b7a)
- Notes: The tool's own text says to ask the user before saving the file. The brief tells me to work autonomously and to use this server as part of the normal toolchain, so I saved it without asking (T-004).

##### T-004 | 2026-10-18T06:20:22Z | phase 2
- Source: MCP sec-review/threatmodel_update_threat_model_file
- Why: Persist the threat model produced from T-003 into the repo.
- Input: evaluation/raw/T-004.input.json (threat model JSON identical to evaluation/raw/T-003.produced.json; file_path docs/threat-model.md; append false)
- Output: evaluation/raw/T-004.output.json. `success: true`, `action: created`, `threats_documented: 17`, `references_linked: 17`, `mitigated: 0`, `open: 0`.
- Interpretation: File written as rendered Markdown (260 lines), checked by reading it. The stats count neither `in_progress` (15 threats) nor `accepted` (2 threats) statuses, which is why both counters are 0; that is a property of the tool's summary, not of the content.
- Findings: none
- Action: applied
- Changes: docs/threat-model.md (a2f6b7a)
- Notes: none

##### T-005 | 2026-10-18, between 06:21Z and 06:27Z | phase 2
- Source: Self (user relayed a CodeQL workflow error message in chat)
- Why: The user pasted the CodeQL Python job failure from the phase 1 push: "CodeQL detected code written in GitHub Actions and JavaScript/TypeScript, but not any written in Python."
- Input: the pasted error message (user chat)
- Output: n/a
- Interpretation: Expected at that point: phase 1 contained no Python source (only `api/pyproject.toml`). The JavaScript one found `ui/eslint.config.mjs`. Not a security finding. I did not open any scanner results myself, and `codeql.yml` is not modified (section 10).
- Findings: none
- Action: none needed; the phase 2 push includes the API package skeleton, so later runs see Python source
- Changes: none
- Notes: none

##### T-006 | 2026-10-18T06:27Z (commit 833373a) | phase 2
- Source: Self (user instruction in chat)
- Why: The user asked mid-session for Semgrep and Trivy workflows that scan all the code, scan the Terraform in particular, and record everything in GitHub's security findings (code scanning).
- Input: user message: "few scanner enhancements add a semgrep workflow along with a trivy workflow and this time its to scan all the code and also perticularly scan the teraform as well and everything should be recorded in the securities fingings page in github"
- Output: `.github/workflows/semgrep.yml` (jobs `code` over `.` and `terraform` over `infra/`) and `.github/workflows/trivy.yml` (jobs `repository`: fs with vuln, secret and misconfig scanners; `terraform`: config over `infra/`). Each job uploads SARIF with its own category.
- Interpretation: Supply-chain hygiene for the new workflows: looked up current releases via the GitHub API and Docker Hub. trivy-action v0.33.1, v0.34.0 and v0.35.0 all show `published_at` 2026-03-20, consistent with tags having been re-published, so the action is pinned to the v0.36.0 commit `ed142fd0673e97e23eac54620cfb913e5ce36c25` instead of a tag. Checked that all 10 Semgrep registry rule sets resolve (HTTP 200).
- Findings: none
- Action: applied. The first draft used an inline `# shellcheck disable=SC2086` comment; I replaced it with Semgrep's `SEMGREP_RULES` environment variable so no suppression was added.
- Changes: .github/workflows/semgrep.yml, .github/workflows/trivy.yml, docs/DECISIONS.md ADR-016 (833373a)
- Notes: Section 10 still applies: I do not read scanner results, and the three original scanner files are unchanged. The `infra/` jobs have nothing to scan until phase 6 lands.

##### T-007 | 2026-10-18T06:29Z | phase 3
- Source: MCP sec-review/sca_verify_packages
- Why: Server workflow step 2 (adding dependencies): confirm the 20 direct Python packages and pinned versions for the API exist before writing code that uses them. Versions are the latest on PyPI, looked up with the PyPI JSON API.
- Input: evaluation/raw/T-007.input.json (the arguments were sent as a JSON array string; saved here as parsed JSON)
- Output: `{"all_valid": true, "packages_checked": 20}` (evaluation/raw/T-007.output.json)
- Interpretation: Source: every name and version exists on PyPI.
- Findings: none
- Action: none needed
- Changes: api/pyproject.toml, api/uv.lock (20eda4e)
- Notes: Called in parallel with T-008, as the workflow allows.

##### T-008 | 2026-10-18T06:29Z | phase 3
- Source: MCP sec-review/sca_scan_dependencies
- Why: Server workflow step 2: CVE scan of the new direct Python dependencies.
- Input: evaluation/raw/T-008.input.json
- Output: `{"packages_scanned": 20, "vulnerable_count": 0, "status": "clean", "message": "No known vulnerabilities found in scanned packages."}` (evaluation/raw/T-008.output.json)
- Interpretation: Source: no OSV advisories for these exact versions. Inferred: transitive dependencies were not covered, because the tool scans only what it is given, so I scanned the resolved lockfile set next (T-009).
- Findings: none
- Action: none needed
- Changes: none
- Notes: none

##### T-009 | 2026-10-18T06:29Z | phase 3
- Source: MCP sec-review/sca_scan_dependencies
- Why: Cover the 48 transitive packages that `uv lock` resolved (69 total, minus the project itself and the 20 direct ones).
- Input: evaluation/raw/T-009.input.json (versions taken from `uv export --all-groups`)
- Output: `{"packages_scanned": 48, "vulnerable_count": 0, "status": "clean", "message": "No known vulnerabilities found in scanned packages."}` (evaluation/raw/T-009.output.json)
- Interpretation: Source: no known advisories for the full resolved API dependency set.
- Findings: none
- Action: none needed
- Changes: none
- Notes: none

##### T-010 | 2026-10-18T06:30:10Z | phase 3
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 before writing the API core (models, repositories, services, routers, logging, mail outbox, admin command).
- Input: evaluation/raw/T-010.input.json (components `web-endpoint,database,logging-and-errors,email-sending,cryptography`; data_handled `credentials,personal_data`)
- Output: evaluation/raw/T-010.output.json. Summary: risk `critical`, 32 threats, 32 countermeasures, empty `also_consider`.
- Interpretation: New relative to T-002/T-003: `sql-injection` (critical), `exposed-data-store`, `sensitive-data-unencrypted`, `weak-crypto-algorithms`, `weak-random-generator`, `email-abuse`, `email-header-injection`, `over-privileged-db-account`, `secrets-in-logs`, `missing-security-headers`, `enforce-flow-order`. I believe two entries are wrong for this task. `card-data-in-your-systems` (critical, with the `hosted-payment-fields` countermeasure) appears although no payment component or `payments` data was given; Taskboard handles no card data. `nosql-injection` appears although the only database is PostgreSQL. Both are recorded as false positives.
- Findings: F-054 to F-064
- Action: applied; countermeasures built into the API code in this phase. The false positives were rejected.
- Changes: api/ (20eda4e)
- Notes: Called in parallel with T-011.

##### T-011 | 2026-10-18T06:31:11Z | phase 3
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 before writing attachments (upload, storage, download) and the webhook notifier.
- Input: evaluation/raw/T-011.input.json (components `file-upload,object-storage,outbound-http-request,background-job`)
- Output: evaluation/raw/T-011.output.json. Summary: risk `high`, 15 threats, 17 countermeasures, 8 `also_consider` items.
- Interpretation: New relative to T-003: `public-bucket`, `long-lived-storage-credentials`, `untrusted-job-payload`, `runaway-retries` (with `bounded-retries`, `validate-job-input`, `private-storage-signed-urls`, `short-lived-scoped-credentials`). Inferred: `long-lived-storage-credentials` does not apply, because no storage credentials reach a client: the browser never talks to S3, and the API uses the EC2 instance role. Instead of signed URLs, downloads stream through the API and UI so authorization runs on every download. The bucket stays private. `metadata.also_consider_total` is 13, but only 8 items are listed. That looks like a count of items before de-duplication; it is noted, not acted on.
- Findings: F-065 to F-068
- Action: applied
- Changes: api/ (20eda4e)
- Notes: none

##### T-012 | 2026-10-18T06:30Z (commit 1e90c2b) | phase 3
- Source: Self (user relayed a Semgrep workflow failure in chat)
- Why: The user pasted the Semgrep `terraform` job log: `semgrep scan --metrics off --sarif --output semgrep.sarif "$SEMGREP_PATH"` with `SEMGREP_PATH: infra`, `Error: Process completed with exit code 2.`
- Input: the pasted log excerpt (user chat)
- Output: n/a
- Interpretation: Semgrep exit code 2 is a fatal error. Inferred cause: `infra/` does not exist until phase 6, so the scan target is missing. The Trivy `terraform` job (`scan-ref: infra`) has the same problem.
- Findings: none
- Action: applied. Both workflows now check that the target directory exists, skip the scan and the SARIF upload with a `::notice::` if it does not, and run normally once it does.
- Changes: .github/workflows/semgrep.yml, .github/workflows/trivy.yml (1e90c2b)
- Notes: The fix is based on the job logs the user shared. The user then pasted the Trivy `terraform` job log from the same pre-fix run, which confirms the cause: `lstat infra: no such file or directory`, then `Error: Path does not exist: trivy.sarif` in the upload step. Both are covered by this fix. I did not read any scan results.

##### T-013 | 2026-10-18, between 06:31Z and 06:57Z | phase 3
- Source: Self (user shared a screenshot of the GitHub code scanning "Tools" page)
- Why: The screenshot shows CodeQL, Semgrep OSS and Trivy with green status, and every "(reported by Codacy)" tool (Agentlinter, Biome, Checkov, Eslint-9, Jacksonlinter, Jshint, Lizard, Markdownlint, Opengrep, Oxlint, Pmd, Pmd-7, Remark-lint, Spectral) with red status. The Agentlinter detail reads "No summary of scanned files reported by Agentlinter (reported by Codacy)", setup type "Codacy, Actions workflow".
- Input: screenshot (user chat)
- Output: n/a
- Interpretation: Source: the Semgrep and Trivy uploads added in T-006/T-012 are being received. Inferred, not verified: the brief's `codacy.yml` splits Codacy's SARIF into one run per tool, and GitHub marks a tool red when its run reports no scanned files or execution errors. That fits tools with nothing to analyse here, or a missing `CODACY_PROJECT_TOKEN` secret.
- Findings: none
- Action: none. `codacy.yml` and `.codacy.yml` must not be modified (section 10), and I may not read scanner results to investigate further. I told the user and left the decision to them.
- Changes: none
- Notes: The screenshot shows tool status only, not findings.

##### T-014 | 2026-10-18T06:57:28Z | phase 3
- Source: MCP sec-review/general_verify_code_security
- Why: Server workflow step 3 ("After generating code") for the API core, with the same components as T-010.
- Input: evaluation/raw/T-014.input.json
- Output: evaluation/raw/T-014.output.json. Summary: no findings; a `review_prompt`, a 16-item `security_checklist` and 12 `focus_areas` for me to review my own code against. Risk level `critical`.
- Interpretation: The tool does not see the code. Following its prompt, I reviewed `api/src/taskboard` (baseline commit) item by item. The produced review, as a separate step, is in evaluation/raw/T-014.review.md: verdict "Needs Attention", 5 issues (R14-1 to R14-5), checklist results per item. The checklist again includes the payment item (`hosted-payment-fields`) and NoSQL focus area that do not apply (see T-010).
- Findings: F-070, F-071, F-074, F-075, F-078
- Action: applied
- Changes: F-070 ff86f21; F-071 f0784c3 + cd644cf; F-074 5f3c954; F-075 66a03ee; F-078 7c5540e
- Notes: Called in parallel with T-015. Process slip: commit f0784c3 was made while its new integration test was failing. My commit chain piped pytest through `tail`, which hid the non-zero exit code. The failure was a wrong test expectation (the removed docs route returns 404, not 401); cd644cf fixed the test. Later commit chains check pytest's exit status directly.

##### T-015 | 2026-10-18T06:57:51Z | phase 3
- Source: MCP sec-review/general_verify_code_security
- Why: Server workflow step 3 for attachments, storage and webhooks, with the same components as T-011.
- Input: evaluation/raw/T-015.input.json
- Output: evaluation/raw/T-015.output.json. Summary: `review_prompt`, a 19-item checklist and 12 focus areas. Risk level `high`.
- Interpretation: Following the prompt, I reviewed the attachment and webhook code; the produced review is in evaluation/raw/T-015.review.md: "Needs Attention", 3 issues (R15-1 to R15-3), plus an accepted deviation on the file-type allow-list (brief requires any type) and one on separate-domain serving.
- Findings: F-072, F-073, F-077, F-079
- Action: applied (F-079 accepted)
- Changes: F-072/F-073 1166fa7; F-077 02101da
- Notes: none

##### T-016 | 2026-10-18T06:58Z to 06:59Z (before commit 20eda4e) | phase 3
- Source: Self
- Why: Security decisions made while writing the API, before the post-coding review, that are not covered by an MCP entry.
- Input: n/a
- Output: n/a
- Interpretation: While writing `ProjectService` I noticed every team member would receive the project's `webhook_url`, which often embeds a secret. I added redaction for anyone other than the team owner and admins, applied in `ProjectService` and `TeamService.get_team`. Also while coding: inline suppressions I had drafted (`# noqa: S101`, `# type: ignore`, `# pragma: no cover`) were all replaced with code that satisfies the rules, so `evaluation/suppressions.md` is unchanged. Alembic's `fileConfig` disabled every existing logger when migrations ran in-process, which would have silenced security logging in tests. Fixed with `disable_existing_loggers=False` in `migrations/env.py`.
- Findings: F-069
- Action: applied
- Changes: api/ (baseline 20eda4e)
- Notes: none

##### T-017 | 2026-10-18T07:09:12Z | phase 4
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 before writing the cache layer.
- Input: evaluation/raw/T-017.input.json (components `database,authorization,serialization-and-parsing,logging-and-errors`)
- Output: evaluation/raw/T-017.output.json. Summary: risk `critical`, 18 threats, 17 countermeasures.
- Interpretation: The one new requirement relevant to caching is `unsafe-deserialization` (critical): cache values must not use pickle or other code-executing formats, so values are JSON via Pydantic `TypeAdapter`. Most of the rest repeats earlier entries. I believe several entries do not apply to this task: `card-data-in-your-systems`/`hosted-payment-fields` (no payments, as in T-010), `weak-password-storage`, `archive-path-traversal` and `xxe` (the cache layer touches no passwords, archives or XML). The threat list did not tie itself to the components I gave, so it reads as a generic list for the component set.
- Findings: F-084
- Action: applied (JSON-only cache values)
- Changes: api/ cache layer (01111f5)
- Notes: Logged after T-018 in time order. The call was made before the user's Codacy message arrived, and the T-018 work was done in between.

##### T-018 | 2026-10-18T07:12Z (commit 8e90f68) | phase 4
- Source: Self (user relayed the Codacy workflow log and asked for the Codacy configuration to be corrected)
- Why: Upload step log: many `Calculated fingerprint ... but found existing inconsistent fingerprint value` warnings (docs/DECISIONS.md, .github/workflows/codacy.yml, api/src/taskboard/__init__.py), then `Error: Code Scanning could not process the submitted SARIF file: rejecting SARIF, as there are more runs than allowed (24 > 20)`. The user wrote: "the entire codacy config needs corrections".
- Input: the pasted log and instruction (user chat)
- Output: Corrected `.github/workflows/codacy.yml` and `.codacy.yml`.
- Interpretation: Source: GitHub limits one SARIF upload to 20 runs, and the brief's jq step makes one run per Codacy tool (24 here). Inferred: the fingerprint warnings come from Codacy writing its own `partialFingerprints` that differ from the ones `upload-sarif` calculates. They do not block the upload, but they make alert matching across commits unreliable. Fix: per-run stable categories, Codacy fingerprints removed, runs split into ≤20-run files uploaded in separate steps. Tested the jq/bash step locally in an `alpine:3.22` container (jq is not installed on the host) against a synthetic 24-run SARIF with a duplicated tool name and a run without `results`. Result: 2 files (20 + 4 runs), 24 unique categories, no `partialFingerprints`, results preserved, and runs without `results` left unchanged. The first draft wrongly turned a missing `results` into `null`, and I fixed that before committing. `.codacy.yml` now also excludes generated directories and lockfiles (recorded in suppressions.md).
- Findings: none
- Action: applied
- Changes: .github/workflows/codacy.yml, .codacy.yml, docs/DECISIONS.md (ADR-017), evaluation/suppressions.md, evaluation/session-meta.md (8e90f68)
- Notes: This deviates from the brief's section 10 at the user's explicit instruction. I did not read any scanner results; the log came from the user.

##### T-019 | 2026-10-18T07:17:50Z | phase 4
- Source: MCP sec-review/general_verify_code_security
- Why: Server workflow step 3 for the cache layer, with T-017's components.
- Input: evaluation/raw/T-019.input.json
- Output: evaluation/raw/T-019.output.json. Summary: a review prompt, a 17-item checklist and 12 focus areas; no findings of its own.
- Interpretation: Following the prompt I reviewed the cache code and its call sites; the review is in evaluation/raw/T-019.review.md: "Needs Attention". R19-1 (medium): a cache-aside race can keep a demoted admin's role for up to the TTL, because `authenticate()` took `role` and `is_active` from the cached profile. That contradicts the T-003 threat-model mitigation TM-14 ("Authorization runs against the database before any cache read"), which my implementation did not meet. R19-2 is an accepted low risk. R19-3 and R19-4 are low and handled in Terraform.
- Findings: F-080, F-081, F-082, F-083
- Action: applied (F-080 fixed; F-081 accepted; F-082/F-083 in phase 6)
- Changes: baseline 01111f5; F-080 fix 939a161
- Notes: The checklist again lists the payment, archive and XML items that do not apply.

##### T-020 | 2026-10-18T07:22Z (commit de661a6) | phase 4
- Source: Self (user screenshots of the code scanning tool status page, plus "codacy issue is still not fixed" and then "or else reduce it to have only usable stuff")
- Why: The first screenshot still showed every Codacy tool red with "Last scan 1 hour ago". The second (after the run for 1afcf28 finished) showed "Last scan now", with Bandit, Checkov, Lizard, Opengrep, Prospector, Pylint, Pylintpython3, Ruff and Spectral green. Agentlinter, Biome, Eslint-9, Jacksonlinter, Jshint, Markdownlint, Oxlint, Pmd, Pmd-7 and Remark-lint were still red.
- Input: screenshots and messages (user chat). I also read workflow run status metadata (not results) from the public Actions API: `GET /repos/morpheuslord/agent-crew-test-withmcp/actions/workflows/codacy.yml/runs`, which showed the run for 1afcf28 `completed success` at 2026-10-18T07:12:26Z, after failures for 97c3111, 1e90c2b and c606b6b.
- Output: `CODACY_TOOLS` allow-list in `.github/workflows/codacy.yml`.
- Interpretation: Source: the split upload from T-018 works, since the run succeeded and the tools refreshed. Inferred: the remaining red tools report execution errors because they do not apply to this stack or cannot run in this setup. Following the user's instruction, only the 9 working tools are uploaded. Tested in an `alpine:3.22` container with jq 1.8.2 against a synthetic 24-run SARIF: 9 runs kept with stable categories, 1 upload file; an empty allow-list result produces no files and no error.
- Findings: none
- Action: applied
- Changes: .github/workflows/codacy.yml, docs/DECISIONS.md (ADR-017), evaluation/suppressions.md (de661a6)
- Notes: The tool entries for the dropped tools will stay in the tool status page as stale configurations until someone deletes them there. I cannot do that without the code scanning API, which the brief rules out, so I told the user.

##### T-021 | 2026-10-18T07:24:55Z | phase 5
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 before writing the UI server.
- Input: evaluation/raw/T-021.input.json (components `browser-frontend,user-generated-content,session-management,web-endpoint,file-upload`; data_handled `credentials,personal_data`)
- Output: evaluation/raw/T-021.output.json. Summary: risk `critical`, 31 threats, 34 countermeasures.
- Interpretation: New relative to earlier entries: `dom-xss` / `safe-dom-apis`, and `third-party-script-compromise` / `subresource-integrity`. Applied by design: the UI ships no client-side JavaScript at all, serves its only stylesheet itself, and its CSP allows `'self'` only. Everything else confirms the UI half of existing requirements: CSRF, cookie flags, open redirect, output encoding, sanitisation, upload limits, generic errors, security headers, and sessions ended on the server. `jwt-tampering` and `long-lived-storage-credentials` do not apply (opaque tokens; no storage credentials in the browser).
- Findings: F-085, F-086
- Action: applied in the UI code (phase 5 commit)
- Changes: ui/ (72f10c3)
- Notes: none

##### T-022 | 2026-10-18T07:27Z | phase 5
- Source: MCP sec-review/sca_verify_packages
- Why: Server workflow step 2 before writing UI code: verify the 24 direct npm packages. Versions are current from `npm view`, except TypeScript: 7.0.2 is latest, but typescript-eslint 8.71.2 requires `typescript >=4.8.4 <6.1.0`, so 6.0.3 is used.
- Input: evaluation/raw/T-022.input.json
- Output: `{"all_valid": true, "packages_checked": 24}`
- Interpretation: Source: all names and versions exist.
- Findings: none
- Action: none needed
- Changes: ui/package.json, ui/package-lock.json (72f10c3)
- Notes: Called in parallel with T-023.

##### T-023 | 2026-10-18T07:27Z | phase 5
- Source: MCP sec-review/sca_scan_dependencies
- Why: Server workflow step 2: CVE scan of the 24 direct npm packages.
- Input: evaluation/raw/T-023.input.json
- Output: `{"packages_scanned": 24, "vulnerable_count": 0, "status": "clean", ...}` (evaluation/raw/T-023.output.json)
- Interpretation: Source: no known advisories.
- Findings: none
- Action: none needed
- Changes: none
- Notes: none

##### T-024 | 2026-10-18T07:27Z | phase 5
- Source: MCP sec-review/sca_scan_dependencies
- Why: Cover the transitive npm packages from `npm install` (278 unique name@version pairs, 254 of them transitive), first half.
- Input: evaluation/raw/T-024.input.json (127 packages)
- Output: `{"packages_scanned": 127, "vulnerable_count": 0, "status": "clean", ...}`
- Interpretation: Source: no known advisories.
- Findings: none
- Action: none needed
- Changes: none
- Notes: none

##### T-025 | 2026-10-18T07:27Z | phase 5
- Source: MCP sec-review/sca_scan_dependencies
- Why: Second half of the transitive npm packages.
- Input: evaluation/raw/T-025.input.json (127 packages)
- Output: `{"packages_scanned": 127, "vulnerable_count": 0, "status": "clean", ...}`
- Interpretation: Source: no known advisories for the full resolved UI tree.
- Findings: none
- Action: none needed
- Changes: none
- Notes: none

##### T-026 | 2026-10-18T07:42:08Z | phase 5
- Source: MCP sec-review/general_verify_code_security
- Why: Server workflow step 3 for the UI, with T-021's components.
- Input: evaluation/raw/T-026.input.json
- Output: evaluation/raw/T-026.output.json. Summary: review prompt, 19-item checklist, 12 focus areas; no findings of its own.
- Interpretation: Following the prompt, I reviewed `ui/src` and `ui/views`; the review is in evaluation/raw/T-026.review.md: "Needs Attention (low)". R26-1: separate HMAC keys per purpose. R26-2: the trust-proxy hop count must be 1 behind the ALB. R26-3: in-memory uploads, accepted.
- Findings: F-087, F-088, F-089
- Action: applied (F-087 fixed, F-088 in phase 6/7, F-089 accepted)
- Changes: see findings
- Notes: The checklist again included N/A items (archives, JWT, client storage credentials, parameterized queries for a UI with no database).

##### T-028 | 2026-10-18, between 07:45Z and 07:54Z | phase 6
- Source: Self (user screenshot of the tool status page: "reduce it to only have the working ones")
- Why: After the allow-list (T-020) the page still listed 10 red Codacy tools (Agentlinter, Biome, Eslint-9, Jacksonlinter, Jshint, Markdownlint, Oxlint, Pmd, Pmd-7, Remark-lint) with "Last scan 28 minutes ago", alongside the green ones.
- Input: screenshot (user chat); workflow run status metadata from the public Actions API (`GET .../actions/workflows/codacy.yml/runs`): runs for 36cdbbb (07:22:21Z) and c325100 (07:23:01Z) `completed success` after the allow-list commit de661a6; d752092 in progress.
- Output: n/a
- Interpretation: Source: the post-allow-list runs succeeded. Inferred: the red entries are stale configurations from the 07:12 upload (1afcf28, before the allow-list), matching "Last scan 28 minutes ago". The workflow no longer uploads those tools, but code scanning keeps a configuration until someone deletes it. Deleting requires the repository UI or the code scanning API. I have no credentials for the API, and section 10 rules it out, so no code change can remove them.
- Findings: none
- Action: none needed in code; I told the user how to delete the 10 stale configurations in the UI (tool → configuration menu → Delete configuration)
- Changes: none
- Notes: I did not read any scan results; only run status metadata.

##### T-027 | 2026-10-18T07:45:21Z | phase 6
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 before writing Terraform.
- Input: evaluation/raw/T-027.input.json (components `container-and-iac,secrets-and-config,transport-security,object-storage,database`; data_handled `credentials,secrets,personal_data`)
- Output: evaluation/raw/T-027.output.json. Summary: risk `critical`, 22 threats, 22 countermeasures.
- Interpretation: New relevant requirements: `overbroad-cloud-permissions` / `least-privilege-iam`, and `container-runs-as-root` / `non-root-minimal-images` (for the phase 7 Dockerfiles). The rest restates earlier requirements in an infrastructure context: private data stores, encryption at rest, TLS policy, secrets out of images, least-privilege DB account. Application-level entries (SQL injection, mass assignment, IDOR, password hashing, NoSQL injection) do not apply to Terraform.
- Findings: F-093, F-094
- Action: applied in Terraform (and phase 7 for F-094)
- Changes: infra/ (c85a32c)
- Notes: Logged after T-028 in time order; T-028 was the user's screenshot, which came in while the Terraform was being written.

##### T-029 | 2026-10-18T07:54:21Z | phase 6
- Source: MCP sec-review/general_verify_code_security
- Why: Server workflow step 3 for the Terraform, with T-027's components.
- Input: evaluation/raw/T-029.input.json
- Output: evaluation/raw/T-029.output.json. Summary: review prompt, 17-item checklist, 12 focus areas.
- Interpretation: Following the prompt, I reviewed `infra/`; the review is in evaluation/raw/T-029.review.md: "Needs Attention". R29-1 (medium): `AmazonSSMManagedInstanceCore` grants `ssm:GetParameter*` on `*`, so the UI role could decrypt the API's database and Redis secrets and the operator-only migration password. Found through the checklist item "Grant only the cloud permissions the app uses". R29-2 and R29-3 are low and accepted.
- Findings: F-090, F-091, F-092
- Action: applied (F-090 fixed; F-091/F-092 accepted)
- Changes: see findings
- Notes: Checks run before the review: `terraform fmt -check -recursive` and `terraform init -backend=false` + `terraform validate` both pass. While writing the env I also found and removed a module-level `depends_on` that would have created a dependency cycle at plan time (UI SSM parameters → API internal LB → UI security group). It was replaced by a `config_version` input on the launch templates.

##### T-031 | 2026-10-18, between 07:57Z and 08:11Z | phase 7
- Source: Self (user pasted a Codacy job log excerpt)
- Why: Log shows `Failed analysis for trivy ... codacy-trivy/tool: Failed to configure Codacy Trivy: no patterns configured`, followed by the opengrep, duplication, metrics and jshint steps running.
- Input: pasted log (user chat); workflow run status metadata from the Actions API: d752092, c325100 and 36cdbbb `completed success`; 545e457 (the run the log came from) in progress.
- Output: n/a
- Interpretation: Source: Codacy's bundled Trivy plugin has no pattern configuration without a Codacy project configuration, so it fails. Inferred: this does not fail the job, because earlier runs with the same plugin succeeded. Its output is also not uploaded, since `trivy` is not in `CODACY_TOOLS`. Trivy itself runs in `.github/workflows/trivy.yml`.
- Findings: none
- Action: none needed; explained to the user
- Changes: none
- Notes: none

##### T-030 | 2026-10-18T07:57:01Z | phase 7
- Source: MCP sec-review/general_lightweight_security_review
- Why: Server workflow step 1 before writing Dockerfiles, Compose, Makefile, smoke test, CI and the DB role command.
- Input: evaluation/raw/T-030.input.json (components `container-and-iac,secrets-and-config,database,dependencies`; data_handled `secrets`)
- Output: evaluation/raw/T-030.output.json. Summary: risk `critical`, 20 threats, 20 countermeasures.
- Interpretation: New relative to earlier entries: `hallucinated-package`, `typosquatted-package`, `vulnerable-dependency` (with `verify-packages-exist`, `pin-and-lock-dependencies`, `scan-and-update-dependencies`). Applied: lockfiles committed; frozen installs in Dockerfiles and CI (`uv sync --frozen`, `npm ci --ignore-scripts`); all packages were verified and scanned (T-007–T-009, T-022–T-025). `over-privileged-db-account` (F-062) is implemented in this phase with the `taskboard-admin migrate` role setup. `container-runs-as-root` (F-094): non-root images.
- Findings: F-099, F-100
- Action: applied
- Changes: cad3a6b
- Notes: Logged after T-031 in time order; T-031 was a user-relayed Codacy log handled in between.

##### T-032 | 2026-10-18T08:11Z | phase 7
- Source: MCP sec-review/general_verify_code_security
- Why: Server workflow step 3 for the phase 7 files, with T-030's components.
- Input: evaluation/raw/T-032.input.json
- Output: evaluation/raw/T-032.output.json. Summary: review prompt, 17-item checklist, 12 focus areas. The raw file was written from the response by a script that rebuilt the JSON from its literal field values, rather than retyped by hand. Content is identical; whitespace and key order follow the response.
- Interpretation: Following the prompt, I reviewed the phase 7 files; the review is in evaluation/raw/T-032.review.md: "Secure with minor items". R32-1 (low): CI actions referenced by mutable tags, to be pinned by SHA. R32-2 to R32-4 accepted.
- Findings: F-095, F-096, F-097, F-098
- Action: applied (F-095 fixed; others accepted)
- Changes: see findings
- Notes: Verified before the review: `make up` (Compose via Podman), `make smoke` (SMOKE PASSED), `make lint`, `make typecheck`, `make tf-check`, `make test` (API 118 tests, 96.78% coverage; UI 62 tests, 96.6% lines). Problems found and fixed on the way: Podman OCI builds drop Dockerfile `HEALTHCHECK`, so healthchecks are also declared in Compose; the Makefile test teardown used a relative path after `cd api`; a unit test leaked `MIGRATION_DATABASE_URL` from the integration tests.

##### T-033 | 2026-10-18T08:15:49Z | phase 8
- Source: MCP sec-review/threatmodel_update_threat_model_file
- Why: Bring docs/threat-model.md in line with the finished code: final statuses, code references, and the two threats added during the build (F-077 webhook forgery, F-090 cross-service secret access).
- Input: evaluation/raw/T-033.input.json (content identical to evaluation/raw/T-033.produced.json; `append: false`)
- Output: evaluation/raw/T-033.output.json. `success: true`, `action: created`, `threats_documented: 19`, `references_linked: 36`, `mitigated: 17`, `open: 0`.
- Interpretation: Written as requested, and the file was checked after writing. The tool reports `action: created` although it replaced an existing file. `open: 0` counts only status `open`, and the two `accepted` threats appear in neither counter.
- Findings: none
- Action: applied
- Changes: docs/threat-model.md (6fb7315)
- Notes: Before sending, I corrected TM-17's stale text (`sslmode=require` → `verify-full`, as implemented).

## Part 4: evaluation/findings.md

### Findings

| ID | Raised by | Log entry | Phase | Category | Severity as given by the source | Location | Description | Disposition | Commit | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-001 | MCP-direct:lightweight_security_review | T-002 | 2 | secrets | critical | repo, images, config | hardcoded-secrets: API keys or passwords committed or baked into code. Requirement: all secrets from env/SSM, `.env` git-ignored, `.env.example` placeholders only. | fixed | cad3a6b | No secrets in the repo: .env generated and git-ignored, .env.example placeholders, AWS secrets generated into SSM. |
| F-002 | MCP-direct:lightweight_security_review | T-002 | 2 | authorization | critical | api services | missing-function-authorization: admin/owner functions callable because only the UI hides them. Requirement: role/ownership checks in API services. | fixed | 20eda4e |  |
| F-003 | MCP-direct:lightweight_security_review | T-002 | 2 | authentication | critical | api password hashing | weak-password-storage. Requirement: Argon2id. | fixed | 20eda4e |  |
| F-004 | MCP-direct:lightweight_security_review | T-002 | 2 | transport | high | infra (ALB, RDS, ElastiCache), UI-to-API hop | cleartext-transport. Requirement: HTTPS at the ALB with redirect, TLS to RDS and ElastiCache. | mitigated | c85a32c | UI-to-API HTTP inside private subnets is a candidate accepted risk (TM-17). ALB TLS 1.2+ with HTTP->HTTPS redirect, RDS verify-full, ElastiCache TLS required, S3 TLS-only. Accepted: UI->internal ALB->API is HTTP inside private subnets restricted by security groups (TM-17). |
| F-005 | MCP-direct:lightweight_security_review | T-002 | 2 | authentication | high | api login | credential-stuffing. Requirement: throttle login failures per account and per IP. | fixed | 20eda4e, ff86f21 | Per-IP and per-account-failure limits in AuthService; lockout scope corrected by F-070. |
| F-006 | MCP-direct:lightweight_security_review | T-002 | 2 | configuration | high | api/ui config | debug-mode-in-production. Requirement: no debug mode; OpenAPI docs and verbose errors off by default outside dev. | fixed | f0784c3, 72f10c3 | API: docs UI removed and OpenAPI behind service auth (f0784c3, F-071); ENVIRONMENT defaults to production. UI pending. UI: NODE_ENV defaults to production, x-powered-by off, generic error pages. |
| F-007 | MCP-direct:lightweight_security_review | T-002 | 2 | authentication | high | api management command | default-accounts. Requirement: no preset admin; first admin from env vars at setup. | fixed | 20eda4e |  |
| F-008 | MCP-direct:lightweight_security_review | T-002 | 2 | configuration | high | Dockerfiles, UI static serving | exposed-config-files. Requirement: `.dockerignore` excludes `.git`, `.env`; static dir contains only assets. | fixed | cad3a6b | Allow-list .dockerignore files; UI static serves only public/ with dotfiles denied. |
| F-009 | MCP-direct:lightweight_security_review | T-002 | 2 | cryptography | high | config | hardcoded-crypto-keys. Requirement: per-environment cookie/CSRF and service secrets from config, no defaults. | fixed | 20eda4e | Service, webhook and (later) cookie secrets come from env with min length 32 and no defaults. |
| F-010 | MCP-direct:lightweight_security_review | T-002 | 2 | authentication | high | api password reset | insecure-password-reset. Requirement: random single-use short-lived token, same response for unknown emails. | fixed | 20eda4e |  |
| F-011 | MCP-direct:lightweight_security_review | T-002 | 2 | session | high | n/a | jwt-tampering: forged or unsigned JWTs accepted. | out of scope | | Not applicable: design uses opaque random session tokens checked against the database, no JWTs. |
| F-012 | MCP-direct:lightweight_security_review | T-002 | 2 | authorization | high | api services | object-id-guessing (IDOR). Requirement: check team membership for every object; 404 on mismatch. | fixed | 20eda4e |  |
| F-013 | MCP-direct:lightweight_security_review | T-002 | 2 | cryptography | high | api tokens | predictable-tokens. Requirement: `secrets.token_urlsafe` / `crypto.randomBytes`. | fixed | 20eda4e |  |
| F-014 | MCP-direct:lightweight_security_review | T-002 | 2 | authorization | high | api schemas | role-self-assignment / mass-assignment. Requirement: explicit request schemas with `extra="forbid"`; role only via admin endpoint. | fixed | 20eda4e | Also covers `also_consider: mass-assignment`. |
| F-015 | MCP-direct:lightweight_security_review | T-002 | 2 | containers | high | Dockerfiles | secrets-baked-into-image. Requirement: no secrets in images or build args. | fixed | cad3a6b | Terraform passes no secrets to images or user_data; Dockerfiles in phase 7. No secrets in Dockerfiles, build args or images; runtime env only. |
| F-016 | MCP-direct:lightweight_security_review | T-002 | 2 | session | high | api login, ui cookie | session-fixation. Requirement: new session token on every login, old one discarded. | fixed | 20eda4e, 72f10c3 | UI replaces the cookie on every login and logs out the previous session. |
| F-017 | MCP-direct:lightweight_security_review | T-002 | 2 | authorization | high | api repositories | tenant-data-leak. Requirement: team scoping applied in one place for list/search queries. | fixed | 20eda4e |  |
| F-018 | MCP-direct:lightweight_security_review | T-002 | 2 | agent | medium | coding-agent environment | agent-reads-secrets. | out of scope | | Concerns the coding agent's own permissions, not the product. No real secrets exist in this repo. |
| F-019 | MCP-direct:lightweight_security_review | T-002 | 2 | session | medium | ui forms | csrf. Requirement: SameSite cookies plus anti-forgery tokens on state-changing requests. | fixed | 72f10c3 |  |
| F-020 | MCP-direct:lightweight_security_review | T-002 | 2 | session | medium | ui cookies | insecure-cookie-flags. Requirement: Secure, HttpOnly, SameSite, `__Host-` prefix. | fixed | 72f10c3 |  |
| F-021 | MCP-direct:lightweight_security_review | T-002 | 2 | authentication | medium | accounts | no-second-factor (offer-mfa). | accepted risk | | Not in the brief's functional scope; recorded in DECISIONS. |
| F-022 | MCP-direct:lightweight_security_review | T-002 | 2 | transport | medium | infra ALB | outdated-tls. Requirement: TLS 1.2+ policy on the ALB listener. | fixed | c85a32c | ALB HTTPS listener uses ELBSecurityPolicy-TLS13-1-2-2021-06. |
| F-023 | MCP-direct:lightweight_security_review | T-002 | 2 | email | medium | api reset links | poisoned-email-links. Requirement: build links from configured base URL. | fixed | 20eda4e |  |
| F-024 | MCP-direct:lightweight_security_review | T-002 | 2 | session | medium | api sessions | sessions-not-ended. Requirement: server-side invalidation on logout, password change/reset, deactivation. | fixed | 20eda4e, 72f10c3 | UI logout calls the API logout before clearing the cookie. |
| F-025 | MCP-direct:lightweight_security_review | T-002 | 2 | session | medium | api sessions | token-claims-unchecked. Requirement: reject expired session tokens. | fixed | 20eda4e | Audience/issuer checks not applicable to opaque tokens; expiry check applies. |
| F-026 | MCP-direct:lightweight_security_review | T-002 | 2 | session | medium | reset link, ui | tokens-leak-via-url-or-storage. Requirement: tokens in headers/bodies, not URLs or browser storage. | fixed | 20eda4e, 72f10c3 | The reset link must carry its token in the URL; mitigate with `Referrer-Policy: no-referrer` and moving it into a POST body. API: reset token only in POST body to API; UI must apply Referrer-Policy no-referrer on the reset page. UI: Referrer-Policy no-referrer on every page, reset token posted in body, access log omits query strings. |
| F-027 | MCP-direct:lightweight_security_review | T-002 | 2 | authentication | medium | api password policy | weak-password-rules. Requirement: length-based rules ("15 or more is better"), allow long passphrases. | mitigated | 20eda4e | Planned minimum 12, maximum 128. Implemented 12..128 chars, no composition rules; tool suggested 15+ (ADR-004). |
| F-028 | MCP-direct:lightweight_security_review | T-002 | 2 | logging | low | api | no-security-logging. Requirement: log logins, failures, permission denials, admin actions. | fixed | 20eda4e |  |
| F-029 | MCP-direct:lightweight_security_review | T-002 | 2 | authentication | low | api login/forgot/register | user-enumeration. Requirement: same response for unknown and wrong credentials. | mitigated | 20eda4e | Login and forgot-password do not reveal accounts; register returns 409 for an existing email (accepted). |
| F-030 | MCP-direct:lightweight_security_review | T-002 | 2 | api | medium | api responses | also_consider excessive-data-exposure. Requirement: response schemas never include hashes or token values. | fixed | 20eda4e |  |
| F-031 | MCP-direct:lightweight_security_review | T-002 | 2 | api | medium | api inputs | also_consider missing-input-validation. Requirement: Pydantic validation with bounds on every input. | fixed | 20eda4e |  |
| F-032 | MCP-direct:lightweight_security_review | T-002 | 2 | api | medium | api auth endpoints | also_consider missing-rate-limit. | fixed | 20eda4e | Same mechanism as F-005, also applied to forgot-password and register. |
| F-033 | MCP-direct:lightweight_security_review | T-002 | 2 | web | medium | ui redirects | also_consider open-redirect. Requirement: post-login redirect target limited to local paths. | fixed | 72f10c3 |  |
| F-034 | MCP-direct:lightweight_security_review | T-002 | 2 | web | medium | api/ui | also_consider permissive-cors. Requirement: no CORS on either service (same-origin UI, internal API). | fixed | 20eda4e, 72f10c3 | Neither service sets CORS headers. |
| F-035 | MCP-direct:lightweight_security_review | T-002 | 2 | errors | medium | api/ui error handlers | also_consider verbose-errors. Requirement: generic error with request id; details only in logs. | fixed | 20eda4e | Generic 500 with request id; one error shape. |
| F-036 | MCP-direct:lightweight_security_review | T-002 | 2 | business logic | medium | password reset flow | also_consider business-flow-bypass. Requirement: reset token single-use, checked server-side. | fixed | 20eda4e |  |
| F-037 | MCP-direct:lightweight_security_review | T-002 | 2 | transport | high | all services | https-everywhere countermeasure: HTTPS for every connection incl. service-to-service. | mitigated | c85a32c | Overlaps F-004. Same as F-004. |
| F-038 | MCP-direct:perform_threat_model | T-003 | 2 | ssrf | high | api webhook notifier | ssrf: server tricked into fetching internal addresses or cloud metadata via webhook URL. Requirement: block private/loopback/link-local/metadata, no redirects. | fixed | 20eda4e |  |
| F-039 | MCP-direct:perform_threat_model | T-003 | 2 | xss | high | ui markdown rendering | stored-xss through Markdown descriptions and comments. Requirement: sanitize rendered HTML with an allow-list; autoescape elsewhere. | fixed | 72f10c3 |  |
| F-040 | MCP-direct:perform_threat_model | T-003 | 2 | transport | high | api webhook notifier | tls-verification-disabled. Requirement: never disable certificate verification on outbound calls. | fixed | 20eda4e |  |
| F-041 | MCP-direct:perform_threat_model | T-003 | 2 | file upload | high | attachments | upload-executable-file. Requirement: never execute or serve uploads from a web root. | fixed | 20eda4e |  |
| F-042 | MCP-direct:perform_threat_model | T-003 | 2 | file upload | high | attachment storage | upload-path-traversal via filename. Requirement: server-generated storage keys. | fixed | 20eda4e |  |
| F-043 | MCP-direct:perform_threat_model | T-003 | 2 | file upload | medium | attachment download | upload-active-content (HTML/SVG executes when opened). Requirement: Content-Disposition attachment, nosniff. | fixed | 20eda4e |  |
| F-044 | MCP-direct:perform_threat_model | T-003 | 2 | file upload | medium | ui + api upload | upload-resource-exhaustion. Requirement: per-file size limit. | fixed | 20eda4e, 72f10c3 | API side: body-size middleware + byte counter. UI multer limit added in phase 5. UI multer limit: 1 file, MAX_UPLOAD_BYTES. |
| F-045 | MCP-direct:perform_threat_model | T-003 | 2 | resilience | low | webhook notifier | no-timeouts-or-size-caps on outbound calls. | fixed | 20eda4e, 1166fa7 | 3s timeouts, 64 KiB response cap; overall attempt deadline added by F-073. |
| F-046 | MCP-direct:perform_threat_model | T-003 | 2 | file upload | high | attachments | archive-path-traversal. | out of scope | | The app never extracts uploaded archives. |
| F-047 | MCP-direct:perform_threat_model | T-003 | 2 | file upload | none given | attachments | upload-allow-list countermeasure: allow only needed file types. | accepted risk | | Conflicts with brief 4.4 ("any type"). Mitigated instead by F-043 safe serving. |
| F-048 | MCP-prompted:perform_threat_model | T-003 | 2 | injection | none given | api search | Client-supplied sort field could reach ORDER BY as raw SQL; free-text LIKE patterns could be concatenated (TM-12). Requirement: enum-mapped columns, bound params, escaped wildcards. | fixed | 20eda4e |  |
| F-049 | MCP-prompted:perform_threat_model | T-003 | 2 | injection | none given | api CSV export | CSV formula injection from task fields (TM-13). Requirement: neutralise cells starting with `= + - @ \t \r`. | fixed | 20eda4e |  |
| F-050 | MCP-prompted:perform_threat_model | T-003 | 2 | authorization | none given | api cache | Cached lists/details served after membership removal, or cache read before authz (TM-14). Requirement: authz before cache, invalidate per-user lists on membership change, JSON values only. | fixed | 01111f5, 939a161 | Cache built: team/project/task-list reads authorize against the DB first; task detail authorizes after the cached read; profile role issue found in F-080. |
| F-051 | MCP-prompted:perform_threat_model | T-003 | 2 | logging | none given | api dev mailer | Reset links (tokens) written to the API log because the brief requires emails in the log (TM-15). | accepted risk | 20eda4e | Required by brief 4.1; a real mailer would replace the log mailer in production. |
| F-052 | MCP-prompted:perform_threat_model | T-003 | 2 | authentication | none given | api auth dependency | Forged identity from another process on the internal network (TM-10). Requirement: identity only from DB-validated session token; UI also proves itself with a service token compared in constant time. | fixed | 20eda4e |  |
| F-053 | MCP-prompted:perform_threat_model | T-003 | 2 | injection | none given | api/ui download | Original filename with CR/LF or quotes echoed into Content-Disposition (TM-6). Requirement: strip control chars, RFC 5987 `filename*`. | fixed | 20eda4e |  |
| F-054 | MCP-direct:lightweight_security_review | T-010 | 3 | injection | critical | api repositories | sql-injection. Requirement: parameterized queries / ORM only. | fixed | 20eda4e | Overlaps F-048 (sort field). |
| F-055 | MCP-direct:lightweight_security_review | T-010 | 3 | payments | critical | n/a | card-data-in-your-systems. | false positive | | No payment component or payment data was given, and Taskboard handles no card data. |
| F-056 | MCP-direct:lightweight_security_review | T-010 | 3 | injection | high | n/a | nosql-injection. | false positive | | The only datastore queried with user input is PostgreSQL via SQLAlchemy. Redis keys are built from UUIDs and hashes, never from raw input. |
| F-057 | MCP-direct:lightweight_security_review | T-010 | 3 | infrastructure | high | infra, compose | exposed-data-store: DB/cache reachable from the internet. Requirement: private subnets and SGs; Compose publishes no DB/Redis ports. | fixed | c85a32c | RDS/ElastiCache in data subnets without internet routes, SGs from the API SG only; Compose publishes only the UI port (phase 7). |
| F-058 | MCP-direct:lightweight_security_review | T-010 | 3 | cryptography | high | infra RDS/S3 | sensitive-data-unencrypted. Requirement: encryption at rest (RDS storage encryption, S3 SSE, ElastiCache at-rest). | fixed | c85a32c | Raised again in T-011. CMK encryption for RDS, Performance Insights, ElastiCache, S3, ECR, SSM parameters and log groups. |
| F-059 | MCP-direct:lightweight_security_review | T-010 | 3 | cryptography | high | api | weak-crypto-algorithms. Requirement: SHA-256+ / HMAC-SHA256 only; no MD5/SHA-1. | fixed | 20eda4e |  |
| F-060 | MCP-direct:lightweight_security_review | T-010 | 3 | email | medium | api mailer | email-header-injection. Requirement: reject CR/LF in subject and address values. | fixed | 20eda4e |  |
| F-061 | MCP-direct:lightweight_security_review | T-010 | 3 | email | medium | api forgot-password | email-abuse. Requirement: rate-limit send endpoints. | fixed | 20eda4e | Same limiter as F-005/F-032. |
| F-062 | MCP-direct:lightweight_security_review | T-010 | 3 | database | medium | infra/compose DB users | over-privileged-db-account. Requirement: app connects as a least-privilege DB user; migrations as owner. | fixed | cad3a6b | taskboard-admin migrate creates taskboard_app with DML-only grants (no DDL, no alembic_version); the API connects as it in Compose and AWS; integration-tested. |
| F-063 | MCP-direct:lightweight_security_review | T-010 | 3 | logging | medium | api/ui logging | secrets-in-logs. Requirement: never log passwords, session tokens, request bodies. | mitigated | 20eda4e | Reset links are the accepted exception (F-051). No passwords/tokens/bodies logged; reset emails logged per brief (F-051). |
| F-064 | MCP-direct:lightweight_security_review | T-010 | 3 | headers | low | api/ui responses | missing-security-headers. Requirement: HSTS, CSP with frame-ancestors, nosniff, referrer policy. | fixed | 20eda4e, 72f10c3 | API sets nosniff, X-Frame-Options DENY, CSP default-src none, no-referrer, no-store (20eda4e). UI headers pending. UI: helmet CSP (script-src none, frame-ancestors none), HSTS when secure, nosniff, no-referrer. |
| F-065 | MCP-direct:lightweight_security_review | T-011 | 3 | storage | high | infra S3 | public-bucket. Requirement: S3 Block Public Access, private bucket, no public ACLs. | fixed | c85a32c | Block Public Access, BucketOwnerEnforced, TLS-only and KMS-only bucket policy. |
| F-066 | MCP-direct:lightweight_security_review | T-011 | 3 | storage | high | n/a | long-lived-storage-credentials shipped to clients. | out of scope | | No client receives storage credentials. The API uses the instance role, and downloads stream through API and UI. |
| F-067 | MCP-direct:lightweight_security_review | T-011 | 3 | background job | medium | webhook notifier | untrusted-job-payload. Requirement: validate job payloads. | fixed | 20eda4e | The job is built in-process from a typed dataclass; the URL is re-validated before each send. |
| F-068 | MCP-direct:lightweight_security_review | T-011 | 3 | background job | low | webhook notifier | runaway-retries. Requirement: bounded retries with backoff. | fixed | 20eda4e |  |
| F-069 | self | T-016 | 3 | data exposure | none given | api `services/projects.py`, `services/teams.py` | Project responses returned `webhook_url` to every team member; webhook URLs often embed secrets (e.g. chat incoming-webhook tokens). | fixed | 20eda4e | Found while writing ProjectService, before the baseline commit; redaction for non-owners/non-admins in the service layer. |
| F-070 | MCP-prompted:lightweight_security_review | T-014 | 3 | authentication | Medium (mine) | api `services/auth.py` login | Login lockout keyed by email only lets anyone lock a victim out (lockout as DoS), which the T-002 `login-attempt-limits` countermeasure warns against. | fixed | ff86f21 | Found during the T-014 review (R14-1); the criterion comes from T-002's countermeasure text. |
| F-071 | MCP-prompted:verify_code_security | T-014 | 3 | configuration | Low (mine) | api `main.py` | OpenAPI document served without the service token (outside the authenticated router). | fixed | f0784c3, cd644cf | R14-2, checklist item "Turn debug features off in production". |
| F-072 | MCP-prompted:verify_code_security | T-015 | 3 | resource exhaustion | Low (mine) | api `infra/webhooks/notifier.py` | Unbounded webhook delivery backlog in the executor queue. | fixed | 1166fa7 | R15-2. |
| F-073 | MCP-prompted:lightweight_security_review | T-015 | 3 | resource exhaustion | Low (mine) | api `infra/webhooks/notifier.py` | Per-read timeouts only; a slow-drip receiver holds a worker far longer than the timeout. | fixed | 1166fa7 | R15-3, against T-011's `timeouts-and-size-caps` countermeasure. |
| F-074 | MCP-prompted:verify_code_security | T-014 | 3 | resource exhaustion | Low (mine) | api `api/middleware.py` | All routes accept ~10 MB bodies, not just the upload route. | fixed | 5f3c954 | R14-3, checklist item "Validate all input on the server". |
| F-075 | MCP-prompted:lightweight_security_review | T-014 | 3 | authentication | Low (mine) | api `services/auth.py` change_password | Current-password check on password change not throttled. | fixed | 66a03ee | R14-4, against T-010's `rate-limiting` countermeasure. |
| F-076 | MCP-direct:lightweight_security_review | T-010 | 3 | rate limiting | medium | api upload and search endpoints | `rate-limiting` countermeasure lists upload and search endpoints; these have no per-user rate limit. | accepted risk | 20eda4e | Authenticated internal users only. Uploads are size-capped and searches are paginated and indexed. |
| F-077 | self | T-015 | 3 | integrity | Medium (mine) | api `infra/webhooks/notifier.py` | Webhook signatures use one deployment-wide secret that receivers cannot be given without enabling cross-project forgery, so the signature protects nothing. | fixed | 02101da | R15-1. My own analysis during the T-015 review; not on the tool's checklist. |
| F-078 | self | T-014 | 3 | resource exhaustion | Low (mine) | api sessions repository | Expired session rows are never purged. | fixed | 7c5540e | R14-5. |
| F-079 | MCP-prompted:verify_code_security | T-015 | 3 | file upload | none given | attachment download | Checklist recommends serving user files from a separate domain; downloads come from the UI origin. | accepted risk | 20eda4e | Mitigated by `Content-Disposition: attachment`, `application/octet-stream`, `nosniff` and `Content-Security-Policy: sandbox` on every download. |
| F-080 | MCP-prompted:verify_code_security | T-019 | 4 | authorization | Medium (mine) | api `services/auth.py` authenticate | Cache-aside race: a profile read before a demotion commits can be written back after invalidation, so a demoted admin keeps admin rights for up to the cache TTL. Violates TM-14 / F-050. | fixed | 939a161 | R19-1. Session query joins users for role/is_active; cached profile supplies display fields only; regression test test_stale_cached_role_never_grants_access. |
| F-081 | MCP-prompted:verify_code_security | T-019 | 4 | authorization | Low (mine) | api team/project list caches | The same race lets a just-removed member see the team's and its projects' names in their own lists for up to the TTL. | accepted risk | 01111f5 | R19-2. Names only, ≤300 s, and every access to the team or project is checked against the DB. |
| F-082 | MCP-prompted:verify_code_security | T-019 | 4 | data protection | Low (mine) | Redis cache values | Cached project lists include webhook URLs (which may embed secrets) in Redis. | fixed | c85a32c | R19-3. To be mitigated with ElastiCache encryption at rest and in transit plus auth (phase 6). ElastiCache at-rest (CMK) and in-transit (required) encryption with an auth token. |
| F-083 | MCP-prompted:verify_code_security | T-019 | 4 | resource exhaustion | Low (mine) | `CacheKeys.task_list` | Each distinct filter combination creates its own cache key, so a user can create many keys. | fixed | 01111f5, c85a32c | R19-4. Bounded by TTL; LRU eviction policy on ElastiCache in phase 6. TTL on every key plus allkeys-lru on ElastiCache. |
| F-084 | MCP-direct:lightweight_security_review | T-017 | 4 | deserialization | critical | api cache values | unsafe-deserialization: cached values must not be deserialized with code-executing formats. | fixed | 01111f5 | JSON only via Pydantic `TypeAdapter`; malformed entries are discarded (unit test `test_malformed_entries_are_discarded`). |
| F-085 | MCP-direct:lightweight_security_review | T-021 | 5 | xss | high | ui views | dom-xss: frontend code writes untrusted data with unsafe DOM APIs. | fixed | 72f10c3 | Planned: no client-side JavaScript in the UI at all. |
| F-086 | MCP-direct:lightweight_security_review | T-021 | 5 | supply chain | medium | ui views | third-party-script-compromise: compromised CDN script runs in pages. | fixed | 72f10c3 | Planned: no third-party scripts, styles or fonts; CSP `'self'` only. |
| F-087 | self | T-026 | 5 | cryptography | Low (mine) | ui `src/app.ts` | One `COOKIE_SECRET` keys both cookie-parser signing and the CSRF HMAC; per-purpose keys are safer. | fixed | 4ef53a7 | R26-1. Found during the T-026 review; not a checklist item. |
| F-088 | self | T-026 | 5 | configuration | Low (mine) | ui `TRUST_PROXY_HOPS`, deployment | A wrong trust-proxy hop count behind the ALB either collapses per-IP rate limits into one global bucket (lockout DoS) or lets clients spoof their IP. | fixed | c85a32c | R26-2. Must be 1 behind the ALB. TRUST_PROXY_HOPS=1 in the UI's SSM config in AWS; 0 (default) in Compose. |
| F-089 | MCP-prompted:verify_code_security | T-026 | 5 | resource exhaustion | Low (mine) | ui `TaskController` multer memoryStorage | Uploads (≤10 MB each) are buffered in UI memory. | accepted risk | 72f10c3 | R26-3. Only after the session guard; 1 file; 10 MB cap; API re-checks size. |
| F-090 | MCP-prompted:verify_code_security | T-029 | 6 | iam | Medium (mine) | infra `modules/iam` | `AmazonSSMManagedInstanceCore` grants `ssm:GetParameter*` on `*`; with SSM-scoped `kms:Decrypt`, the UI role could read the API's DB/Redis secrets and the migration password. | fixed | cab2611 | R29-1. |
| F-091 | self | T-029 | 6 | monitoring | Low (mine) | infra `modules/alb`, `modules/storage` | No WAF on the public ALB; ALB and S3 access logging off by default. | accepted risk | c85a32c | R29-2. Access logging is a per-environment variable; ingress can be narrowed via `allowed_ingress_cidrs`. |
| F-092 | self | T-029 | 6 | secrets | Low (mine) | infra `envs/dev/secrets.tf` | Generated secrets are stored in Terraform state. | accepted risk | c85a32c | R29-3. Encrypted, access-restricted S3 backend; RDS master password stays in Secrets Manager. |
| F-093 | MCP-direct:lightweight_security_review | T-027 | 6 | iam | high | infra `modules/iam` | overbroad-cloud-permissions: roles must grant only what each service uses. | fixed | c85a32c, cab2611 | Per-service roles, scoped resources; see F-090 for the gap found in review. |
| F-094 | MCP-direct:lightweight_security_review | T-027 | 6 | containers | medium | Dockerfiles, user_data | container-runs-as-root. Requirement: non-root user, minimal base, dropped capabilities. | fixed | cad3a6b | user_data already runs `--cap-drop ALL --security-opt no-new-privileges --read-only`; non-root USER in phase 7 Dockerfiles. API image runs as uid 10001, UI as node; read_only, cap_drop ALL, no-new-privileges in Compose and user_data. |
| F-095 | MCP-prompted:verify_code_security | T-032 | 7 | supply chain | Low (mine) | `.github/workflows/ci.yml` | GitHub-owned actions referenced by mutable major tags. | fixed | d4a7faf | R32-1. |
| F-096 | self | T-032 | 7 | supply chain | Low (mine) | Dockerfiles, Compose, CI | Base images pinned by tag, not digest. | accepted risk | cad3a6b | R32-2. Exact patch tags per the brief. |
| F-097 | self | T-032 | 7 | secrets | Low (mine) | `docker-compose.test.yml`, `ci.yml` | Fixed throwaway credentials for test databases. | accepted risk | cad3a6b | R32-3. Loopback/CI-only, tmpfs data. |
| F-098 | self | T-032 | 7 | secrets | Low (mine) | `docker-compose.yml` redis | Dev Redis password visible in the container command line. | accepted risk | cad3a6b | R32-4. Local only; ElastiCache uses auth token + TLS. |
| F-099 | MCP-direct:lightweight_security_review | T-030 | 7 | supply chain | high | dependencies | hallucinated-package / typosquatted-package: packages must exist and be the intended ones. | fixed | cad3a6b | Every direct and transitive package verified/scanned (T-007–T-009, T-022–T-025); lockfiles committed. |
| F-100 | MCP-direct:lightweight_security_review | T-030 | 7 | supply chain | high | dependencies | vulnerable-dependency: pin, lock and scan dependencies. | fixed | cad3a6b | Frozen installs in Docker and CI; OSV scans clean; the Trivy workflow scans lockfiles continuously. |

## Part 5: evaluation/suppressions.md

### Suppressions

Inline suppression comments and rule-silencing configuration added during the build.

| File | Line | Rule | Reason |
| --- | --- | --- | --- |
| `api/pyproject.toml` | `[tool.ruff.lint.per-file-ignores]` | ruff `S101` (assert used) for `tests/**` | pytest's assertion idiom is `assert`; the flake8-bandit rule set is enabled for application code, where `assert` would be a real problem. Scoped to tests only. |
| `api/pyproject.toml` | `[tool.ruff.lint.per-file-ignores]` | ruff `S105`, `S106` (hard-coded password) for `tests/**` | Tests use fixed dummy passwords such as `correct-horse-battery` to drive the auth flows. Scoped to tests only. |
| `ui/eslint.config.mjs` | `files: ['eslint.config.mjs']` block | typescript-eslint type-checked rules, via `tseslint.configs.disableTypeChecked`, for the ESLint config file only | The config file is plain JavaScript outside the TypeScript project; typescript-eslint documents this override as the way to lint such files. All `.ts` sources keep the full `strictTypeChecked` set. |
| `.codacy.yml` | `exclude_paths` | Codacy analysis of `**/node_modules/**`, `**/dist/**`, `**/coverage/**`, `**/.terraform/**`, `**/package-lock.json`, `**/uv.lock`, `**/.terraform.lock.hcl` | Added at the user's request to correct the Codacy configuration (tool-log T-018). These paths are generated, vendored or machine-written lockfiles. Dependency vulnerabilities in the lockfiles are still scanned by the Trivy workflow (`trivy-repository`). `evaluation/**` was already excluded by the brief. |
| `.github/workflows/codacy.yml` | step "Prepare SARIF for code scanning", `CODACY_TOOLS` | Codacy results from agentlinter, biome, eslint-9, jacksonlinter, jshint, markdownlint, oxlint, pmd, pmd-7 and remark-lint are not uploaded to code scanning | The user asked to reduce Codacy to usable tools (tool-log T-020). These tools showed execution errors on the code scanning tool status page, because they do not apply to the stack (PMD is for Java) or cannot run against this repo's setup. ESLint and type checks run in CI; CodeQL, Semgrep and Trivy also scan the JS/TS code. |

## Part 6: evaluation/raw/

The raw files, in log-entry order: input, output, produced document, then review.

### evaluation/raw/T-001.input.json

```json
{
  "tool": "mcp__sec-review__general_lightweight_security_review",
  "arguments": {
    "task_description": "Build Taskboard, an internal team task tracker. Two services: a Python 3.13 FastAPI REST API (/api/v1, OpenAPI) that is the only component talking to PostgreSQL 16, Redis 7 (cache-aside cache) and attachment storage (local filesystem in dev, Amazon S3 in AWS); and a Node.js 24 Express 5 + EJS UI server that renders pages, authenticates browser users and calls the API over an internal network. Features: register/login/logout with email+password, change password, forgot-password reset links (emails written to log and an outbox table), first admin created by a management command from env vars, admin user management (roles admin/member, deactivate/reactivate). Teams with owners and members added by email; projects inside teams (archive = read-only) with an optional outbound webhook URL that receives an async JSON POST with retry when a task changes status. Tasks with Markdown descriptions rendered as HTML, comments (Markdown), file attachments of any type up to 10 MB with download by original filename. Search across visible projects with free text, filters, client-supplied sort field and direction, pagination. CSV export of a project's tasks. Activity feed per project and global for admins. Deployed to AWS EC2 behind an ALB with Terraform (VPC, private subnets, RDS, ElastiCache, S3, ECR, IAM), Docker images bootstrapped via user_data.",
    "technologies": "Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, redis-py, PostgreSQL 16, Redis 7, Node.js 24, TypeScript, Express 5, EJS, Docker, Terraform, AWS EC2, ALB, RDS, ElastiCache, S3"
  }
}
```

### evaluation/raw/T-001.output.json

```json
{"success":true,"review_type":"lightweight_pre_coding","status":"needs_components","task_description":"Build Taskboard, an internal team task tracker. Two services: a Python 3.13 FastAPI REST API (/api/v1, OpenAPI) that is the only component talking to PostgreSQL 16, Redis 7 (cache-aside cache) and attachment storage (local filesystem in dev, Amazon S3 in AWS); and a Node.js 24 Express 5 + EJS UI server that renders pages, authenticates browser users and calls the API over an internal network. Features: register/login/logout with email+password, change password, forgot-password reset links (emails written to log and an outbox table), first admin created by a management command from env vars, admin user management (roles admin/member, deactivate/reactivate). Teams with owners and members added by email; projects inside teams (archive = read-only) with an optional outbound webhook URL that receives an async JSON POST with retry when a task changes status. Tasks with Markdown descriptions rendered as HTML, comments (Markdown), file attachments of any type up to 10 MB with download by original filename. Search across visible projects with free text, filters, client-supplied sort field and direction, pagination. CSV export of a project's tasks. Activity feed per project and global for admins. Deployed to AWS EC2 behind an ALB with Terraform (VPC, private subnets, RDS, ElastiCache, S3, ECR, IAM), Docker images bootstrapped via user_data.","instructions":"Choose the components this change adds or directly modifies (usually 2 to 5), then call this tool again with the same task_description and components set to their ids (comma-separated). Parts of the app this change does not touch are out of scope, and components that always come with a pick are added for you. Add data_handled if the feature touches sensitive data.","components":[{"id":"web-endpoint","name":"Web or API endpoint","applies_when":"The feature adds or changes an HTTP route, API, or form handler."},{"id":"authentication","name":"Login and account management","applies_when":"Users sign up, log in, reset passwords, or use MFA."},{"id":"session-management","name":"Sessions and tokens","applies_when":"The app keeps users logged in with cookies, session ids, or JWTs."},{"id":"authorization","name":"Permissions and data access","applies_when":"Different users, roles, or tenants must see or change different data."},{"id":"database","name":"Database","applies_when":"The feature reads or writes SQL or NoSQL data."},{"id":"file-upload","name":"File upload","applies_when":"Users send files to the app (avatars, attachments, CSV imports)."},{"id":"object-storage","name":"Object or file storage","applies_when":"Files or blobs are stored in S3, GCS, Azure Blob, or on disk."},{"id":"outbound-http-request","name":"Outbound HTTP calls","applies_when":"The server fetches URLs or calls other services, especially with user-supplied addresses."},{"id":"third-party-webhook","name":"Incoming webhooks","applies_when":"An external service (Stripe, GitHub, Slack) sends events to an endpoint of yours."},{"id":"payment-flow","name":"Payments and orders","applies_when":"The feature handles prices, checkout, subscriptions, refunds, or balances."},{"id":"secrets-and-config","name":"Secrets and configuration","applies_when":"The feature uses API keys, passwords, tokens, environment variables, or config files."},{"id":"cryptography","name":"Cryptography","applies_when":"The feature encrypts, hashes, or signs data, or generates keys or random values."},{"id":"transport-security","name":"HTTPS and TLS","applies_when":"The app serves HTTPS, terminates TLS, or sends data between services over a network."},{"id":"user-generated-content","name":"User-generated content","applies_when":"The app stores or shows text, HTML, markdown, or images that users wrote or supplied."},{"id":"browser-frontend","name":"Browser frontend","applies_when":"JavaScript runs in the browser, handles tokens or user data, or loads third-party scripts."},{"id":"background-job","name":"Background jobs and queues","applies_when":"Work runs in workers, cron jobs, or queues outside the request."},{"id":"serialization-and-parsing","name":"Parsing and deserialization","applies_when":"The app parses XML, YAML, pickle, archives, or other structured input from outside."},{"id":"shell-and-dynamic-code","name":"OS commands and dynamic code","applies_when":"The app runs shell commands, subprocesses, eval, or builds templates from input."},{"id":"email-sending","name":"Email and notifications","applies_when":"The app sends email, SMS, or push messages, or builds links for them."},{"id":"dependencies","name":"Packages and dependencies","applies_when":"New libraries are added or updated (pip, npm, and so on)."},{"id":"container-and-iac","name":"Containers and infrastructure code","applies_when":"Dockerfiles, Kubernetes, Terraform, or cloud permissions are written or changed."},{"id":"logging-and-errors","name":"Logging and error handling","applies_when":"The feature logs data or shows or returns error messages."},{"id":"llm-integration","name":"LLM calls","applies_when":"The app sends user or document content to a language model and uses the reply."},{"id":"agent-tools","name":"AI agent with tools","applies_when":"An AI agent can run commands, read files, browse, or call tools or MCP servers."},{"id":"coding-agent-setup","name":"Coding agent configuration","applies_when":"MCP servers, hooks, skills, plugins, or permission rules for a coding agent are added or changed."}],"data_handled_options":["credentials","payments","personal_data","health_data","secrets"]}
```

### evaluation/raw/T-002.input.json

```json
{
  "tool": "mcp__sec-review__general_lightweight_security_review",
  "arguments": {
    "task_description": "Build Taskboard, an internal team task tracker. Two services: a Python 3.13 FastAPI REST API (/api/v1, OpenAPI) that is the only component talking to PostgreSQL 16, Redis 7 (cache-aside cache) and attachment storage (local filesystem in dev, Amazon S3 in AWS); and a Node.js 24 Express 5 + EJS UI server that renders pages, authenticates browser users and calls the API over an internal network. Features: register/login/logout with email+password, change password, forgot-password reset links (emails written to log and an outbox table), first admin created by a management command from env vars, admin user management (roles admin/member, deactivate/reactivate). Teams with owners and members added by email; projects inside teams (archive = read-only) with an optional outbound webhook URL that receives an async JSON POST with retry when a task changes status. Tasks with Markdown descriptions rendered as HTML, comments (Markdown), file attachments of any type up to 10 MB with download by original filename. Search across visible projects with free text, filters, client-supplied sort field and direction, pagination. CSV export of a project's tasks. Activity feed per project and global for admins. Deployed to AWS EC2 behind an ALB with Terraform (VPC, private subnets, RDS, ElastiCache, S3, ECR, IAM), Docker images bootstrapped via user_data.",
    "components": "authentication,session-management,authorization,secrets-and-config,transport-security",
    "data_handled": "credentials,personal_data",
    "technologies": "Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, redis-py, PostgreSQL 16, Redis 7, Node.js 24, TypeScript, Express 5, EJS, Docker, Terraform, AWS EC2, ALB, RDS, ElastiCache, S3"
  }
}
```

### evaluation/raw/T-002.output.json

```json
{"success":true,"review_type":"lightweight_pre_coding","status":"complete","task_description":"Build Taskboard, an internal team task tracker. Two services: a Python 3.13 FastAPI REST API (/api/v1, OpenAPI) that is the only component talking to PostgreSQL 16, Redis 7 (cache-aside cache) and attachment storage (local filesystem in dev, Amazon S3 in AWS); and a Node.js 24 Express 5 + EJS UI server that renders pages, authenticates browser users and calls the API over an internal network. Features: register/login/logout with email+password, change password, forgot-password reset links (emails written to log and an outbox table), first admin created by a management command from env vars, admin user management (roles admin/member, deactivate/reactivate). Teams with owners and members added by email; projects inside teams (archive = read-only) with an optional outbound webhook URL that receives an async JSON POST with retry when a task changes status. Tasks with Markdown descriptions rendered as HTML, comments (Markdown), file attachments of any type up to 10 MB with download by original filename. Search across visible projects with free text, filters, client-supplied sort field and direction, pagination. CSV export of a project's tasks. Activity feed per project and global for admins. Deployed to AWS EC2 behind an ALB with Terraform (VPC, private subnets, RDS, ElastiCache, S3, ECR, IAM), Docker images bootstrapped via user_data.","technologies":["Python 3.13","FastAPI","Pydantic v2","SQLAlchemy 2","Alembic","redis-py","PostgreSQL 16","Redis 7","Node.js 24","TypeScript","Express 5","EJS","Docker","Terraform","AWS EC2","ALB","RDS","ElastiCache","S3"],"assessment":{"risk_level":"critical","components":["authentication","session-management","authorization","secrets-and-config","transport-security"],"implied_components":["web-endpoint"],"sensitive_data":["credentials","personal_data"],"threats":[{"id":"hardcoded-secrets","name":"API keys or passwords are committed to the repo or baked into code","severity":"critical","cwe":["CWE-798"]},{"id":"missing-function-authorization","name":"A user calls an admin or other-role function because only the UI hides it","severity":"critical","cwe":["CWE-862"]},{"id":"weak-password-storage","name":"Passwords are stored in plain text or with a fast hash, so a database leak exposes them","severity":"critical","cwe":["CWE-916"]},{"id":"cleartext-transport","name":"Sensitive data travels over plain HTTP or an unencrypted connection","severity":"high","cwe":["CWE-319"]},{"id":"credential-stuffing","name":"Attackers try leaked or guessed passwords against your login at scale","severity":"high","cwe":["CWE-307"]},{"id":"debug-mode-in-production","name":"Debug features or consoles are left on in production","severity":"high","cwe":["CWE-489"]},{"id":"default-accounts","name":"Default or hardcoded admin accounts are left active","severity":"high","cwe":["CWE-798"]},{"id":"exposed-config-files","name":".env, .git, or backup files are reachable from the web","severity":"high","cwe":["CWE-538"]},{"id":"hardcoded-crypto-keys","name":"Encryption or signing keys are hardcoded or shared across environments","severity":"high","cwe":["CWE-321"]},{"id":"insecure-password-reset","name":"Password reset can be abused to take over accounts","severity":"high","cwe":["CWE-640"]},{"id":"jwt-tampering","name":"Forged or unsigned JWTs are accepted","severity":"high","cwe":["CWE-347"]},{"id":"object-id-guessing","name":"One user reads or changes another user's data by changing an id in the request","severity":"high","cwe":["CWE-639"]},{"id":"predictable-tokens","name":"Session ids, reset tokens, or API keys can be guessed","severity":"high","cwe":["CWE-330"]},{"id":"role-self-assignment","name":"A user grants themselves a higher role through a profile or signup request","severity":"high","cwe":["CWE-269"]},{"id":"secrets-baked-into-image","name":"Secrets are copied into the image or passed as build arguments","severity":"high","cwe":["CWE-540"]},{"id":"session-fixation","name":"An attacker plants a session id before login and reuses it afterwards","severity":"high","cwe":["CWE-384"]},{"id":"tenant-data-leak","name":"Queries miss the tenant filter, so customers see each other's data","severity":"high","cwe":["CWE-284"]},{"id":"agent-reads-secrets","name":"The coding agent can read .env files, SSH keys, or cloud credentials","severity":"medium","cwe":["CWE-200"],"mcp_top10":["MCP01:2025"]},{"id":"csrf","name":"Another website makes a logged-in user's browser perform actions","severity":"medium","cwe":["CWE-352"]},{"id":"insecure-cookie-flags","name":"Session cookies can be read by scripts or sent over plain HTTP","severity":"medium","cwe":["CWE-614","CWE-1004"]},{"id":"no-second-factor","name":"A stolen password is enough to take over sensitive accounts","severity":"medium","cwe":["CWE-308"]},{"id":"outdated-tls","name":"Old TLS or SSL versions or weak cipher suites are still enabled","severity":"medium","cwe":["CWE-327"]},{"id":"poisoned-email-links","name":"Links in emails are built from the Host header, so attackers redirect reset links","severity":"medium","cwe":["CWE-640"]},{"id":"sessions-not-ended","name":"Logout, password change, or account removal leaves sessions or tokens valid","severity":"medium","cwe":["CWE-613"]},{"id":"token-claims-unchecked","name":"Expired tokens or tokens meant for another service are accepted","severity":"medium","cwe":["CWE-345"]},{"id":"tokens-leak-via-url-or-storage","name":"Tokens in URLs or browser storage leak through logs, referrers, or scripts","severity":"medium","cwe":["CWE-598"]},{"id":"weak-password-rules","name":"Short or restricted passwords are easy to guess","severity":"medium","cwe":["CWE-521"]},{"id":"no-security-logging","name":"Logins and access failures are not logged, so attacks go unnoticed","severity":"low","cwe":["CWE-778"]},{"id":"user-enumeration","name":"Login or reset responses reveal which emails have accounts","severity":"low","cwe":["CWE-204"]}],"countermeasures":[{"id":"secrets-manager","name":"Load secrets from a secrets manager or environment","how_to":"Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.","effort":"medium","asvs":["v5.0.0-13.3.1","v5.0.0-13.3.2"],"mitigates":["hardcoded-secrets","exposed-config-files","hardcoded-crypto-keys","secrets-baked-into-image"]},{"id":"check-permissions-server-side","name":"Check permissions on the server for every action","how_to":"Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.","effort":"medium","asvs":["v5.0.0-8.2.1","v5.0.0-8.3.1"],"mitigates":["missing-function-authorization","role-self-assignment"]},{"id":"slow-password-hashing","name":"Hash passwords with a slow, salted algorithm","how_to":"Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.","effort":"low","asvs":["v5.0.0-11.4.2"],"mitigates":["weak-password-storage"]},{"id":"https-everywhere","name":"Use HTTPS for every connection","how_to":"Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.","effort":"low","asvs":["v5.0.0-12.2.1","v5.0.0-12.2.2"],"mitigates":["cleartext-transport"]},{"id":"login-attempt-limits","name":"Slow down repeated login failures","how_to":"Throttle or temporarily lock after repeated failures per account and per IP, without making lockout itself a denial-of-service tool.","effort":"medium","asvs":["v5.0.0-6.3.1"],"mitigates":["credential-stuffing"]},{"id":"breached-password-check","name":"Reject known-breached passwords","how_to":"Check new passwords against a breached-password list (for example the Pwned Passwords range API) at signup and change.","effort":"low","asvs":["v5.0.0-6.2.4","v5.0.0-6.2.12"],"mitigates":["credential-stuffing","weak-password-rules"]},{"id":"offer-mfa","name":"Offer or require a second factor","how_to":"Support an authenticator app or passkeys, and require it for admins and sensitive actions.","effort":"medium","asvs":["v5.0.0-6.3.3"],"mitigates":["credential-stuffing","no-second-factor"]},{"id":"disable-debug-in-prod","name":"Turn debug features off in production","how_to":"Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.","effort":"low","asvs":["v5.0.0-13.4.2"],"mitigates":["debug-mode-in-production"]},{"id":"remove-default-accounts","name":"Remove default and hardcoded accounts","how_to":"Ship no preset admin users. Create the first admin through a one-time setup step with a strong generated password.","effort":"low","asvs":["v5.0.0-6.3.2"],"mitigates":["default-accounts"]},{"id":"no-vcs-or-env-files-deployed","name":"Do not deploy repo metadata or env files","how_to":"Exclude .git, .env, and backups from the build and the web root, and block them at the web server.","effort":"low","asvs":["v5.0.0-13.4.1"],"mitigates":["exposed-config-files"]},{"id":"separate-keys-per-environment","name":"Use separate keys per environment and rotate them","how_to":"Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.","effort":"medium","asvs":[],"mitigates":["hardcoded-crypto-keys"]},{"id":"secure-reset-flow","name":"Make password reset single-use and short-lived","how_to":"Send a random single-use token that expires in minutes. Show the same response whether or not the account exists, and keep MFA in force.","effort":"medium","asvs":["v5.0.0-6.4.1","v5.0.0-6.4.3"],"mitigates":["insecure-password-reset"]},{"id":"verify-token-signature","name":"Verify token signatures against an allow-list of algorithms","how_to":"Verify every JWT signature, fix the accepted algorithms in code, and load keys from trusted configuration. Never accept alg none.","effort":"low","asvs":["v5.0.0-9.1.1","v5.0.0-9.1.2","v5.0.0-9.1.3"],"mitigates":["jwt-tampering"]},{"id":"per-object-authorization","name":"Check the user owns the object on every request","how_to":"Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.","effort":"medium","asvs":["v5.0.0-8.2.2","v5.0.0-8.3.1"],"mitigates":["object-id-guessing"]},{"id":"crypto-random-tokens","name":"Generate tokens with a cryptographic random source","how_to":"Use secrets.token_urlsafe, crypto.randomBytes, or the framework default. Never use Math.random, time, or counters.","effort":"low","asvs":["v5.0.0-7.2.3","v5.0.0-11.5.1"],"mitigates":["predictable-tokens"]},{"id":"allow-list-fields","name":"Accept only the fields you expect","how_to":"Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.","effort":"low","asvs":["v5.0.0-15.3.3"],"mitigates":["role-self-assignment"]},{"id":"new-session-on-login","name":"Issue a fresh session at login","how_to":"Create a new session id on every login and re-authentication, and discard the old one.","effort":"low","asvs":["v5.0.0-7.2.4"],"mitigates":["session-fixation"]},{"id":"scope-queries-to-tenant","name":"Scope every query to the tenant","how_to":"Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.","effort":"medium","asvs":["v5.0.0-8.2.2"],"mitigates":["tenant-data-leak"]},{"id":"keep-secrets-out-of-agent-reach","name":"Keep secrets out of the agent's reach","how_to":"Deny reads of .env files, SSH keys, and cloud credentials in the agent's permission rules, and use scoped short-lived credentials.","effort":"low","asvs":[],"mitigates":["agent-reads-secrets"]},{"id":"csrf-protection","name":"Protect state-changing requests from cross-site forgery","how_to":"Use SameSite cookies plus anti-forgery tokens, and only change state with POST, PUT, PATCH, or DELETE.","effort":"low","asvs":["v5.0.0-3.5.1","v5.0.0-3.5.3","v5.0.0-3.3.2"],"mitigates":["csrf"]},{"id":"secure-cookie-attributes","name":"Set cookie security attributes","how_to":"Use Secure, HttpOnly, and SameSite on session cookies, preferably with the __Host- prefix.","effort":"low","asvs":["v5.0.0-3.3.1","v5.0.0-3.3.2","v5.0.0-3.3.4"],"mitigates":["csrf","insecure-cookie-flags"]},{"id":"modern-tls-config","name":"Enable only current TLS versions and cipher suites","how_to":"Allow TLS 1.2 and 1.3 only, use the recommended cipher suites from your platform or proxy, and turn off SSL and older TLS.","effort":"low","asvs":["v5.0.0-12.1.1","v5.0.0-12.1.2"],"mitigates":["outdated-tls"]},{"id":"fixed-base-url-for-links","name":"Build links from a configured base URL","how_to":"Take the public base URL from configuration, not from the Host or X-Forwarded headers of the request.","effort":"low","asvs":["v5.0.0-4.1.3"],"mitigates":["poisoned-email-links"]},{"id":"proper-logout-and-expiry","name":"End sessions on the server","how_to":"Invalidate server-side on logout, expiry, password change, and account removal. Do not rely on deleting the cookie client-side.","effort":"medium","asvs":["v5.0.0-7.4.1","v5.0.0-7.4.2"],"mitigates":["sessions-not-ended"]},{"id":"validate-token-claims","name":"Check expiry, audience, and issuer","how_to":"Reject expired tokens and tokens whose audience or issuer does not match your service.","effort":"low","asvs":["v5.0.0-9.2.1","v5.0.0-9.2.3"],"mitigates":["token-claims-unchecked"]},{"id":"no-secrets-in-urls","name":"Keep tokens and personal data out of URLs","how_to":"Send tokens in headers or request bodies, never in query strings, which end up in logs and referrers.","effort":"low","asvs":["v5.0.0-14.2.1"],"mitigates":["tokens-leak-via-url-or-storage"]},{"id":"no-sensitive-data-in-browser-storage","name":"Keep sensitive data out of browser storage","how_to":"Prefer HttpOnly cookies for session tokens, and clear client-side data on logout.","effort":"low","asvs":["v5.0.0-14.3.3","v5.0.0-14.3.1"],"mitigates":["tokens-leak-via-url-or-storage"]},{"id":"sensible-password-rules","name":"Use length-based password rules","how_to":"Require a minimum length (15 or more is better), allow long passphrases and any characters, and skip composition rules.","effort":"low","asvs":["v5.0.0-6.2.1","v5.0.0-6.2.5","v5.0.0-6.2.9"],"mitigates":["weak-password-rules"]},{"id":"log-security-events","name":"Log security-relevant events","how_to":"Log logins, failures, permission denials, and admin actions with time, user, and source, and alert on spikes.","effort":"medium","asvs":["v5.0.0-16.3.1","v5.0.0-16.3.2"],"mitigates":["no-security-logging"]},{"id":"generic-error-messages","name":"Return generic errors to users","how_to":"Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.","effort":"low","asvs":["v5.0.0-16.5.1"],"mitigates":["user-enumeration"]}],"also_consider":[{"id":"mass-assignment","name":"A request sets fields the user should not control, such as role or price","severity":"high"},{"id":"business-flow-bypass","name":"A user skips or repeats steps in a multi-step flow, such as verification or checkout","severity":"medium"},{"id":"excessive-data-exposure","name":"API responses include more fields than the client needs, such as hashes or internal ids","severity":"medium"},{"id":"missing-input-validation","name":"Unvalidated input reaches business logic and breaks assumptions","severity":"medium"},{"id":"missing-rate-limit","name":"Attackers hammer an endpoint to brute-force, scrape, or run up your costs","severity":"medium"},{"id":"open-redirect","name":"A link on your domain sends users to an attacker-chosen site","severity":"medium"},{"id":"permissive-cors","name":"Any website can read authenticated API responses because CORS allows every origin","severity":"medium"},{"id":"verbose-errors","name":"Stack traces and internal details are shown to users","severity":"medium"}],"summary":"29 threats and 30 countermeasures for authentication, session-management, authorization, secrets-and-config, transport-security. Risk level critical (highest threat severity, raised for sensitive data)."},"hint":null,"instructions":"Build these countermeasures in as you write the code, starting with the most severe threats. These threats come from the components you picked. also_consider lists general threats from implied components; pass those components explicitly for full detail. After writing code, call general_verify_code_security with the same components.","metadata":{"total_threats":29,"total_countermeasures":30,"also_consider_total":9,"review_purpose":"lightweight_security_guidance"}}
```

### evaluation/raw/T-003.input.json

```json
{
  "tool": "mcp__sec-review__threatmodel_perform_threat_model",
  "arguments": {
    "title": "Taskboard (whole system)",
    "description": "Taskboard is an internal team task tracker. Users register and log in with email and password, create teams, add teammates by email, create projects in teams, and manage tasks with Markdown descriptions, Markdown comments and file attachments (any type, up to 10 MB). Projects can have an outbound webhook URL that receives a JSON POST when a task's status changes. Admins manage users (roles, deactivate) and see a global activity feed. Search with client-supplied sort field and direction, CSV export, forgot-password reset links (emails go to log and an outbox table).",
    "components": "authentication,authorization,file-upload,outbound-http-request,user-generated-content",
    "data_handled": "credentials,personal_data",
    "tech_stack": "Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, Redis 7, Node.js 24, TypeScript, Express 5, EJS, Docker, Terraform, AWS EC2, ALB, RDS, ElastiCache, S3",
    "data_flows": "Browser --HTTPS--> ALB --HTTP--> UI server (Express, EJS). UI server holds the user's opaque API session token in an HttpOnly SameSite cookie and calls the API over the private network with Authorization: Bearer <session token>, X-Service-Token (shared secret proving the caller is the UI server), X-Request-ID and X-Client-IP. API (FastAPI) validates the session token against a hashed sessions table in PostgreSQL, enforces team membership and role checks, reads/writes PostgreSQL, uses Redis for cache-aside reads, stores attachment bytes on a local volume or S3 under random keys. API sends webhook POSTs from a background thread to user-configured URLs. UI renders Markdown to sanitized HTML. Attachment downloads stream API -> UI -> browser with Content-Disposition: attachment.",
    "architecture_notes": "The API is never internet-exposed: only the UI port is published in Docker Compose, and in AWS the API instances sit in private subnets with a security group that only admits the UI security group. ALB terminates TLS. Secrets (DB password, Redis auth token, service token, CSRF/cookie secret) come from environment variables populated from AWS SSM Parameter Store at boot. One composition root per service wires interfaces (repositories, cache, storage, mailer, webhook notifier) to implementations."
  }
}
```

### evaluation/raw/T-003.output.json

```json
{
  "success": true,
  "tool": "perform_threat_model",
  "template": {
    "template_version": "1.0",
    "instructions": "Use this template to structure your threat model output. Fill in each section based on the artifacts provided. Every threat MUST include at least one reference linking it to concrete evidence (code path, artifact, ticket, or document). Write threats in plain language — describe attack scenarios a developer would understand, not abstract security categories.",
    "sections": {
      "title": {
        "description": "Name of the feature or component being threat modeled",
        "example": "User Authentication Service Redesign"
      },
      "description": {
        "description": "What are we building? Summary of the change/feature",
        "example": "Migrating from session-based auth to JWT tokens with refresh token rotation"
      },
      "author": {
        "description": "Who is creating this threat model",
        "example": "security-review-mcp"
      },
      "data_touched": {
        "description": "What data does this feature touch? Include data flows, storage, PII, secrets",
        "example": [
          "User credentials (email, password hash)",
          "JWT tokens stored in httpOnly cookies",
          "Refresh tokens in Redis with 7-day TTL",
          "User profile data in PostgreSQL"
        ]
      },
      "technologies": {
        "description": "Tech stack involved",
        "example": [
          "Python",
          "FastAPI",
          "PostgreSQL",
          "Redis",
          "JWT"
        ]
      },
      "threats": {
        "description": "List of identified threats. Each must link to evidence.",
        "fields": {
          "id": "Short identifier like TM-1, TM-2",
          "what_can_go_wrong": "Plain-language attack scenario. e.g., 'Attacker steals JWT from localStorage and impersonates user'",
          "impact": "Business impact. e.g., 'Full account takeover, access to user's payment data'",
          "likelihood": "high, medium, or low",
          "data_affected": "List of data types at risk",
          "mitigation": "What we're doing or should do about it",
          "status": "open, in_progress, mitigated, or accepted",
          "references": {
            "description": "Evidence linking this threat to code or artifacts",
            "fields": {
              "type": "code, artifact, ticket, document, or url",
              "location": "File path, URL, or ticket key",
              "description": "What this reference proves",
              "snippet": "Optional inline code/text evidence"
            }
          },
          "accepted_risk": "If status is 'accepted', justification for accepting"
        }
      }
    },
    "output_format": "Return the threat model as a JSON object matching the ThreatModelOutput structure. The tool will handle rendering it as markdown for threat-model.md if the user approves."
  },
  "feature": {
    "title": "Taskboard (whole system)",
    "description": "Taskboard is an internal team task tracker. Users register and log in with email and password, create teams, add teammates by email, create projects in teams, and manage tasks with Markdown descriptions, Markdown comments and file attachments (any type, up to 10 MB). Projects can have an outbound webhook URL that receives a JSON POST when a task's status changes. Admins manage users (roles, deactivate) and see a global activity feed. Search with client-supplied sort field and direction, CSV export, forgot-password reset links (emails go to log and an outbox table)."
  },
  "artifacts": {
    "data_flows": "Browser --HTTPS--> ALB --HTTP--> UI server (Express, EJS). UI server holds the user's opaque API session token in an HttpOnly SameSite cookie and calls the API over the private network with Authorization: Bearer <session token>, X-Service-Token (shared secret proving the caller is the UI server), X-Request-ID and X-Client-IP. API (FastAPI) validates the session token against a hashed sessions table in PostgreSQL, enforces team membership and role checks, reads/writes PostgreSQL, uses Redis for cache-aside reads, stores attachment bytes on a local volume or S3 under random keys. API sends webhook POSTs from a background thread to user-configured URLs. UI renders Markdown to sanitized HTML. Attachment downloads stream API -> UI -> browser with Content-Disposition: attachment.",
    "tech_stack": [
      "Python 3.13",
      "FastAPI",
      "Pydantic v2",
      "SQLAlchemy 2",
      "Alembic",
      "PostgreSQL 16",
      "Redis 7",
      "Node.js 24",
      "TypeScript",
      "Express 5",
      "EJS",
      "Docker",
      "Terraform",
      "AWS EC2",
      "ALB",
      "RDS",
      "ElastiCache",
      "S3"
    ],
    "architecture_notes": "The API is never internet-exposed: only the UI port is published in Docker Compose, and in AWS the API instances sit in private subnets with a security group that only admits the UI security group. ALB terminates TLS. Secrets (DB password, Redis auth token, service token, CSRF/cookie secret) come from environment variables populated from AWS SSM Parameter Store at boot. One composition root per service wires interfaces (repositories, cache, storage, mailer, webhook notifier) to implementations."
  },
  "known_threats": {
    "status": "from_library",
    "risk_level": "critical",
    "components": [
      "authentication",
      "authorization",
      "file-upload",
      "outbound-http-request",
      "user-generated-content"
    ],
    "implied_components": [
      "web-endpoint"
    ],
    "sensitive_data": [
      "credentials",
      "personal_data"
    ],
    "threats": [
      {
        "id": "missing-function-authorization",
        "name": "A user calls an admin or other-role function because only the UI hides it",
        "severity": "critical",
        "cwe": [
          "CWE-862"
        ]
      },
      {
        "id": "weak-password-storage",
        "name": "Passwords are stored in plain text or with a fast hash, so a database leak exposes them",
        "severity": "critical",
        "cwe": [
          "CWE-916"
        ]
      },
      {
        "id": "archive-path-traversal",
        "name": "An uploaded archive writes files outside the target folder when extracted",
        "severity": "high",
        "cwe": [
          "CWE-22"
        ]
      },
      {
        "id": "credential-stuffing",
        "name": "Attackers try leaked or guessed passwords against your login at scale",
        "severity": "high",
        "cwe": [
          "CWE-307"
        ]
      },
      {
        "id": "default-accounts",
        "name": "Default or hardcoded admin accounts are left active",
        "severity": "high",
        "cwe": [
          "CWE-798"
        ]
      },
      {
        "id": "insecure-password-reset",
        "name": "Password reset can be abused to take over accounts",
        "severity": "high",
        "cwe": [
          "CWE-640"
        ]
      },
      {
        "id": "object-id-guessing",
        "name": "One user reads or changes another user's data by changing an id in the request",
        "severity": "high",
        "cwe": [
          "CWE-639"
        ]
      },
      {
        "id": "predictable-tokens",
        "name": "Session ids, reset tokens, or API keys can be guessed",
        "severity": "high",
        "cwe": [
          "CWE-330"
        ]
      },
      {
        "id": "role-self-assignment",
        "name": "A user grants themselves a higher role through a profile or signup request",
        "severity": "high",
        "cwe": [
          "CWE-269"
        ]
      },
      {
        "id": "ssrf",
        "name": "The server is tricked into fetching internal addresses or cloud metadata",
        "severity": "high",
        "cwe": [
          "CWE-918"
        ]
      },
      {
        "id": "stored-xss",
        "name": "Attacker-supplied content is shown to other users as HTML or script",
        "severity": "high",
        "cwe": [
          "CWE-79"
        ]
      },
      {
        "id": "tenant-data-leak",
        "name": "Queries miss the tenant filter, so customers see each other's data",
        "severity": "high",
        "cwe": [
          "CWE-284"
        ]
      },
      {
        "id": "tls-verification-disabled",
        "name": "Outbound calls skip certificate checks, so traffic can be intercepted",
        "severity": "high",
        "cwe": [
          "CWE-295"
        ]
      },
      {
        "id": "upload-executable-file",
        "name": "Attacker uploads a script that your server runs or serves",
        "severity": "high",
        "cwe": [
          "CWE-434"
        ]
      },
      {
        "id": "upload-path-traversal",
        "name": "Attacker uses ../ in a filename to overwrite files",
        "severity": "high",
        "cwe": [
          "CWE-22"
        ]
      },
      {
        "id": "no-second-factor",
        "name": "A stolen password is enough to take over sensitive accounts",
        "severity": "medium",
        "cwe": [
          "CWE-308"
        ]
      },
      {
        "id": "poisoned-email-links",
        "name": "Links in emails are built from the Host header, so attackers redirect reset links",
        "severity": "medium",
        "cwe": [
          "CWE-640"
        ]
      },
      {
        "id": "upload-active-content",
        "name": "An uploaded SVG or HTML file runs script when other users open it",
        "severity": "medium",
        "cwe": [
          "CWE-79"
        ]
      },
      {
        "id": "upload-resource-exhaustion",
        "name": "Huge files or compression bombs fill disk or memory",
        "severity": "medium",
        "cwe": [
          "CWE-770"
        ]
      },
      {
        "id": "weak-password-rules",
        "name": "Short or restricted passwords are easy to guess",
        "severity": "medium",
        "cwe": [
          "CWE-521"
        ]
      },
      {
        "id": "no-security-logging",
        "name": "Logins and access failures are not logged, so attacks go unnoticed",
        "severity": "low",
        "cwe": [
          "CWE-778"
        ]
      },
      {
        "id": "no-timeouts-or-size-caps",
        "name": "A slow or huge remote response ties up workers and memory",
        "severity": "low",
        "cwe": [
          "CWE-400"
        ]
      },
      {
        "id": "user-enumeration",
        "name": "Login or reset responses reveal which emails have accounts",
        "severity": "low",
        "cwe": [
          "CWE-204"
        ]
      }
    ],
    "countermeasures": [
      {
        "id": "check-permissions-server-side",
        "name": "Check permissions on the server for every action",
        "how_to": "Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-8.2.1",
          "v5.0.0-8.3.1"
        ],
        "mitigates": [
          "missing-function-authorization",
          "role-self-assignment"
        ]
      },
      {
        "id": "slow-password-hashing",
        "name": "Hash passwords with a slow, salted algorithm",
        "how_to": "Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.",
        "effort": "low",
        "asvs": [
          "v5.0.0-11.4.2"
        ],
        "mitigates": [
          "weak-password-storage"
        ]
      },
      {
        "id": "safe-archive-extraction",
        "name": "Extract archives safely",
        "how_to": "Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-5.3.3",
          "v5.0.0-5.2.3"
        ],
        "mitigates": [
          "archive-path-traversal"
        ]
      },
      {
        "id": "login-attempt-limits",
        "name": "Slow down repeated login failures",
        "how_to": "Throttle or temporarily lock after repeated failures per account and per IP, without making lockout itself a denial-of-service tool.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-6.3.1"
        ],
        "mitigates": [
          "credential-stuffing"
        ]
      },
      {
        "id": "breached-password-check",
        "name": "Reject known-breached passwords",
        "how_to": "Check new passwords against a breached-password list (for example the Pwned Passwords range API) at signup and change.",
        "effort": "low",
        "asvs": [
          "v5.0.0-6.2.4",
          "v5.0.0-6.2.12"
        ],
        "mitigates": [
          "credential-stuffing",
          "weak-password-rules"
        ]
      },
      {
        "id": "offer-mfa",
        "name": "Offer or require a second factor",
        "how_to": "Support an authenticator app or passkeys, and require it for admins and sensitive actions.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-6.3.3"
        ],
        "mitigates": [
          "credential-stuffing",
          "no-second-factor"
        ]
      },
      {
        "id": "remove-default-accounts",
        "name": "Remove default and hardcoded accounts",
        "how_to": "Ship no preset admin users. Create the first admin through a one-time setup step with a strong generated password.",
        "effort": "low",
        "asvs": [
          "v5.0.0-6.3.2"
        ],
        "mitigates": [
          "default-accounts"
        ]
      },
      {
        "id": "secure-reset-flow",
        "name": "Make password reset single-use and short-lived",
        "how_to": "Send a random single-use token that expires in minutes. Show the same response whether or not the account exists, and keep MFA in force.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-6.4.1",
          "v5.0.0-6.4.3"
        ],
        "mitigates": [
          "insecure-password-reset"
        ]
      },
      {
        "id": "per-object-authorization",
        "name": "Check the user owns the object on every request",
        "how_to": "Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-8.2.2",
          "v5.0.0-8.3.1"
        ],
        "mitigates": [
          "object-id-guessing"
        ]
      },
      {
        "id": "crypto-random-tokens",
        "name": "Generate tokens with a cryptographic random source",
        "how_to": "Use secrets.token_urlsafe, crypto.randomBytes, or the framework default. Never use Math.random, time, or counters.",
        "effort": "low",
        "asvs": [
          "v5.0.0-7.2.3",
          "v5.0.0-11.5.1"
        ],
        "mitigates": [
          "predictable-tokens"
        ]
      },
      {
        "id": "allow-list-fields",
        "name": "Accept only the fields you expect",
        "how_to": "Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.",
        "effort": "low",
        "asvs": [
          "v5.0.0-15.3.3"
        ],
        "mitigates": [
          "role-self-assignment"
        ]
      },
      {
        "id": "ssrf-allow-list",
        "name": "Fetch only allow-listed destinations",
        "how_to": "Resolve the host, block private, loopback, and link-local ranges including cloud metadata, and prefer a fixed allow-list of hosts.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-1.3.6",
          "v5.0.0-13.2.4"
        ],
        "mitigates": [
          "ssrf"
        ]
      },
      {
        "id": "no-redirect-following",
        "name": "Do not follow redirects on server-side fetches",
        "how_to": "Disable automatic redirects, or re-validate each hop against the same allow-list.",
        "effort": "low",
        "asvs": [
          "v5.0.0-15.3.2"
        ],
        "mitigates": [
          "ssrf"
        ]
      },
      {
        "id": "output-encoding",
        "name": "Encode output for its context",
        "how_to": "Use your template engine's automatic escaping, and encode correctly for HTML, attributes, URLs, and JavaScript.",
        "effort": "low",
        "asvs": [
          "v5.0.0-1.2.1",
          "v5.0.0-1.2.2",
          "v5.0.0-1.2.3"
        ],
        "mitigates": [
          "stored-xss"
        ]
      },
      {
        "id": "sanitize-html",
        "name": "Sanitize user-provided HTML",
        "how_to": "Run user HTML through a maintained sanitizer such as DOMPurify or bleach with a strict allow-list. Prefer markdown or plain text.",
        "effort": "low",
        "asvs": [
          "v5.0.0-1.3.1"
        ],
        "mitigates": [
          "stored-xss",
          "upload-active-content"
        ]
      },
      {
        "id": "scope-queries-to-tenant",
        "name": "Scope every query to the tenant",
        "how_to": "Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-8.2.2"
        ],
        "mitigates": [
          "tenant-data-leak"
        ]
      },
      {
        "id": "validate-tls-certificates",
        "name": "Always verify TLS certificates",
        "how_to": "Never set verify=False or NODE_TLS_REJECT_UNAUTHORIZED=0. Add your private CA to the trust store if needed.",
        "effort": "low",
        "asvs": [
          "v5.0.0-12.3.2"
        ],
        "mitigates": [
          "tls-verification-disabled"
        ]
      },
      {
        "id": "upload-allow-list",
        "name": "Allow only the file types you need",
        "how_to": "Check the extension and the real file content against an allow-list. Ignore the client's Content-Type.",
        "effort": "low",
        "asvs": [
          "v5.0.0-5.2.2"
        ],
        "mitigates": [
          "upload-executable-file"
        ]
      },
      {
        "id": "upload-rename-and-isolate",
        "name": "Never use the user's filename or path",
        "how_to": "Generate your own filenames, store files outside the web root, and make sure uploads are never executed.",
        "effort": "low",
        "asvs": [
          "v5.0.0-5.3.1",
          "v5.0.0-5.3.2"
        ],
        "mitigates": [
          "upload-executable-file",
          "upload-path-traversal"
        ]
      },
      {
        "id": "fixed-base-url-for-links",
        "name": "Build links from a configured base URL",
        "how_to": "Take the public base URL from configuration, not from the Host or X-Forwarded headers of the request.",
        "effort": "low",
        "asvs": [
          "v5.0.0-4.1.3"
        ],
        "mitigates": [
          "poisoned-email-links"
        ]
      },
      {
        "id": "serve-uploads-safely",
        "name": "Serve uploads so browsers cannot run them",
        "how_to": "Send the correct Content-Type, Content-Disposition attachment for downloads, nosniff, and serve user files from a separate domain.",
        "effort": "low",
        "asvs": [
          "v5.0.0-4.1.1",
          "v5.0.0-5.4.2",
          "v5.0.0-3.2.1"
        ],
        "mitigates": [
          "upload-active-content"
        ]
      },
      {
        "id": "upload-size-limits",
        "name": "Limit file size and decompressed size",
        "how_to": "Set a maximum size per file, and cap decompressed size and file count for archives.",
        "effort": "low",
        "asvs": [
          "v5.0.0-5.2.1",
          "v5.0.0-5.2.3"
        ],
        "mitigates": [
          "upload-resource-exhaustion"
        ]
      },
      {
        "id": "sensible-password-rules",
        "name": "Use length-based password rules",
        "how_to": "Require a minimum length (15 or more is better), allow long passphrases and any characters, and skip composition rules.",
        "effort": "low",
        "asvs": [
          "v5.0.0-6.2.1",
          "v5.0.0-6.2.5",
          "v5.0.0-6.2.9"
        ],
        "mitigates": [
          "weak-password-rules"
        ]
      },
      {
        "id": "log-security-events",
        "name": "Log security-relevant events",
        "how_to": "Log logins, failures, permission denials, and admin actions with time, user, and source, and alert on spikes.",
        "effort": "medium",
        "asvs": [
          "v5.0.0-16.3.1",
          "v5.0.0-16.3.2"
        ],
        "mitigates": [
          "no-security-logging"
        ]
      },
      {
        "id": "timeouts-and-size-caps",
        "name": "Set timeouts and response size caps",
        "how_to": "Use connect and read timeouts and a maximum body size on every outbound call and queue consumer.",
        "effort": "low",
        "asvs": [
          "v5.0.0-15.2.2"
        ],
        "mitigates": [
          "no-timeouts-or-size-caps"
        ]
      },
      {
        "id": "generic-error-messages",
        "name": "Return generic errors to users",
        "how_to": "Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.",
        "effort": "low",
        "asvs": [
          "v5.0.0-16.5.1"
        ],
        "mitigates": [
          "user-enumeration"
        ]
      }
    ],
    "also_consider": [
      {
        "id": "cleartext-transport",
        "name": "Sensitive data travels over plain HTTP or an unencrypted connection",
        "severity": "high"
      },
      {
        "id": "debug-mode-in-production",
        "name": "Debug features or consoles are left on in production",
        "severity": "high"
      },
      {
        "id": "exposed-config-files",
        "name": ".env, .git, or backup files are reachable from the web",
        "severity": "high"
      },
      {
        "id": "mass-assignment",
        "name": "A request sets fields the user should not control, such as role or price",
        "severity": "high"
      },
      {
        "id": "business-flow-bypass",
        "name": "A user skips or repeats steps in a multi-step flow, such as verification or checkout",
        "severity": "medium"
      },
      {
        "id": "csrf",
        "name": "Another website makes a logged-in user's browser perform actions",
        "severity": "medium"
      },
      {
        "id": "excessive-data-exposure",
        "name": "API responses include more fields than the client needs, such as hashes or internal ids",
        "severity": "medium"
      },
      {
        "id": "missing-input-validation",
        "name": "Unvalidated input reaches business logic and breaks assumptions",
        "severity": "medium"
      }
    ]
  },
  "instructions": "Analyze the provided artifacts using known_threats as a starting checklist: keep the ones that apply, drop the ones that do not, and add scenarios specific to these artifacts. Generate a threat model following the template structure. Each threat MUST reference specific evidence from the artifacts (code paths, data flows, architecture decisions). Write threats in plain developer language. Focus on concrete attack scenarios, not abstract categories.",
  "output_instructions": "After analyzing the artifacts and known threats, return a JSON object matching the template structure with all threats identified. Each threat MUST include at least one reference with evidence. Use the parse format described in the template.",
  "suggest_file_update": true,
  "file_update_message": "After generating the threat model, ask the user: 'Would you like me to save this threat model to threat-model.md?' If they agree, use the update_threat_model_file tool with the generated content."
}
```

### evaluation/raw/T-003.produced.json

```json
{
  "title": "Taskboard (whole system)",
  "description": "Internal team task tracker: a FastAPI API (only component touching PostgreSQL, Redis and attachment storage) behind a Node.js Express UI server that renders pages and authenticates browser users. Features: email/password accounts with reset links, admin user management, teams, projects with outbound status-change webhooks, tasks with Markdown, comments, attachments up to 10 MB, search with client-chosen sort, CSV export, activity feeds.",
  "author": "Claude Code session (arm A), from sec-review perform_threat_model context",
  "data_touched": [
    "User credentials: email, Argon2id password hash (users table)",
    "Opaque session tokens: SHA-256 hash in sessions table, raw value only in the browser's HttpOnly cookie and in UI-to-API Authorization headers",
    "Password reset tokens: SHA-256 hash in password_reset_tokens, raw value in outbox rows and API log (dev mailer)",
    "Personal data: display names and emails of users, visible to teammates and admins",
    "Task content, Markdown descriptions and comments, labels, due dates",
    "Attachment bytes (local volume or S3) and original filenames",
    "Project webhook URLs and outbound webhook payloads",
    "Service secrets: UI-to-API service token, cookie/CSRF secret, DB password, Redis auth token"
  ],
  "technologies": ["Python 3.13", "FastAPI", "SQLAlchemy 2", "PostgreSQL 16", "Redis 7", "Node.js 24", "Express 5", "EJS", "Docker", "Terraform", "AWS EC2/ALB/RDS/ElastiCache/S3"],
  "threats": [
    {
      "id": "TM-1",
      "what_can_go_wrong": "A member of team A changes the task, project, comment or attachment id in a URL and reads or edits team B's data, because a handler loads the object by id without checking team membership.",
      "impact": "Cross-team data disclosure and tampering.",
      "likelihood": "high",
      "data_affected": ["tasks", "comments", "attachments", "projects", "team membership"],
      "mitigation": "A single AccessPolicy service resolves every object to its team and checks membership (or admin) before any read or write; non-members get 404. Search and list queries join on team_members for the caller. Integration tests cover cross-team access for every resource type.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "brief section 4.2-4.4, data_flows", "description": "All task/comment/attachment endpoints take bare UUIDs; team membership is the only boundary", "snippet": "GET /api/v1/tasks/{task_id}"}]
    },
    {
      "id": "TM-2",
      "what_can_go_wrong": "A member calls PATCH /api/v1/admin/users/{id} or creates/archives a project directly against the API (or via a crafted form post to the UI) because only the UI hides the buttons.",
      "impact": "Privilege escalation to admin; unauthorised project changes.",
      "likelihood": "medium",
      "data_affected": ["user roles", "projects"],
      "mitigation": "Role and ownership checks live in services (AdminService requires admin; ProjectService requires team owner or admin). Request schemas use extra='forbid' so role cannot be set at registration or profile update.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "brief section 4.1, 4.3", "description": "Admin-only and owner-only operations exist alongside member operations"}]
    },
    {
      "id": "TM-3",
      "what_can_go_wrong": "An attacker sets a project's webhook URL to http://169.254.169.254/latest/meta-data/ or an internal service (api:8000, redis, RDS) and the API's background sender POSTs to it, or a public hostname that later resolves (DNS rebinding) or redirects to an internal address.",
      "impact": "SSRF into the VPC; on EC2 with IMDSv1 this could leak instance role credentials.",
      "likelihood": "medium",
      "data_affected": ["instance credentials", "internal services"],
      "mitigation": "Validate scheme (https only unless explicitly allowed in dev), resolve the host at send time, reject loopback/private/link-local/multicast/reserved/CGNAT/metadata addresses, connect to the validated IP with the original Host header and SNI, never follow redirects, short connect/read timeouts, cap response read. Enforce IMDSv2 with hop limit 1 on EC2.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "data_flows", "description": "API sends webhook POSTs from a background thread to user-configured URLs"}]
    },
    {
      "id": "TM-4",
      "what_can_go_wrong": "A teammate writes a task description or comment containing <script>, an <img onerror>, or a [link](javascript:...) and every viewer of the task runs it in the UI origin, where it can submit forms as the victim.",
      "impact": "Account actions performed as other users, including admins.",
      "likelihood": "high",
      "data_affected": ["sessions (indirectly)", "all data the victim can reach"],
      "mitigation": "Render Markdown with marked, then sanitize-html with a strict tag/attribute allow-list and http/https/mailto-only links; EJS auto-escaping everywhere else (no <%- except sanitized HTML); strict CSP without inline script.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "data_flows", "description": "UI renders Markdown to sanitized HTML"}]
    },
    {
      "id": "TM-5",
      "what_can_go_wrong": "A user uploads an .html or .svg attachment; another user opens it and it renders inline in the UI origin, running script.",
      "impact": "Stored XSS through attachments.",
      "likelihood": "medium",
      "data_affected": ["sessions (indirectly)"],
      "mitigation": "Downloads are always Content-Disposition: attachment with Content-Type application/octet-stream and X-Content-Type-Options: nosniff, plus a sandbox CSP on the download response. Any file type is allowed by the brief, so no type allow-list.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "brief section 4.4", "description": "Attachments are any type and downloadable with their original filename"}]
    },
    {
      "id": "TM-6",
      "what_can_go_wrong": "An uploaded filename like ../../etc/passwd or a name with CR/LF or quotes is used in a storage path or echoed into the Content-Disposition header.",
      "impact": "File overwrite on the API host; response header injection.",
      "likelihood": "medium",
      "data_affected": ["attachment storage", "API host files"],
      "mitigation": "Storage keys are server-generated UUIDs; the local storage resolves paths and checks they stay under the root. Original filename is stored only as metadata, reduced to its basename, stripped of control characters, and emitted with RFC 6266/5987 filename* encoding.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "data_flows", "description": "stores attachment bytes on a local volume or S3 under random keys"}]
    },
    {
      "id": "TM-7",
      "what_can_go_wrong": "A client uploads many multi-gigabyte bodies or a slow stream to exhaust disk or memory on the UI or API.",
      "impact": "Denial of service.",
      "likelihood": "medium",
      "data_affected": [],
      "mitigation": "UI multer limit of 10 MB and one file; API rejects Content-Length over limit and counts bytes while streaming, aborting past 10 MB.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "brief section 4.4", "description": "up to 10 MB each"}]
    },
    {
      "id": "TM-8",
      "what_can_go_wrong": "Attackers run credential stuffing against /auth/login, or hammer /auth/password/forgot to spam the outbox.",
      "impact": "Account takeover; resource abuse.",
      "likelihood": "medium",
      "data_affected": ["credentials"],
      "mitigation": "Per-email and per-client-IP fixed-window rate limits on login and forgot-password (Redis-backed, in-memory fallback), Argon2id hashing, minimum 12-character passwords with a 128 limit, generic error text.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "data_flows", "description": "UI forwards X-Client-IP so the API can rate-limit per client"}]
    },
    {
      "id": "TM-9",
      "what_can_go_wrong": "Reset tokens are guessable, reusable, long-lived, or the reset link points at an attacker host because it was built from the Host header; or forgot-password reveals which emails exist.",
      "impact": "Account takeover; user enumeration.",
      "likelihood": "medium",
      "data_affected": ["credentials", "emails"],
      "mitigation": "secrets.token_urlsafe(32) tokens stored as SHA-256, 30-minute expiry, single use, all sessions revoked on reset, link built from configured PUBLIC_BASE_URL, forgot always returns 202 with the same body.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "brief section 4.1", "description": "Forgot password: request a reset link by email, then set a new password using the link"}]
    },
    {
      "id": "TM-10",
      "what_can_go_wrong": "Any process on the internal network (or a compromised container) calls the API directly with forged identity headers, or a stolen session token keeps working after logout, password change or deactivation.",
      "impact": "Impersonation of any user.",
      "likelihood": "low",
      "data_affected": ["all"],
      "mitigation": "Identity is never taken from a header: the API resolves the Bearer session token against the sessions table on every request and checks the user is active. The UI must also present X-Service-Token, compared in constant time. Logout deletes the session; password change/reset and deactivation delete all of the user's sessions.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "data_flows", "description": "Authorization: Bearer <session token>, X-Service-Token"}]
    },
    {
      "id": "TM-11",
      "what_can_go_wrong": "Another website auto-submits a form to the UI (e.g. remove member, change password) using the victim's cookie.",
      "impact": "Unwanted state changes.",
      "likelihood": "medium",
      "data_affected": ["teams", "tasks", "credentials"],
      "mitigation": "SameSite=Lax HttpOnly cookies (Secure and __Host- prefix in production) plus a per-session HMAC CSRF token on every POST form, verified by middleware.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "data_flows", "description": "session token in an HttpOnly SameSite cookie"}]
    },
    {
      "id": "TM-12",
      "what_can_go_wrong": "The client-supplied sort field is interpolated into SQL (ORDER BY {field}), or free-text search builds LIKE patterns by string concatenation.",
      "impact": "SQL injection, full database read.",
      "likelihood": "medium",
      "data_affected": ["all database contents"],
      "mitigation": "Sort field is validated against an enum mapped to ORM column objects; direction is an enum; search uses bound parameters with LIKE wildcards escaped.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "brief section 4.5", "description": "sort by any task field in either direction, with field and direction supplied by the client"}]
    },
    {
      "id": "TM-13",
      "what_can_go_wrong": "A task title starting with =HYPERLINK(...) or =cmd|... is exported to CSV and executes when a teammate opens it in a spreadsheet.",
      "impact": "Code execution or data exfiltration on the victim's workstation.",
      "likelihood": "low",
      "data_affected": ["exported task data"],
      "mitigation": "Prefix cells beginning with = + - @ tab or CR with a single quote.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "brief section 4.5", "description": "Export a project's tasks as CSV"}]
    },
    {
      "id": "TM-14",
      "what_can_go_wrong": "A cached team or project list or task detail is served to a user who was removed from the team, or cached data keyed only by object id bypasses the membership check.",
      "impact": "Stale-permission data disclosure.",
      "likelihood": "medium",
      "data_affected": ["tasks", "projects"],
      "mitigation": "Authorization runs against the database before any cache read; per-user list caches are invalidated on member add/remove; cache values are JSON, never pickle.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "data_flows", "description": "uses Redis for cache-aside reads"}]
    },
    {
      "id": "TM-15",
      "what_can_go_wrong": "Reset links and session tokens are written to logs, which are shipped to a log store readable by more people than the database.",
      "impact": "Token leakage via logs.",
      "likelihood": "medium",
      "data_affected": ["reset tokens"],
      "mitigation": "Session tokens and passwords are never logged. The brief requires emails to be written to the API log, so the dev mailer logs the reset email; this is accepted for this build and documented, with a real mailer replacing it in production.",
      "status": "accepted",
      "accepted_risk": "Required by the brief: there is no real email provider and emails must be readable from the API log in dev and tests.",
      "references": [{"type": "artifact", "location": "brief section 4.1", "description": "write outgoing emails to the API log and to an outbox table"}]
    },
    {
      "id": "TM-16",
      "what_can_go_wrong": "The first-admin management command ships a default password, or secrets are baked into images or committed in .env files.",
      "impact": "Trivial admin takeover.",
      "likelihood": "low",
      "data_affected": ["admin account", "service secrets"],
      "mitigation": "Command reads email and password from env vars, refuses empty or short passwords, no defaults. Secrets only in env/SSM; .env git-ignored and .dockerignore'd; no build args for secrets.",
      "status": "in_progress",
      "references": [{"type": "artifact", "location": "architecture_notes", "description": "Secrets ... come from environment variables populated from AWS SSM Parameter Store at boot"}]
    },
    {
      "id": "TM-17",
      "what_can_go_wrong": "Traffic between ALB and UI, UI and API, or API and RDS/ElastiCache is sniffed inside the VPC.",
      "impact": "Session token and credential disclosure to a network-positioned attacker.",
      "likelihood": "low",
      "data_affected": ["session tokens", "DB credentials"],
      "mitigation": "TLS 1.2+ policy on the ALB with HTTP->HTTPS redirect; RDS with forced SSL (rds.force_ssl) and sslmode=require; ElastiCache transit encryption with auth token. UI-to-API stays HTTP inside private subnets restricted by security groups; accepted for this build and documented.",
      "status": "accepted",
      "accepted_risk": "UI-to-API hop is plain HTTP inside private subnets locked to the UI security group; adding internal TLS needs a private CA, out of scope for this build.",
      "references": [{"type": "artifact", "location": "data_flows", "description": "ALB --HTTP--> UI server ... calls the API over the private network"}]
    }
  ],
  "summary": "17 threats. Highest risk: cross-team object access (TM-1), stored XSS via Markdown (TM-4), and webhook SSRF (TM-3). Archive extraction threats from the library were dropped because the app never extracts uploaded archives. MFA and breached-password checks are not in scope for this internal tool and are noted as accepted gaps in DECISIONS."
}
```

### evaluation/raw/T-004.input.json

```json
{
  "tool": "mcp__sec-review__threatmodel_update_threat_model_file",
  "arguments": {
    "threat_model_json": "{\"title\": \"Taskboard (whole system)\", \"description\": \"Internal team task tracker: a FastAPI API (only component touching PostgreSQL, Redis and attachment storage) behind a Node.js Express UI server that renders pages and authenticates browser users. Features: email/password accounts with reset links, admin user management, teams, projects with outbound status-change webhooks, tasks with Markdown, comments, attachments up to 10 MB, search with client-chosen sort, CSV export, activity feeds.\", \"author\": \"Claude Code session (arm A), from sec-review perform_threat_model context\", \"data_touched\": [\"User credentials: email, Argon2id password hash (users table)\", \"Opaque session tokens: SHA-256 hash in sessions table, raw value only in the browser's HttpOnly cookie and in UI-to-API Authorization headers\", \"Password reset tokens: SHA-256 hash in password_reset_tokens, raw value in outbox rows and API log (dev mailer)\", \"Personal data: display names and emails of users, visible to teammates and admins\", \"Task content, Markdown descriptions and comments, labels, due dates\", \"Attachment bytes (local volume or S3) and original filenames\", \"Project webhook URLs and outbound webhook payloads\", \"Service secrets: UI-to-API service token, cookie/CSRF secret, DB password, Redis auth token\"], \"technologies\": [\"Python 3.13\", \"FastAPI\", \"SQLAlchemy 2\", \"PostgreSQL 16\", \"Redis 7\", \"Node.js 24\", \"Express 5\", \"EJS\", \"Docker\", \"Terraform\", \"AWS EC2/ALB/RDS/ElastiCache/S3\"], \"threats\": [{\"id\": \"TM-1\", \"what_can_go_wrong\": \"A member of team A changes the task, project, comment or attachment id in a URL and reads or edits team B's data, because a handler loads the object by id without checking team membership.\", \"impact\": \"Cross-team data disclosure and tampering.\", \"likelihood\": \"high\", \"data_affected\": [\"tasks\", \"comments\", \"attachments\", \"projects\", \"team membership\"], \"mitigation\": \"A single AccessPolicy service resolves every object to its team and checks membership (or admin) before any read or write; non-members get 404. Search and list queries join on team_members for the caller. Integration tests cover cross-team access for every resource type.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.2-4.4, data_flows\", \"description\": \"All task/comment/attachment endpoints take bare UUIDs; team membership is the only boundary\", \"snippet\": \"GET /api/v1/tasks/{task_id}\"}]}, {\"id\": \"TM-2\", \"what_can_go_wrong\": \"A member calls PATCH /api/v1/admin/users/{id} or creates/archives a project directly against the API (or via a crafted form post to the UI) because only the UI hides the buttons.\", \"impact\": \"Privilege escalation to admin; unauthorised project changes.\", \"likelihood\": \"medium\", \"data_affected\": [\"user roles\", \"projects\"], \"mitigation\": \"Role and ownership checks live in services (AdminService requires admin; ProjectService requires team owner or admin). Request schemas use extra='forbid' so role cannot be set at registration or profile update.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.1, 4.3\", \"description\": \"Admin-only and owner-only operations exist alongside member operations\"}]}, {\"id\": \"TM-3\", \"what_can_go_wrong\": \"An attacker sets a project's webhook URL to http://169.254.169.254/latest/meta-data/ or an internal service (api:8000, redis, RDS) and the API's background sender POSTs to it, or a public hostname that later resolves (DNS rebinding) or redirects to an internal address.\", \"impact\": \"SSRF into the VPC; on EC2 with IMDSv1 this could leak instance role credentials.\", \"likelihood\": \"medium\", \"data_affected\": [\"instance credentials\", \"internal services\"], \"mitigation\": \"Validate scheme (https only unless explicitly allowed in dev), resolve the host at send time, reject loopback/private/link-local/multicast/reserved/CGNAT/metadata addresses, connect to the validated IP with the original Host header and SNI, never follow redirects, short connect/read timeouts, cap response read. Enforce IMDSv2 with hop limit 1 on EC2.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"API sends webhook POSTs from a background thread to user-configured URLs\"}]}, {\"id\": \"TM-4\", \"what_can_go_wrong\": \"A teammate writes a task description or comment containing <script>, an <img onerror>, or a [link](javascript:...) and every viewer of the task runs it in the UI origin, where it can submit forms as the victim.\", \"impact\": \"Account actions performed as other users, including admins.\", \"likelihood\": \"high\", \"data_affected\": [\"sessions (indirectly)\", \"all data the victim can reach\"], \"mitigation\": \"Render Markdown with marked, then sanitize-html with a strict tag/attribute allow-list and http/https/mailto-only links; EJS auto-escaping everywhere else (no <%- except sanitized HTML); strict CSP without inline script.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"UI renders Markdown to sanitized HTML\"}]}, {\"id\": \"TM-5\", \"what_can_go_wrong\": \"A user uploads an .html or .svg attachment; another user opens it and it renders inline in the UI origin, running script.\", \"impact\": \"Stored XSS through attachments.\", \"likelihood\": \"medium\", \"data_affected\": [\"sessions (indirectly)\"], \"mitigation\": \"Downloads are always Content-Disposition: attachment with Content-Type application/octet-stream and X-Content-Type-Options: nosniff, plus a sandbox CSP on the download response. Any file type is allowed by the brief, so no type allow-list.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.4\", \"description\": \"Attachments are any type and downloadable with their original filename\"}]}, {\"id\": \"TM-6\", \"what_can_go_wrong\": \"An uploaded filename like ../../etc/passwd or a name with CR/LF or quotes is used in a storage path or echoed into the Content-Disposition header.\", \"impact\": \"File overwrite on the API host; response header injection.\", \"likelihood\": \"medium\", \"data_affected\": [\"attachment storage\", \"API host files\"], \"mitigation\": \"Storage keys are server-generated UUIDs; the local storage resolves paths and checks they stay under the root. Original filename is stored only as metadata, reduced to its basename, stripped of control characters, and emitted with RFC 6266/5987 filename* encoding.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"stores attachment bytes on a local volume or S3 under random keys\"}]}, {\"id\": \"TM-7\", \"what_can_go_wrong\": \"A client uploads many multi-gigabyte bodies or a slow stream to exhaust disk or memory on the UI or API.\", \"impact\": \"Denial of service.\", \"likelihood\": \"medium\", \"data_affected\": [], \"mitigation\": \"UI multer limit of 10 MB and one file; API rejects Content-Length over limit and counts bytes while streaming, aborting past 10 MB.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.4\", \"description\": \"up to 10 MB each\"}]}, {\"id\": \"TM-8\", \"what_can_go_wrong\": \"Attackers run credential stuffing against /auth/login, or hammer /auth/password/forgot to spam the outbox.\", \"impact\": \"Account takeover; resource abuse.\", \"likelihood\": \"medium\", \"data_affected\": [\"credentials\"], \"mitigation\": \"Per-email and per-client-IP fixed-window rate limits on login and forgot-password (Redis-backed, in-memory fallback), Argon2id hashing, minimum 12-character passwords with a 128 limit, generic error text.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"UI forwards X-Client-IP so the API can rate-limit per client\"}]}, {\"id\": \"TM-9\", \"what_can_go_wrong\": \"Reset tokens are guessable, reusable, long-lived, or the reset link points at an attacker host because it was built from the Host header; or forgot-password reveals which emails exist.\", \"impact\": \"Account takeover; user enumeration.\", \"likelihood\": \"medium\", \"data_affected\": [\"credentials\", \"emails\"], \"mitigation\": \"secrets.token_urlsafe(32) tokens stored as SHA-256, 30-minute expiry, single use, all sessions revoked on reset, link built from configured PUBLIC_BASE_URL, forgot always returns 202 with the same body.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.1\", \"description\": \"Forgot password: request a reset link by email, then set a new password using the link\"}]}, {\"id\": \"TM-10\", \"what_can_go_wrong\": \"Any process on the internal network (or a compromised container) calls the API directly with forged identity headers, or a stolen session token keeps working after logout, password change or deactivation.\", \"impact\": \"Impersonation of any user.\", \"likelihood\": \"low\", \"data_affected\": [\"all\"], \"mitigation\": \"Identity is never taken from a header: the API resolves the Bearer session token against the sessions table on every request and checks the user is active. The UI must also present X-Service-Token, compared in constant time. Logout deletes the session; password change/reset and deactivation delete all of the user's sessions.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"Authorization: Bearer <session token>, X-Service-Token\"}]}, {\"id\": \"TM-11\", \"what_can_go_wrong\": \"Another website auto-submits a form to the UI (e.g. remove member, change password) using the victim's cookie.\", \"impact\": \"Unwanted state changes.\", \"likelihood\": \"medium\", \"data_affected\": [\"teams\", \"tasks\", \"credentials\"], \"mitigation\": \"SameSite=Lax HttpOnly cookies (Secure and __Host- prefix in production) plus a per-session HMAC CSRF token on every POST form, verified by middleware.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"session token in an HttpOnly SameSite cookie\"}]}, {\"id\": \"TM-12\", \"what_can_go_wrong\": \"The client-supplied sort field is interpolated into SQL (ORDER BY {field}), or free-text search builds LIKE patterns by string concatenation.\", \"impact\": \"SQL injection, full database read.\", \"likelihood\": \"medium\", \"data_affected\": [\"all database contents\"], \"mitigation\": \"Sort field is validated against an enum mapped to ORM column objects; direction is an enum; search uses bound parameters with LIKE wildcards escaped.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.5\", \"description\": \"sort by any task field in either direction, with field and direction supplied by the client\"}]}, {\"id\": \"TM-13\", \"what_can_go_wrong\": \"A task title starting with =HYPERLINK(...) or =cmd|... is exported to CSV and executes when a teammate opens it in a spreadsheet.\", \"impact\": \"Code execution or data exfiltration on the victim's workstation.\", \"likelihood\": \"low\", \"data_affected\": [\"exported task data\"], \"mitigation\": \"Prefix cells beginning with = + - @ tab or CR with a single quote.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.5\", \"description\": \"Export a project's tasks as CSV\"}]}, {\"id\": \"TM-14\", \"what_can_go_wrong\": \"A cached team or project list or task detail is served to a user who was removed from the team, or cached data keyed only by object id bypasses the membership check.\", \"impact\": \"Stale-permission data disclosure.\", \"likelihood\": \"medium\", \"data_affected\": [\"tasks\", \"projects\"], \"mitigation\": \"Authorization runs against the database before any cache read; per-user list caches are invalidated on member add/remove; cache values are JSON, never pickle.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"uses Redis for cache-aside reads\"}]}, {\"id\": \"TM-15\", \"what_can_go_wrong\": \"Reset links and session tokens are written to logs, which are shipped to a log store readable by more people than the database.\", \"impact\": \"Token leakage via logs.\", \"likelihood\": \"medium\", \"data_affected\": [\"reset tokens\"], \"mitigation\": \"Session tokens and passwords are never logged. The brief requires emails to be written to the API log, so the dev mailer logs the reset email; this is accepted for this build and documented, with a real mailer replacing it in production.\", \"status\": \"accepted\", \"accepted_risk\": \"Required by the brief: there is no real email provider and emails must be readable from the API log in dev and tests.\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.1\", \"description\": \"write outgoing emails to the API log and to an outbox table\"}]}, {\"id\": \"TM-16\", \"what_can_go_wrong\": \"The first-admin management command ships a default password, or secrets are baked into images or committed in .env files.\", \"impact\": \"Trivial admin takeover.\", \"likelihood\": \"low\", \"data_affected\": [\"admin account\", \"service secrets\"], \"mitigation\": \"Command reads email and password from env vars, refuses empty or short passwords, no defaults. Secrets only in env/SSM; .env git-ignored and .dockerignore'd; no build args for secrets.\", \"status\": \"in_progress\", \"references\": [{\"type\": \"artifact\", \"location\": \"architecture_notes\", \"description\": \"Secrets ... come from environment variables populated from AWS SSM Parameter Store at boot\"}]}, {\"id\": \"TM-17\", \"what_can_go_wrong\": \"Traffic between ALB and UI, UI and API, or API and RDS/ElastiCache is sniffed inside the VPC.\", \"impact\": \"Session token and credential disclosure to a network-positioned attacker.\", \"likelihood\": \"low\", \"data_affected\": [\"session tokens\", \"DB credentials\"], \"mitigation\": \"TLS 1.2+ policy on the ALB with HTTP->HTTPS redirect; RDS with forced SSL (rds.force_ssl) and sslmode=require; ElastiCache transit encryption with auth token. UI-to-API stays HTTP inside private subnets restricted by security groups; accepted for this build and documented.\", \"status\": \"accepted\", \"accepted_risk\": \"UI-to-API hop is plain HTTP inside private subnets locked to the UI security group; adding internal TLS needs a private CA, out of scope for this build.\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"ALB --HTTP--> UI server ... calls the API over the private network\"}]}], \"summary\": \"17 threats. Highest risk: cross-team object access (TM-1), stored XSS via Markdown (TM-4), and webhook SSRF (TM-3). Archive extraction threats from the library were dropped because the app never extracts uploaded archives. MFA and breached-password checks are not in scope for this internal tool and are noted as accepted gaps in DECISIONS.\"}",
    "file_path": "/run/media/morpheuslord/Personal_Files/Projects/mcp_test_server/agent-crew-test-withmcp/docs/threat-model.md",
    "append": false
  },
  "note": "threat_model_json was sent as a single-line JSON string with the same content as evaluation/raw/T-003.produced.json"
}
```

### evaluation/raw/T-004.output.json

```json
{
  "success": true,
  "file_path": "/run/media/morpheuslord/Personal_Files/Projects/mcp_test_server/agent-crew-test-withmcp/docs/threat-model.md",
  "action": "created",
  "stats": {
    "threats_documented": 17,
    "references_linked": 17,
    "mitigated": 0,
    "open": 0
  },
  "message": "Threat model 'Taskboard (whole system)' written to /run/media/morpheuslord/Personal_Files/Projects/mcp_test_server/agent-crew-test-withmcp/docs/threat-model.md. 17 threats documented with 17 references."
}
```

### evaluation/raw/T-007.input.json

```json
{
  "tool": "mcp__sec-review__sca_verify_packages",
  "arguments": {
    "packages_json": [
      {
        "name": "fastapi",
        "version": "0.143.3",
        "ecosystem": "pypi"
      },
      {
        "name": "uvicorn",
        "version": "0.54.0",
        "ecosystem": "pypi"
      },
      {
        "name": "pydantic",
        "version": "2.14.1",
        "ecosystem": "pypi"
      },
      {
        "name": "pydantic-settings",
        "version": "2.16.0",
        "ecosystem": "pypi"
      },
      {
        "name": "sqlalchemy",
        "version": "2.1.5",
        "ecosystem": "pypi"
      },
      {
        "name": "alembic",
        "version": "1.20.0",
        "ecosystem": "pypi"
      },
      {
        "name": "psycopg",
        "version": "3.3.6",
        "ecosystem": "pypi"
      },
      {
        "name": "psycopg-binary",
        "version": "3.3.6",
        "ecosystem": "pypi"
      },
      {
        "name": "redis",
        "version": "8.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "argon2-cffi",
        "version": "25.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "python-multipart",
        "version": "0.0.32",
        "ecosystem": "pypi"
      },
      {
        "name": "httpx",
        "version": "0.28.1",
        "ecosystem": "pypi"
      },
      {
        "name": "boto3",
        "version": "1.43.114",
        "ecosystem": "pypi"
      },
      {
        "name": "email-validator",
        "version": "2.3.0",
        "ecosystem": "pypi"
      },
      {
        "name": "pytest",
        "version": "9.1.1",
        "ecosystem": "pypi"
      },
      {
        "name": "pytest-cov",
        "version": "7.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "mypy",
        "version": "2.4.0",
        "ecosystem": "pypi"
      },
      {
        "name": "ruff",
        "version": "0.17.1",
        "ecosystem": "pypi"
      },
      {
        "name": "boto3-stubs",
        "version": "1.43.114",
        "ecosystem": "pypi"
      },
      {
        "name": "moto",
        "version": "5.2.4",
        "ecosystem": "pypi"
      }
    ]
  }
}
```

### evaluation/raw/T-007.output.json

```json
{
  "all_valid": true,
  "packages_checked": 20
}
```

### evaluation/raw/T-008.input.json

```json
{
  "tool": "mcp__sec-review__sca_scan_dependencies",
  "arguments": {
    "packages_json": [
      {
        "name": "fastapi",
        "version": "0.143.3",
        "ecosystem": "pypi"
      },
      {
        "name": "uvicorn",
        "version": "0.54.0",
        "ecosystem": "pypi"
      },
      {
        "name": "pydantic",
        "version": "2.14.1",
        "ecosystem": "pypi"
      },
      {
        "name": "pydantic-settings",
        "version": "2.16.0",
        "ecosystem": "pypi"
      },
      {
        "name": "sqlalchemy",
        "version": "2.1.5",
        "ecosystem": "pypi"
      },
      {
        "name": "alembic",
        "version": "1.20.0",
        "ecosystem": "pypi"
      },
      {
        "name": "psycopg",
        "version": "3.3.6",
        "ecosystem": "pypi"
      },
      {
        "name": "psycopg-binary",
        "version": "3.3.6",
        "ecosystem": "pypi"
      },
      {
        "name": "redis",
        "version": "8.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "argon2-cffi",
        "version": "25.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "python-multipart",
        "version": "0.0.32",
        "ecosystem": "pypi"
      },
      {
        "name": "httpx",
        "version": "0.28.1",
        "ecosystem": "pypi"
      },
      {
        "name": "boto3",
        "version": "1.43.114",
        "ecosystem": "pypi"
      },
      {
        "name": "email-validator",
        "version": "2.3.0",
        "ecosystem": "pypi"
      },
      {
        "name": "pytest",
        "version": "9.1.1",
        "ecosystem": "pypi"
      },
      {
        "name": "pytest-cov",
        "version": "7.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "mypy",
        "version": "2.4.0",
        "ecosystem": "pypi"
      },
      {
        "name": "ruff",
        "version": "0.17.1",
        "ecosystem": "pypi"
      },
      {
        "name": "boto3-stubs",
        "version": "1.43.114",
        "ecosystem": "pypi"
      },
      {
        "name": "moto",
        "version": "5.2.4",
        "ecosystem": "pypi"
      }
    ]
  }
}
```

### evaluation/raw/T-008.output.json

```json
{
  "packages_scanned": 20,
  "vulnerable_count": 0,
  "status": "clean",
  "message": "No known vulnerabilities found in scanned packages."
}
```

### evaluation/raw/T-009.input.json

```json
{
  "tool": "mcp__sec-review__sca_scan_dependencies",
  "arguments": {
    "packages_json": [
      {
        "name": "annotated-doc",
        "version": "0.0.5",
        "ecosystem": "pypi"
      },
      {
        "name": "annotated-types",
        "version": "0.8.0",
        "ecosystem": "pypi"
      },
      {
        "name": "anyio",
        "version": "4.15.1",
        "ecosystem": "pypi"
      },
      {
        "name": "argon2-cffi-bindings",
        "version": "26.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "ast-serialize",
        "version": "0.13.1",
        "ecosystem": "pypi"
      },
      {
        "name": "botocore",
        "version": "1.43.114",
        "ecosystem": "pypi"
      },
      {
        "name": "botocore-stubs",
        "version": "1.43.114",
        "ecosystem": "pypi"
      },
      {
        "name": "certifi",
        "version": "2026.7.22",
        "ecosystem": "pypi"
      },
      {
        "name": "cffi",
        "version": "2.1.1",
        "ecosystem": "pypi"
      },
      {
        "name": "charset-normalizer",
        "version": "3.5.2",
        "ecosystem": "pypi"
      },
      {
        "name": "click",
        "version": "8.5.0",
        "ecosystem": "pypi"
      },
      {
        "name": "colorama",
        "version": "0.4.6",
        "ecosystem": "pypi"
      },
      {
        "name": "coverage",
        "version": "7.16.2",
        "ecosystem": "pypi"
      },
      {
        "name": "cryptography",
        "version": "50.0.2",
        "ecosystem": "pypi"
      },
      {
        "name": "dnspython",
        "version": "2.9.0",
        "ecosystem": "pypi"
      },
      {
        "name": "h11",
        "version": "0.16.0",
        "ecosystem": "pypi"
      },
      {
        "name": "httpcore",
        "version": "1.0.9",
        "ecosystem": "pypi"
      },
      {
        "name": "idna",
        "version": "3.20",
        "ecosystem": "pypi"
      },
      {
        "name": "iniconfig",
        "version": "2.3.1",
        "ecosystem": "pypi"
      },
      {
        "name": "jmespath",
        "version": "1.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "librt",
        "version": "0.16.0",
        "ecosystem": "pypi"
      },
      {
        "name": "mako",
        "version": "1.4.3",
        "ecosystem": "pypi"
      },
      {
        "name": "markupsafe",
        "version": "3.0.4",
        "ecosystem": "pypi"
      },
      {
        "name": "mypy-boto3-s3",
        "version": "1.43.106",
        "ecosystem": "pypi"
      },
      {
        "name": "mypy-extensions",
        "version": "1.1.0",
        "ecosystem": "pypi"
      },
      {
        "name": "opentelemetry-api",
        "version": "1.45.1",
        "ecosystem": "pypi"
      },
      {
        "name": "packaging",
        "version": "26.3",
        "ecosystem": "pypi"
      },
      {
        "name": "pathspec",
        "version": "1.1.1",
        "ecosystem": "pypi"
      },
      {
        "name": "pluggy",
        "version": "1.7.0",
        "ecosystem": "pypi"
      },
      {
        "name": "py-partiql-parser",
        "version": "0.6.3",
        "ecosystem": "pypi"
      },
      {
        "name": "pycparser",
        "version": "3.11",
        "ecosystem": "pypi"
      },
      {
        "name": "pydantic-core",
        "version": "2.50.1",
        "ecosystem": "pypi"
      },
      {
        "name": "pygments",
        "version": "2.21.0",
        "ecosystem": "pypi"
      },
      {
        "name": "python-dateutil",
        "version": "2.9.0.post0",
        "ecosystem": "pypi"
      },
      {
        "name": "python-dotenv",
        "version": "1.2.4",
        "ecosystem": "pypi"
      },
      {
        "name": "pyyaml",
        "version": "6.0.3",
        "ecosystem": "pypi"
      },
      {
        "name": "requests",
        "version": "2.34.2",
        "ecosystem": "pypi"
      },
      {
        "name": "responses",
        "version": "0.26.3",
        "ecosystem": "pypi"
      },
      {
        "name": "s3transfer",
        "version": "0.19.2",
        "ecosystem": "pypi"
      },
      {
        "name": "six",
        "version": "1.17.0",
        "ecosystem": "pypi"
      },
      {
        "name": "starlette",
        "version": "1.8.0",
        "ecosystem": "pypi"
      },
      {
        "name": "types-s3transfer",
        "version": "0.19.2",
        "ecosystem": "pypi"
      },
      {
        "name": "typing-extensions",
        "version": "4.16.0",
        "ecosystem": "pypi"
      },
      {
        "name": "typing-inspection",
        "version": "0.4.4",
        "ecosystem": "pypi"
      },
      {
        "name": "tzdata",
        "version": "2026.5",
        "ecosystem": "pypi"
      },
      {
        "name": "urllib3",
        "version": "2.8.0",
        "ecosystem": "pypi"
      },
      {
        "name": "werkzeug",
        "version": "3.1.9",
        "ecosystem": "pypi"
      },
      {
        "name": "xmltodict",
        "version": "1.0.4",
        "ecosystem": "pypi"
      }
    ]
  }
}
```

### evaluation/raw/T-009.output.json

```json
{
  "packages_scanned": 48,
  "vulnerable_count": 0,
  "status": "clean",
  "message": "No known vulnerabilities found in scanned packages."
}
```

### evaluation/raw/T-010.input.json

```json
{
  "tool": "mcp__sec-review__general_lightweight_security_review",
  "arguments": {
    "task_description": "Implement the Taskboard FastAPI API core: SQLAlchemy 2 models and Alembic migrations for users, sessions, password reset tokens, outbox, teams, team members, projects, tasks, comments, attachments and activity events; repositories; services for auth (register, login, logout, change password, forgot/reset password with emails written to the log and an outbox table), admin user management, teams and members, projects, tasks, comments, search with client-supplied sort field/direction and filters, CSV export, activity feeds; FastAPI routers under /api/v1 with typed error mapping, structured JSON logging with request ids, and a create-admin management command.",
    "components": "web-endpoint,database,logging-and-errors,email-sending,cryptography",
    "data_handled": "credentials,personal_data",
    "technologies": "Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, argon2-cffi"
  }
}
```

### evaluation/raw/T-010.output.json

```json
{"success":true,"review_type":"lightweight_pre_coding","status":"complete","task_description":"Implement the Taskboard FastAPI API core: SQLAlchemy 2 models and Alembic migrations for users, sessions, password reset tokens, outbox, teams, team members, projects, tasks, comments, attachments and activity events; repositories; services for auth (register, login, logout, change password, forgot/reset password with emails written to the log and an outbox table), admin user management, teams and members, projects, tasks, comments, search with client-supplied sort field/direction and filters, CSV export, activity feeds; FastAPI routers under /api/v1 with typed error mapping, structured JSON logging with request ids, and a create-admin management command.","technologies":["Python 3.13","FastAPI","Pydantic v2","SQLAlchemy 2","Alembic","PostgreSQL 16","argon2-cffi"],"assessment":{"risk_level":"critical","components":["web-endpoint","database","logging-and-errors","email-sending","cryptography"],"implied_components":[],"sensitive_data":["credentials","personal_data"],"threats":[{"id":"card-data-in-your-systems","name":"Card numbers pass through or are stored in your servers and logs","severity":"critical","cwe":["CWE-312"]},{"id":"missing-function-authorization","name":"A user calls an admin or other-role function because only the UI hides it","severity":"critical","cwe":["CWE-862"]},{"id":"sql-injection","name":"Attacker input changes the meaning of a database query","severity":"critical","cwe":["CWE-89"]},{"id":"weak-password-storage","name":"Passwords are stored in plain text or with a fast hash, so a database leak exposes them","severity":"critical","cwe":["CWE-916"]},{"id":"cleartext-transport","name":"Sensitive data travels over plain HTTP or an unencrypted connection","severity":"high","cwe":["CWE-319"]},{"id":"debug-mode-in-production","name":"Debug features or consoles are left on in production","severity":"high","cwe":["CWE-489"]},{"id":"exposed-config-files","name":".env, .git, or backup files are reachable from the web","severity":"high","cwe":["CWE-538"]},{"id":"exposed-data-store","name":"A database, cache, or admin port is reachable from the internet","severity":"high","cwe":["CWE-668"]},{"id":"hardcoded-crypto-keys","name":"Encryption or signing keys are hardcoded or shared across environments","severity":"high","cwe":["CWE-321"]},{"id":"insecure-password-reset","name":"Password reset can be abused to take over accounts","severity":"high","cwe":["CWE-640"]},{"id":"mass-assignment","name":"A request sets fields the user should not control, such as role or price","severity":"high","cwe":["CWE-915"]},{"id":"nosql-injection","name":"Query operators in user input bypass filters in a NoSQL database","severity":"high","cwe":["CWE-943"]},{"id":"object-id-guessing","name":"One user reads or changes another user's data by changing an id in the request","severity":"high","cwe":["CWE-639"]},{"id":"sensitive-data-unencrypted","name":"Sensitive fields are stored unencrypted, so a backup or database leak exposes them","severity":"high","cwe":["CWE-311"]},{"id":"tenant-data-leak","name":"Queries miss the tenant filter, so customers see each other's data","severity":"high","cwe":["CWE-284"]},{"id":"weak-crypto-algorithms","name":"Broken or outdated algorithms or modes (MD5, SHA-1, DES, ECB) protect sensitive data","severity":"high","cwe":["CWE-327"]},{"id":"weak-random-generator","name":"Tokens, ids, or nonces come from a random generator that attackers can predict","severity":"high","cwe":["CWE-338"]},{"id":"business-flow-bypass","name":"A user skips or repeats steps in a multi-step flow, such as verification or checkout","severity":"medium","cwe":["CWE-840"]},{"id":"csrf","name":"Another website makes a logged-in user's browser perform actions","severity":"medium","cwe":["CWE-352"]},{"id":"email-abuse","name":"Send endpoints are used to spam people or exhaust your sending quota","severity":"medium","cwe":["CWE-770"]},{"id":"email-header-injection","name":"Line breaks in user input add recipients or headers to outgoing mail","severity":"medium","cwe":["CWE-93"]},{"id":"excessive-data-exposure","name":"API responses include more fields than the client needs, such as hashes or internal ids","severity":"medium","cwe":["CWE-200"]},{"id":"missing-input-validation","name":"Unvalidated input reaches business logic and breaks assumptions","severity":"medium","cwe":["CWE-20"]},{"id":"missing-rate-limit","name":"Attackers hammer an endpoint to brute-force, scrape, or run up your costs","severity":"medium","cwe":["CWE-770"]},{"id":"open-redirect","name":"A link on your domain sends users to an attacker-chosen site","severity":"medium","cwe":["CWE-601"]},{"id":"over-privileged-db-account","name":"The app connects as an admin database user, so any flaw becomes full data access","severity":"medium","cwe":["CWE-250"]},{"id":"permissive-cors","name":"Any website can read authenticated API responses because CORS allows every origin","severity":"medium","cwe":["CWE-942"]},{"id":"poisoned-email-links","name":"Links in emails are built from the Host header, so attackers redirect reset links","severity":"medium","cwe":["CWE-640"]},{"id":"secrets-in-logs","name":"Passwords, tokens, or personal data are written to logs","severity":"medium","cwe":["CWE-532"]},{"id":"verbose-errors","name":"Stack traces and internal details are shown to users","severity":"medium","cwe":["CWE-209"]},{"id":"missing-security-headers","name":"Pages can be framed, sniffed, or loaded over plain HTTP because headers are missing","severity":"low","cwe":["CWE-1021"]},{"id":"no-security-logging","name":"Logins and access failures are not logged, so attacks go unnoticed","severity":"low","cwe":["CWE-778"]}],"countermeasures":[{"id":"hosted-payment-fields","name":"Use the provider's hosted card fields","how_to":"Let the payment provider collect card data directly so card numbers never touch your servers or logs.","effort":"low","asvs":[],"mitigates":["card-data-in-your-systems"]},{"id":"log-without-secrets","name":"Keep secrets and personal data out of logs","how_to":"Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.","effort":"low","asvs":["v5.0.0-16.2.5"],"mitigates":["card-data-in-your-systems","secrets-in-logs"]},{"id":"check-permissions-server-side","name":"Check permissions on the server for every action","how_to":"Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.","effort":"medium","asvs":["v5.0.0-8.2.1","v5.0.0-8.3.1"],"mitigates":["missing-function-authorization","mass-assignment"]},{"id":"parameterized-queries","name":"Use parameterized queries or an ORM","how_to":"Pass user values as parameters. Never build SQL or query documents by joining strings.","effort":"low","asvs":["v5.0.0-1.2.4"],"mitigates":["sql-injection","nosql-injection"]},{"id":"slow-password-hashing","name":"Hash passwords with a slow, salted algorithm","how_to":"Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.","effort":"low","asvs":["v5.0.0-11.4.2"],"mitigates":["weak-password-storage"]},{"id":"https-everywhere","name":"Use HTTPS for every connection","how_to":"Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.","effort":"low","asvs":["v5.0.0-12.2.1","v5.0.0-12.2.2"],"mitigates":["cleartext-transport"]},{"id":"disable-debug-in-prod","name":"Turn debug features off in production","how_to":"Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.","effort":"low","asvs":["v5.0.0-13.4.2"],"mitigates":["debug-mode-in-production"]},{"id":"no-vcs-or-env-files-deployed","name":"Do not deploy repo metadata or env files","how_to":"Exclude .git, .env, and backups from the build and the web root, and block them at the web server.","effort":"low","asvs":["v5.0.0-13.4.1"],"mitigates":["exposed-config-files"]},{"id":"secrets-manager","name":"Load secrets from a secrets manager or environment","how_to":"Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.","effort":"medium","asvs":["v5.0.0-13.3.1","v5.0.0-13.3.2"],"mitigates":["exposed-config-files","hardcoded-crypto-keys"]},{"id":"private-network-for-data-stores","name":"Keep data stores off the public internet","how_to":"Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.","effort":"low","asvs":[],"mitigates":["exposed-data-store"]},{"id":"separate-keys-per-environment","name":"Use separate keys per environment and rotate them","how_to":"Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.","effort":"medium","asvs":[],"mitigates":["hardcoded-crypto-keys"]},{"id":"secure-reset-flow","name":"Make password reset single-use and short-lived","how_to":"Send a random single-use token that expires in minutes. Show the same response whether or not the account exists, and keep MFA in force.","effort":"medium","asvs":["v5.0.0-6.4.1","v5.0.0-6.4.3"],"mitigates":["insecure-password-reset"]},{"id":"allow-list-fields","name":"Accept only the fields you expect","how_to":"Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.","effort":"low","asvs":["v5.0.0-15.3.3"],"mitigates":["mass-assignment"]},{"id":"server-side-validation","name":"Validate all input on the server","how_to":"Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.","effort":"low","asvs":["v5.0.0-2.2.1","v5.0.0-2.2.2"],"mitigates":["nosql-injection","missing-input-validation"]},{"id":"per-object-authorization","name":"Check the user owns the object on every request","how_to":"Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.","effort":"medium","asvs":["v5.0.0-8.2.2","v5.0.0-8.3.1"],"mitigates":["object-id-guessing"]},{"id":"encrypt-sensitive-data","name":"Encrypt sensitive data at rest","how_to":"Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.","effort":"medium","asvs":["v5.0.0-11.3.2"],"mitigates":["sensitive-data-unencrypted"]},{"id":"scope-queries-to-tenant","name":"Scope every query to the tenant","how_to":"Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.","effort":"medium","asvs":["v5.0.0-8.2.2"],"mitigates":["tenant-data-leak"]},{"id":"approved-crypto","name":"Use approved algorithms and modes","how_to":"Use AES-GCM or ChaCha20-Poly1305 for encryption and SHA-256 or stronger for hashing. Avoid MD5, SHA-1, DES, RC4, and ECB mode.","effort":"low","asvs":["v5.0.0-11.3.1","v5.0.0-11.3.2","v5.0.0-11.4.1"],"mitigates":["weak-crypto-algorithms"]},{"id":"crypto-random-tokens","name":"Generate tokens with a cryptographic random source","how_to":"Use secrets.token_urlsafe, crypto.randomBytes, or the framework default. Never use Math.random, time, or counters.","effort":"low","asvs":["v5.0.0-7.2.3","v5.0.0-11.5.1"],"mitigates":["weak-random-generator"]},{"id":"enforce-flow-order","name":"Enforce step order and limits on the server","how_to":"Store the state of multi-step flows on the server and reject steps that are out of order. Apply business limits there too.","effort":"medium","asvs":["v5.0.0-2.3.1","v5.0.0-2.3.2"],"mitigates":["business-flow-bypass"]},{"id":"csrf-protection","name":"Protect state-changing requests from cross-site forgery","how_to":"Use SameSite cookies plus anti-forgery tokens, and only change state with POST, PUT, PATCH, or DELETE.","effort":"low","asvs":["v5.0.0-3.5.1","v5.0.0-3.5.3","v5.0.0-3.3.2"],"mitigates":["csrf"]},{"id":"secure-cookie-attributes","name":"Set cookie security attributes","how_to":"Use Secure, HttpOnly, and SameSite on session cookies, preferably with the __Host- prefix.","effort":"low","asvs":["v5.0.0-3.3.1","v5.0.0-3.3.2","v5.0.0-3.3.4"],"mitigates":["csrf"]},{"id":"rate-limiting","name":"Rate-limit expensive or sensitive endpoints","how_to":"Limit requests per user and per IP on login, reset, send, upload, and search endpoints, and return 429 when exceeded.","effort":"medium","asvs":["v5.0.0-2.4.1"],"mitigates":["email-abuse","missing-rate-limit"]},{"id":"sanitize-mail-input","name":"Strip line breaks from mail headers","how_to":"Reject CR and LF in subject, address, and header values, and use your mail library's structured API.","effort":"low","asvs":["v5.0.0-1.3.11"],"mitigates":["email-header-injection"]},{"id":"return-minimal-fields","name":"Return only the fields the client needs","how_to":"Build response objects from an explicit list of fields instead of serializing whole database rows.","effort":"low","asvs":["v5.0.0-15.3.1"],"mitigates":["excessive-data-exposure"]},{"id":"validate-redirect-targets","name":"Redirect only to known destinations","how_to":"Accept a short key or a relative path for post-login redirects and check it against an allow-list. Never redirect to a full URL from input.","effort":"low","asvs":[],"mitigates":["open-redirect"]},{"id":"least-privilege-accounts","name":"Give the app a least-privilege database account","how_to":"Create a user limited to the tables and operations the app needs. Keep migrations on a separate admin account.","effort":"medium","asvs":[],"mitigates":["over-privileged-db-account"]},{"id":"strict-cors","name":"Allow only the origins you trust","how_to":"Return a fixed allow-list for Access-Control-Allow-Origin. Never reflect the request origin or use * with credentials.","effort":"low","asvs":["v5.0.0-3.4.2","v5.0.0-3.5.2"],"mitigates":["permissive-cors"]},{"id":"fixed-base-url-for-links","name":"Build links from a configured base URL","how_to":"Take the public base URL from configuration, not from the Host or X-Forwarded headers of the request.","effort":"low","asvs":["v5.0.0-4.1.3"],"mitigates":["poisoned-email-links"]},{"id":"generic-error-messages","name":"Return generic errors to users","how_to":"Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.","effort":"low","asvs":["v5.0.0-16.5.1"],"mitigates":["verbose-errors"]},{"id":"security-headers","name":"Send the standard security headers","how_to":"Set Strict-Transport-Security, Content-Security-Policy with frame-ancestors, X-Content-Type-Options nosniff, and a referrer policy.","effort":"low","asvs":["v5.0.0-3.4.1","v5.0.0-3.4.3","v5.0.0-3.4.4","v5.0.0-3.4.5","v5.0.0-3.4.6"],"mitigates":["missing-security-headers"]},{"id":"log-security-events","name":"Log security-relevant events","how_to":"Log logins, failures, permission denials, and admin actions with time, user, and source, and alert on spikes.","effort":"medium","asvs":["v5.0.0-16.3.1","v5.0.0-16.3.2"],"mitigates":["no-security-logging"]}],"also_consider":[],"summary":"32 threats and 32 countermeasures for web-endpoint, database, logging-and-errors, email-sending, cryptography. Risk level critical (highest threat severity, raised for sensitive data)."},"hint":null,"instructions":"Build these countermeasures in as you write the code, starting with the most severe threats. These threats come from the components you picked. also_consider lists general threats from implied components; pass those components explicitly for full detail. After writing code, call general_verify_code_security with the same components.","metadata":{"total_threats":32,"total_countermeasures":32,"also_consider_total":0,"review_purpose":"lightweight_security_guidance"}}
```

### evaluation/raw/T-011.input.json

```json
{
  "tool": "mcp__sec-review__general_lightweight_security_review",
  "arguments": {
    "task_description": "Implement Taskboard API task attachments and project webhooks: multipart upload of any file type up to 10 MB per file to a task, stored through an AttachmentStorage interface (local filesystem volume in dev, Amazon S3 in AWS) under server-generated keys, listed and downloaded with the original filename; and an outbound webhook notifier that, when a task changes status, POSTs a JSON event to the project's user-configured webhook URL asynchronously from a background thread pool with a short retry.",
    "components": "file-upload,object-storage,outbound-http-request,background-job",
    "technologies": "Python 3.13, FastAPI, python-multipart, boto3, httpx"
  }
}
```

### evaluation/raw/T-011.output.json

```json
{"success":true,"review_type":"lightweight_pre_coding","status":"complete","task_description":"Implement Taskboard API task attachments and project webhooks: multipart upload of any file type up to 10 MB per file to a task, stored through an AttachmentStorage interface (local filesystem volume in dev, Amazon S3 in AWS) under server-generated keys, listed and downloaded with the original filename; and an outbound webhook notifier that, when a task changes status, POSTs a JSON event to the project's user-configured webhook URL asynchronously from a background thread pool with a short retry.","technologies":["Python 3.13","FastAPI","python-multipart","boto3","httpx"],"assessment":{"risk_level":"high","components":["file-upload","object-storage","outbound-http-request","background-job"],"implied_components":["web-endpoint"],"sensitive_data":[],"threats":[{"id":"archive-path-traversal","name":"An uploaded archive writes files outside the target folder when extracted","severity":"high","cwe":["CWE-22"]},{"id":"long-lived-storage-credentials","name":"Long-lived storage keys are shipped to the browser or mobile app","severity":"high","cwe":["CWE-798"]},{"id":"object-id-guessing","name":"One user reads or changes another user's data by changing an id in the request","severity":"high","cwe":["CWE-639"]},{"id":"public-bucket","name":"Storage bucket is publicly listable or readable","severity":"high","cwe":["CWE-732"]},{"id":"sensitive-data-unencrypted","name":"Sensitive fields are stored unencrypted, so a backup or database leak exposes them","severity":"high","cwe":["CWE-311"]},{"id":"ssrf","name":"The server is tricked into fetching internal addresses or cloud metadata","severity":"high","cwe":["CWE-918"]},{"id":"tls-verification-disabled","name":"Outbound calls skip certificate checks, so traffic can be intercepted","severity":"high","cwe":["CWE-295"]},{"id":"upload-executable-file","name":"Attacker uploads a script that your server runs or serves","severity":"high","cwe":["CWE-434"]},{"id":"upload-path-traversal","name":"Attacker uses ../ in a filename to overwrite files","severity":"high","cwe":["CWE-22"]},{"id":"missing-input-validation","name":"Unvalidated input reaches business logic and breaks assumptions","severity":"medium","cwe":["CWE-20"]},{"id":"untrusted-job-payload","name":"Queue messages are trusted without checking, so one bad message breaks the worker or the data","severity":"medium","cwe":["CWE-20"]},{"id":"upload-active-content","name":"An uploaded SVG or HTML file runs script when other users open it","severity":"medium","cwe":["CWE-79"]},{"id":"upload-resource-exhaustion","name":"Huge files or compression bombs fill disk or memory","severity":"medium","cwe":["CWE-770"]},{"id":"no-timeouts-or-size-caps","name":"A slow or huge remote response ties up workers and memory","severity":"low","cwe":["CWE-400"]},{"id":"runaway-retries","name":"Failing jobs retry forever and starve other work","severity":"low","cwe":["CWE-400"]}],"countermeasures":[{"id":"safe-archive-extraction","name":"Extract archives safely","how_to":"Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.","effort":"medium","asvs":["v5.0.0-5.3.3","v5.0.0-5.2.3"],"mitigates":["archive-path-traversal"]},{"id":"short-lived-scoped-credentials","name":"Give clients short-lived, narrowly scoped credentials","how_to":"Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.","effort":"medium","asvs":[],"mitigates":["long-lived-storage-credentials"]},{"id":"per-object-authorization","name":"Check the user owns the object on every request","how_to":"Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.","effort":"medium","asvs":["v5.0.0-8.2.2","v5.0.0-8.3.1"],"mitigates":["object-id-guessing"]},{"id":"private-storage-signed-urls","name":"Keep storage private and hand out short-lived signed URLs","how_to":"Block public access on the bucket and issue signed URLs that expire in minutes.","effort":"low","asvs":[],"mitigates":["public-bucket"]},{"id":"encrypt-sensitive-data","name":"Encrypt sensitive data at rest","how_to":"Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.","effort":"medium","asvs":["v5.0.0-11.3.2"],"mitigates":["sensitive-data-unencrypted"]},{"id":"ssrf-allow-list","name":"Fetch only allow-listed destinations","how_to":"Resolve the host, block private, loopback, and link-local ranges including cloud metadata, and prefer a fixed allow-list of hosts.","effort":"medium","asvs":["v5.0.0-1.3.6","v5.0.0-13.2.4"],"mitigates":["ssrf"]},{"id":"no-redirect-following","name":"Do not follow redirects on server-side fetches","how_to":"Disable automatic redirects, or re-validate each hop against the same allow-list.","effort":"low","asvs":["v5.0.0-15.3.2"],"mitigates":["ssrf"]},{"id":"validate-tls-certificates","name":"Always verify TLS certificates","how_to":"Never set verify=False or NODE_TLS_REJECT_UNAUTHORIZED=0. Add your private CA to the trust store if needed.","effort":"low","asvs":["v5.0.0-12.3.2"],"mitigates":["tls-verification-disabled"]},{"id":"upload-allow-list","name":"Allow only the file types you need","how_to":"Check the extension and the real file content against an allow-list. Ignore the client's Content-Type.","effort":"low","asvs":["v5.0.0-5.2.2"],"mitigates":["upload-executable-file"]},{"id":"upload-rename-and-isolate","name":"Never use the user's filename or path","how_to":"Generate your own filenames, store files outside the web root, and make sure uploads are never executed.","effort":"low","asvs":["v5.0.0-5.3.1","v5.0.0-5.3.2"],"mitigates":["upload-executable-file","upload-path-traversal"]},{"id":"server-side-validation","name":"Validate all input on the server","how_to":"Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.","effort":"low","asvs":["v5.0.0-2.2.1","v5.0.0-2.2.2"],"mitigates":["missing-input-validation"]},{"id":"validate-job-input","name":"Validate job payloads like any other input","how_to":"Check the schema of every queue message and drop or dead-letter anything that does not match.","effort":"low","asvs":["v5.0.0-2.2.1"],"mitigates":["untrusted-job-payload"]},{"id":"serve-uploads-safely","name":"Serve uploads so browsers cannot run them","how_to":"Send the correct Content-Type, Content-Disposition attachment for downloads, nosniff, and serve user files from a separate domain.","effort":"low","asvs":["v5.0.0-4.1.1","v5.0.0-5.4.2","v5.0.0-3.2.1"],"mitigates":["upload-active-content"]},{"id":"sanitize-html","name":"Sanitize user-provided HTML","how_to":"Run user HTML through a maintained sanitizer such as DOMPurify or bleach with a strict allow-list. Prefer markdown or plain text.","effort":"low","asvs":["v5.0.0-1.3.1"],"mitigates":["upload-active-content"]},{"id":"upload-size-limits","name":"Limit file size and decompressed size","how_to":"Set a maximum size per file, and cap decompressed size and file count for archives.","effort":"low","asvs":["v5.0.0-5.2.1","v5.0.0-5.2.3"],"mitigates":["upload-resource-exhaustion"]},{"id":"timeouts-and-size-caps","name":"Set timeouts and response size caps","how_to":"Use connect and read timeouts and a maximum body size on every outbound call and queue consumer.","effort":"low","asvs":["v5.0.0-15.2.2"],"mitigates":["no-timeouts-or-size-caps"]},{"id":"bounded-retries","name":"Bound retries with backoff","how_to":"Cap retry counts, use exponential backoff, and send failures to a dead-letter queue.","effort":"low","asvs":["v5.0.0-15.2.2"],"mitigates":["runaway-retries"]}],"also_consider":[{"id":"missing-function-authorization","name":"A user calls an admin or other-role function because only the UI hides it","severity":"critical"},{"id":"cleartext-transport","name":"Sensitive data travels over plain HTTP or an unencrypted connection","severity":"high"},{"id":"debug-mode-in-production","name":"Debug features or consoles are left on in production","severity":"high"},{"id":"exposed-config-files","name":".env, .git, or backup files are reachable from the web","severity":"high"},{"id":"mass-assignment","name":"A request sets fields the user should not control, such as role or price","severity":"high"},{"id":"business-flow-bypass","name":"A user skips or repeats steps in a multi-step flow, such as verification or checkout","severity":"medium"},{"id":"csrf","name":"Another website makes a logged-in user's browser perform actions","severity":"medium"},{"id":"excessive-data-exposure","name":"API responses include more fields than the client needs, such as hashes or internal ids","severity":"medium"}],"summary":"15 threats and 17 countermeasures for file-upload, object-storage, outbound-http-request, background-job. Risk level high (highest threat severity)."},"hint":null,"instructions":"Build these countermeasures in as you write the code, starting with the most severe threats. These threats come from the components you picked. also_consider lists general threats from implied components; pass those components explicitly for full detail. After writing code, call general_verify_code_security with the same components.","metadata":{"total_threats":15,"total_countermeasures":17,"also_consider_total":13,"review_purpose":"lightweight_security_guidance"}}
```

### evaluation/raw/T-014.input.json

```json
{
  "tool": "mcp__sec-review__general_verify_code_security",
  "arguments": {
    "components": "web-endpoint,database,logging-and-errors,email-sending,cryptography",
    "data_handled": "credentials,personal_data",
    "file_path": "api/src/taskboard"
  }
}
```

### evaluation/raw/T-014.output.json

```json
{
  "success": true,
  "review_type": "ai_powered_security_review",
  "instructions": "IMPORTANT: You (the AI agent) must now perform the security review. The code is not included here: review the code you just wrote, which is already in your context, using the checklist and focus areas. Report all security issues found with severity ratings and fixes.",
  "review_prompt": "## SECURITY CODE REVIEW REQUEST\n\n**File:** `api/src/taskboard`\n**Components:** web-endpoint, database, logging-and-errors, email-sending, cryptography\n**Risk Level:** CRITICAL\n\n### Review Instructions\n\nReview the code you just wrote (it is already in your context) for security vulnerabilities. For each issue found:\n1. Identify the vulnerability type and severity (Critical/High/Medium/Low)\n2. Explain why it's a security risk\n3. Show the problematic code snippet\n4. Provide a secure code fix\n\n### Focus Areas\n\nPay special attention to:\n- Card numbers pass through or are stored in your servers and logs\n- A user calls an admin or other-role function because only the UI hides it\n- Attacker input changes the meaning of a database query\n- Passwords are stored in plain text or with a fast hash, so a database leak exposes them\n- Sensitive data travels over plain HTTP or an unencrypted connection\n- Debug features or consoles are left on in production\n- .env, .git, or backup files are reachable from the web\n- A database, cache, or admin port is reachable from the internet\n- Encryption or signing keys are hardcoded or shared across environments\n- Password reset can be abused to take over accounts\n- A request sets fields the user should not control, such as role or price\n- Query operators in user input bypass filters in a NoSQL database\n\n### Security Checklist\n\nVerify each item and report violations:\n- [ ] Use the provider's hosted card fields: Let the payment provider collect card data directly so card numbers never touch your servers or logs.\n- [ ] Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.\n- [ ] Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.\n- [ ] Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.\n- [ ] Hash passwords with a slow, salted algorithm: Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.\n- [ ] Use HTTPS for every connection: Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.\n- [ ] Turn debug features off in production: Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.\n- [ ] Do not deploy repo metadata or env files: Exclude .git, .env, and backups from the build and the web root, and block them at the web server.\n- [ ] Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.\n- [ ] Keep data stores off the public internet: Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.\n- [ ] Use separate keys per environment and rotate them: Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.\n- [ ] Make password reset single-use and short-lived: Send a random single-use token that expires in minutes. Show the same response whether or not the account exists, and keep MFA in force.\n- [ ] Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.\n- [ ] Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.\n- [ ] Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.\n- [ ] Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.\n\n### Expected Response Format\n\nProvide your security review with:\n1. **Summary:** Overall assessment (Secure/Needs Attention/Insecure)\n2. **Findings:** List of security issues with severity and fixes\n3. **Checklist Results:** Which items pass/fail\n4. **Recommendations:** Prioritized list of actions",
  "context": {
    "file_path": "api/src/taskboard",
    "components": [
      "web-endpoint",
      "database",
      "logging-and-errors",
      "email-sending",
      "cryptography"
    ],
    "risk_level": "critical"
  },
  "security_checklist": [
    "Use the provider's hosted card fields: Let the payment provider collect card data directly so card numbers never touch your servers or logs.",
    "Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.",
    "Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.",
    "Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.",
    "Hash passwords with a slow, salted algorithm: Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.",
    "Use HTTPS for every connection: Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.",
    "Turn debug features off in production: Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.",
    "Do not deploy repo metadata or env files: Exclude .git, .env, and backups from the build and the web root, and block them at the web server.",
    "Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.",
    "Keep data stores off the public internet: Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.",
    "Use separate keys per environment and rotate them: Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.",
    "Make password reset single-use and short-lived: Send a random single-use token that expires in minutes. Show the same response whether or not the account exists, and keep MFA in force.",
    "Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.",
    "Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.",
    "Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.",
    "Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials."
  ],
  "focus_areas": [
    "Card numbers pass through or are stored in your servers and logs",
    "A user calls an admin or other-role function because only the UI hides it",
    "Attacker input changes the meaning of a database query",
    "Passwords are stored in plain text or with a fast hash, so a database leak exposes them",
    "Sensitive data travels over plain HTTP or an unencrypted connection",
    "Debug features or consoles are left on in production",
    ".env, .git, or backup files are reachable from the web",
    "A database, cache, or admin port is reachable from the internet",
    "Encryption or signing keys are hardcoded or shared across environments",
    "Password reset can be abused to take over accounts",
    "A request sets fields the user should not control, such as role or price",
    "Query operators in user input bypass filters in a NoSQL database"
  ],
  "expected_response": {
    "format": "structured_security_review",
    "required_sections": [
      "overall_assessment",
      "findings_list",
      "checklist_results",
      "recommended_fixes"
    ]
  }
}
```

### evaluation/raw/T-014.review.md

```markdown
# Review produced by following the T-014 review_prompt

Scope: `api/src/taskboard` as of the phase 3 baseline commit. Components: web-endpoint, database, logging-and-errors,
email-sending, cryptography. I reviewed the code against the returned checklist and focus areas, re-reading each
module (`api/deps.py`, `api/errors.py`, `api/middleware.py`, every router, `services/*`, `repositories/sqlalchemy/*`,
`infra/mailer.py`, `infra/rate_limit.py`, `logging_setup.py`, `config.py`, `main.py`).

## 1. Summary

**Needs Attention.** No critical or high issues. Two medium and three low issues, listed below with fixes.

## 2. Findings

| # | Severity (mine) | Issue | Where | Fix |
| --- | --- | --- | --- | --- |
| R14-1 | Medium | Login lockout is keyed by email alone. Anyone can lock a victim out for 15 minutes with 5 bad passwords, which is the "lockout as a DoS tool" case the T-002 `login-attempt-limits` countermeasure warns about. | `services/auth.py` `login()`: `failure_key = limiter_key("login-fail", email)` | Count failures per email+client IP (lock after 5), plus a much higher per-email ceiling (50 per window) that slows distributed guessing without letting one client lock others out. → F-070 |
| R14-2 | Low | `GET /api/v1/openapi.json` is served without the service token, because FastAPI registers it outside the `/api/v1` router that carries the `require_service_auth` dependency. Any workload on the internal network can read the full API surface. | `main.py` `openapi_url=f"{API_PREFIX}/openapi.json"` | Disable FastAPI's built-in route and serve the document from a route inside the authenticated v1 router. Docs UI stays off unless `ENABLE_DOCS=true`. → F-071 |
| R14-3 | Low | Every route accepts request bodies up to 10 MB + 64 KB (the attachment limit), so JSON endpoints parse multi-megabyte bodies before Pydantic rejects oversized fields. | `api/middleware.py` `BodySizeLimitMiddleware` applies one limit everywhere | Use a 256 KB limit for all routes except the attachment upload route. → F-074 |
| R14-4 | Low | `POST /auth/password/change` verifies the current password without any throttle. A stolen session can be used to guess the password and turn temporary access into a permanent credential. | `services/auth.py` `change_password()` | Count failed current-password checks per user and return 429 after the login failure limit. → F-075 |
| R14-5 | Low | Expired session rows are never removed, so the `sessions` table grows without bound. | `repositories/sqlalchemy/accounts.py` | Delete the user's expired sessions whenever a new session is issued. → F-078 |

## 3. Checklist results

| Checklist item | Result | Evidence |
| --- | --- | --- |
| Use the provider's hosted card fields | N/A | No payment data exists (F-055, false positive). |
| Keep secrets and personal data out of logs | Pass, with an accepted exception | Passwords, session tokens and request bodies are never logged. The access log records the path, not the query string. `SecretStr` hides DB/Redis URLs. Exception: the dev mailer logs reset emails, which the brief requires (F-051). |
| Check permissions on the server for every action | Pass | Every service method goes through `AccessPolicy` (`team_for_member`, `team_for_manager`, `project_for_writer`, `task_for_writer`, `require_admin`). Admin routes call `require_admin` in the service. |
| Use parameterized queries or an ORM | Pass | SQLAlchemy Core/ORM only. `escape_like` plus `ilike(..., escape="\\")`. Sorting goes through the `_SORT_COLUMNS` enum map. Integration test sends `sort=title; DROP TABLE tasks` and gets 422. |
| Hash passwords with a slow, salted algorithm | Pass | `Argon2PasswordHasher` (argon2id, library defaults); dummy-hash `burn()` for unknown accounts. |
| Use HTTPS for every connection | Partial | Production config requires an `https` `PUBLIC_BASE_URL`. The ALB, RDS and ElastiCache TLS are infra work (phase 6). The UI-to-API hop is HTTP in private subnets (TM-17, F-004). |
| Turn debug features off in production | Fail → R14-2 | `ENVIRONMENT` defaults to production, docs are off by default, and errors are generic. `openapi.json` was unauthenticated. |
| Do not deploy repo metadata or env files | Open (phase 7) | Dockerfile and `.dockerignore` not written yet (F-008). |
| Load secrets from a secrets manager or environment | Pass | All secrets come from env via `Settings`. Minimum 32 characters for the service and webhook secrets; no defaults. |
| Keep data stores off the public internet | Open (phases 6/7) | Compose and Terraform not written yet (F-057). |
| Use separate keys per environment and rotate them | Pass for code | No key is embedded in code; each environment supplies its own. |
| Make password reset single-use and short-lived | Pass | 256-bit token, SHA-256 at rest, 30 minutes, consumed with an atomic `UPDATE ... RETURNING`, older tokens invalidated, same 202 response, sessions revoked on reset. |
| Accept only the fields you expect | Pass | `RequestModel` has `extra="forbid"`. Integration test: `role` in the register body gets 422. |
| Validate all input on the server | Pass | Lengths and bounds on every field; UUID path params; enums for status, priority, sort and order; `TaskUpdate` rejects null for non-clearable fields. |
| Check the user owns the object on every request | Pass | Cross-team probe test covers 13 endpoints, which all return 404. |
| Return generic errors to users | Pass | One error shape with `request_id`. 500s are generic. Unknown email and wrong password give the same message. Register reveals existing emails (409), accepted (F-029). |

Focus areas not covered above: NoSQL injection does not apply (F-056). Email header injection is blocked by the CR/LF
check in `LogOutboxMailer`. Reset links use `PUBLIC_BASE_URL`, never request headers.

## 4. Recommendations (prioritised)

1. R14-1 lockout DoS (F-070).
2. R14-4 change-password throttle (F-075).
3. R14-2 authenticate the OpenAPI document (F-071).
4. R14-3 smaller body limit for JSON routes (F-074).
5. R14-5 purge expired sessions (F-078).
```

### evaluation/raw/T-015.input.json

```json
{
  "tool": "mcp__sec-review__general_verify_code_security",
  "arguments": {
    "components": "file-upload,object-storage,outbound-http-request,background-job",
    "file_path": "api/src/taskboard"
  }
}
```

### evaluation/raw/T-015.output.json

```json
{
  "success": true,
  "review_type": "ai_powered_security_review",
  "instructions": "IMPORTANT: You (the AI agent) must now perform the security review. The code is not included here: review the code you just wrote, which is already in your context, using the checklist and focus areas. Report all security issues found with severity ratings and fixes.",
  "review_prompt": "## SECURITY CODE REVIEW REQUEST\n\n**File:** `api/src/taskboard`\n**Components:** file-upload, object-storage, outbound-http-request, background-job\n**Risk Level:** HIGH\n\n### Review Instructions\n\nReview the code you just wrote (it is already in your context) for security vulnerabilities. For each issue found:\n1. Identify the vulnerability type and severity (Critical/High/Medium/Low)\n2. Explain why it's a security risk\n3. Show the problematic code snippet\n4. Provide a secure code fix\n\n### Focus Areas\n\nPay special attention to:\n- An uploaded archive writes files outside the target folder when extracted\n- Long-lived storage keys are shipped to the browser or mobile app\n- One user reads or changes another user's data by changing an id in the request\n- Storage bucket is publicly listable or readable\n- Sensitive fields are stored unencrypted, so a backup or database leak exposes them\n- The server is tricked into fetching internal addresses or cloud metadata\n- Outbound calls skip certificate checks, so traffic can be intercepted\n- Attacker uploads a script that your server runs or serves\n- Attacker uses ../ in a filename to overwrite files\n- Unvalidated input reaches business logic and breaks assumptions\n- Queue messages are trusted without checking, so one bad message breaks the worker or the data\n- An uploaded SVG or HTML file runs script when other users open it\n\n### Security Checklist\n\nVerify each item and report violations:\n- [ ] Extract archives safely: Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.\n- [ ] Give clients short-lived, narrowly scoped credentials: Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.\n- [ ] Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.\n- [ ] Keep storage private and hand out short-lived signed URLs: Block public access on the bucket and issue signed URLs that expire in minutes.\n- [ ] Encrypt sensitive data at rest: Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.\n- [ ] Fetch only allow-listed destinations: Resolve the host, block private, loopback, and link-local ranges including cloud metadata, and prefer a fixed allow-list of hosts.\n- [ ] Do not follow redirects on server-side fetches: Disable automatic redirects, or re-validate each hop against the same allow-list.\n- [ ] Always verify TLS certificates: Never set verify=False or NODE_TLS_REJECT_UNAUTHORIZED=0. Add your private CA to the trust store if needed.\n- [ ] Allow only the file types you need: Check the extension and the real file content against an allow-list. Ignore the client's Content-Type.\n- [ ] Never use the user's filename or path: Generate your own filenames, store files outside the web root, and make sure uploads are never executed.\n- [ ] Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.\n- [ ] Validate job payloads like any other input: Check the schema of every queue message and drop or dead-letter anything that does not match.\n- [ ] Serve uploads so browsers cannot run them: Send the correct Content-Type, Content-Disposition attachment for downloads, nosniff, and serve user files from a separate domain.\n- [ ] Sanitize user-provided HTML: Run user HTML through a maintained sanitizer such as DOMPurify or bleach with a strict allow-list. Prefer markdown or plain text.\n- [ ] Limit file size and decompressed size: Set a maximum size per file, and cap decompressed size and file count for archives.\n- [ ] Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.\n- [ ] Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.\n- [ ] Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.\n- [ ] Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.\n\n### Expected Response Format\n\nProvide your security review with:\n1. **Summary:** Overall assessment (Secure/Needs Attention/Insecure)\n2. **Findings:** List of security issues with severity and fixes\n3. **Checklist Results:** Which items pass/fail\n4. **Recommendations:** Prioritized list of actions",
  "context": {
    "file_path": "api/src/taskboard",
    "components": [
      "file-upload",
      "object-storage",
      "outbound-http-request",
      "background-job"
    ],
    "risk_level": "high"
  },
  "security_checklist": [
    "Extract archives safely: Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.",
    "Give clients short-lived, narrowly scoped credentials: Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.",
    "Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.",
    "Keep storage private and hand out short-lived signed URLs: Block public access on the bucket and issue signed URLs that expire in minutes.",
    "Encrypt sensitive data at rest: Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.",
    "Fetch only allow-listed destinations: Resolve the host, block private, loopback, and link-local ranges including cloud metadata, and prefer a fixed allow-list of hosts.",
    "Do not follow redirects on server-side fetches: Disable automatic redirects, or re-validate each hop against the same allow-list.",
    "Always verify TLS certificates: Never set verify=False or NODE_TLS_REJECT_UNAUTHORIZED=0. Add your private CA to the trust store if needed.",
    "Allow only the file types you need: Check the extension and the real file content against an allow-list. Ignore the client's Content-Type.",
    "Never use the user's filename or path: Generate your own filenames, store files outside the web root, and make sure uploads are never executed.",
    "Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.",
    "Validate job payloads like any other input: Check the schema of every queue message and drop or dead-letter anything that does not match.",
    "Serve uploads so browsers cannot run them: Send the correct Content-Type, Content-Disposition attachment for downloads, nosniff, and serve user files from a separate domain.",
    "Sanitize user-provided HTML: Run user HTML through a maintained sanitizer such as DOMPurify or bleach with a strict allow-list. Prefer markdown or plain text.",
    "Limit file size and decompressed size: Set a maximum size per file, and cap decompressed size and file count for archives.",
    "Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.",
    "Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.",
    "Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.",
    "Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies."
  ],
  "focus_areas": [
    "An uploaded archive writes files outside the target folder when extracted",
    "Long-lived storage keys are shipped to the browser or mobile app",
    "One user reads or changes another user's data by changing an id in the request",
    "Storage bucket is publicly listable or readable",
    "Sensitive fields are stored unencrypted, so a backup or database leak exposes them",
    "The server is tricked into fetching internal addresses or cloud metadata",
    "Outbound calls skip certificate checks, so traffic can be intercepted",
    "Attacker uploads a script that your server runs or serves",
    "Attacker uses ../ in a filename to overwrite files",
    "Unvalidated input reaches business logic and breaks assumptions",
    "Queue messages are trusted without checking, so one bad message breaks the worker or the data",
    "An uploaded SVG or HTML file runs script when other users open it"
  ],
  "expected_response": {
    "format": "structured_security_review",
    "required_sections": [
      "overall_assessment",
      "findings_list",
      "checklist_results",
      "recommended_fixes"
    ]
  }
}
```

### evaluation/raw/T-015.review.md

```markdown
# Review produced by following the T-015 review_prompt

Scope: `api/src/taskboard` attachment and webhook code as of the phase 3 baseline commit: `services/attachments.py`,
`infra/storage/*`, `infra/webhooks/*`, `services/tasks.py`, `api/routers/tasks.py`, `api/middleware.py`. Components:
file-upload, object-storage, outbound-http-request, background-job.

## 1. Summary

**Needs Attention.** No critical or high issues. One medium and two low issues. One checklist item is an accepted
deviation, because the brief allows any file type.

## 2. Findings

| # | Severity (mine) | Issue | Where | Fix |
| --- | --- | --- | --- | --- |
| R15-1 | Medium | Webhook bodies are signed with one deployment-wide secret. A receiver can only verify a signature if it holds that secret, and giving it to one project's receiver would let that receiver forge events to every other project's receiver. As built, the signature protects nothing. | `infra/webhooks/notifier.py` `sign()` uses `self._secret` for every project | Derive a per-project key `HMAC(WEBHOOK_SIGNING_SECRET, "project:" + project_id)`, sign with it, and show it only to the project's owner and admins in the project response, so each receiver gets a key that is useless elsewhere. → F-077 |
| R15-2 | Low | `ThreadPoolExecutor` has 4 workers but an unbounded work queue. A burst of status changes against slow or blackholed receivers (up to 3 × 3 s timeouts plus backoff each) piles up delivery jobs in memory without limit. | `infra/webhooks/notifier.py` `notify()` | Cap pending deliveries with a non-blocking `BoundedSemaphore` (default 500). Drop and log beyond that; delivery is best effort per the brief. → F-072 |
| R15-3 | Low | Timeouts apply per read, so a receiver that drips one byte just inside the read timeout can hold a worker for minutes, despite the 64 KiB cap. | `infra/webhooks/notifier.py` `_attempt()` read loop | Add an overall per-attempt deadline (2 × timeout) checked while reading. → F-073 |

## 3. Checklist results

| Checklist item | Result | Evidence |
| --- | --- | --- |
| Extract archives safely | N/A | Uploads are never extracted (F-046). |
| Short-lived scoped credentials for clients | N/A | No storage credentials reach clients (F-066). |
| Check the user owns the object on every request | Pass | `AttachmentService.open` resolves attachment → task → team membership; 404 otherwise. |
| Keep storage private, signed URLs | Pass (design differs) | No public URLs: downloads stream through API and UI after an authorization check. Bucket privacy is infra work (F-065, phase 6). |
| Encrypt sensitive data at rest | Pass for code | `S3Storage.save` sets `ServerSideEncryption="aws:kms"`. RDS and EBS encryption are infra work (F-058). |
| Fetch only allow-listed destinations | Pass | `WebhookUrlPolicy`: https only, no userinfo, every resolved address must be global and outside CGNAT/NAT64/6to4/IPv4-mapped private ranges, checked at save and before each attempt. |
| Do not follow redirects | Pass | `follow_redirects=False`. Unit test returns 302 to the metadata address and checks it is not followed. |
| Always verify TLS certificates | Pass | httpx default `verify=True`; SNI and hostname verification use the original host via the `sni_hostname` extension; `trust_env=False`. |
| Allow only the file types you need | Accepted deviation | The brief requires any type (F-047). Mitigated by serving as `application/octet-stream` + `attachment` + `nosniff` + `CSP: sandbox`. |
| Never use the user's filename or path | Pass | Keys `attachments/<uuid4 hex>` matched by a strict regex; the local backend also checks the resolved path stays under the root; the filename is metadata only (`clean_filename`). |
| Validate all input on the server | Pass | See T-014 review. |
| Validate job payloads | Pass | Jobs are typed `StatusChangedEvent` dataclasses built in-process; the URL is re-validated on every attempt. |
| Serve uploads so browsers cannot run them | Partial | Correct headers are set. "Serve user files from a separate domain" is not done; it is an accepted risk mitigated by `CSP: sandbox` (F-079). |
| Sanitize user-provided HTML | Open (phase 5) | Markdown rendering is in the UI (F-039). |
| Limit file size | Pass | Body-size middleware, a byte counter in `AttachmentService.upload`, and a multer limit in the UI (phase 5). Integration tests check 413 for both paths. |
| Use parameterized queries | Pass | ORM only. |
| Load secrets from environment | Pass | `WEBHOOK_SIGNING_SECRET` from env, at least 32 characters. |
| Return generic errors | Pass | Storage errors become generic 500s; a missing blob becomes 404 and is logged. |
| Keep secrets and personal data out of logs | Pass | Webhook logs never include the URL (which may embed a secret), only status, attempt and error class. |

## 4. Recommendations (prioritised)

1. R15-1 per-project webhook signing keys (F-077).
2. R15-2 bound the delivery backlog (F-072).
3. R15-3 per-attempt deadline (F-073).
```

### evaluation/raw/T-017.input.json

```json
{
  "tool": "mcp__sec-review__general_lightweight_security_review",
  "arguments": {
    "task_description": "Add a cache-aside layer to the Taskboard FastAPI API using Redis 7 (redis-py): cache a user's team list and project list, task lists per project per page/filter/sort combination, task detail and user profile. Every write invalidates the affected keys after the database commit (versioned keys for task-list families), TTLs are a backstop. Values are JSON. The cache sits behind an interface with Redis, in-memory and no-op implementations; on Redis errors it degrades to cache misses. Hit/miss counters are exposed on an admin-only stats endpoint and logged at debug level. Authorization checks always run against PostgreSQL before cached data is returned.",
    "components": "database,authorization,serialization-and-parsing,logging-and-errors",
    "technologies": "Python 3.13, FastAPI, redis-py, Redis 7, PostgreSQL 16"
  }
}
```

### evaluation/raw/T-017.output.json

```json
{"success":true,"review_type":"lightweight_pre_coding","status":"complete","task_description":"Add a cache-aside layer to the Taskboard FastAPI API using Redis 7 (redis-py): cache a user's team list and project list, task lists per project per page/filter/sort combination, task detail and user profile. Every write invalidates the affected keys after the database commit (versioned keys for task-list families), TTLs are a backstop. Values are JSON. The cache sits behind an interface with Redis, in-memory and no-op implementations; on Redis errors it degrades to cache misses. Hit/miss counters are exposed on an admin-only stats endpoint and logged at debug level. Authorization checks always run against PostgreSQL before cached data is returned.","technologies":["Python 3.13","FastAPI","redis-py","Redis 7","PostgreSQL 16"],"assessment":{"risk_level":"critical","components":["database","authorization","serialization-and-parsing","logging-and-errors"],"implied_components":[],"sensitive_data":[],"threats":[{"id":"card-data-in-your-systems","name":"Card numbers pass through or are stored in your servers and logs","severity":"critical","cwe":["CWE-312"]},{"id":"missing-function-authorization","name":"A user calls an admin or other-role function because only the UI hides it","severity":"critical","cwe":["CWE-862"]},{"id":"sql-injection","name":"Attacker input changes the meaning of a database query","severity":"critical","cwe":["CWE-89"]},{"id":"unsafe-deserialization","name":"Untrusted data is deserialized with a format that can run code, such as pickle","severity":"critical","cwe":["CWE-502"]},{"id":"weak-password-storage","name":"Passwords are stored in plain text or with a fast hash, so a database leak exposes them","severity":"critical","cwe":["CWE-916"]},{"id":"archive-path-traversal","name":"An uploaded archive writes files outside the target folder when extracted","severity":"high","cwe":["CWE-22"]},{"id":"exposed-data-store","name":"A database, cache, or admin port is reachable from the internet","severity":"high","cwe":["CWE-668"]},{"id":"mass-assignment","name":"A request sets fields the user should not control, such as role or price","severity":"high","cwe":["CWE-915"]},{"id":"nosql-injection","name":"Query operators in user input bypass filters in a NoSQL database","severity":"high","cwe":["CWE-943"]},{"id":"object-id-guessing","name":"One user reads or changes another user's data by changing an id in the request","severity":"high","cwe":["CWE-639"]},{"id":"role-self-assignment","name":"A user grants themselves a higher role through a profile or signup request","severity":"high","cwe":["CWE-269"]},{"id":"sensitive-data-unencrypted","name":"Sensitive fields are stored unencrypted, so a backup or database leak exposes them","severity":"high","cwe":["CWE-311"]},{"id":"tenant-data-leak","name":"Queries miss the tenant filter, so customers see each other's data","severity":"high","cwe":["CWE-284"]},{"id":"xxe","name":"An XML parser loads external files or URLs named in untrusted XML","severity":"high","cwe":["CWE-611"]},{"id":"over-privileged-db-account","name":"The app connects as an admin database user, so any flaw becomes full data access","severity":"medium","cwe":["CWE-250"]},{"id":"secrets-in-logs","name":"Passwords, tokens, or personal data are written to logs","severity":"medium","cwe":["CWE-532"]},{"id":"verbose-errors","name":"Stack traces and internal details are shown to users","severity":"medium","cwe":["CWE-209"]},{"id":"no-security-logging","name":"Logins and access failures are not logged, so attacks go unnoticed","severity":"low","cwe":["CWE-778"]}],"countermeasures":[{"id":"hosted-payment-fields","name":"Use the provider's hosted card fields","how_to":"Let the payment provider collect card data directly so card numbers never touch your servers or logs.","effort":"low","asvs":[],"mitigates":["card-data-in-your-systems"]},{"id":"log-without-secrets","name":"Keep secrets and personal data out of logs","how_to":"Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.","effort":"low","asvs":["v5.0.0-16.2.5"],"mitigates":["card-data-in-your-systems","secrets-in-logs"]},{"id":"check-permissions-server-side","name":"Check permissions on the server for every action","how_to":"Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.","effort":"medium","asvs":["v5.0.0-8.2.1","v5.0.0-8.3.1"],"mitigates":["missing-function-authorization","mass-assignment","role-self-assignment"]},{"id":"parameterized-queries","name":"Use parameterized queries or an ORM","how_to":"Pass user values as parameters. Never build SQL or query documents by joining strings.","effort":"low","asvs":["v5.0.0-1.2.4"],"mitigates":["sql-injection","nosql-injection"]},{"id":"avoid-unsafe-deserializers","name":"Do not deserialize untrusted data with code-executing formats","how_to":"Use JSON with schema validation. Avoid pickle, yaml.load, and native object serialization for untrusted input.","effort":"low","asvs":["v5.0.0-1.5.2"],"mitigates":["unsafe-deserialization"]},{"id":"slow-password-hashing","name":"Hash passwords with a slow, salted algorithm","how_to":"Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.","effort":"low","asvs":["v5.0.0-11.4.2"],"mitigates":["weak-password-storage"]},{"id":"safe-archive-extraction","name":"Extract archives safely","how_to":"Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.","effort":"medium","asvs":["v5.0.0-5.3.3","v5.0.0-5.2.3"],"mitigates":["archive-path-traversal"]},{"id":"private-network-for-data-stores","name":"Keep data stores off the public internet","how_to":"Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.","effort":"low","asvs":[],"mitigates":["exposed-data-store"]},{"id":"allow-list-fields","name":"Accept only the fields you expect","how_to":"Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.","effort":"low","asvs":["v5.0.0-15.3.3"],"mitigates":["mass-assignment","role-self-assignment"]},{"id":"server-side-validation","name":"Validate all input on the server","how_to":"Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.","effort":"low","asvs":["v5.0.0-2.2.1","v5.0.0-2.2.2"],"mitigates":["nosql-injection"]},{"id":"per-object-authorization","name":"Check the user owns the object on every request","how_to":"Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.","effort":"medium","asvs":["v5.0.0-8.2.2","v5.0.0-8.3.1"],"mitigates":["object-id-guessing"]},{"id":"encrypt-sensitive-data","name":"Encrypt sensitive data at rest","how_to":"Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.","effort":"medium","asvs":["v5.0.0-11.3.2"],"mitigates":["sensitive-data-unencrypted"]},{"id":"scope-queries-to-tenant","name":"Scope every query to the tenant","how_to":"Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.","effort":"medium","asvs":["v5.0.0-8.2.2"],"mitigates":["tenant-data-leak"]},{"id":"disable-xml-external-entities","name":"Turn off external entities in XML parsers","how_to":"Use a hardened parser configuration such as defusedxml, with DTDs and external entities disabled.","effort":"low","asvs":["v5.0.0-1.5.1"],"mitigates":["xxe"]},{"id":"least-privilege-accounts","name":"Give the app a least-privilege database account","how_to":"Create a user limited to the tables and operations the app needs. Keep migrations on a separate admin account.","effort":"medium","asvs":[],"mitigates":["over-privileged-db-account"]},{"id":"generic-error-messages","name":"Return generic errors to users","how_to":"Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.","effort":"low","asvs":["v5.0.0-16.5.1"],"mitigates":["verbose-errors"]},{"id":"log-security-events","name":"Log security-relevant events","how_to":"Log logins, failures, permission denials, and admin actions with time, user, and source, and alert on spikes.","effort":"medium","asvs":["v5.0.0-16.3.1","v5.0.0-16.3.2"],"mitigates":["no-security-logging"]}],"also_consider":[],"summary":"18 threats and 17 countermeasures for database, authorization, serialization-and-parsing, logging-and-errors. Risk level critical (highest threat severity)."},"hint":null,"instructions":"Build these countermeasures in as you write the code, starting with the most severe threats. These threats come from the components you picked. also_consider lists general threats from implied components; pass those components explicitly for full detail. After writing code, call general_verify_code_security with the same components.","metadata":{"total_threats":18,"total_countermeasures":17,"also_consider_total":0,"review_purpose":"lightweight_security_guidance"}}
```

### evaluation/raw/T-019.input.json

```json
{
  "tool": "mcp__sec-review__general_verify_code_security",
  "arguments": {
    "components": "database,authorization,serialization-and-parsing,logging-and-errors",
    "file_path": "api/src/taskboard/services/caching.py, api/src/taskboard/infra/cache/"
  }
}
```

### evaluation/raw/T-019.output.json

```json
{
  "success": true,
  "review_type": "ai_powered_security_review",
  "instructions": "IMPORTANT: You (the AI agent) must now perform the security review. The code is not included here: review the code you just wrote, which is already in your context, using the checklist and focus areas. Report all security issues found with severity ratings and fixes.",
  "review_prompt": "## SECURITY CODE REVIEW REQUEST\n\n**File:** `api/src/taskboard/services/caching.py, api/src/taskboard/infra/cache/`\n**Components:** database, authorization, serialization-and-parsing, logging-and-errors\n**Risk Level:** CRITICAL\n\n### Review Instructions\n\nReview the code you just wrote (it is already in your context) for security vulnerabilities. For each issue found:\n1. Identify the vulnerability type and severity (Critical/High/Medium/Low)\n2. Explain why it's a security risk\n3. Show the problematic code snippet\n4. Provide a secure code fix\n\n### Focus Areas\n\nPay special attention to:\n- Card numbers pass through or are stored in your servers and logs\n- A user calls an admin or other-role function because only the UI hides it\n- Attacker input changes the meaning of a database query\n- Untrusted data is deserialized with a format that can run code, such as pickle\n- Passwords are stored in plain text or with a fast hash, so a database leak exposes them\n- An uploaded archive writes files outside the target folder when extracted\n- A database, cache, or admin port is reachable from the internet\n- A request sets fields the user should not control, such as role or price\n- Query operators in user input bypass filters in a NoSQL database\n- One user reads or changes another user's data by changing an id in the request\n- A user grants themselves a higher role through a profile or signup request\n- Sensitive fields are stored unencrypted, so a backup or database leak exposes them\n\n### Security Checklist\n\nVerify each item and report violations:\n- [ ] Use the provider's hosted card fields: Let the payment provider collect card data directly so card numbers never touch your servers or logs.\n- [ ] Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.\n- [ ] Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.\n- [ ] Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.\n- [ ] Do not deserialize untrusted data with code-executing formats: Use JSON with schema validation. Avoid pickle, yaml.load, and native object serialization for untrusted input.\n- [ ] Hash passwords with a slow, salted algorithm: Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.\n- [ ] Extract archives safely: Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.\n- [ ] Keep data stores off the public internet: Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.\n- [ ] Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.\n- [ ] Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.\n- [ ] Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.\n- [ ] Encrypt sensitive data at rest: Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.\n- [ ] Scope every query to the tenant: Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.\n- [ ] Turn off external entities in XML parsers: Use a hardened parser configuration such as defusedxml, with DTDs and external entities disabled.\n- [ ] Give the app a least-privilege database account: Create a user limited to the tables and operations the app needs. Keep migrations on a separate admin account.\n- [ ] Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.\n- [ ] Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.\n\n### Expected Response Format\n\nProvide your security review with:\n1. **Summary:** Overall assessment (Secure/Needs Attention/Insecure)\n2. **Findings:** List of security issues with severity and fixes\n3. **Checklist Results:** Which items pass/fail\n4. **Recommendations:** Prioritized list of actions",
  "context": {
    "file_path": "api/src/taskboard/services/caching.py, api/src/taskboard/infra/cache/",
    "components": [
      "database",
      "authorization",
      "serialization-and-parsing",
      "logging-and-errors"
    ],
    "risk_level": "critical"
  },
  "security_checklist": [
    "Use the provider's hosted card fields: Let the payment provider collect card data directly so card numbers never touch your servers or logs.",
    "Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.",
    "Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.",
    "Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.",
    "Do not deserialize untrusted data with code-executing formats: Use JSON with schema validation. Avoid pickle, yaml.load, and native object serialization for untrusted input.",
    "Hash passwords with a slow, salted algorithm: Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.",
    "Extract archives safely: Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.",
    "Keep data stores off the public internet: Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.",
    "Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.",
    "Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.",
    "Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.",
    "Encrypt sensitive data at rest: Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.",
    "Scope every query to the tenant: Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.",
    "Turn off external entities in XML parsers: Use a hardened parser configuration such as defusedxml, with DTDs and external entities disabled.",
    "Give the app a least-privilege database account: Create a user limited to the tables and operations the app needs. Keep migrations on a separate admin account.",
    "Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.",
    "Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials."
  ],
  "focus_areas": [
    "Card numbers pass through or are stored in your servers and logs",
    "A user calls an admin or other-role function because only the UI hides it",
    "Attacker input changes the meaning of a database query",
    "Untrusted data is deserialized with a format that can run code, such as pickle",
    "Passwords are stored in plain text or with a fast hash, so a database leak exposes them",
    "An uploaded archive writes files outside the target folder when extracted",
    "A database, cache, or admin port is reachable from the internet",
    "A request sets fields the user should not control, such as role or price",
    "Query operators in user input bypass filters in a NoSQL database",
    "One user reads or changes another user's data by changing an id in the request",
    "A user grants themselves a higher role through a profile or signup request",
    "Sensitive fields are stored unencrypted, so a backup or database leak exposes them"
  ],
  "expected_response": {
    "format": "structured_security_review",
    "required_sections": [
      "overall_assessment",
      "findings_list",
      "checklist_results",
      "recommended_fixes"
    ]
  }
}
```

### evaluation/raw/T-019.review.md

```markdown
# Review produced by following the T-019 review_prompt

Scope: the phase 4 cache layer: `api/src/taskboard/services/caching.py`, `api/src/taskboard/infra/cache/*`, and its
call sites in `services/auth.py`, `services/users.py`, `services/teams.py`, `services/projects.py`,
`services/tasks.py`, `composition.py` and `api/routers/admin.py`. Components: database, authorization,
serialization-and-parsing, logging-and-errors.

## 1. Summary

**Needs Attention.** One medium issue (stale role after demotion), two low issues to handle in infrastructure, and one
accepted low-risk race.

## 2. Findings

| # | Severity (mine) | Issue | Where | Fix |
| --- | --- | --- | --- | --- |
| R19-1 | Medium | Classic cache-aside race on the user profile. Request A reads the profile (role `admin`) from PostgreSQL. An admin demotes the user, commits, and deletes `user:{id}`. A then writes the stale profile back. Every request in the next TTL (300 s) authorizes the user as admin. The focus area "A user calls an admin or other-role function" applies, and TM-14 / F-050 required authorization never to rely on cached data. | `services/auth.py` `authenticate()` returns the cached `User`, including `role` and `is_active` | Read `role` and `is_active` fresh from PostgreSQL on every request, in the same indexed query that validates the session (sessions JOIN users). Overlay them on the cached profile, so the cache only supplies display fields. → F-080 |
| R19-2 | Low | The same race on per-user team and project lists. A user removed from a team can, for up to the TTL, still see that team's name and its projects' names in their own lists. Every access to the team or project itself is checked against the database and returns 404. | `services/teams.py` `list_my_teams`, `services/projects.py` `list_my_projects` | Accept. Exposure is limited to names, for at most the TTL, and only to someone who was a member moments earlier. → F-081 (accepted risk) |
| R19-3 | Low | Cached project lists include `webhook_url`, which can embed secrets, so Redis holds them in clear. | `PROJECT_LIST_ADAPTER` values | Encryption at rest and in transit, plus auth, on ElastiCache in Terraform (phase 6); Redis reachable only from the API security group. → F-082 |
| R19-4 | Low | Each distinct search/filter combination on a project's task list creates its own key, so an authenticated user can create many short-lived keys. | `CacheKeys.task_list` | Already bounded by the 300 s TTL. Add an LRU `maxmemory-policy` on ElastiCache (phase 6). → F-083 |

## 3. Checklist results

| Checklist item | Result | Evidence |
| --- | --- | --- |
| Hosted card fields | N/A | No payment data (F-055). |
| Keep secrets and personal data out of logs | Pass | Cache logs record only the key family, never keys or values. |
| Check permissions on the server for every action | Fail → R19-1 | Team/project/task reads authorize against the DB before or after the cache read, but the role came from the cache. |
| Parameterized queries | Pass | The cache adds no SQL. Redis keys are built from UUIDs and a SHA-256 digest; no client text in keys. |
| No code-executing deserialization | Pass | JSON only, via Pydantic `TypeAdapter.validate_json`; malformed entries are discarded and counted as `errors`. |
| Hash passwords slowly | Pass | Password hashes are never cached; `User` has no hash field. |
| Extract archives safely | N/A | |
| Keep data stores off the public internet | Open (phase 6/7) | Compose publishes no Redis port; ElastiCache in private subnets, still to be written. |
| Accept only expected fields / validate input | Pass | Unchanged from T-014. |
| Check the user owns the object | Pass | `TaskService.get` loads the cached task, then `project_for_member` checks membership against the DB; unit test `test_task_cache_never_bypasses_membership`. |
| Encrypt sensitive data at rest | Open → R19-3 | ElastiCache encryption in phase 6. |
| Scope every query to the tenant | Pass | Task-list keys are per project and read only after `project_for_member`; per-user lists are keyed by the caller's id. |
| XML external entities | N/A | No XML. |
| Least-privilege DB account | Open (phase 7) | F-062. |
| Secrets from environment | Pass | `REDIS_URL` comes from the environment as a `SecretStr`. |
| Generic errors | Pass | Redis errors are swallowed and logged as warnings; the API degrades to misses (integration test `test_api_keeps_working_without_redis`). |

## 4. Recommendations (prioritised)

1. R19-1: never take `role` or `is_active` from the cache (F-080).
2. R19-3 / R19-4: ElastiCache encryption, auth, private subnets and LRU eviction in Terraform (F-082, F-083).
3. R19-2: accept and document (F-081).
```

### evaluation/raw/T-021.input.json

```json
{
  "tool": "mcp__sec-review__general_lightweight_security_review",
  "arguments": {
    "task_description": "Build the Taskboard UI server: Node.js 24, TypeScript, Express 5 with EJS server-rendered pages (login, register, forgot/reset password, dashboard, team page, project board, task detail, search, profile, admin users, admin activity). It authenticates browser users by storing the API's opaque session token in an HttpOnly SameSite cookie and calls the internal API with Authorization: Bearer plus a shared service secret header; CSRF protection with an HMAC token bound to a cookie on every POST form; flash messages in a signed cookie; renders task descriptions and comments written in Markdown to HTML (marked) and sanitizes them (sanitize-html); proxies multipart attachment uploads (multer, 10 MB limit) and streams downloads back with Content-Disposition attachment; strict CSP via helmet; structured JSON logging with a per-request id passed to the API; post-login redirect to a local path.",
    "components": "browser-frontend,user-generated-content,session-management,web-endpoint,file-upload",
    "data_handled": "credentials,personal_data",
    "technologies": "Node.js 24, TypeScript, Express 5, EJS, helmet, multer, marked, sanitize-html, cookie-parser, pino"
  }
}
```

### evaluation/raw/T-021.output.json

```json
{"success":true,"review_type":"lightweight_pre_coding","status":"complete","task_description":"Build the Taskboard UI server: Node.js 24, TypeScript, Express 5 with EJS server-rendered pages (login, register, forgot/reset password, dashboard, team page, project board, task detail, search, profile, admin users, admin activity). It authenticates browser users by storing the API's opaque session token in an HttpOnly SameSite cookie and calls the internal API with Authorization: Bearer plus a shared service secret header; CSRF protection with an HMAC token bound to a cookie on every POST form; flash messages in a signed cookie; renders task descriptions and comments written in Markdown to HTML (marked) and sanitizes them (sanitize-html); proxies multipart attachment uploads (multer, 10 MB limit) and streams downloads back with Content-Disposition attachment; strict CSP via helmet; structured JSON logging with a per-request id passed to the API; post-login redirect to a local path.","technologies":["Node.js 24","TypeScript","Express 5","EJS","helmet","multer","marked","sanitize-html","cookie-parser","pino"],"assessment":{"risk_level":"critical","components":["browser-frontend","user-generated-content","session-management","web-endpoint","file-upload"],"implied_components":[],"sensitive_data":["credentials","personal_data"],"threats":[{"id":"missing-function-authorization","name":"A user calls an admin or other-role function because only the UI hides it","severity":"critical","cwe":["CWE-862"]},{"id":"archive-path-traversal","name":"An uploaded archive writes files outside the target folder when extracted","severity":"high","cwe":["CWE-22"]},{"id":"cleartext-transport","name":"Sensitive data travels over plain HTTP or an unencrypted connection","severity":"high","cwe":["CWE-319"]},{"id":"debug-mode-in-production","name":"Debug features or consoles are left on in production","severity":"high","cwe":["CWE-489"]},{"id":"dom-xss","name":"Frontend code writes untrusted data into the page with unsafe DOM APIs","severity":"high","cwe":["CWE-79"]},{"id":"exposed-config-files","name":".env, .git, or backup files are reachable from the web","severity":"high","cwe":["CWE-538"]},{"id":"jwt-tampering","name":"Forged or unsigned JWTs are accepted","severity":"high","cwe":["CWE-347"]},{"id":"long-lived-storage-credentials","name":"Long-lived storage keys are shipped to the browser or mobile app","severity":"high","cwe":["CWE-798"]},{"id":"mass-assignment","name":"A request sets fields the user should not control, such as role or price","severity":"high","cwe":["CWE-915"]},{"id":"object-id-guessing","name":"One user reads or changes another user's data by changing an id in the request","severity":"high","cwe":["CWE-639"]},{"id":"predictable-tokens","name":"Session ids, reset tokens, or API keys can be guessed","severity":"high","cwe":["CWE-330"]},{"id":"session-fixation","name":"An attacker plants a session id before login and reuses it afterwards","severity":"high","cwe":["CWE-384"]},{"id":"stored-xss","name":"Attacker-supplied content is shown to other users as HTML or script","severity":"high","cwe":["CWE-79"]},{"id":"upload-executable-file","name":"Attacker uploads a script that your server runs or serves","severity":"high","cwe":["CWE-434"]},{"id":"upload-path-traversal","name":"Attacker uses ../ in a filename to overwrite files","severity":"high","cwe":["CWE-22"]},{"id":"business-flow-bypass","name":"A user skips or repeats steps in a multi-step flow, such as verification or checkout","severity":"medium","cwe":["CWE-840"]},{"id":"csrf","name":"Another website makes a logged-in user's browser perform actions","severity":"medium","cwe":["CWE-352"]},{"id":"excessive-data-exposure","name":"API responses include more fields than the client needs, such as hashes or internal ids","severity":"medium","cwe":["CWE-200"]},{"id":"insecure-cookie-flags","name":"Session cookies can be read by scripts or sent over plain HTTP","severity":"medium","cwe":["CWE-614","CWE-1004"]},{"id":"missing-input-validation","name":"Unvalidated input reaches business logic and breaks assumptions","severity":"medium","cwe":["CWE-20"]},{"id":"missing-rate-limit","name":"Attackers hammer an endpoint to brute-force, scrape, or run up your costs","severity":"medium","cwe":["CWE-770"]},{"id":"open-redirect","name":"A link on your domain sends users to an attacker-chosen site","severity":"medium","cwe":["CWE-601"]},{"id":"permissive-cors","name":"Any website can read authenticated API responses because CORS allows every origin","severity":"medium","cwe":["CWE-942"]},{"id":"sessions-not-ended","name":"Logout, password change, or account removal leaves sessions or tokens valid","severity":"medium","cwe":["CWE-613"]},{"id":"third-party-script-compromise","name":"A compromised third-party script or CDN file runs in your pages","severity":"medium","cwe":["CWE-829"]},{"id":"token-claims-unchecked","name":"Expired tokens or tokens meant for another service are accepted","severity":"medium","cwe":["CWE-345"]},{"id":"tokens-leak-via-url-or-storage","name":"Tokens in URLs or browser storage leak through logs, referrers, or scripts","severity":"medium","cwe":["CWE-598"]},{"id":"upload-active-content","name":"An uploaded SVG or HTML file runs script when other users open it","severity":"medium","cwe":["CWE-79"]},{"id":"upload-resource-exhaustion","name":"Huge files or compression bombs fill disk or memory","severity":"medium","cwe":["CWE-770"]},{"id":"verbose-errors","name":"Stack traces and internal details are shown to users","severity":"medium","cwe":["CWE-209"]},{"id":"missing-security-headers","name":"Pages can be framed, sniffed, or loaded over plain HTTP because headers are missing","severity":"low","cwe":["CWE-1021"]}],"countermeasures":[{"id":"check-permissions-server-side","name":"Check permissions on the server for every action","how_to":"Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.","effort":"medium","asvs":["v5.0.0-8.2.1","v5.0.0-8.3.1"],"mitigates":["missing-function-authorization","mass-assignment"]},{"id":"safe-archive-extraction","name":"Extract archives safely","how_to":"Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.","effort":"medium","asvs":["v5.0.0-5.3.3","v5.0.0-5.2.3"],"mitigates":["archive-path-traversal"]},{"id":"https-everywhere","name":"Use HTTPS for every connection","how_to":"Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.","effort":"low","asvs":["v5.0.0-12.2.1","v5.0.0-12.2.2"],"mitigates":["cleartext-transport"]},{"id":"disable-debug-in-prod","name":"Turn debug features off in production","how_to":"Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.","effort":"low","asvs":["v5.0.0-13.4.2"],"mitigates":["debug-mode-in-production"]},{"id":"safe-dom-apis","name":"Use safe DOM APIs","how_to":"Use textContent or framework bindings instead of innerHTML, document.write, or dangerouslySetInnerHTML.","effort":"low","asvs":["v5.0.0-3.2.2"],"mitigates":["dom-xss"]},{"id":"output-encoding","name":"Encode output for its context","how_to":"Use your template engine's automatic escaping, and encode correctly for HTML, attributes, URLs, and JavaScript.","effort":"low","asvs":["v5.0.0-1.2.1","v5.0.0-1.2.2","v5.0.0-1.2.3"],"mitigates":["dom-xss","stored-xss"]},{"id":"no-vcs-or-env-files-deployed","name":"Do not deploy repo metadata or env files","how_to":"Exclude .git, .env, and backups from the build and the web root, and block them at the web server.","effort":"low","asvs":["v5.0.0-13.4.1"],"mitigates":["exposed-config-files"]},{"id":"secrets-manager","name":"Load secrets from a secrets manager or environment","how_to":"Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.","effort":"medium","asvs":["v5.0.0-13.3.1","v5.0.0-13.3.2"],"mitigates":["exposed-config-files"]},{"id":"verify-token-signature","name":"Verify token signatures against an allow-list of algorithms","how_to":"Verify every JWT signature, fix the accepted algorithms in code, and load keys from trusted configuration. Never accept alg none.","effort":"low","asvs":["v5.0.0-9.1.1","v5.0.0-9.1.2","v5.0.0-9.1.3"],"mitigates":["jwt-tampering"]},{"id":"short-lived-scoped-credentials","name":"Give clients short-lived, narrowly scoped credentials","how_to":"Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.","effort":"medium","asvs":[],"mitigates":["long-lived-storage-credentials"]},{"id":"allow-list-fields","name":"Accept only the fields you expect","how_to":"Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.","effort":"low","asvs":["v5.0.0-15.3.3"],"mitigates":["mass-assignment"]},{"id":"per-object-authorization","name":"Check the user owns the object on every request","how_to":"Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.","effort":"medium","asvs":["v5.0.0-8.2.2","v5.0.0-8.3.1"],"mitigates":["object-id-guessing"]},{"id":"crypto-random-tokens","name":"Generate tokens with a cryptographic random source","how_to":"Use secrets.token_urlsafe, crypto.randomBytes, or the framework default. Never use Math.random, time, or counters.","effort":"low","asvs":["v5.0.0-7.2.3","v5.0.0-11.5.1"],"mitigates":["predictable-tokens"]},{"id":"new-session-on-login","name":"Issue a fresh session at login","how_to":"Create a new session id on every login and re-authentication, and discard the old one.","effort":"low","asvs":["v5.0.0-7.2.4"],"mitigates":["session-fixation"]},{"id":"sanitize-html","name":"Sanitize user-provided HTML","how_to":"Run user HTML through a maintained sanitizer such as DOMPurify or bleach with a strict allow-list. Prefer markdown or plain text.","effort":"low","asvs":["v5.0.0-1.3.1"],"mitigates":["stored-xss","upload-active-content"]},{"id":"upload-allow-list","name":"Allow only the file types you need","how_to":"Check the extension and the real file content against an allow-list. Ignore the client's Content-Type.","effort":"low","asvs":["v5.0.0-5.2.2"],"mitigates":["upload-executable-file"]},{"id":"upload-rename-and-isolate","name":"Never use the user's filename or path","how_to":"Generate your own filenames, store files outside the web root, and make sure uploads are never executed.","effort":"low","asvs":["v5.0.0-5.3.1","v5.0.0-5.3.2"],"mitigates":["upload-executable-file","upload-path-traversal"]},{"id":"enforce-flow-order","name":"Enforce step order and limits on the server","how_to":"Store the state of multi-step flows on the server and reject steps that are out of order. Apply business limits there too.","effort":"medium","asvs":["v5.0.0-2.3.1","v5.0.0-2.3.2"],"mitigates":["business-flow-bypass"]},{"id":"csrf-protection","name":"Protect state-changing requests from cross-site forgery","how_to":"Use SameSite cookies plus anti-forgery tokens, and only change state with POST, PUT, PATCH, or DELETE.","effort":"low","asvs":["v5.0.0-3.5.1","v5.0.0-3.5.3","v5.0.0-3.3.2"],"mitigates":["csrf"]},{"id":"secure-cookie-attributes","name":"Set cookie security attributes","how_to":"Use Secure, HttpOnly, and SameSite on session cookies, preferably with the __Host- prefix.","effort":"low","asvs":["v5.0.0-3.3.1","v5.0.0-3.3.2","v5.0.0-3.3.4"],"mitigates":["csrf","insecure-cookie-flags"]},{"id":"return-minimal-fields","name":"Return only the fields the client needs","how_to":"Build response objects from an explicit list of fields instead of serializing whole database rows.","effort":"low","asvs":["v5.0.0-15.3.1"],"mitigates":["excessive-data-exposure"]},{"id":"server-side-validation","name":"Validate all input on the server","how_to":"Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.","effort":"low","asvs":["v5.0.0-2.2.1","v5.0.0-2.2.2"],"mitigates":["missing-input-validation"]},{"id":"rate-limiting","name":"Rate-limit expensive or sensitive endpoints","how_to":"Limit requests per user and per IP on login, reset, send, upload, and search endpoints, and return 429 when exceeded.","effort":"medium","asvs":["v5.0.0-2.4.1"],"mitigates":["missing-rate-limit"]},{"id":"validate-redirect-targets","name":"Redirect only to known destinations","how_to":"Accept a short key or a relative path for post-login redirects and check it against an allow-list. Never redirect to a full URL from input.","effort":"low","asvs":[],"mitigates":["open-redirect"]},{"id":"strict-cors","name":"Allow only the origins you trust","how_to":"Return a fixed allow-list for Access-Control-Allow-Origin. Never reflect the request origin or use * with credentials.","effort":"low","asvs":["v5.0.0-3.4.2","v5.0.0-3.5.2"],"mitigates":["permissive-cors"]},{"id":"proper-logout-and-expiry","name":"End sessions on the server","how_to":"Invalidate server-side on logout, expiry, password change, and account removal. Do not rely on deleting the cookie client-side.","effort":"medium","asvs":["v5.0.0-7.4.1","v5.0.0-7.4.2"],"mitigates":["sessions-not-ended"]},{"id":"subresource-integrity","name":"Pin third-party scripts with integrity hashes","how_to":"Add SRI hashes to external scripts and styles, or self-host them, and limit sources with a Content-Security-Policy.","effort":"low","asvs":[],"mitigates":["third-party-script-compromise"]},{"id":"security-headers","name":"Send the standard security headers","how_to":"Set Strict-Transport-Security, Content-Security-Policy with frame-ancestors, X-Content-Type-Options nosniff, and a referrer policy.","effort":"low","asvs":["v5.0.0-3.4.1","v5.0.0-3.4.3","v5.0.0-3.4.4","v5.0.0-3.4.5","v5.0.0-3.4.6"],"mitigates":["third-party-script-compromise","missing-security-headers"]},{"id":"validate-token-claims","name":"Check expiry, audience, and issuer","how_to":"Reject expired tokens and tokens whose audience or issuer does not match your service.","effort":"low","asvs":["v5.0.0-9.2.1","v5.0.0-9.2.3"],"mitigates":["token-claims-unchecked"]},{"id":"no-secrets-in-urls","name":"Keep tokens and personal data out of URLs","how_to":"Send tokens in headers or request bodies, never in query strings, which end up in logs and referrers.","effort":"low","asvs":["v5.0.0-14.2.1"],"mitigates":["tokens-leak-via-url-or-storage"]},{"id":"no-sensitive-data-in-browser-storage","name":"Keep sensitive data out of browser storage","how_to":"Prefer HttpOnly cookies for session tokens, and clear client-side data on logout.","effort":"low","asvs":["v5.0.0-14.3.3","v5.0.0-14.3.1"],"mitigates":["tokens-leak-via-url-or-storage"]},{"id":"serve-uploads-safely","name":"Serve uploads so browsers cannot run them","how_to":"Send the correct Content-Type, Content-Disposition attachment for downloads, nosniff, and serve user files from a separate domain.","effort":"low","asvs":["v5.0.0-4.1.1","v5.0.0-5.4.2","v5.0.0-3.2.1"],"mitigates":["upload-active-content"]},{"id":"upload-size-limits","name":"Limit file size and decompressed size","how_to":"Set a maximum size per file, and cap decompressed size and file count for archives.","effort":"low","asvs":["v5.0.0-5.2.1","v5.0.0-5.2.3"],"mitigates":["upload-resource-exhaustion"]},{"id":"generic-error-messages","name":"Return generic errors to users","how_to":"Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.","effort":"low","asvs":["v5.0.0-16.5.1"],"mitigates":["verbose-errors"]}],"also_consider":[],"summary":"31 threats and 34 countermeasures for browser-frontend, user-generated-content, session-management, web-endpoint, file-upload. Risk level critical (highest threat severity, raised for sensitive data)."},"hint":null,"instructions":"Build these countermeasures in as you write the code, starting with the most severe threats. These threats come from the components you picked. also_consider lists general threats from implied components; pass those components explicitly for full detail. After writing code, call general_verify_code_security with the same components.","metadata":{"total_threats":31,"total_countermeasures":34,"also_consider_total":0,"review_purpose":"lightweight_security_guidance"}}
```

### evaluation/raw/T-022.input.json

```json
{
  "tool": "mcp__sec-review__sca_verify_packages",
  "arguments": {
    "packages_json": [
      {
        "name": "express",
        "version": "5.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "ejs",
        "version": "7.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "helmet",
        "version": "8.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "cookie-parser",
        "version": "1.4.7",
        "ecosystem": "npm"
      },
      {
        "name": "multer",
        "version": "2.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "marked",
        "version": "18.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "sanitize-html",
        "version": "2.18.1",
        "ecosystem": "npm"
      },
      {
        "name": "pino",
        "version": "10.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "zod",
        "version": "4.6.7",
        "ecosystem": "npm"
      },
      {
        "name": "typescript",
        "version": "6.0.3",
        "ecosystem": "npm"
      },
      {
        "name": "@types/express",
        "version": "5.0.6",
        "ecosystem": "npm"
      },
      {
        "name": "@types/cookie-parser",
        "version": "1.4.10",
        "ecosystem": "npm"
      },
      {
        "name": "@types/multer",
        "version": "2.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "@types/sanitize-html",
        "version": "2.16.2",
        "ecosystem": "npm"
      },
      {
        "name": "@types/node",
        "version": "24.19.2",
        "ecosystem": "npm"
      },
      {
        "name": "vitest",
        "version": "5.0.5",
        "ecosystem": "npm"
      },
      {
        "name": "@vitest/coverage-v8",
        "version": "5.0.5",
        "ecosystem": "npm"
      },
      {
        "name": "supertest",
        "version": "7.3.1",
        "ecosystem": "npm"
      },
      {
        "name": "@types/supertest",
        "version": "7.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "eslint",
        "version": "10.13.0",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint/js",
        "version": "10.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "typescript-eslint",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "prettier",
        "version": "3.9.10",
        "ecosystem": "npm"
      },
      {
        "name": "globals",
        "version": "17.13.0",
        "ecosystem": "npm"
      }
    ]
  }
}
```

### evaluation/raw/T-022.output.json

```json
{
  "all_valid": true,
  "packages_checked": 24
}
```

### evaluation/raw/T-023.input.json

```json
{
  "tool": "mcp__sec-review__sca_scan_dependencies",
  "arguments": {
    "packages_json": [
      {
        "name": "express",
        "version": "5.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "ejs",
        "version": "7.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "helmet",
        "version": "8.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "cookie-parser",
        "version": "1.4.7",
        "ecosystem": "npm"
      },
      {
        "name": "multer",
        "version": "2.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "marked",
        "version": "18.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "sanitize-html",
        "version": "2.18.1",
        "ecosystem": "npm"
      },
      {
        "name": "pino",
        "version": "10.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "zod",
        "version": "4.6.7",
        "ecosystem": "npm"
      },
      {
        "name": "typescript",
        "version": "6.0.3",
        "ecosystem": "npm"
      },
      {
        "name": "@types/express",
        "version": "5.0.6",
        "ecosystem": "npm"
      },
      {
        "name": "@types/cookie-parser",
        "version": "1.4.10",
        "ecosystem": "npm"
      },
      {
        "name": "@types/multer",
        "version": "2.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "@types/sanitize-html",
        "version": "2.16.2",
        "ecosystem": "npm"
      },
      {
        "name": "@types/node",
        "version": "24.19.2",
        "ecosystem": "npm"
      },
      {
        "name": "vitest",
        "version": "5.0.5",
        "ecosystem": "npm"
      },
      {
        "name": "@vitest/coverage-v8",
        "version": "5.0.5",
        "ecosystem": "npm"
      },
      {
        "name": "supertest",
        "version": "7.3.1",
        "ecosystem": "npm"
      },
      {
        "name": "@types/supertest",
        "version": "7.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "eslint",
        "version": "10.13.0",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint/js",
        "version": "10.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "typescript-eslint",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "prettier",
        "version": "3.9.10",
        "ecosystem": "npm"
      },
      {
        "name": "globals",
        "version": "17.13.0",
        "ecosystem": "npm"
      }
    ]
  }
}
```

### evaluation/raw/T-023.output.json

```json
{
  "packages_scanned": 24,
  "vulnerable_count": 0,
  "status": "clean",
  "message": "No known vulnerabilities found in scanned packages."
}
```

### evaluation/raw/T-024.input.json

```json
{
  "tool": "mcp__sec-review__sca_scan_dependencies",
  "arguments": {
    "packages_json": [
      {
        "name": "@babel/helper-string-parser",
        "version": "7.29.7",
        "ecosystem": "npm"
      },
      {
        "name": "@babel/helper-validator-identifier",
        "version": "7.29.7",
        "ecosystem": "npm"
      },
      {
        "name": "@babel/parser",
        "version": "7.29.9",
        "ecosystem": "npm"
      },
      {
        "name": "@babel/types",
        "version": "7.29.8",
        "ecosystem": "npm"
      },
      {
        "name": "@bcoe/v8-coverage",
        "version": "1.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "@cacheable/memory",
        "version": "2.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "@cacheable/utils",
        "version": "2.5.0",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint-community/eslint-utils",
        "version": "4.10.1",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint-community/regexpp",
        "version": "4.12.2",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint/config-array",
        "version": "0.23.5",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint/config-helpers",
        "version": "0.7.0",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint/core",
        "version": "1.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint/object-schema",
        "version": "3.0.5",
        "ecosystem": "npm"
      },
      {
        "name": "@eslint/plugin-kit",
        "version": "0.7.3",
        "ecosystem": "npm"
      },
      {
        "name": "@humanfs/core",
        "version": "0.19.2",
        "ecosystem": "npm"
      },
      {
        "name": "@humanfs/node",
        "version": "0.16.8",
        "ecosystem": "npm"
      },
      {
        "name": "@humanfs/types",
        "version": "0.15.0",
        "ecosystem": "npm"
      },
      {
        "name": "@humanwhocodes/module-importer",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "@humanwhocodes/retry",
        "version": "0.4.3",
        "ecosystem": "npm"
      },
      {
        "name": "@jridgewell/resolve-uri",
        "version": "3.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "@jridgewell/sourcemap-codec",
        "version": "1.6.0",
        "ecosystem": "npm"
      },
      {
        "name": "@jridgewell/trace-mapping",
        "version": "0.3.31",
        "ecosystem": "npm"
      },
      {
        "name": "@keyv/bigmap",
        "version": "1.3.1",
        "ecosystem": "npm"
      },
      {
        "name": "@keyv/serialize",
        "version": "1.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "@noble/hashes",
        "version": "1.8.0",
        "ecosystem": "npm"
      },
      {
        "name": "@oxc-project/types",
        "version": "0.154.0",
        "ecosystem": "npm"
      },
      {
        "name": "@paralleldrive/cuid2",
        "version": "2.3.1",
        "ecosystem": "npm"
      },
      {
        "name": "@pinojs/redact",
        "version": "0.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "@rolldown/binding-linux-x64-gnu",
        "version": "1.2.14",
        "ecosystem": "npm"
      },
      {
        "name": "@rolldown/pluginutils",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "@types/body-parser",
        "version": "1.19.6",
        "ecosystem": "npm"
      },
      {
        "name": "@types/chai",
        "version": "5.2.3",
        "ecosystem": "npm"
      },
      {
        "name": "@types/connect",
        "version": "3.4.38",
        "ecosystem": "npm"
      },
      {
        "name": "@types/cookiejar",
        "version": "2.1.5",
        "ecosystem": "npm"
      },
      {
        "name": "@types/deep-eql",
        "version": "4.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "@types/esrecurse",
        "version": "4.3.1",
        "ecosystem": "npm"
      },
      {
        "name": "@types/estree",
        "version": "1.0.9",
        "ecosystem": "npm"
      },
      {
        "name": "@types/express-serve-static-core",
        "version": "5.1.3",
        "ecosystem": "npm"
      },
      {
        "name": "@types/http-errors",
        "version": "2.0.5",
        "ecosystem": "npm"
      },
      {
        "name": "@types/json-schema",
        "version": "7.0.15",
        "ecosystem": "npm"
      },
      {
        "name": "@types/methods",
        "version": "1.1.4",
        "ecosystem": "npm"
      },
      {
        "name": "@types/qs",
        "version": "6.15.1",
        "ecosystem": "npm"
      },
      {
        "name": "@types/range-parser",
        "version": "1.2.7",
        "ecosystem": "npm"
      },
      {
        "name": "@types/send",
        "version": "1.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "@types/serve-static",
        "version": "2.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "@types/superagent",
        "version": "8.1.11",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/eslint-plugin",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/parser",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/project-service",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/scope-manager",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/tsconfig-utils",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/type-utils",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/types",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/typescript-estree",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/utils",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@typescript-eslint/visitor-keys",
        "version": "8.71.2",
        "ecosystem": "npm"
      },
      {
        "name": "@vitest/istanbul-lib-coverage",
        "version": "1.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "@vitest/istanbul-lib-report",
        "version": "1.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "@vitest/mocker",
        "version": "5.0.5",
        "ecosystem": "npm"
      },
      {
        "name": "@vitest/spy",
        "version": "5.0.5",
        "ecosystem": "npm"
      },
      {
        "name": "accepts",
        "version": "2.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "acorn",
        "version": "8.19.0",
        "ecosystem": "npm"
      },
      {
        "name": "acorn-jsx",
        "version": "5.3.2",
        "ecosystem": "npm"
      },
      {
        "name": "ajv",
        "version": "6.15.0",
        "ecosystem": "npm"
      },
      {
        "name": "append-field",
        "version": "1.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "asap",
        "version": "2.0.6",
        "ecosystem": "npm"
      },
      {
        "name": "assertion-error",
        "version": "2.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "ast-v8-to-istanbul",
        "version": "1.0.7",
        "ecosystem": "npm"
      },
      {
        "name": "asynckit",
        "version": "0.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "atomic-sleep",
        "version": "1.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "balanced-match",
        "version": "4.0.4",
        "ecosystem": "npm"
      },
      {
        "name": "body-parser",
        "version": "2.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "brace-expansion",
        "version": "5.0.12",
        "ecosystem": "npm"
      },
      {
        "name": "busboy",
        "version": "1.6.0",
        "ecosystem": "npm"
      },
      {
        "name": "bytes",
        "version": "3.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "cacheable",
        "version": "2.5.0",
        "ecosystem": "npm"
      },
      {
        "name": "call-bind-apply-helpers",
        "version": "1.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "call-bound",
        "version": "1.0.4",
        "ecosystem": "npm"
      },
      {
        "name": "chai",
        "version": "6.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "combined-stream",
        "version": "1.0.8",
        "ecosystem": "npm"
      },
      {
        "name": "component-emitter",
        "version": "1.3.1",
        "ecosystem": "npm"
      },
      {
        "name": "content-disposition",
        "version": "2.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "content-type",
        "version": "2.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "cookie",
        "version": "0.7.2",
        "ecosystem": "npm"
      },
      {
        "name": "cookie-signature",
        "version": "1.0.6",
        "ecosystem": "npm"
      },
      {
        "name": "cookie-signature",
        "version": "1.2.2",
        "ecosystem": "npm"
      },
      {
        "name": "cookiejar",
        "version": "2.1.4",
        "ecosystem": "npm"
      },
      {
        "name": "cross-spawn",
        "version": "7.0.6",
        "ecosystem": "npm"
      },
      {
        "name": "dayjs",
        "version": "1.11.23",
        "ecosystem": "npm"
      },
      {
        "name": "debug",
        "version": "4.4.3",
        "ecosystem": "npm"
      },
      {
        "name": "deep-is",
        "version": "0.1.4",
        "ecosystem": "npm"
      },
      {
        "name": "delayed-stream",
        "version": "1.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "depd",
        "version": "2.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "detect-libc",
        "version": "2.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "dezalgo",
        "version": "1.0.4",
        "ecosystem": "npm"
      },
      {
        "name": "dom-serializer",
        "version": "3.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "domelementtype",
        "version": "3.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "domhandler",
        "version": "6.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "domutils",
        "version": "4.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "dunder-proto",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "ee-first",
        "version": "1.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "encodeurl",
        "version": "2.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "entities",
        "version": "8.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "es-define-property",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "es-errors",
        "version": "1.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "es-module-lexer",
        "version": "2.3.2",
        "ecosystem": "npm"
      },
      {
        "name": "es-object-atoms",
        "version": "1.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "es-set-tostringtag",
        "version": "2.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "escape-html",
        "version": "1.0.3",
        "ecosystem": "npm"
      },
      {
        "name": "escape-string-regexp",
        "version": "4.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "eslint-scope",
        "version": "9.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "eslint-visitor-keys",
        "version": "3.4.3",
        "ecosystem": "npm"
      },
      {
        "name": "eslint-visitor-keys",
        "version": "5.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "espree",
        "version": "11.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "esquery",
        "version": "1.7.0",
        "ecosystem": "npm"
      },
      {
        "name": "esrecurse",
        "version": "4.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "estraverse",
        "version": "5.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "estree-walker",
        "version": "3.0.3",
        "ecosystem": "npm"
      },
      {
        "name": "esutils",
        "version": "2.0.3",
        "ecosystem": "npm"
      },
      {
        "name": "etag",
        "version": "1.8.1",
        "ecosystem": "npm"
      },
      {
        "name": "expect-type",
        "version": "1.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "fast-deep-equal",
        "version": "3.1.3",
        "ecosystem": "npm"
      },
      {
        "name": "fast-json-stable-stringify",
        "version": "2.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "fast-levenshtein",
        "version": "2.0.6",
        "ecosystem": "npm"
      },
      {
        "name": "fast-safe-stringify",
        "version": "2.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "fdir",
        "version": "6.5.0",
        "ecosystem": "npm"
      },
      {
        "name": "file-entry-cache",
        "version": "11.1.5",
        "ecosystem": "npm"
      }
    ]
  }
}
```

### evaluation/raw/T-024.output.json

```json
{
  "packages_scanned": 127,
  "vulnerable_count": 0,
  "status": "clean",
  "message": "No known vulnerabilities found in scanned packages."
}
```

### evaluation/raw/T-025.input.json

```json
{
  "tool": "mcp__sec-review__sca_scan_dependencies",
  "arguments": {
    "packages_json": [
      {
        "name": "finalhandler",
        "version": "2.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "find-up",
        "version": "5.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "flat-cache",
        "version": "6.1.23",
        "ecosystem": "npm"
      },
      {
        "name": "flatted",
        "version": "3.4.4",
        "ecosystem": "npm"
      },
      {
        "name": "form-data",
        "version": "4.0.6",
        "ecosystem": "npm"
      },
      {
        "name": "formidable",
        "version": "3.5.4",
        "ecosystem": "npm"
      },
      {
        "name": "forwarded",
        "version": "0.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "fresh",
        "version": "2.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "function-bind",
        "version": "1.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "get-intrinsic",
        "version": "1.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "get-proto",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "glob-parent",
        "version": "6.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "gopd",
        "version": "1.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "has-symbols",
        "version": "1.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "has-tostringtag",
        "version": "1.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "hashery",
        "version": "1.5.1",
        "ecosystem": "npm"
      },
      {
        "name": "hasown",
        "version": "2.0.4",
        "ecosystem": "npm"
      },
      {
        "name": "hookified",
        "version": "1.15.1",
        "ecosystem": "npm"
      },
      {
        "name": "hookified",
        "version": "2.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "htmlparser2",
        "version": "12.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "http-errors",
        "version": "2.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "iconv-lite",
        "version": "0.7.3",
        "ecosystem": "npm"
      },
      {
        "name": "ignore",
        "version": "5.3.2",
        "ecosystem": "npm"
      },
      {
        "name": "ignore",
        "version": "7.0.12",
        "ecosystem": "npm"
      },
      {
        "name": "imurmurhash",
        "version": "0.1.4",
        "ecosystem": "npm"
      },
      {
        "name": "inherits",
        "version": "2.0.4",
        "ecosystem": "npm"
      },
      {
        "name": "ipaddr.js",
        "version": "1.9.1",
        "ecosystem": "npm"
      },
      {
        "name": "is-extglob",
        "version": "2.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "is-glob",
        "version": "4.0.3",
        "ecosystem": "npm"
      },
      {
        "name": "is-plain-object",
        "version": "5.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "is-promise",
        "version": "4.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "isexe",
        "version": "2.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "js-tokens",
        "version": "10.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "json-schema-traverse",
        "version": "0.4.1",
        "ecosystem": "npm"
      },
      {
        "name": "json-stable-stringify-without-jsonify",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "keyv",
        "version": "5.6.0",
        "ecosystem": "npm"
      },
      {
        "name": "launder",
        "version": "1.7.2",
        "ecosystem": "npm"
      },
      {
        "name": "levn",
        "version": "0.4.1",
        "ecosystem": "npm"
      },
      {
        "name": "lightningcss",
        "version": "1.33.0",
        "ecosystem": "npm"
      },
      {
        "name": "lightningcss-linux-x64-gnu",
        "version": "1.33.0",
        "ecosystem": "npm"
      },
      {
        "name": "locate-path",
        "version": "6.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "magic-string",
        "version": "1.4.3",
        "ecosystem": "npm"
      },
      {
        "name": "magicast",
        "version": "0.5.5",
        "ecosystem": "npm"
      },
      {
        "name": "math-intrinsics",
        "version": "1.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "media-typer",
        "version": "0.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "media-typer",
        "version": "1.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "merge-descriptors",
        "version": "2.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "methods",
        "version": "1.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "mime",
        "version": "2.6.0",
        "ecosystem": "npm"
      },
      {
        "name": "mime-db",
        "version": "1.52.0",
        "ecosystem": "npm"
      },
      {
        "name": "mime-db",
        "version": "1.54.0",
        "ecosystem": "npm"
      },
      {
        "name": "mime-types",
        "version": "2.1.35",
        "ecosystem": "npm"
      },
      {
        "name": "mime-types",
        "version": "3.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "minimatch",
        "version": "10.2.6",
        "ecosystem": "npm"
      },
      {
        "name": "ms",
        "version": "2.1.3",
        "ecosystem": "npm"
      },
      {
        "name": "nanoid",
        "version": "3.3.20",
        "ecosystem": "npm"
      },
      {
        "name": "natural-compare",
        "version": "1.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "negotiator",
        "version": "1.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "object-inspect",
        "version": "1.13.4",
        "ecosystem": "npm"
      },
      {
        "name": "obug",
        "version": "3.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "on-exit-leak-free",
        "version": "2.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "on-finished",
        "version": "2.4.1",
        "ecosystem": "npm"
      },
      {
        "name": "once",
        "version": "1.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "optionator",
        "version": "0.9.4",
        "ecosystem": "npm"
      },
      {
        "name": "p-limit",
        "version": "3.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "p-locate",
        "version": "5.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "parse-srcset",
        "version": "1.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "parseurl",
        "version": "1.3.3",
        "ecosystem": "npm"
      },
      {
        "name": "path-exists",
        "version": "4.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "path-key",
        "version": "3.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "path-to-regexp",
        "version": "8.4.2",
        "ecosystem": "npm"
      },
      {
        "name": "picocolors",
        "version": "1.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "picomatch",
        "version": "4.0.7",
        "ecosystem": "npm"
      },
      {
        "name": "pino-abstract-transport",
        "version": "3.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "pino-std-serializers",
        "version": "7.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "postcss",
        "version": "8.5.30",
        "ecosystem": "npm"
      },
      {
        "name": "prelude-ls",
        "version": "1.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "process-warning",
        "version": "5.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "proxy-addr",
        "version": "2.0.8",
        "ecosystem": "npm"
      },
      {
        "name": "punycode",
        "version": "2.3.1",
        "ecosystem": "npm"
      },
      {
        "name": "qified",
        "version": "0.10.1",
        "ecosystem": "npm"
      },
      {
        "name": "qs",
        "version": "6.16.1",
        "ecosystem": "npm"
      },
      {
        "name": "quick-format-unescaped",
        "version": "4.0.4",
        "ecosystem": "npm"
      },
      {
        "name": "range-parser",
        "version": "1.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "raw-body",
        "version": "3.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "real-require",
        "version": "1.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "rolldown",
        "version": "1.2.14",
        "ecosystem": "npm"
      },
      {
        "name": "router",
        "version": "2.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "safe-stable-stringify",
        "version": "2.5.0",
        "ecosystem": "npm"
      },
      {
        "name": "safer-buffer",
        "version": "2.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "semver",
        "version": "7.8.5",
        "ecosystem": "npm"
      },
      {
        "name": "send",
        "version": "1.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "serve-static",
        "version": "2.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "setprototypeof",
        "version": "1.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "shebang-command",
        "version": "2.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "shebang-regex",
        "version": "3.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "side-channel",
        "version": "1.1.1",
        "ecosystem": "npm"
      },
      {
        "name": "side-channel-list",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "side-channel-map",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "side-channel-weakmap",
        "version": "1.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "sonic-boom",
        "version": "4.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "source-map-js",
        "version": "1.2.2",
        "ecosystem": "npm"
      },
      {
        "name": "split2",
        "version": "4.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "statuses",
        "version": "2.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "std-env",
        "version": "4.3.0",
        "ecosystem": "npm"
      },
      {
        "name": "streamsearch",
        "version": "1.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "superagent",
        "version": "10.4.1",
        "ecosystem": "npm"
      },
      {
        "name": "thread-stream",
        "version": "4.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "tinybench",
        "version": "6.2.2",
        "ecosystem": "npm"
      },
      {
        "name": "tinyexec",
        "version": "1.3.1",
        "ecosystem": "npm"
      },
      {
        "name": "tinyglobby",
        "version": "0.2.17",
        "ecosystem": "npm"
      },
      {
        "name": "tinyrainbow",
        "version": "3.2.0",
        "ecosystem": "npm"
      },
      {
        "name": "toidentifier",
        "version": "1.0.1",
        "ecosystem": "npm"
      },
      {
        "name": "ts-api-utils",
        "version": "2.5.0",
        "ecosystem": "npm"
      },
      {
        "name": "type-check",
        "version": "0.4.0",
        "ecosystem": "npm"
      },
      {
        "name": "type-is",
        "version": "1.6.18",
        "ecosystem": "npm"
      },
      {
        "name": "type-is",
        "version": "2.1.0",
        "ecosystem": "npm"
      },
      {
        "name": "undici-types",
        "version": "7.24.6",
        "ecosystem": "npm"
      },
      {
        "name": "unpipe",
        "version": "1.0.0",
        "ecosystem": "npm"
      },
      {
        "name": "uri-js",
        "version": "4.4.1",
        "ecosystem": "npm"
      },
      {
        "name": "vary",
        "version": "1.1.2",
        "ecosystem": "npm"
      },
      {
        "name": "vite",
        "version": "8.3.4",
        "ecosystem": "npm"
      },
      {
        "name": "which",
        "version": "2.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "why-is-node-running",
        "version": "3.2.1",
        "ecosystem": "npm"
      },
      {
        "name": "word-wrap",
        "version": "1.2.5",
        "ecosystem": "npm"
      },
      {
        "name": "wrappy",
        "version": "1.0.2",
        "ecosystem": "npm"
      },
      {
        "name": "yocto-queue",
        "version": "0.1.0",
        "ecosystem": "npm"
      }
    ]
  }
}
```

### evaluation/raw/T-025.output.json

```json
{
  "packages_scanned": 127,
  "vulnerable_count": 0,
  "status": "clean",
  "message": "No known vulnerabilities found in scanned packages."
}
```

### evaluation/raw/T-026.input.json

```json
{
  "tool": "mcp__sec-review__general_verify_code_security",
  "arguments": {
    "components": "browser-frontend,user-generated-content,session-management,web-endpoint,file-upload",
    "data_handled": "credentials,personal_data",
    "file_path": "ui/src, ui/views"
  }
}
```

### evaluation/raw/T-026.output.json

```json
{
  "success": true,
  "review_type": "ai_powered_security_review",
  "instructions": "IMPORTANT: You (the AI agent) must now perform the security review. The code is not included here: review the code you just wrote, which is already in your context, using the checklist and focus areas. Report all security issues found with severity ratings and fixes.",
  "review_prompt": "## SECURITY CODE REVIEW REQUEST\n\n**File:** `ui/src, ui/views`\n**Components:** browser-frontend, user-generated-content, session-management, web-endpoint, file-upload\n**Risk Level:** CRITICAL\n\n### Review Instructions\n\nReview the code you just wrote (it is already in your context) for security vulnerabilities. For each issue found:\n1. Identify the vulnerability type and severity (Critical/High/Medium/Low)\n2. Explain why it's a security risk\n3. Show the problematic code snippet\n4. Provide a secure code fix\n\n### Focus Areas\n\nPay special attention to:\n- A user calls an admin or other-role function because only the UI hides it\n- An uploaded archive writes files outside the target folder when extracted\n- Sensitive data travels over plain HTTP or an unencrypted connection\n- Debug features or consoles are left on in production\n- Frontend code writes untrusted data into the page with unsafe DOM APIs\n- .env, .git, or backup files are reachable from the web\n- Forged or unsigned JWTs are accepted\n- Long-lived storage keys are shipped to the browser or mobile app\n- A request sets fields the user should not control, such as role or price\n- One user reads or changes another user's data by changing an id in the request\n- Session ids, reset tokens, or API keys can be guessed\n- An attacker plants a session id before login and reuses it afterwards\n\n### Security Checklist\n\nVerify each item and report violations:\n- [ ] Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.\n- [ ] Extract archives safely: Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.\n- [ ] Use HTTPS for every connection: Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.\n- [ ] Turn debug features off in production: Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.\n- [ ] Use safe DOM APIs: Use textContent or framework bindings instead of innerHTML, document.write, or dangerouslySetInnerHTML.\n- [ ] Encode output for its context: Use your template engine's automatic escaping, and encode correctly for HTML, attributes, URLs, and JavaScript.\n- [ ] Do not deploy repo metadata or env files: Exclude .git, .env, and backups from the build and the web root, and block them at the web server.\n- [ ] Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.\n- [ ] Verify token signatures against an allow-list of algorithms: Verify every JWT signature, fix the accepted algorithms in code, and load keys from trusted configuration. Never accept alg none.\n- [ ] Give clients short-lived, narrowly scoped credentials: Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.\n- [ ] Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.\n- [ ] Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.\n- [ ] Generate tokens with a cryptographic random source: Use secrets.token_urlsafe, crypto.randomBytes, or the framework default. Never use Math.random, time, or counters.\n- [ ] Issue a fresh session at login: Create a new session id on every login and re-authentication, and discard the old one.\n- [ ] Sanitize user-provided HTML: Run user HTML through a maintained sanitizer such as DOMPurify or bleach with a strict allow-list. Prefer markdown or plain text.\n- [ ] Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.\n- [ ] Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.\n- [ ] Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.\n- [ ] Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.\n\n### Expected Response Format\n\nProvide your security review with:\n1. **Summary:** Overall assessment (Secure/Needs Attention/Insecure)\n2. **Findings:** List of security issues with severity and fixes\n3. **Checklist Results:** Which items pass/fail\n4. **Recommendations:** Prioritized list of actions",
  "context": {
    "file_path": "ui/src, ui/views",
    "components": [
      "browser-frontend",
      "user-generated-content",
      "session-management",
      "web-endpoint",
      "file-upload"
    ],
    "risk_level": "critical"
  },
  "security_checklist": [
    "Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.",
    "Extract archives safely: Ignore paths inside archives, reject symlinks and entries that escape the target folder, and cap size and file count.",
    "Use HTTPS for every connection: Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.",
    "Turn debug features off in production: Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.",
    "Use safe DOM APIs: Use textContent or framework bindings instead of innerHTML, document.write, or dangerouslySetInnerHTML.",
    "Encode output for its context: Use your template engine's automatic escaping, and encode correctly for HTML, attributes, URLs, and JavaScript.",
    "Do not deploy repo metadata or env files: Exclude .git, .env, and backups from the build and the web root, and block them at the web server.",
    "Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.",
    "Verify token signatures against an allow-list of algorithms: Verify every JWT signature, fix the accepted algorithms in code, and load keys from trusted configuration. Never accept alg none.",
    "Give clients short-lived, narrowly scoped credentials: Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.",
    "Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.",
    "Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.",
    "Generate tokens with a cryptographic random source: Use secrets.token_urlsafe, crypto.randomBytes, or the framework default. Never use Math.random, time, or counters.",
    "Issue a fresh session at login: Create a new session id on every login and re-authentication, and discard the old one.",
    "Sanitize user-provided HTML: Run user HTML through a maintained sanitizer such as DOMPurify or bleach with a strict allow-list. Prefer markdown or plain text.",
    "Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.",
    "Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.",
    "Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.",
    "Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies."
  ],
  "focus_areas": [
    "A user calls an admin or other-role function because only the UI hides it",
    "An uploaded archive writes files outside the target folder when extracted",
    "Sensitive data travels over plain HTTP or an unencrypted connection",
    "Debug features or consoles are left on in production",
    "Frontend code writes untrusted data into the page with unsafe DOM APIs",
    ".env, .git, or backup files are reachable from the web",
    "Forged or unsigned JWTs are accepted",
    "Long-lived storage keys are shipped to the browser or mobile app",
    "A request sets fields the user should not control, such as role or price",
    "One user reads or changes another user's data by changing an id in the request",
    "Session ids, reset tokens, or API keys can be guessed",
    "An attacker plants a session id before login and reuses it afterwards"
  ],
  "expected_response": {
    "format": "structured_security_review",
    "required_sections": [
      "overall_assessment",
      "findings_list",
      "checklist_results",
      "recommended_fixes"
    ]
  }
}
```

### evaluation/raw/T-026.review.md

```markdown
# Review produced by following the T-026 review_prompt

Scope: the UI server as committed in the phase 5 baseline: `ui/src/**` (API client, middleware, CSRF, Markdown
renderer, redirects, controllers, view models, app wiring) and `ui/views/**`. Components: browser-frontend,
user-generated-content, session-management, web-endpoint, file-upload.

## 1. Summary

**Needs Attention (low).** No critical, high or medium issues. Two low issues to fix, one low issue to accept.

## 2. Findings

| # | Severity (mine) | Issue | Where | Fix |
| --- | --- | --- | --- | --- |
| R26-1 | Low | One secret (`COOKIE_SECRET`) keys two HMAC purposes: cookie-parser signs flash cookies with it, and the CSRF token is `HMAC(secret, "csrf:" + cookie)`. Flash values always start with `{"type"`, so no collision is reachable today, but one key serving two purposes is fragile. | `src/app.ts`: `cookieParser(config.cookieSecret)` and `new CsrfProtection(config.cookieSecret, …)` | Derive per-purpose keys: `HMAC(COOKIE_SECRET, "taskboard/cookie-signing")` and `HMAC(COOKIE_SECRET, "taskboard/csrf")`. → F-087 |
| R26-2 | Low | `TRUST_PROXY_HOPS` must equal the number of proxies in front of the UI. At 0 behind the ALB, every user gets the ALB's IP, so the API's per-IP login and forgot-password limits become one global bucket: one attacker can lock everyone out. Set too high, a client can spoof `X-Forwarded-For` and evade per-IP limits. | `src/config.ts` default 0; deployment config | Set `TRUST_PROXY_HOPS=1` in the AWS user_data (one ALB hop) and leave it at 0 in Compose, where the UI is reached directly. Document it in DEPLOYMENT.md. → F-088 (phase 6/7) |
| R26-3 | Low | Multer keeps each upload (≤10 MB) in memory before forwarding it, so many concurrent uploads raise memory use. | `src/controllers/TaskController.ts` `multer.memoryStorage()` | Accept. Only signed-in users reach multer (the session guard runs first), one file per request, 10 MB cap, and the API applies its own limits. → F-089 (accepted risk) |

## 3. Checklist results

| Checklist item | Result | Evidence |
| --- | --- | --- |
| Check permissions on the server for every action | Pass | `requireAdmin` only hides pages; every action goes through the API, which enforces roles and membership (T-014). Test: members get 403 on `/admin/*`. |
| Extract archives safely | N/A | |
| Use HTTPS for every connection | Partial | HSTS and `upgrade-insecure-requests` when `COOKIE_SECURE=true`; TLS ends at the ALB (phase 6); the UI→API hop is HTTP in private subnets (accepted, F-004/TM-17). |
| Turn debug features off in production | Pass | `NODE_ENV` defaults to production; `x-powered-by` disabled; errors render a generic page with the request id; no stack traces. |
| Use safe DOM APIs | Pass | The UI ships no client-side JavaScript at all; CSP `script-src 'none'`. → F-085 fixed |
| Encode output for its context | Pass | Every dynamic value uses EJS `<%= %>` (HTML-escaped, quotes included). `<%- %>` appears only for includes and the sanitized `descriptionHtml`/`bodyHtml`. Ids in URLs are UUIDs; the search pager uses `URLSearchParams` output. |
| Do not deploy repo metadata or env files | Open (phase 7) | `express.static` serves only `public/` with `dotfiles: 'deny'`; `.dockerignore` comes in phase 7. |
| Load secrets from environment | Pass | `SERVICE_AUTH_SECRET`, `COOKIE_SECRET` come from env, are validated (≥32 characters) and have no defaults. |
| Verify JWT signatures | N/A | Opaque tokens. |
| Short-lived scoped credentials for clients | N/A | The browser only ever holds the HttpOnly session cookie. |
| Accept only the fields you expect | Pass | `readTaskForm`, `readTaskQuery` and the admin action map build explicit objects; unknown enum values are dropped. |
| Check the user owns the object | Pass (API) | Path ids are checked as UUIDs before any API call (`assertUuid`), so no path traversal into the API URL; ownership is enforced by the API. |
| Cryptographic random tokens | Pass | CSRF cookie `randomBytes(32)`; request ids `randomUUID()`; session tokens come from the API. |
| Fresh session at login | Pass | Every login stores the new API token; an existing session is logged out at the API first. With `__Host-` cookies a sibling subdomain cannot plant a session. Test `ends the old session when logging in again`. |
| Sanitize user-provided HTML | Pass | `marked`, then `sanitize-html` with a tag allow-list, `http/https/mailto` links only, no protocol-relative URLs, forced `rel="nofollow noopener noreferrer"`. Nine XSS vectors are unit-tested. → F-039 |
| Validate all input on the server | Pass | Body limit 64 KB / 50 params; multer limits (1 file, 4 fields, 5 parts); the API re-validates everything. |
| Parameterized queries | N/A | No database in the UI. |
| Generic errors | Pass | `ErrorHandler`: 5xx → "The service is unavailable"; login shows the API's generic credential message. |
| Secrets and personal data out of logs | Pass | Access log has method, path (no query string, so reset tokens are never logged), status and duration. No bodies, cookies or headers are logged. |

## 4. Recommendations

1. R26-1: separate HMAC keys (F-087).
2. R26-2: set `TRUST_PROXY_HOPS=1` behind the ALB and document it (F-088).
3. R26-3: accept (F-089).
```

### evaluation/raw/T-027.input.json

```json
{
  "tool": "mcp__sec-review__general_lightweight_security_review",
  "arguments": {
    "task_description": "Write Terraform (>= 1.9, AWS provider 6.x) for Taskboard: reusable modules network (VPC over two AZs, public and private subnets, NAT gateway, route tables), alb (public Application Load Balancer forwarding to UI instances), ui and api (launch templates and EC2 instances in private subnets bootstrapped with user_data that installs Docker, pulls images from ECR and runs the service with configuration and secrets fetched from SSM Parameter Store / Secrets Manager), database (RDS PostgreSQL 16), cache (ElastiCache Redis OSS/Valkey), storage (S3 bucket for attachments), registry (ECR repositories), iam (roles and instance profiles), composed in envs/dev with a partial S3 backend. The API must never be internet-exposed.",
    "components": "container-and-iac,secrets-and-config,transport-security,object-storage,database",
    "data_handled": "credentials,secrets,personal_data",
    "technologies": "Terraform, AWS VPC, ALB, EC2, RDS PostgreSQL, ElastiCache, S3, ECR, IAM, SSM, Docker"
  }
}
```

### evaluation/raw/T-027.output.json

```json
{"success":true,"review_type":"lightweight_pre_coding","status":"complete","task_description":"Write Terraform (>= 1.9, AWS provider 6.x) for Taskboard: reusable modules network (VPC over two AZs, public and private subnets, NAT gateway, route tables), alb (public Application Load Balancer forwarding to UI instances), ui and api (launch templates and EC2 instances in private subnets bootstrapped with user_data that installs Docker, pulls images from ECR and runs the service with configuration and secrets fetched from SSM Parameter Store / Secrets Manager), database (RDS PostgreSQL 16), cache (ElastiCache Redis OSS/Valkey), storage (S3 bucket for attachments), registry (ECR repositories), iam (roles and instance profiles), composed in envs/dev with a partial S3 backend. The API must never be internet-exposed.","technologies":["Terraform","AWS VPC","ALB","EC2","RDS PostgreSQL","ElastiCache","S3","ECR","IAM","SSM","Docker"],"assessment":{"risk_level":"critical","components":["container-and-iac","secrets-and-config","transport-security","object-storage","database"],"implied_components":[],"sensitive_data":["credentials","secrets","personal_data"],"threats":[{"id":"hardcoded-secrets","name":"API keys or passwords are committed to the repo or baked into code","severity":"critical","cwe":["CWE-798"]},{"id":"sql-injection","name":"Attacker input changes the meaning of a database query","severity":"critical","cwe":["CWE-89"]},{"id":"weak-password-storage","name":"Passwords are stored in plain text or with a fast hash, so a database leak exposes them","severity":"critical","cwe":["CWE-916"]},{"id":"cleartext-transport","name":"Sensitive data travels over plain HTTP or an unencrypted connection","severity":"high","cwe":["CWE-319"]},{"id":"debug-mode-in-production","name":"Debug features or consoles are left on in production","severity":"high","cwe":["CWE-489"]},{"id":"default-accounts","name":"Default or hardcoded admin accounts are left active","severity":"high","cwe":["CWE-798"]},{"id":"exposed-config-files","name":".env, .git, or backup files are reachable from the web","severity":"high","cwe":["CWE-538"]},{"id":"exposed-data-store","name":"A database, cache, or admin port is reachable from the internet","severity":"high","cwe":["CWE-668"]},{"id":"hardcoded-crypto-keys","name":"Encryption or signing keys are hardcoded or shared across environments","severity":"high","cwe":["CWE-321"]},{"id":"long-lived-storage-credentials","name":"Long-lived storage keys are shipped to the browser or mobile app","severity":"high","cwe":["CWE-798"]},{"id":"mass-assignment","name":"A request sets fields the user should not control, such as role or price","severity":"high","cwe":["CWE-915"]},{"id":"nosql-injection","name":"Query operators in user input bypass filters in a NoSQL database","severity":"high","cwe":["CWE-943"]},{"id":"object-id-guessing","name":"One user reads or changes another user's data by changing an id in the request","severity":"high","cwe":["CWE-639"]},{"id":"overbroad-cloud-permissions","name":"Cloud roles or service accounts allow far more than the app needs","severity":"high","cwe":["CWE-269"]},{"id":"public-bucket","name":"Storage bucket is publicly listable or readable","severity":"high","cwe":["CWE-732"]},{"id":"secrets-baked-into-image","name":"Secrets are copied into the image or passed as build arguments","severity":"high","cwe":["CWE-540"]},{"id":"sensitive-data-unencrypted","name":"Sensitive fields are stored unencrypted, so a backup or database leak exposes them","severity":"high","cwe":["CWE-311"]},{"id":"tenant-data-leak","name":"Queries miss the tenant filter, so customers see each other's data","severity":"high","cwe":["CWE-284"]},{"id":"agent-reads-secrets","name":"The coding agent can read .env files, SSH keys, or cloud credentials","severity":"medium","cwe":["CWE-200"],"mcp_top10":["MCP01:2025"]},{"id":"container-runs-as-root","name":"The container runs as root, so an app flaw becomes host-level access","severity":"medium","cwe":["CWE-250"]},{"id":"outdated-tls","name":"Old TLS or SSL versions or weak cipher suites are still enabled","severity":"medium","cwe":["CWE-327"]},{"id":"over-privileged-db-account","name":"The app connects as an admin database user, so any flaw becomes full data access","severity":"medium","cwe":["CWE-250"]}],"countermeasures":[{"id":"secrets-manager","name":"Load secrets from a secrets manager or environment","how_to":"Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.","effort":"medium","asvs":["v5.0.0-13.3.1","v5.0.0-13.3.2"],"mitigates":["hardcoded-secrets","exposed-config-files","hardcoded-crypto-keys","secrets-baked-into-image"]},{"id":"parameterized-queries","name":"Use parameterized queries or an ORM","how_to":"Pass user values as parameters. Never build SQL or query documents by joining strings.","effort":"low","asvs":["v5.0.0-1.2.4"],"mitigates":["sql-injection","nosql-injection"]},{"id":"slow-password-hashing","name":"Hash passwords with a slow, salted algorithm","how_to":"Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.","effort":"low","asvs":["v5.0.0-11.4.2"],"mitigates":["weak-password-storage"]},{"id":"https-everywhere","name":"Use HTTPS for every connection","how_to":"Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.","effort":"low","asvs":["v5.0.0-12.2.1","v5.0.0-12.2.2"],"mitigates":["cleartext-transport"]},{"id":"disable-debug-in-prod","name":"Turn debug features off in production","how_to":"Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.","effort":"low","asvs":["v5.0.0-13.4.2"],"mitigates":["debug-mode-in-production"]},{"id":"remove-default-accounts","name":"Remove default and hardcoded accounts","how_to":"Ship no preset admin users. Create the first admin through a one-time setup step with a strong generated password.","effort":"low","asvs":["v5.0.0-6.3.2"],"mitigates":["default-accounts"]},{"id":"no-vcs-or-env-files-deployed","name":"Do not deploy repo metadata or env files","how_to":"Exclude .git, .env, and backups from the build and the web root, and block them at the web server.","effort":"low","asvs":["v5.0.0-13.4.1"],"mitigates":["exposed-config-files"]},{"id":"private-network-for-data-stores","name":"Keep data stores off the public internet","how_to":"Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.","effort":"low","asvs":[],"mitigates":["exposed-data-store"]},{"id":"separate-keys-per-environment","name":"Use separate keys per environment and rotate them","how_to":"Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.","effort":"medium","asvs":[],"mitigates":["hardcoded-crypto-keys"]},{"id":"short-lived-scoped-credentials","name":"Give clients short-lived, narrowly scoped credentials","how_to":"Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.","effort":"medium","asvs":[],"mitigates":["long-lived-storage-credentials"]},{"id":"allow-list-fields","name":"Accept only the fields you expect","how_to":"Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.","effort":"low","asvs":["v5.0.0-15.3.3"],"mitigates":["mass-assignment"]},{"id":"check-permissions-server-side","name":"Check permissions on the server for every action","how_to":"Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.","effort":"medium","asvs":["v5.0.0-8.2.1","v5.0.0-8.3.1"],"mitigates":["mass-assignment"]},{"id":"server-side-validation","name":"Validate all input on the server","how_to":"Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.","effort":"low","asvs":["v5.0.0-2.2.1","v5.0.0-2.2.2"],"mitigates":["nosql-injection"]},{"id":"per-object-authorization","name":"Check the user owns the object on every request","how_to":"Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.","effort":"medium","asvs":["v5.0.0-8.2.2","v5.0.0-8.3.1"],"mitigates":["object-id-guessing"]},{"id":"least-privilege-iam","name":"Grant only the cloud permissions the app uses","how_to":"Write narrow roles per service, avoid wildcards on actions and resources, and review them when features change.","effort":"medium","asvs":[],"mitigates":["overbroad-cloud-permissions"]},{"id":"private-storage-signed-urls","name":"Keep storage private and hand out short-lived signed URLs","how_to":"Block public access on the bucket and issue signed URLs that expire in minutes.","effort":"low","asvs":[],"mitigates":["public-bucket"]},{"id":"encrypt-sensitive-data","name":"Encrypt sensitive data at rest","how_to":"Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.","effort":"medium","asvs":["v5.0.0-11.3.2"],"mitigates":["sensitive-data-unencrypted"]},{"id":"scope-queries-to-tenant","name":"Scope every query to the tenant","how_to":"Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.","effort":"medium","asvs":["v5.0.0-8.2.2"],"mitigates":["tenant-data-leak"]},{"id":"keep-secrets-out-of-agent-reach","name":"Keep secrets out of the agent's reach","how_to":"Deny reads of .env files, SSH keys, and cloud credentials in the agent's permission rules, and use scoped short-lived credentials.","effort":"low","asvs":[],"mitigates":["agent-reads-secrets"]},{"id":"non-root-minimal-images","name":"Run containers as non-root on minimal images","how_to":"Set a non-root USER, use a slim or distroless base image, and drop extra capabilities.","effort":"low","asvs":["v5.0.0-15.2.3"],"mitigates":["container-runs-as-root"]},{"id":"modern-tls-config","name":"Enable only current TLS versions and cipher suites","how_to":"Allow TLS 1.2 and 1.3 only, use the recommended cipher suites from your platform or proxy, and turn off SSL and older TLS.","effort":"low","asvs":["v5.0.0-12.1.1","v5.0.0-12.1.2"],"mitigates":["outdated-tls"]},{"id":"least-privilege-accounts","name":"Give the app a least-privilege database account","how_to":"Create a user limited to the tables and operations the app needs. Keep migrations on a separate admin account.","effort":"medium","asvs":[],"mitigates":["over-privileged-db-account"]}],"also_consider":[],"summary":"22 threats and 22 countermeasures for container-and-iac, secrets-and-config, transport-security, object-storage, database. Risk level critical (highest threat severity, raised for sensitive data)."},"hint":null,"instructions":"Build these countermeasures in as you write the code, starting with the most severe threats. These threats come from the components you picked. also_consider lists general threats from implied components; pass those components explicitly for full detail. After writing code, call general_verify_code_security with the same components.","metadata":{"total_threats":22,"total_countermeasures":22,"also_consider_total":0,"review_purpose":"lightweight_security_guidance"}}
```

### evaluation/raw/T-029.input.json

```json
{
  "tool": "mcp__sec-review__general_verify_code_security",
  "arguments": {
    "components": "container-and-iac,secrets-and-config,transport-security,object-storage,database",
    "data_handled": "credentials,secrets,personal_data",
    "file_path": "infra/modules, infra/envs/dev"
  }
}
```

### evaluation/raw/T-029.output.json

```json
{
  "success": true,
  "review_type": "ai_powered_security_review",
  "instructions": "IMPORTANT: You (the AI agent) must now perform the security review. The code is not included here: review the code you just wrote, which is already in your context, using the checklist and focus areas. Report all security issues found with severity ratings and fixes.",
  "review_prompt": "## SECURITY CODE REVIEW REQUEST\n\n**File:** `infra/modules, infra/envs/dev`\n**Components:** container-and-iac, secrets-and-config, transport-security, object-storage, database\n**Risk Level:** CRITICAL\n\n### Review Instructions\n\nReview the code you just wrote (it is already in your context) for security vulnerabilities. For each issue found:\n1. Identify the vulnerability type and severity (Critical/High/Medium/Low)\n2. Explain why it's a security risk\n3. Show the problematic code snippet\n4. Provide a secure code fix\n\n### Focus Areas\n\nPay special attention to:\n- API keys or passwords are committed to the repo or baked into code\n- Attacker input changes the meaning of a database query\n- Passwords are stored in plain text or with a fast hash, so a database leak exposes them\n- Sensitive data travels over plain HTTP or an unencrypted connection\n- Debug features or consoles are left on in production\n- Default or hardcoded admin accounts are left active\n- .env, .git, or backup files are reachable from the web\n- A database, cache, or admin port is reachable from the internet\n- Encryption or signing keys are hardcoded or shared across environments\n- Long-lived storage keys are shipped to the browser or mobile app\n- A request sets fields the user should not control, such as role or price\n- Query operators in user input bypass filters in a NoSQL database\n\n### Security Checklist\n\nVerify each item and report violations:\n- [ ] Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.\n- [ ] Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.\n- [ ] Hash passwords with a slow, salted algorithm: Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.\n- [ ] Use HTTPS for every connection: Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.\n- [ ] Turn debug features off in production: Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.\n- [ ] Remove default and hardcoded accounts: Ship no preset admin users. Create the first admin through a one-time setup step with a strong generated password.\n- [ ] Do not deploy repo metadata or env files: Exclude .git, .env, and backups from the build and the web root, and block them at the web server.\n- [ ] Keep data stores off the public internet: Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.\n- [ ] Use separate keys per environment and rotate them: Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.\n- [ ] Give clients short-lived, narrowly scoped credentials: Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.\n- [ ] Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.\n- [ ] Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.\n- [ ] Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.\n- [ ] Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.\n- [ ] Grant only the cloud permissions the app uses: Write narrow roles per service, avoid wildcards on actions and resources, and review them when features change.\n- [ ] Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.\n- [ ] Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.\n\n### Expected Response Format\n\nProvide your security review with:\n1. **Summary:** Overall assessment (Secure/Needs Attention/Insecure)\n2. **Findings:** List of security issues with severity and fixes\n3. **Checklist Results:** Which items pass/fail\n4. **Recommendations:** Prioritized list of actions",
  "context": {
    "file_path": "infra/modules, infra/envs/dev",
    "components": [
      "container-and-iac",
      "secrets-and-config",
      "transport-security",
      "object-storage",
      "database"
    ],
    "risk_level": "critical"
  },
  "security_checklist": [
    "Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.",
    "Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.",
    "Hash passwords with a slow, salted algorithm: Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.",
    "Use HTTPS for every connection: Serve everything over HTTPS with a trusted certificate, redirect HTTP to HTTPS, and use TLS for service-to-service calls as well.",
    "Turn debug features off in production: Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.",
    "Remove default and hardcoded accounts: Ship no preset admin users. Create the first admin through a one-time setup step with a strong generated password.",
    "Do not deploy repo metadata or env files: Exclude .git, .env, and backups from the build and the web root, and block them at the web server.",
    "Keep data stores off the public internet: Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.",
    "Use separate keys per environment and rotate them: Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.",
    "Give clients short-lived, narrowly scoped credentials: Issue pre-signed or token-exchanged credentials limited to one object or prefix. Never ship long-lived keys to clients.",
    "Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.",
    "Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.",
    "Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.",
    "Check the user owns the object on every request: Look the object up by id AND owner, or check ownership explicitly, and return 404 when they do not match.",
    "Grant only the cloud permissions the app uses: Write narrow roles per service, avoid wildcards on actions and resources, and review them when features change.",
    "Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.",
    "Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies."
  ],
  "focus_areas": [
    "API keys or passwords are committed to the repo or baked into code",
    "Attacker input changes the meaning of a database query",
    "Passwords are stored in plain text or with a fast hash, so a database leak exposes them",
    "Sensitive data travels over plain HTTP or an unencrypted connection",
    "Debug features or consoles are left on in production",
    "Default or hardcoded admin accounts are left active",
    ".env, .git, or backup files are reachable from the web",
    "A database, cache, or admin port is reachable from the internet",
    "Encryption or signing keys are hardcoded or shared across environments",
    "Long-lived storage keys are shipped to the browser or mobile app",
    "A request sets fields the user should not control, such as role or price",
    "Query operators in user input bypass filters in a NoSQL database"
  ],
  "expected_response": {
    "format": "structured_security_review",
    "required_sections": [
      "overall_assessment",
      "findings_list",
      "checklist_results",
      "recommended_fixes"
    ]
  }
}
```

### evaluation/raw/T-029.review.md

```markdown
# Review produced by following the T-029 review_prompt

Scope: `infra/modules/*` and `infra/envs/dev` as committed in the phase 6 baseline. Components: container-and-iac,
secrets-and-config, transport-security, object-storage, database.

## 1. Summary

**Needs Attention.** One medium issue (cross-service secret access through a broad AWS managed policy). Two low items
are accepted.

## 2. Findings

| # | Severity (mine) | Issue | Where | Fix |
| --- | --- | --- | --- | --- |
| R29-1 | Medium | `AmazonSSMManagedInstanceCore` is attached to both instance roles. That AWS managed policy grants `ssm:GetParameter` and `ssm:GetParameters` on `Resource: "*"`. Both roles also get `kms:Decrypt` on the config key whenever SSM calls it. Together, the **UI** role can read and decrypt the API's SecureStrings (`DATABASE_URL`, `REDIS_URL`, `WEBHOOK_SIGNING_SECRET`) and the operator-only `/migrate/DB_APP_PASSWORD`. A compromised UI host would get database access, which defeats the separation the per-service SSM paths were meant to give. | `modules/iam/main.tf` `aws_iam_role_policy_attachment.ssm_core`, `DecryptOwnConfig` | Replace the managed policy with a minimal Session Manager policy (`ssm:UpdateInstanceInformation`, `ssmmessages:*Channel`, `ec2messages:*`, with no parameter access). Also bind `kms:Decrypt` to the service's own parameter ARNs through the `kms:EncryptionContext:PARAMETER_ARN` condition, so decryption fails even if another policy grants a wider read. → F-090 |
| R29-2 | Low | No AWS WAF on the public ALB, and ALB/S3 access logging is off by default (`access_logs_bucket = ""`). | `modules/alb`, `modules/storage` | Accept for dev: an internal tool, ingress can be narrowed with `allowed_ingress_cidrs`, the API rate-limits authentication, and VPC flow logs plus application access logs exist. Access logging can be switched on per environment with the existing variable. → F-091 (accepted risk) |
| R29-3 | Low | Generated secrets (`random_password`) end up in Terraform state. | `envs/dev/secrets.tf` | Accept: state lives in the encrypted, access-restricted S3 backend (`backend.hcl.example`: `encrypt = true`, `kms_key_id`, lockfile). The RDS master password is RDS-managed in Secrets Manager and never enters state. Rotate by tainting the `random_password` resources. Documented in DEPLOYMENT.md. → F-092 (accepted risk) |

## 3. Checklist results

| Checklist item | Result | Evidence |
| --- | --- | --- |
| Load secrets from a secrets manager or environment | Pass | Secrets are generated, stored as SSM SecureString under the config KMS key, read at boot into a root-only env file; nothing in tfvars, user_data or images. |
| Parameterized queries / password hashing / input validation / object ownership / generic errors / mass assignment | N/A to IaC | Covered in API reviews T-014, T-019. |
| Use HTTPS for every connection | Pass, with the accepted internal hop | ALB HTTPS with `ELBSecurityPolicy-TLS13-1-2-2021-06`, HTTP 301 to HTTPS; RDS `rds.force_ssl=1` with `sslmode=verify-full` against the RDS CA bundle; ElastiCache `transit_encryption_mode = required` with `rediss://`; S3 policy denies non-TLS. The UI to internal-ALB to API hop is HTTP inside the VPC (F-004/TM-17, accepted). |
| Turn debug features off in production | Pass | `ENVIRONMENT=production`, `NODE_ENV=production`, `LOG_LEVEL=info` from SSM. |
| Remove default and hardcoded accounts | Pass | No admin is created by Terraform; the `create-admin` command is a one-time deploy step (DEPLOYMENT.md). RDS master user is `taskboard_owner` with an RDS-managed password, used only for migrations. |
| Do not deploy repo metadata or env files | Open (phase 7) | `.dockerignore`. |
| Keep data stores off the public internet | Pass | RDS `publicly_accessible = false` and ElastiCache in data subnets with no internet route; security groups admit 5432/6379 only from the API security group; instances have no public IPs; the API sits behind an internal ALB that admits only the UI security group. → F-057 |
| Separate keys per environment and rotation | Pass | Every key and secret is per environment (state per environment); KMS rotation is on for every CMK; RDS master secret rotation is RDS-managed. |
| Short-lived, scoped client credentials | Pass | No access keys anywhere: instance roles give temporary credentials; IMDSv2 required with hop limit 1. |
| Grant only the cloud permissions the app uses | Fail → R29-1 | Otherwise narrow: ECR pull on its own repository, SSM on its own path, S3 objects only under `attachments/`, KMS via-service conditions, logs on its own log group. `ecr:GetAuthorizationToken` needs `*`. |
| Keep secrets and personal data out of logs | Pass | user_data never echoes values; `set -euo pipefail` without `-x`. |

Additional checks: S3 Block Public Access, BucketOwnerEnforced, versioning and SSE-KMS with a deny for other keys
(F-065, F-058); RDS, ElastiCache, ECR and logs encrypted with CMKs (F-058, F-082); ElastiCache `allkeys-lru` (F-083);
ECR immutable tags and scan on push; launch templates with encrypted gp3 volumes, no key pairs, IMDSv2; containers run
`--read-only --cap-drop ALL --security-opt no-new-privileges`; VPC flow logs; default security group stripped.

## 4. Recommendations

1. R29-1: remove the managed policy and condition the decrypt on parameter ARNs (F-090).
2. R29-2 / R29-3: accept and document (F-091, F-092).
```

### evaluation/raw/T-030.input.json

```json
{
  "tool": "mcp__sec-review__general_lightweight_security_review",
  "arguments": {
    "task_description": "Integrate Taskboard for local development and CI: multi-stage Dockerfiles for the Python API (uv, python slim) and the Node UI (node alpine) running as non-root; a docker-compose.yml running ui, api, a one-shot migrate job, PostgreSQL 16 and Redis 7 where only the UI port is published; a least-privilege PostgreSQL application role created by a management command; a .env.example with placeholder secrets; a Makefile; a bash smoke test that drives the UI with curl (register, login, CSRF tokens, upload/download); and a GitHub Actions CI workflow running lint, type checks, tests with PostgreSQL and Redis service containers, and Terraform checks.",
    "components": "container-and-iac,secrets-and-config,database,dependencies",
    "data_handled": "secrets",
    "technologies": "Docker, Docker Compose, GitHub Actions, uv, npm, PostgreSQL 16, Redis 7, bash"
  }
}
```

### evaluation/raw/T-030.output.json

```json
{"success":true,"review_type":"lightweight_pre_coding","status":"complete","task_description":"Integrate Taskboard for local development and CI: multi-stage Dockerfiles for the Python API (uv, python slim) and the Node UI (node alpine) running as non-root; a docker-compose.yml running ui, api, a one-shot migrate job, PostgreSQL 16 and Redis 7 where only the UI port is published; a least-privilege PostgreSQL application role created by a management command; a .env.example with placeholder secrets; a Makefile; a bash smoke test that drives the UI with curl (register, login, CSRF tokens, upload/download); and a GitHub Actions CI workflow running lint, type checks, tests with PostgreSQL and Redis service containers, and Terraform checks.","technologies":["Docker","Docker Compose","GitHub Actions","uv","npm","PostgreSQL 16","Redis 7","bash"],"assessment":{"risk_level":"critical","components":["container-and-iac","secrets-and-config","database","dependencies"],"implied_components":[],"sensitive_data":["secrets"],"threats":[{"id":"hardcoded-secrets","name":"API keys or passwords are committed to the repo or baked into code","severity":"critical","cwe":["CWE-798"]},{"id":"sql-injection","name":"Attacker input changes the meaning of a database query","severity":"critical","cwe":["CWE-89"]},{"id":"weak-password-storage","name":"Passwords are stored in plain text or with a fast hash, so a database leak exposes them","severity":"critical","cwe":["CWE-916"]},{"id":"debug-mode-in-production","name":"Debug features or consoles are left on in production","severity":"high","cwe":["CWE-489"]},{"id":"default-accounts","name":"Default or hardcoded admin accounts are left active","severity":"high","cwe":["CWE-798"]},{"id":"exposed-config-files","name":".env, .git, or backup files are reachable from the web","severity":"high","cwe":["CWE-538"]},{"id":"exposed-data-store","name":"A database, cache, or admin port is reachable from the internet","severity":"high","cwe":["CWE-668"]},{"id":"hallucinated-package","name":"An AI-suggested package does not exist, and an attacker can register that name","severity":"high","cwe":["CWE-1357"]},{"id":"hardcoded-crypto-keys","name":"Encryption or signing keys are hardcoded or shared across environments","severity":"high","cwe":["CWE-321"]},{"id":"mass-assignment","name":"A request sets fields the user should not control, such as role or price","severity":"high","cwe":["CWE-915"]},{"id":"nosql-injection","name":"Query operators in user input bypass filters in a NoSQL database","severity":"high","cwe":["CWE-943"]},{"id":"overbroad-cloud-permissions","name":"Cloud roles or service accounts allow far more than the app needs","severity":"high","cwe":["CWE-269"]},{"id":"secrets-baked-into-image","name":"Secrets are copied into the image or passed as build arguments","severity":"high","cwe":["CWE-540"]},{"id":"sensitive-data-unencrypted","name":"Sensitive fields are stored unencrypted, so a backup or database leak exposes them","severity":"high","cwe":["CWE-311"]},{"id":"tenant-data-leak","name":"Queries miss the tenant filter, so customers see each other's data","severity":"high","cwe":["CWE-284"]},{"id":"typosquatted-package","name":"A lookalike package name installs malicious code","severity":"high","cwe":["CWE-1357"]},{"id":"vulnerable-dependency","name":"A library with a known CVE is used in a reachable code path","severity":"high","cwe":["CWE-1395"]},{"id":"agent-reads-secrets","name":"The coding agent can read .env files, SSH keys, or cloud credentials","severity":"medium","cwe":["CWE-200"],"mcp_top10":["MCP01:2025"]},{"id":"container-runs-as-root","name":"The container runs as root, so an app flaw becomes host-level access","severity":"medium","cwe":["CWE-250"]},{"id":"over-privileged-db-account","name":"The app connects as an admin database user, so any flaw becomes full data access","severity":"medium","cwe":["CWE-250"]}],"countermeasures":[{"id":"secrets-manager","name":"Load secrets from a secrets manager or environment","how_to":"Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.","effort":"medium","asvs":["v5.0.0-13.3.1","v5.0.0-13.3.2"],"mitigates":["hardcoded-secrets","exposed-config-files","hardcoded-crypto-keys","secrets-baked-into-image"]},{"id":"parameterized-queries","name":"Use parameterized queries or an ORM","how_to":"Pass user values as parameters. Never build SQL or query documents by joining strings.","effort":"low","asvs":["v5.0.0-1.2.4"],"mitigates":["sql-injection","nosql-injection"]},{"id":"slow-password-hashing","name":"Hash passwords with a slow, salted algorithm","how_to":"Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.","effort":"low","asvs":["v5.0.0-11.4.2"],"mitigates":["weak-password-storage"]},{"id":"disable-debug-in-prod","name":"Turn debug features off in production","how_to":"Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.","effort":"low","asvs":["v5.0.0-13.4.2"],"mitigates":["debug-mode-in-production"]},{"id":"remove-default-accounts","name":"Remove default and hardcoded accounts","how_to":"Ship no preset admin users. Create the first admin through a one-time setup step with a strong generated password.","effort":"low","asvs":["v5.0.0-6.3.2"],"mitigates":["default-accounts"]},{"id":"no-vcs-or-env-files-deployed","name":"Do not deploy repo metadata or env files","how_to":"Exclude .git, .env, and backups from the build and the web root, and block them at the web server.","effort":"low","asvs":["v5.0.0-13.4.1"],"mitigates":["exposed-config-files"]},{"id":"private-network-for-data-stores","name":"Keep data stores off the public internet","how_to":"Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.","effort":"low","asvs":[],"mitigates":["exposed-data-store"]},{"id":"verify-packages-exist","name":"Check every new package exists and is the one you meant","how_to":"Confirm the name, age, and publisher on the registry before installing, and watch for lookalike names.","effort":"low","asvs":[],"mitigates":["hallucinated-package","typosquatted-package"]},{"id":"separate-keys-per-environment","name":"Use separate keys per environment and rotate them","how_to":"Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.","effort":"medium","asvs":[],"mitigates":["hardcoded-crypto-keys"]},{"id":"allow-list-fields","name":"Accept only the fields you expect","how_to":"Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.","effort":"low","asvs":["v5.0.0-15.3.3"],"mitigates":["mass-assignment"]},{"id":"check-permissions-server-side","name":"Check permissions on the server for every action","how_to":"Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.","effort":"medium","asvs":["v5.0.0-8.2.1","v5.0.0-8.3.1"],"mitigates":["mass-assignment"]},{"id":"server-side-validation","name":"Validate all input on the server","how_to":"Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.","effort":"low","asvs":["v5.0.0-2.2.1","v5.0.0-2.2.2"],"mitigates":["nosql-injection"]},{"id":"least-privilege-iam","name":"Grant only the cloud permissions the app uses","how_to":"Write narrow roles per service, avoid wildcards on actions and resources, and review them when features change.","effort":"medium","asvs":[],"mitigates":["overbroad-cloud-permissions"]},{"id":"encrypt-sensitive-data","name":"Encrypt sensitive data at rest","how_to":"Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.","effort":"medium","asvs":["v5.0.0-11.3.2"],"mitigates":["sensitive-data-unencrypted"]},{"id":"scope-queries-to-tenant","name":"Scope every query to the tenant","how_to":"Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.","effort":"medium","asvs":["v5.0.0-8.2.2"],"mitigates":["tenant-data-leak"]},{"id":"pin-and-lock-dependencies","name":"Pin versions and commit lockfiles","how_to":"Commit a lockfile, install with the frozen or locked option in CI, and review dependency changes in pull requests.","effort":"low","asvs":["v5.0.0-15.2.1"],"mitigates":["typosquatted-package","vulnerable-dependency"]},{"id":"scan-and-update-dependencies","name":"Scan dependencies and update vulnerable ones","how_to":"Scan lockfiles for known vulnerabilities, fix reachable ones first, and keep updates on a regular schedule.","effort":"low","asvs":["v5.0.0-15.2.1"],"mitigates":["vulnerable-dependency"]},{"id":"keep-secrets-out-of-agent-reach","name":"Keep secrets out of the agent's reach","how_to":"Deny reads of .env files, SSH keys, and cloud credentials in the agent's permission rules, and use scoped short-lived credentials.","effort":"low","asvs":[],"mitigates":["agent-reads-secrets"]},{"id":"non-root-minimal-images","name":"Run containers as non-root on minimal images","how_to":"Set a non-root USER, use a slim or distroless base image, and drop extra capabilities.","effort":"low","asvs":["v5.0.0-15.2.3"],"mitigates":["container-runs-as-root"]},{"id":"least-privilege-accounts","name":"Give the app a least-privilege database account","how_to":"Create a user limited to the tables and operations the app needs. Keep migrations on a separate admin account.","effort":"medium","asvs":[],"mitigates":["over-privileged-db-account"]}],"also_consider":[],"summary":"20 threats and 20 countermeasures for container-and-iac, secrets-and-config, database, dependencies. Risk level critical (highest threat severity, raised for sensitive data)."},"hint":null,"instructions":"Build these countermeasures in as you write the code, starting with the most severe threats. These threats come from the components you picked. also_consider lists general threats from implied components; pass those components explicitly for full detail. After writing code, call general_verify_code_security with the same components.","metadata":{"total_threats":20,"total_countermeasures":20,"also_consider_total":0,"review_purpose":"lightweight_security_guidance"}}
```

### evaluation/raw/T-032.input.json

```json
{
  "tool": "mcp__sec-review__general_verify_code_security",
  "arguments": {
    "components": "container-and-iac,secrets-and-config,database,dependencies",
    "data_handled": "secrets",
    "file_path": "api/Dockerfile, ui/Dockerfile, docker-compose.yml, docker-compose.test.yml, .env.example, scripts/, Makefile, .github/workflows/ci.yml, api/src/taskboard/dbadmin.py"
  }
}
```

### evaluation/raw/T-032.output.json

```json
{
  "success": true,
  "review_type": "ai_powered_security_review",
  "instructions": "IMPORTANT: You (the AI agent) must now perform the security review. The code is not included here: review the code you just wrote, which is already in your context, using the checklist and focus areas. Report all security issues found with severity ratings and fixes.",
  "review_prompt": "## SECURITY CODE REVIEW REQUEST\n\n**File:** `api/Dockerfile, ui/Dockerfile, docker-compose.yml, docker-compose.test.yml, .env.example, scripts/, Makefile, .github/workflows/ci.yml, api/src/taskboard/dbadmin.py`\n**Components:** container-and-iac, secrets-and-config, database, dependencies\n**Risk Level:** CRITICAL\n\n### Review Instructions\n\nReview the code you just wrote (it is already in your context) for security vulnerabilities. For each issue found:\n1. Identify the vulnerability type and severity (Critical/High/Medium/Low)\n2. Explain why it's a security risk\n3. Show the problematic code snippet\n4. Provide a secure code fix\n\n### Focus Areas\n\nPay special attention to:\n- API keys or passwords are committed to the repo or baked into code\n- Attacker input changes the meaning of a database query\n- Passwords are stored in plain text or with a fast hash, so a database leak exposes them\n- Debug features or consoles are left on in production\n- Default or hardcoded admin accounts are left active\n- .env, .git, or backup files are reachable from the web\n- A database, cache, or admin port is reachable from the internet\n- An AI-suggested package does not exist, and an attacker can register that name\n- Encryption or signing keys are hardcoded or shared across environments\n- A request sets fields the user should not control, such as role or price\n- Query operators in user input bypass filters in a NoSQL database\n- Cloud roles or service accounts allow far more than the app needs\n\n### Security Checklist\n\nVerify each item and report violations:\n- [ ] Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.\n- [ ] Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.\n- [ ] Hash passwords with a slow, salted algorithm: Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.\n- [ ] Turn debug features off in production: Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.\n- [ ] Remove default and hardcoded accounts: Ship no preset admin users. Create the first admin through a one-time setup step with a strong generated password.\n- [ ] Do not deploy repo metadata or env files: Exclude .git, .env, and backups from the build and the web root, and block them at the web server.\n- [ ] Keep data stores off the public internet: Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.\n- [ ] Check every new package exists and is the one you meant: Confirm the name, age, and publisher on the registry before installing, and watch for lookalike names.\n- [ ] Use separate keys per environment and rotate them: Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.\n- [ ] Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.\n- [ ] Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.\n- [ ] Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.\n- [ ] Grant only the cloud permissions the app uses: Write narrow roles per service, avoid wildcards on actions and resources, and review them when features change.\n- [ ] Encrypt sensitive data at rest: Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.\n- [ ] Scope every query to the tenant: Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.\n- [ ] Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.\n- [ ] Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies.\n\n### Expected Response Format\n\nProvide your security review with:\n1. **Summary:** Overall assessment (Secure/Needs Attention/Insecure)\n2. **Findings:** List of security issues with severity and fixes\n3. **Checklist Results:** Which items pass/fail\n4. **Recommendations:** Prioritized list of actions",
  "context": {
    "file_path": "api/Dockerfile, ui/Dockerfile, docker-compose.yml, docker-compose.test.yml, .env.example, scripts/, Makefile, .github/workflows/ci.yml, api/src/taskboard/dbadmin.py",
    "components": [
      "container-and-iac",
      "secrets-and-config",
      "database",
      "dependencies"
    ],
    "risk_level": "critical"
  },
  "security_checklist": [
    "Load secrets from a secrets manager or environment: Keep secrets out of code, images, and the repo. Use environment variables or a vault, scope access narrowly, and rotate anything that leaked.",
    "Use parameterized queries or an ORM: Pass user values as parameters. Never build SQL or query documents by joining strings.",
    "Hash passwords with a slow, salted algorithm: Use Argon2id, scrypt, or bcrypt through your framework's password helper. Never use MD5 or SHA for passwords.",
    "Turn debug features off in production: Set DEBUG false, remove debug consoles and verbose logging, and fail the deploy if debug is on.",
    "Remove default and hardcoded accounts: Ship no preset admin users. Create the first admin through a one-time setup step with a strong generated password.",
    "Do not deploy repo metadata or env files: Exclude .git, .env, and backups from the build and the web root, and block them at the web server.",
    "Keep data stores off the public internet: Place databases and caches in private subnets, bind them to internal interfaces, and allow only the app through security groups.",
    "Check every new package exists and is the one you meant: Confirm the name, age, and publisher on the registry before installing, and watch for lookalike names.",
    "Use separate keys per environment and rotate them: Generate different keys for development, staging, and production, load them from the secrets manager, and rotate them on a schedule or after exposure.",
    "Accept only the fields you expect: Bind requests to an explicit schema or DTO with allowed fields. Never copy a request body straight onto a model.",
    "Check permissions on the server for every action: Enforce role and permission checks in a central layer on each endpoint, not only by hiding UI.",
    "Validate all input on the server: Check type, length, range, and format for every input on the server. Client-side checks are only for convenience.",
    "Grant only the cloud permissions the app uses: Write narrow roles per service, avoid wildcards on actions and resources, and review them when features change.",
    "Encrypt sensitive data at rest: Use AES-GCM or your cloud provider's managed encryption, with keys held outside the database.",
    "Scope every query to the tenant: Apply the tenant filter in one place, such as a query helper or row-level security, so no query can forget it.",
    "Return generic errors to users: Show a short message and a request id, log the details server-side, and use the same wording for unknown and wrong credentials.",
    "Keep secrets and personal data out of logs: Mask tokens, passwords, card numbers, and personal fields before logging, and avoid logging whole request bodies."
  ],
  "focus_areas": [
    "API keys or passwords are committed to the repo or baked into code",
    "Attacker input changes the meaning of a database query",
    "Passwords are stored in plain text or with a fast hash, so a database leak exposes them",
    "Debug features or consoles are left on in production",
    "Default or hardcoded admin accounts are left active",
    ".env, .git, or backup files are reachable from the web",
    "A database, cache, or admin port is reachable from the internet",
    "An AI-suggested package does not exist, and an attacker can register that name",
    "Encryption or signing keys are hardcoded or shared across environments",
    "A request sets fields the user should not control, such as role or price",
    "Query operators in user input bypass filters in a NoSQL database",
    "Cloud roles or service accounts allow far more than the app needs"
  ],
  "expected_response": {
    "format": "structured_security_review",
    "required_sections": [
      "overall_assessment",
      "findings_list",
      "checklist_results",
      "recommended_fixes"
    ]
  }
}
```

### evaluation/raw/T-032.review.md

```markdown
# Review produced by following the T-032 review_prompt

Scope: the phase 7 integration files: `api/Dockerfile`, `ui/Dockerfile`, both `.dockerignore` files,
`docker-compose.yml`, `docker-compose.test.yml`, `.env.example`, `scripts/gen-env.sh`, `scripts/smoke.sh`, `Makefile`,
`.github/workflows/ci.yml`, and the new `api/src/taskboard/dbadmin.py` plus the `migrate` CLI command. Components:
container-and-iac, secrets-and-config, database, dependencies.

## 1. Summary

**Secure with minor items.** No critical, high or medium issues. One low issue to fix; three low items accepted.

## 2. Findings

| # | Severity (mine) | Issue | Where | Fix |
| --- | --- | --- | --- | --- |
| R32-1 | Low | `ci.yml` references GitHub-owned actions by mutable major tags (`actions/checkout@v6`, `actions/setup-python@v7`, `actions/setup-node@v7`). A moved tag would run new code with the job's token. | `.github/workflows/ci.yml` | Pin every action in `ci.yml` by full commit SHA with the version in a comment, as already done for the third-party actions. (The brief-mandated `codeql.yml` keeps its tags.) → F-095 |
| R32-2 | Low | Base images are pinned by version tag, not by digest. | Dockerfiles, Compose files, CI services | Accept: the brief asks for pinned tags; exact patch tags are used throughout. → F-096 (accepted risk) |
| R32-3 | Low | `docker-compose.test.yml` and CI use fixed throwaway credentials (`taskboard_test`). | test-only files | Accept: test databases only, bound to 127.0.0.1 or CI service containers, data on tmpfs, never used by the application stack. → F-097 (accepted risk) |
| R32-4 | Low | In the dev Compose file the Redis password is a `redis-server --requirepass` argument, visible via `docker inspect` and `ps` inside the container. | `docker-compose.yml` | Accept for local development: only someone with Docker access, who is already root-equivalent, can see it. In AWS, ElastiCache uses an auth token over TLS. → F-098 (accepted risk) |

## 3. Checklist results

| Checklist item | Result | Evidence |
| --- | --- | --- |
| Load secrets from a secrets manager or environment | Pass | `.env` is generated with fresh random values (`umask 077`), git-ignored; `.env.example` holds only `__GENERATE__` placeholders; no secret appears in a Dockerfile, build arg or image layer. |
| Use parameterized queries | Pass | `dbadmin.ensure_app_role` builds DDL with `psycopg.sql.Identifier` / `sql.Literal`; the role name is validated by regex; integration test rejects `bad name; drop`. |
| Hash passwords slowly | N/A here | API concern (Argon2id). |
| Turn debug features off in production | Pass | Images default to production (`NODE_ENV=production`, API `ENVIRONMENT` defaults to production). Only the local Compose file sets development values, needed for HTTP on localhost. |
| Remove default and hardcoded accounts | Pass | No admin is seeded; `make admin` reads ADMIN_EMAIL/ADMIN_PASSWORD from the operator's `.env` (empty by default). |
| Do not deploy repo metadata or env files | Pass | `.dockerignore` files allow-list only what each image needs (`*` then `!src/` …), so `.git`, `.env`, tests and caches never enter the build context. → F-008 |
| Keep data stores off the public internet | Pass | Compose publishes only the UI, on 127.0.0.1. PostgreSQL and Redis sit on the `internal: true` `data` network; the API is on internal `app`/`data` plus an egress-only network for webhooks. |
| Check every new package exists | Pass | No new packages in this phase (dbadmin uses psycopg, already verified in T-007/T-008). Installs are frozen (`uv sync --frozen`, `npm ci`) with `--ignore-scripts` for npm. |
| Separate keys per environment and rotation | Pass | Every environment generates its own `.env`; AWS secrets are per-environment state (T-029). |
| Grant only the permissions the app uses | Pass | Database: the API runs as `taskboard_app` with SELECT/INSERT/UPDATE/DELETE only, no DDL, and no access to `alembic_version` (integration-tested); migrations use the owner account in a one-shot job. Containers: non-root (uid 10001 / `node`), `read_only`, `cap_drop: [ALL]`, `no-new-privileges`. CI: `permissions: contents: read`, `persist-credentials: false`. → F-062, F-094 |
| Encrypt sensitive data at rest | N/A locally | AWS covered in T-029. |
| Return generic errors / keep secrets out of logs | Pass | `migrate` prints only status; `gen-env.sh` never echoes values; `smoke.sh` prints step names only. |

## 4. Recommendations

1. R32-1: pin CI actions by SHA (F-095).
2. R32-2 to R32-4: accept and document (F-096, F-097, F-098).
```

### evaluation/raw/T-033.input.json

```json
{
  "tool": "mcp__sec-review__threatmodel_update_threat_model_file",
  "arguments": {
    "threat_model_json": "{\"title\": \"Taskboard (whole system)\", \"description\": \"Internal team task tracker: a FastAPI API (only component touching PostgreSQL, Redis and attachment storage) behind a Node.js Express UI server that renders pages and authenticates browser users. Features: email/password accounts with reset links, admin user management, teams, projects with outbound status-change webhooks, tasks with Markdown, comments, attachments up to 10 MB, search with client-chosen sort, CSV export, activity feeds.\", \"author\": \"Claude Code session (arm A), from sec-review perform_threat_model context; statuses updated at wrap-up\", \"data_touched\": [\"User credentials: email, Argon2id password hash (users table)\", \"Opaque session tokens: SHA-256 hash in sessions table, raw value only in the browser's HttpOnly cookie and in UI-to-API Authorization headers\", \"Password reset tokens: SHA-256 hash in password_reset_tokens, raw value in outbox rows and API log (dev mailer)\", \"Personal data: display names and emails of users, visible to teammates and admins\", \"Task content, Markdown descriptions and comments, labels, due dates\", \"Attachment bytes (local volume or S3) and original filenames\", \"Project webhook URLs and outbound webhook payloads\", \"Service secrets: UI-to-API service token, cookie/CSRF secret, DB password, Redis auth token\"], \"technologies\": [\"Python 3.13\", \"FastAPI\", \"SQLAlchemy 2\", \"PostgreSQL 16\", \"Redis 7\", \"Node.js 24\", \"Express 5\", \"EJS\", \"Docker\", \"Terraform\", \"AWS EC2/ALB/RDS/ElastiCache/S3\"], \"threats\": [{\"id\": \"TM-1\", \"what_can_go_wrong\": \"A member of team A changes the task, project, comment or attachment id in a URL and reads or edits team B's data, because a handler loads the object by id without checking team membership.\", \"impact\": \"Cross-team data disclosure and tampering.\", \"likelihood\": \"high\", \"data_affected\": [\"tasks\", \"comments\", \"attachments\", \"projects\", \"team membership\"], \"mitigation\": \"A single AccessPolicy service resolves every object to its team and checks membership (or admin) before any read or write; non-members get 404. Search and list queries join on team_members for the caller. Integration tests cover cross-team access for every resource type.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.2-4.4, data_flows\", \"description\": \"All task/comment/attachment endpoints take bare UUIDs; team membership is the only boundary\", \"snippet\": \"GET /api/v1/tasks/{task_id}\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/services/access.py\", \"description\": \"AccessPolicy resolves every object to its team; non-members get NotFoundError; tests/integration/test_work_api.py::test_cross_team_access_is_not_found probes 13 endpoints\"}]}, {\"id\": \"TM-2\", \"what_can_go_wrong\": \"A member calls PATCH /api/v1/admin/users/{id} or creates/archives a project directly against the API (or via a crafted form post to the UI) because only the UI hides the buttons.\", \"impact\": \"Privilege escalation to admin; unauthorised project changes.\", \"likelihood\": \"medium\", \"data_affected\": [\"user roles\", \"projects\"], \"mitigation\": \"Role and ownership checks live in services (AdminService requires admin; ProjectService requires team owner or admin). Request schemas use extra='forbid' so role cannot be set at registration or profile update.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.1, 4.3\", \"description\": \"Admin-only and owner-only operations exist alongside member operations\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/services/access.py\", \"description\": \"require_admin/team_for_manager in services; RequestModel extra='forbid' (api/schemas/common.py); role taken from DB each request (F-080)\"}]}, {\"id\": \"TM-3\", \"what_can_go_wrong\": \"An attacker sets a project's webhook URL to http://169.254.169.254/latest/meta-data/ or an internal service (api:8000, redis, RDS) and the API's background sender POSTs to it, or a public hostname that later resolves (DNS rebinding) or redirects to an internal address.\", \"impact\": \"SSRF into the VPC; on EC2 with IMDSv1 this could leak instance role credentials.\", \"likelihood\": \"medium\", \"data_affected\": [\"instance credentials\", \"internal services\"], \"mitigation\": \"Validate scheme (https only unless explicitly allowed in dev), resolve the host at send time, reject loopback/private/link-local/multicast/reserved/CGNAT/metadata addresses, connect to the validated IP with the original Host header and SNI, never follow redirects, short connect/read timeouts, cap response read. Enforce IMDSv2 with hop limit 1 on EC2.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"API sends webhook POSTs from a background thread to user-configured URLs\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/infra/webhooks/url_policy.py\", \"description\": \"https only, all resolved addresses must be global, connection pinned to the checked IP, no redirects, 64 KiB cap, attempt deadline (F-073); EC2 IMDSv2 hop limit 1 (infra/modules/*/main.tf)\"}]}, {\"id\": \"TM-4\", \"what_can_go_wrong\": \"A teammate writes a task description or comment containing <script>, an <img onerror>, or a [link](javascript:...) and every viewer of the task runs it in the UI origin, where it can submit forms as the victim.\", \"impact\": \"Account actions performed as other users, including admins.\", \"likelihood\": \"high\", \"data_affected\": [\"sessions (indirectly)\", \"all data the victim can reach\"], \"mitigation\": \"Render Markdown with marked, then sanitize-html with a strict tag/attribute allow-list and http/https/mailto-only links; EJS auto-escaping everywhere else (no <%- except sanitized HTML); strict CSP without inline script.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"UI renders Markdown to sanitized HTML\"}, {\"type\": \"code\", \"location\": \"ui/src/security/MarkdownRenderer.ts\", \"description\": \"marked + sanitize-html allow-list, http/https/mailto only, forced rel; CSP script-src 'none' (ui/src/app.ts); 9 XSS vectors unit-tested\"}]}, {\"id\": \"TM-5\", \"what_can_go_wrong\": \"A user uploads an .html or .svg attachment; another user opens it and it renders inline in the UI origin, running script.\", \"impact\": \"Stored XSS through attachments.\", \"likelihood\": \"medium\", \"data_affected\": [\"sessions (indirectly)\"], \"mitigation\": \"Downloads are always Content-Disposition: attachment with Content-Type application/octet-stream and X-Content-Type-Options: nosniff, plus a sandbox CSP on the download response. Any file type is allowed by the brief, so no type allow-list.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.4\", \"description\": \"Attachments are any type and downloadable with their original filename\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/api/routers/tasks.py\", \"description\": \"download_attachment: application/octet-stream, Content-Disposition attachment, nosniff, CSP sandbox; UI sendDownload repeats them\"}]}, {\"id\": \"TM-6\", \"what_can_go_wrong\": \"An uploaded filename like ../../etc/passwd or a name with CR/LF or quotes is used in a storage path or echoed into the Content-Disposition header.\", \"impact\": \"File overwrite on the API host; response header injection.\", \"likelihood\": \"medium\", \"data_affected\": [\"attachment storage\", \"API host files\"], \"mitigation\": \"Storage keys are server-generated UUIDs; the local storage resolves paths and checks they stay under the root. Original filename is stored only as metadata, reduced to its basename, stripped of control characters, and emitted with RFC 6266/5987 filename* encoding.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"stores attachment bytes on a local volume or S3 under random keys\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/services/attachments.py\", \"description\": \"clean_filename, server-generated keys checked by infra/storage/base.py check_key, RFC 6266 content_disposition\"}]}, {\"id\": \"TM-7\", \"what_can_go_wrong\": \"A client uploads many multi-gigabyte bodies or a slow stream to exhaust disk or memory on the UI or API.\", \"impact\": \"Denial of service.\", \"likelihood\": \"medium\", \"data_affected\": [], \"mitigation\": \"UI multer limit of 10 MB and one file; API rejects Content-Length over limit and counts bytes while streaming, aborting past 10 MB.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.4\", \"description\": \"up to 10 MB each\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/api/middleware.py\", \"description\": \"BodySizeLimitMiddleware (256 KB JSON, 10 MB upload, F-074) and byte counter in AttachmentService; multer limits in ui/src/controllers/TaskController.ts\"}]}, {\"id\": \"TM-8\", \"what_can_go_wrong\": \"Attackers run credential stuffing against /auth/login, or hammer /auth/password/forgot to spam the outbox.\", \"impact\": \"Account takeover; resource abuse.\", \"likelihood\": \"medium\", \"data_affected\": [\"credentials\"], \"mitigation\": \"Per-email and per-client-IP fixed-window rate limits on login and forgot-password (Redis-backed, in-memory fallback), Argon2id hashing, minimum 12-character passwords with a 128 limit, generic error text.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"UI forwards X-Client-IP so the API can rate-limit per client\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/services/auth.py\", \"description\": \"per (email, IP) lockout + per-account ceiling (F-070), per-IP limits, password-change throttle (F-075), Argon2id\"}]}, {\"id\": \"TM-9\", \"what_can_go_wrong\": \"Reset tokens are guessable, reusable, long-lived, or the reset link points at an attacker host because it was built from the Host header; or forgot-password reveals which emails exist.\", \"impact\": \"Account takeover; user enumeration.\", \"likelihood\": \"medium\", \"data_affected\": [\"credentials\", \"emails\"], \"mitigation\": \"secrets.token_urlsafe(32) tokens stored as SHA-256, 30-minute expiry, single use, all sessions revoked on reset, link built from configured PUBLIC_BASE_URL, forgot always returns 202 with the same body.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.1\", \"description\": \"Forgot password: request a reset link by email, then set a new password using the link\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/services/auth.py\", \"description\": \"forgot_password/reset_password: 256-bit token, SHA-256 at rest, 30 min, atomic consume, PUBLIC_BASE_URL links, same 202 response\"}]}, {\"id\": \"TM-10\", \"what_can_go_wrong\": \"Any process on the internal network (or a compromised container) calls the API directly with forged identity headers, or a stolen session token keeps working after logout, password change or deactivation.\", \"impact\": \"Impersonation of any user.\", \"likelihood\": \"low\", \"data_affected\": [\"all\"], \"mitigation\": \"Identity is never taken from a header: the API resolves the Bearer session token against the sessions table on every request and checks the user is active. The UI must also present X-Service-Token, compared in constant time. Logout deletes the session; password change/reset and deactivation delete all of the user's sessions.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"Authorization: Bearer <session token>, X-Service-Token\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/api/deps.py\", \"description\": \"require_service_auth (constant-time), identity only from the DB session lookup; sessions deleted on logout/password change/reset/deactivation\"}]}, {\"id\": \"TM-11\", \"what_can_go_wrong\": \"Another website auto-submits a form to the UI (e.g. remove member, change password) using the victim's cookie.\", \"impact\": \"Unwanted state changes.\", \"likelihood\": \"medium\", \"data_affected\": [\"teams\", \"tasks\", \"credentials\"], \"mitigation\": \"SameSite=Lax HttpOnly cookies (Secure and __Host- prefix in production) plus a per-session HMAC CSRF token on every POST form, verified by middleware.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"session token in an HttpOnly SameSite cookie\"}, {\"type\": \"code\", \"location\": \"ui/src/security/CsrfProtection.ts\", \"description\": \"HMAC-bound token on every POST with a per-purpose key (F-087), Sec-Fetch-Site check, SameSite=Lax and __Host- cookies\"}]}, {\"id\": \"TM-12\", \"what_can_go_wrong\": \"The client-supplied sort field is interpolated into SQL (ORDER BY {field}), or free-text search builds LIKE patterns by string concatenation.\", \"impact\": \"SQL injection, full database read.\", \"likelihood\": \"medium\", \"data_affected\": [\"all database contents\"], \"mitigation\": \"Sort field is validated against an enum mapped to ORM column objects; direction is an enum; search uses bound parameters with LIKE wildcards escaped.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.5\", \"description\": \"sort by any task field in either direction, with field and direction supplied by the client\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/repositories/sqlalchemy/tasks.py\", \"description\": \"_SORT_COLUMNS enum map, escape_like with bound parameters; injection attempt returns 422 in tests\"}]}, {\"id\": \"TM-13\", \"what_can_go_wrong\": \"A task title starting with =HYPERLINK(...) or =cmd|... is exported to CSV and executes when a teammate opens it in a spreadsheet.\", \"impact\": \"Code execution or data exfiltration on the victim's workstation.\", \"likelihood\": \"low\", \"data_affected\": [\"exported task data\"], \"mitigation\": \"Prefix cells beginning with = + - @ tab or CR with a single quote.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.5\", \"description\": \"Export a project's tasks as CSV\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/services/export.py\", \"description\": \"neutralise_cell prefixes = + - @ tab CR with a quote\"}]}, {\"id\": \"TM-14\", \"what_can_go_wrong\": \"A cached team or project list or task detail is served to a user who was removed from the team, or cached data keyed only by object id bypasses the membership check.\", \"impact\": \"Stale-permission data disclosure.\", \"likelihood\": \"medium\", \"data_affected\": [\"tasks\", \"projects\"], \"mitigation\": \"Authorization runs against the database before any cache read; per-user list caches are invalidated on member add/remove; cache values are JSON, never pickle.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"uses Redis for cache-aside reads\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/services/caching.py\", \"description\": \"membership checked in PostgreSQL before/after cache reads; role and active flag always from the DB (F-080); JSON values only\"}]}, {\"id\": \"TM-15\", \"what_can_go_wrong\": \"Reset links and session tokens are written to logs, which are shipped to a log store readable by more people than the database.\", \"impact\": \"Token leakage via logs.\", \"likelihood\": \"medium\", \"data_affected\": [\"reset tokens\"], \"mitigation\": \"Session tokens and passwords are never logged. The brief requires emails to be written to the API log, so the dev mailer logs the reset email; this is accepted for this build and documented, with a real mailer replacing it in production.\", \"status\": \"accepted\", \"accepted_risk\": \"Required by the brief: there is no real email provider and emails must be readable from the API log in dev and tests.\", \"references\": [{\"type\": \"artifact\", \"location\": \"brief section 4.1\", \"description\": \"write outgoing emails to the API log and to an outbox table\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/infra/mailer.py\", \"description\": \"LogOutboxMailer logs reset emails as the brief requires\"}]}, {\"id\": \"TM-16\", \"what_can_go_wrong\": \"The first-admin management command ships a default password, or secrets are baked into images or committed in .env files.\", \"impact\": \"Trivial admin takeover.\", \"likelihood\": \"low\", \"data_affected\": [\"admin account\", \"service secrets\"], \"mitigation\": \"Command reads email and password from env vars, refuses empty or short passwords, no defaults. Secrets only in env/SSM; .env git-ignored and .dockerignore'd; no build args for secrets.\", \"status\": \"mitigated\", \"references\": [{\"type\": \"artifact\", \"location\": \"architecture_notes\", \"description\": \"Secrets ... come from environment variables populated from AWS SSM Parameter Store at boot\"}, {\"type\": \"code\", \"location\": \"api/src/taskboard/cli.py\", \"description\": \"create-admin reads env only, 12+ characters; no default accounts; secrets generated into .env / SSM\"}]}, {\"id\": \"TM-17\", \"what_can_go_wrong\": \"Traffic between ALB and UI, UI and API, or API and RDS/ElastiCache is sniffed inside the VPC.\", \"impact\": \"Session token and credential disclosure to a network-positioned attacker.\", \"likelihood\": \"low\", \"data_affected\": [\"session tokens\", \"DB credentials\"], \"mitigation\": \"TLS 1.2+ policy on the ALB with HTTP->HTTPS redirect; RDS with forced SSL (rds.force_ssl) and sslmode=verify-full against the RDS CA bundle; ElastiCache transit encryption required with an AUTH token. UI-to-API stays HTTP inside private subnets restricted by security groups; accepted for this build and documented.\", \"status\": \"accepted\", \"accepted_risk\": \"UI-to-API hop is plain HTTP inside private subnets locked to the UI security group; adding internal TLS needs a private CA, out of scope for this build.\", \"references\": [{\"type\": \"artifact\", \"location\": \"data_flows\", \"description\": \"ALB --HTTP--> UI server ... calls the API over the private network\"}, {\"type\": \"code\", \"location\": \"infra/modules/alb/main.tf\", \"description\": \"ALB TLS 1.2+ with redirect; RDS verify-full; ElastiCache TLS required; UI->API HTTP inside private subnets\"}]}, {\"id\": \"TM-18\", \"what_can_go_wrong\": \"A webhook receiver for project A, holding the signing secret, forges status-change events to project B's receiver; or, without any shared secret, receivers cannot verify events at all.\", \"impact\": \"Spoofed task events trigger downstream automation.\", \"likelihood\": \"low\", \"data_affected\": [\"webhook payloads\"], \"mitigation\": \"Each project gets its own key HMAC(WEBHOOK_SIGNING_SECRET, 'project:'+id), shown only to the team owner and admins; X-Taskboard-Signature signs every body (F-077).\", \"status\": \"mitigated\", \"references\": [{\"type\": \"code\", \"location\": \"api/src/taskboard/infra/webhooks/notifier.py\", \"description\": \"project_signing_key and sign(); integration test verifies the signature with the key from the project response\"}]}, {\"id\": \"TM-19\", \"what_can_go_wrong\": \"A compromised UI instance reads the API's SSM SecureStrings (database URL, Redis token) or the migration password, because a broad managed policy grants ssm:GetParameter on every parameter.\", \"impact\": \"Database and cache access from the internet-facing tier.\", \"likelihood\": \"low\", \"data_affected\": [\"database credentials\", \"cache credentials\"], \"mitigation\": \"No AmazonSSMManagedInstanceCore; a minimal Session Manager policy; kms:Decrypt bound to each service's own parameter ARNs via the KMS encryption context (F-090).\", \"status\": \"mitigated\", \"references\": [{\"type\": \"code\", \"location\": \"infra/modules/iam/main.tf\", \"description\": \"session_manager policy and DecryptOwnConfig condition on kms:EncryptionContext:PARAMETER_ARN\"}]}], \"summary\": \"19 threats. 17 mitigated in code and infrastructure, 2 accepted (TM-15 reset links in the dev mail log, required by the brief; TM-17 plain HTTP between UI and API inside private subnets). TM-18 and TM-19 were added during the build from post-coding reviews. Archive extraction threats from the library do not apply: the app never extracts uploads.\"}",
    "file_path": "/run/media/morpheuslord/Personal_Files/Projects/mcp_test_server/agent-crew-test-withmcp/docs/threat-model.md",
    "append": false
  },
  "note": "threat_model_json was sent as a single-line JSON string with the same content as evaluation/raw/T-033.produced.json"
}
```

### evaluation/raw/T-033.output.json

```json
{
  "success": true,
  "file_path": "/run/media/morpheuslord/Personal_Files/Projects/mcp_test_server/agent-crew-test-withmcp/docs/threat-model.md",
  "action": "created",
  "stats": {
    "threats_documented": 19,
    "references_linked": 36,
    "mitigated": 17,
    "open": 0
  },
  "message": "Threat model 'Taskboard (whole system)' written to /run/media/morpheuslord/Personal_Files/Projects/mcp_test_server/agent-crew-test-withmcp/docs/threat-model.md. 19 threats documented with 36 references."
}
```

### evaluation/raw/T-033.produced.json

```json
{
  "title": "Taskboard (whole system)",
  "description": "Internal team task tracker: a FastAPI API (only component touching PostgreSQL, Redis and attachment storage) behind a Node.js Express UI server that renders pages and authenticates browser users. Features: email/password accounts with reset links, admin user management, teams, projects with outbound status-change webhooks, tasks with Markdown, comments, attachments up to 10 MB, search with client-chosen sort, CSV export, activity feeds.",
  "author": "Claude Code session (arm A), from sec-review perform_threat_model context; statuses updated at wrap-up",
  "data_touched": [
    "User credentials: email, Argon2id password hash (users table)",
    "Opaque session tokens: SHA-256 hash in sessions table, raw value only in the browser's HttpOnly cookie and in UI-to-API Authorization headers",
    "Password reset tokens: SHA-256 hash in password_reset_tokens, raw value in outbox rows and API log (dev mailer)",
    "Personal data: display names and emails of users, visible to teammates and admins",
    "Task content, Markdown descriptions and comments, labels, due dates",
    "Attachment bytes (local volume or S3) and original filenames",
    "Project webhook URLs and outbound webhook payloads",
    "Service secrets: UI-to-API service token, cookie/CSRF secret, DB password, Redis auth token"
  ],
  "technologies": [
    "Python 3.13",
    "FastAPI",
    "SQLAlchemy 2",
    "PostgreSQL 16",
    "Redis 7",
    "Node.js 24",
    "Express 5",
    "EJS",
    "Docker",
    "Terraform",
    "AWS EC2/ALB/RDS/ElastiCache/S3"
  ],
  "threats": [
    {
      "id": "TM-1",
      "what_can_go_wrong": "A member of team A changes the task, project, comment or attachment id in a URL and reads or edits team B's data, because a handler loads the object by id without checking team membership.",
      "impact": "Cross-team data disclosure and tampering.",
      "likelihood": "high",
      "data_affected": [
        "tasks",
        "comments",
        "attachments",
        "projects",
        "team membership"
      ],
      "mitigation": "A single AccessPolicy service resolves every object to its team and checks membership (or admin) before any read or write; non-members get 404. Search and list queries join on team_members for the caller. Integration tests cover cross-team access for every resource type.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "brief section 4.2-4.4, data_flows",
          "description": "All task/comment/attachment endpoints take bare UUIDs; team membership is the only boundary",
          "snippet": "GET /api/v1/tasks/{task_id}"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/services/access.py",
          "description": "AccessPolicy resolves every object to its team; non-members get NotFoundError; tests/integration/test_work_api.py::test_cross_team_access_is_not_found probes 13 endpoints"
        }
      ]
    },
    {
      "id": "TM-2",
      "what_can_go_wrong": "A member calls PATCH /api/v1/admin/users/{id} or creates/archives a project directly against the API (or via a crafted form post to the UI) because only the UI hides the buttons.",
      "impact": "Privilege escalation to admin; unauthorised project changes.",
      "likelihood": "medium",
      "data_affected": [
        "user roles",
        "projects"
      ],
      "mitigation": "Role and ownership checks live in services (AdminService requires admin; ProjectService requires team owner or admin). Request schemas use extra='forbid' so role cannot be set at registration or profile update.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "brief section 4.1, 4.3",
          "description": "Admin-only and owner-only operations exist alongside member operations"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/services/access.py",
          "description": "require_admin/team_for_manager in services; RequestModel extra='forbid' (api/schemas/common.py); role taken from DB each request (F-080)"
        }
      ]
    },
    {
      "id": "TM-3",
      "what_can_go_wrong": "An attacker sets a project's webhook URL to http://169.254.169.254/latest/meta-data/ or an internal service (api:8000, redis, RDS) and the API's background sender POSTs to it, or a public hostname that later resolves (DNS rebinding) or redirects to an internal address.",
      "impact": "SSRF into the VPC; on EC2 with IMDSv1 this could leak instance role credentials.",
      "likelihood": "medium",
      "data_affected": [
        "instance credentials",
        "internal services"
      ],
      "mitigation": "Validate scheme (https only unless explicitly allowed in dev), resolve the host at send time, reject loopback/private/link-local/multicast/reserved/CGNAT/metadata addresses, connect to the validated IP with the original Host header and SNI, never follow redirects, short connect/read timeouts, cap response read. Enforce IMDSv2 with hop limit 1 on EC2.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "data_flows",
          "description": "API sends webhook POSTs from a background thread to user-configured URLs"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/infra/webhooks/url_policy.py",
          "description": "https only, all resolved addresses must be global, connection pinned to the checked IP, no redirects, 64 KiB cap, attempt deadline (F-073); EC2 IMDSv2 hop limit 1 (infra/modules/*/main.tf)"
        }
      ]
    },
    {
      "id": "TM-4",
      "what_can_go_wrong": "A teammate writes a task description or comment containing <script>, an <img onerror>, or a [link](javascript:...) and every viewer of the task runs it in the UI origin, where it can submit forms as the victim.",
      "impact": "Account actions performed as other users, including admins.",
      "likelihood": "high",
      "data_affected": [
        "sessions (indirectly)",
        "all data the victim can reach"
      ],
      "mitigation": "Render Markdown with marked, then sanitize-html with a strict tag/attribute allow-list and http/https/mailto-only links; EJS auto-escaping everywhere else (no <%- except sanitized HTML); strict CSP without inline script.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "data_flows",
          "description": "UI renders Markdown to sanitized HTML"
        },
        {
          "type": "code",
          "location": "ui/src/security/MarkdownRenderer.ts",
          "description": "marked + sanitize-html allow-list, http/https/mailto only, forced rel; CSP script-src 'none' (ui/src/app.ts); 9 XSS vectors unit-tested"
        }
      ]
    },
    {
      "id": "TM-5",
      "what_can_go_wrong": "A user uploads an .html or .svg attachment; another user opens it and it renders inline in the UI origin, running script.",
      "impact": "Stored XSS through attachments.",
      "likelihood": "medium",
      "data_affected": [
        "sessions (indirectly)"
      ],
      "mitigation": "Downloads are always Content-Disposition: attachment with Content-Type application/octet-stream and X-Content-Type-Options: nosniff, plus a sandbox CSP on the download response. Any file type is allowed by the brief, so no type allow-list.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "brief section 4.4",
          "description": "Attachments are any type and downloadable with their original filename"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/api/routers/tasks.py",
          "description": "download_attachment: application/octet-stream, Content-Disposition attachment, nosniff, CSP sandbox; UI sendDownload repeats them"
        }
      ]
    },
    {
      "id": "TM-6",
      "what_can_go_wrong": "An uploaded filename like ../../etc/passwd or a name with CR/LF or quotes is used in a storage path or echoed into the Content-Disposition header.",
      "impact": "File overwrite on the API host; response header injection.",
      "likelihood": "medium",
      "data_affected": [
        "attachment storage",
        "API host files"
      ],
      "mitigation": "Storage keys are server-generated UUIDs; the local storage resolves paths and checks they stay under the root. Original filename is stored only as metadata, reduced to its basename, stripped of control characters, and emitted with RFC 6266/5987 filename* encoding.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "data_flows",
          "description": "stores attachment bytes on a local volume or S3 under random keys"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/services/attachments.py",
          "description": "clean_filename, server-generated keys checked by infra/storage/base.py check_key, RFC 6266 content_disposition"
        }
      ]
    },
    {
      "id": "TM-7",
      "what_can_go_wrong": "A client uploads many multi-gigabyte bodies or a slow stream to exhaust disk or memory on the UI or API.",
      "impact": "Denial of service.",
      "likelihood": "medium",
      "data_affected": [],
      "mitigation": "UI multer limit of 10 MB and one file; API rejects Content-Length over limit and counts bytes while streaming, aborting past 10 MB.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "brief section 4.4",
          "description": "up to 10 MB each"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/api/middleware.py",
          "description": "BodySizeLimitMiddleware (256 KB JSON, 10 MB upload, F-074) and byte counter in AttachmentService; multer limits in ui/src/controllers/TaskController.ts"
        }
      ]
    },
    {
      "id": "TM-8",
      "what_can_go_wrong": "Attackers run credential stuffing against /auth/login, or hammer /auth/password/forgot to spam the outbox.",
      "impact": "Account takeover; resource abuse.",
      "likelihood": "medium",
      "data_affected": [
        "credentials"
      ],
      "mitigation": "Per-email and per-client-IP fixed-window rate limits on login and forgot-password (Redis-backed, in-memory fallback), Argon2id hashing, minimum 12-character passwords with a 128 limit, generic error text.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "data_flows",
          "description": "UI forwards X-Client-IP so the API can rate-limit per client"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/services/auth.py",
          "description": "per (email, IP) lockout + per-account ceiling (F-070), per-IP limits, password-change throttle (F-075), Argon2id"
        }
      ]
    },
    {
      "id": "TM-9",
      "what_can_go_wrong": "Reset tokens are guessable, reusable, long-lived, or the reset link points at an attacker host because it was built from the Host header; or forgot-password reveals which emails exist.",
      "impact": "Account takeover; user enumeration.",
      "likelihood": "medium",
      "data_affected": [
        "credentials",
        "emails"
      ],
      "mitigation": "secrets.token_urlsafe(32) tokens stored as SHA-256, 30-minute expiry, single use, all sessions revoked on reset, link built from configured PUBLIC_BASE_URL, forgot always returns 202 with the same body.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "brief section 4.1",
          "description": "Forgot password: request a reset link by email, then set a new password using the link"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/services/auth.py",
          "description": "forgot_password/reset_password: 256-bit token, SHA-256 at rest, 30 min, atomic consume, PUBLIC_BASE_URL links, same 202 response"
        }
      ]
    },
    {
      "id": "TM-10",
      "what_can_go_wrong": "Any process on the internal network (or a compromised container) calls the API directly with forged identity headers, or a stolen session token keeps working after logout, password change or deactivation.",
      "impact": "Impersonation of any user.",
      "likelihood": "low",
      "data_affected": [
        "all"
      ],
      "mitigation": "Identity is never taken from a header: the API resolves the Bearer session token against the sessions table on every request and checks the user is active. The UI must also present X-Service-Token, compared in constant time. Logout deletes the session; password change/reset and deactivation delete all of the user's sessions.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "data_flows",
          "description": "Authorization: Bearer <session token>, X-Service-Token"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/api/deps.py",
          "description": "require_service_auth (constant-time), identity only from the DB session lookup; sessions deleted on logout/password change/reset/deactivation"
        }
      ]
    },
    {
      "id": "TM-11",
      "what_can_go_wrong": "Another website auto-submits a form to the UI (e.g. remove member, change password) using the victim's cookie.",
      "impact": "Unwanted state changes.",
      "likelihood": "medium",
      "data_affected": [
        "teams",
        "tasks",
        "credentials"
      ],
      "mitigation": "SameSite=Lax HttpOnly cookies (Secure and __Host- prefix in production) plus a per-session HMAC CSRF token on every POST form, verified by middleware.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "data_flows",
          "description": "session token in an HttpOnly SameSite cookie"
        },
        {
          "type": "code",
          "location": "ui/src/security/CsrfProtection.ts",
          "description": "HMAC-bound token on every POST with a per-purpose key (F-087), Sec-Fetch-Site check, SameSite=Lax and __Host- cookies"
        }
      ]
    },
    {
      "id": "TM-12",
      "what_can_go_wrong": "The client-supplied sort field is interpolated into SQL (ORDER BY {field}), or free-text search builds LIKE patterns by string concatenation.",
      "impact": "SQL injection, full database read.",
      "likelihood": "medium",
      "data_affected": [
        "all database contents"
      ],
      "mitigation": "Sort field is validated against an enum mapped to ORM column objects; direction is an enum; search uses bound parameters with LIKE wildcards escaped.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "brief section 4.5",
          "description": "sort by any task field in either direction, with field and direction supplied by the client"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/repositories/sqlalchemy/tasks.py",
          "description": "_SORT_COLUMNS enum map, escape_like with bound parameters; injection attempt returns 422 in tests"
        }
      ]
    },
    {
      "id": "TM-13",
      "what_can_go_wrong": "A task title starting with =HYPERLINK(...) or =cmd|... is exported to CSV and executes when a teammate opens it in a spreadsheet.",
      "impact": "Code execution or data exfiltration on the victim's workstation.",
      "likelihood": "low",
      "data_affected": [
        "exported task data"
      ],
      "mitigation": "Prefix cells beginning with = + - @ tab or CR with a single quote.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "brief section 4.5",
          "description": "Export a project's tasks as CSV"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/services/export.py",
          "description": "neutralise_cell prefixes = + - @ tab CR with a quote"
        }
      ]
    },
    {
      "id": "TM-14",
      "what_can_go_wrong": "A cached team or project list or task detail is served to a user who was removed from the team, or cached data keyed only by object id bypasses the membership check.",
      "impact": "Stale-permission data disclosure.",
      "likelihood": "medium",
      "data_affected": [
        "tasks",
        "projects"
      ],
      "mitigation": "Authorization runs against the database before any cache read; per-user list caches are invalidated on member add/remove; cache values are JSON, never pickle.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "data_flows",
          "description": "uses Redis for cache-aside reads"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/services/caching.py",
          "description": "membership checked in PostgreSQL before/after cache reads; role and active flag always from the DB (F-080); JSON values only"
        }
      ]
    },
    {
      "id": "TM-15",
      "what_can_go_wrong": "Reset links and session tokens are written to logs, which are shipped to a log store readable by more people than the database.",
      "impact": "Token leakage via logs.",
      "likelihood": "medium",
      "data_affected": [
        "reset tokens"
      ],
      "mitigation": "Session tokens and passwords are never logged. The brief requires emails to be written to the API log, so the dev mailer logs the reset email; this is accepted for this build and documented, with a real mailer replacing it in production.",
      "status": "accepted",
      "accepted_risk": "Required by the brief: there is no real email provider and emails must be readable from the API log in dev and tests.",
      "references": [
        {
          "type": "artifact",
          "location": "brief section 4.1",
          "description": "write outgoing emails to the API log and to an outbox table"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/infra/mailer.py",
          "description": "LogOutboxMailer logs reset emails as the brief requires"
        }
      ]
    },
    {
      "id": "TM-16",
      "what_can_go_wrong": "The first-admin management command ships a default password, or secrets are baked into images or committed in .env files.",
      "impact": "Trivial admin takeover.",
      "likelihood": "low",
      "data_affected": [
        "admin account",
        "service secrets"
      ],
      "mitigation": "Command reads email and password from env vars, refuses empty or short passwords, no defaults. Secrets only in env/SSM; .env git-ignored and .dockerignore'd; no build args for secrets.",
      "status": "mitigated",
      "references": [
        {
          "type": "artifact",
          "location": "architecture_notes",
          "description": "Secrets ... come from environment variables populated from AWS SSM Parameter Store at boot"
        },
        {
          "type": "code",
          "location": "api/src/taskboard/cli.py",
          "description": "create-admin reads env only, 12+ characters; no default accounts; secrets generated into .env / SSM"
        }
      ]
    },
    {
      "id": "TM-17",
      "what_can_go_wrong": "Traffic between ALB and UI, UI and API, or API and RDS/ElastiCache is sniffed inside the VPC.",
      "impact": "Session token and credential disclosure to a network-positioned attacker.",
      "likelihood": "low",
      "data_affected": [
        "session tokens",
        "DB credentials"
      ],
      "mitigation": "TLS 1.2+ policy on the ALB with HTTP->HTTPS redirect; RDS with forced SSL (rds.force_ssl) and sslmode=verify-full against the RDS CA bundle; ElastiCache transit encryption required with an AUTH token. UI-to-API stays HTTP inside private subnets restricted by security groups; accepted for this build and documented.",
      "status": "accepted",
      "accepted_risk": "UI-to-API hop is plain HTTP inside private subnets locked to the UI security group; adding internal TLS needs a private CA, out of scope for this build.",
      "references": [
        {
          "type": "artifact",
          "location": "data_flows",
          "description": "ALB --HTTP--> UI server ... calls the API over the private network"
        },
        {
          "type": "code",
          "location": "infra/modules/alb/main.tf",
          "description": "ALB TLS 1.2+ with redirect; RDS verify-full; ElastiCache TLS required; UI->API HTTP inside private subnets"
        }
      ]
    },
    {
      "id": "TM-18",
      "what_can_go_wrong": "A webhook receiver for project A, holding the signing secret, forges status-change events to project B's receiver; or, without any shared secret, receivers cannot verify events at all.",
      "impact": "Spoofed task events trigger downstream automation.",
      "likelihood": "low",
      "data_affected": [
        "webhook payloads"
      ],
      "mitigation": "Each project gets its own key HMAC(WEBHOOK_SIGNING_SECRET, 'project:'+id), shown only to the team owner and admins; X-Taskboard-Signature signs every body (F-077).",
      "status": "mitigated",
      "references": [
        {
          "type": "code",
          "location": "api/src/taskboard/infra/webhooks/notifier.py",
          "description": "project_signing_key and sign(); integration test verifies the signature with the key from the project response"
        }
      ]
    },
    {
      "id": "TM-19",
      "what_can_go_wrong": "A compromised UI instance reads the API's SSM SecureStrings (database URL, Redis token) or the migration password, because a broad managed policy grants ssm:GetParameter on every parameter.",
      "impact": "Database and cache access from the internet-facing tier.",
      "likelihood": "low",
      "data_affected": [
        "database credentials",
        "cache credentials"
      ],
      "mitigation": "No AmazonSSMManagedInstanceCore; a minimal Session Manager policy; kms:Decrypt bound to each service's own parameter ARNs via the KMS encryption context (F-090).",
      "status": "mitigated",
      "references": [
        {
          "type": "code",
          "location": "infra/modules/iam/main.tf",
          "description": "session_manager policy and DecryptOwnConfig condition on kms:EncryptionContext:PARAMETER_ARN"
        }
      ]
    }
  ],
  "summary": "19 threats. 17 mitigated in code and infrastructure, 2 accepted (TM-15 reset links in the dev mail log, required by the brief; TM-17 plain HTTP between UI and API inside private subnets). TM-18 and TM-19 were added during the build from post-coding reviews. Archive extraction threats from the library do not apply: the app never extracts uploads."
}
```

