# Suppressions

Inline suppression comments and rule-silencing configuration added during the build.

| File | Line | Rule | Reason |
| --- | --- | --- | --- |
| `api/pyproject.toml` | `[tool.ruff.lint.per-file-ignores]` | ruff `S101` (assert used) for `tests/**` | pytest's assertion idiom is `assert`; the flake8-bandit rule set is enabled for application code, where `assert` would be a real problem. Scoped to tests only. |
| `api/pyproject.toml` | `[tool.ruff.lint.per-file-ignores]` | ruff `S105`, `S106` (hard-coded password) for `tests/**` | Tests use fixed dummy passwords such as `correct-horse-battery` to drive the auth flows. Scoped to tests only. |
| `ui/eslint.config.mjs` | `files: ['eslint.config.mjs']` block | typescript-eslint type-checked rules, via `tseslint.configs.disableTypeChecked`, for the ESLint config file only | The config file is plain JavaScript outside the TypeScript project; typescript-eslint documents this override as the way to lint such files. All `.ts` sources keep the full `strictTypeChecked` set. |
