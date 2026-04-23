# Happy Farm Workspace Notes

- Use `uv` for dependency and environment management.
- Treat `${workspaceFolder}/.venv` as the single project virtual environment. Do not create or document additional `venv/`, `env/`, or `.direnv` Python environments for this repo.
- Prefer `uv sync` to create or update the environment and `uv run ...` to execute project commands.
- Keep VS Code workspace settings aligned to `.venv/bin/python` so Jupyter and Data Wrangler resolve the same interpreter.
- Prefer repo docs under `docs/` and update them when workflow conventions change.
- Do not revert or overwrite user changes outside the task at hand.
