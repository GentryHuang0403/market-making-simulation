# AGENTS.md

## Role

You are working as an autonomous coding agent inside this repository.

Your goal is to make small, correct, reviewable changes. Prefer clarity over cleverness.

## Repository rules

* Before making changes, run `git status`.
* Work only inside this repository.
* Modify only files directly related to the current task.
* Do not modify files outside the current workspace.
* Do not read, print, modify, commit, or push secrets, including `.env`, API keys, tokens, credentials, private keys, or local config files.
* Do not use `git push --force`.
* Do not amend, rebase, squash, or rewrite existing commits unless the user explicitly asks.
* Do not push directly to `main` or `master`.
* If the current branch is `main` or `master`, stop and ask the user to create a working branch.

## Python workflow

* Prefer simple, readable Python.
* Add type hints when they improve clarity.
* For numerical or quant-finance code, include small sanity-check examples.
* If tests exist, run the relevant tests before committing.
* If no tests exist, run at least a smoke test, for example the relevant Python file or a small script that exercises the changed function.
* Do not install new dependencies unless they are clearly necessary.
* If a new dependency is necessary, explain why before adding it.

## Git workflow

After completing a task:

1. Run `git status`.
2. Run the relevant tests or smoke tests.
3. If checks pass, run:

   * `git add .`
   * `git commit -m "<clear concise commit message>"`
   * `git push`
4. If checks fail, do not commit. Report the failure and the likely cause.
5. If `git push` fails, stop and report the exact error.

## Definition of done

A task is done only when:

* The requested change is implemented.
* The code has been run or tested.
* The final diff has been reviewed for obvious mistakes.
* The change is committed and pushed to the current non-main branch.
* Any unresolved issue is clearly reported.


## Python environment

Use the local virtual environment `.venv`.

For running Python files, use:

```powershell
.\.venv\Scripts\python.exe

For installing packages, use:

.\.venv\Scripts\python.exe -m pip install <package>

For running tests, use the Python interpreter inside .venv.

Do not use global Python. Do not use Python 3.15 or any beta/pre-release Python interpreter for this repository.

Do not commit .venv/.