# Suppressions

Inline suppression comments and rule-silencing configuration added during the build.

| File | Line | Rule | Reason |
| --- | --- | --- | --- |
| `api/pyproject.toml` | `[tool.ruff.lint.per-file-ignores]` | ruff `S101` (assert used) for `tests/**` | pytest's assertion idiom is `assert`; the flake8-bandit rule set is enabled for application code, where `assert` would be a real problem. Scoped to tests only. |
| `api/pyproject.toml` | `[tool.ruff.lint.per-file-ignores]` | ruff `S105`, `S106` (hard-coded password) for `tests/**` | Tests use fixed dummy passwords such as `correct-horse-battery` to drive the auth flows. Scoped to tests only. |
| `ui/eslint.config.mjs` | `files: ['eslint.config.mjs']` block | typescript-eslint type-checked rules, via `tseslint.configs.disableTypeChecked`, for the ESLint config file only | The config file is plain JavaScript outside the TypeScript project; typescript-eslint documents this override as the way to lint such files. All `.ts` sources keep the full `strictTypeChecked` set. |
| `.codacy.yml` | `exclude_paths` | Codacy analysis of `**/node_modules/**`, `**/dist/**`, `**/coverage/**`, `**/.terraform/**`, `**/package-lock.json`, `**/uv.lock`, `**/.terraform.lock.hcl` | Added at the user's request to correct the Codacy configuration (tool-log T-018). These paths are generated, vendored or machine-written lockfiles. Dependency vulnerabilities in the lockfiles are still scanned by the Trivy workflow (`trivy-repository`). `evaluation/**` was already excluded by the brief. |
| `.github/workflows/codacy.yml` | step "Prepare SARIF for code scanning", `CODACY_TOOLS` | Codacy results from agentlinter, biome, eslint-9, jacksonlinter, jshint, markdownlint, oxlint, pmd, pmd-7 and remark-lint are not uploaded to code scanning | The user asked to reduce Codacy to usable tools (tool-log T-020). These tools showed execution errors on the code scanning tool status page, because they do not apply to the stack (PMD is for Java) or cannot run against this repo's setup. ESLint and type checks run in CI; CodeQL, Semgrep and Trivy also scan the JS/TS code. |
