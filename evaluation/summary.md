# Evaluation summary (arm A, with ai-security-crew MCP)

Written last, at wrap-up. The tables come from `tool-log.md` and `findings.md`; the commit counts come from `git log`.

## Time

| | UTC |
| --- | --- |
| Start | 2026-10-18T06:11:07Z |
| End | 2026-10-18T08:18:52Z |
| Elapsed | 2 h 07 min 45 s |

## Log entries (tool-log.md)

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

## Findings (findings.md)

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

## Commits

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

## False positives

| ID | Source | Why it is a false positive |
| --- | --- | --- |
| F-055 | MCP-direct:lightweight_security_review | Raised `card-data-in-your-systems`, although no payment component and no payment data were given. Taskboard handles no card data. |
| F-056 | MCP-direct:lightweight_security_review | Raised `nosql-injection`. The only store queried with user input is PostgreSQL through SQLAlchemy. Redis keys are built from UUIDs and hashes, never from raw input. |

The 4 out-of-scope items are also off-target generic content:

- F-011 JWT tampering: the design uses opaque session tokens.
- F-018 agent reads secrets.
- F-046 archive path traversal: there is no archive extraction.
- F-066 long-lived storage credentials shipped to clients.

## Suppressions

There are no inline suppression comments in the source (`noqa`, `type: ignore`, `eslint-disable`, `pragma`,
`nosec`, `shellcheck disable`). `suppressions.md` has 5 configuration-level rows:

- ruff S101, and S105/S106, for tests (2 rows)
- the typescript-eslint `disableTypeChecked` override for the ESLint config file
- the `.codacy.yml` exclusions for generated files and lockfiles
- the Codacy tool allow-list, added at the user's request

## Final check status

- **Passed:**
  - `make up` and `make smoke`
  - `make lint` and `make typecheck`
  - `make test`: API 118 tests at 96.78 % coverage, UI 62 tests at 96.6 % lines
  - `make tf-check`
  - CI `ci.yml` run for 303d2ed: success (status only)
- **Skipped:** none. Docker ran through rootless Podman.
- **Not run, by rule:** `terraform plan`/`apply`, local CodeQL and Codacy CLI, and reading scanner results.

## Observations on the MCP tooling

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
