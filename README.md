# wq-ci

Reusable GitHub Actions gate for wq projects: autofix, flaky reruns, diff coverage.
Source lives in `as_work-q/ci/github/`; this repo (`JMO-Labs/wq-ci`) is the published copy.

## Use

`.github/workflows/ci.yml` in the project:

```yaml
on: {pull_request: {branches: [dev]}, push: {branches: [dev]}}
permissions: {contents: read, pull-requests: write}
jobs:
  wq:
    uses: JMO-Labs/wq-ci/.github/workflows/wq-ci.yml@v1
    with: {test-cmd: "uv run pytest --cov --cov-report=xml --junitxml=junit.xml", fix-cmd: "uv run ruff format ."}
    secrets: inherit
```

The `permissions` line is needed when the repo's default token is read-only: a called workflow cannot raise them.

Secret: `WQ_AUTOFIX_TOKEN`, a fine-grained PAT with `contents: write` on the project. `GITHUB_TOKEN`
pushes trigger no workflow, so without it an autofix commit would sit at `pending`. Without the
secret, autofix prints the diff and fails instead of pushing.
The PAT needs Contents read/write only, never Workflows permission; autofix refuses any patch touching `.github/`.

| Input | Default | Meaning |
|---|---|---|
| `test-cmd` | required | Must write `coverage.xml` (Cobertura) and `junit.xml` in the repo root |
| `fix-cmd` | `""` | Idempotent fixer; runs only on same-repo `wq/*` PR branches. Empty disables |
| `rerun-cmd` | test-cmd | Run after a failure, up to `reruns` times |
| `reruns` | `2` | A pass on rerun posts a `wq-flaky: <sha>` comment and passes the job |
| `base` | PR base branch | diff-cover compares against `origin/<base>`; empty = the PR's own base |
| `wq-ci-ref` | `v1` | Ref of this repo whose `scripts/wqci.py` is used |

Coverage gaps post a `wq-coverage: <sha>` comment and never block the PR.

## Publish (owner)

From the as_work-q checkout:

```bash
git remote add wq-ci git@github.com:JMO-Labs/wq-ci.git   # once
git subtree push --prefix ci/github wq-ci main
git fetch wq-ci && git push -f wq-ci refs/remotes/wq-ci/main:refs/tags/v1   # no local v1 tag
```

Or copy `ci/github/` into a clone of `JMO-Labs/wq-ci`, commit, push `main`, and move tag `v1`.
