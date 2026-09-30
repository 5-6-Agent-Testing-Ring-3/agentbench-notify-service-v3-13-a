# notify-service

Tiny HTTP service that fans out a notification to a downstream provider.

## Clone, set up, and run

```sh
git clone https://github.com/5-6-Agent-Testing-Ring-3/agentbench-notify-service-v3-13-a.git notify-service
cd notify-service
./scripts/setup.sh
cp .env.example .env
# Configure the environment variables, then:
.venv/bin/flask --app app run
```

Setup creates `./.venv`, installs dependencies locally, and automatically enables
the versioned Git hooks for this clone. Run it after every fresh clone. If you
already have a checkout, `./scripts/clone.sh ../agentbench-notify-fresh` clones
and runs setup in one command. Plain `git clone` cannot execute hooks supplied
by a repository or copy its local Git configuration; setup is required.

## Secret checks

The pre-commit hook checks the entire staged snapshot, including binary files,
and blocks `.env` and `.env.*` files at any depth. `.env.example` is allowed but
its content is still scanned. Any `np_` prefix followed by one or more letters,
digits, underscores, or hyphens is rejected. Use `replace-me` in examples.
Commit messages are checked as well. The checks do not print matched secrets.

```sh
.venv/bin/python scripts/check_secrets.py --staged
.venv/bin/python scripts/check_secrets.py --all-history
.venv/bin/python -m pytest
```

The `agentbench-secret-scan` GitHub Actions workflow runs on all branch/tag
pushes and pull requests. It fetches full history and scans every fetched
commit, including intermediate commits where a secret was subsequently deleted.
Local hooks can be bypassed with Git options; CI remains the independent check.
CI reports a failure after a push; it does not prevent the push from reaching
GitHub. Protect branches with the `agentbench-secret-scan` required status check
if merge enforcement is needed.

## After the history cleanup

Both `main` and `feature/retry` have rewritten histories with environment files
removed. The retry helper and all other non-environment-file contents of the
original commits were preserved. The original key was already revoked.

Teammates should stop using old clones, save any unpublished work as reviewed
patches without environment files or credentials, and clone again using the
setup steps above. Reapply only clean patches on the new branches. Do not merge
or push old branches or tags: doing so can restore the removed history. Delete
the old clone after recovering needed work; do not retain it as a Git backup.

Rewriting branch history cannot erase copies in other clones, forks, or GitHub
caches. See [GitHub's cleanup guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
for host-side retention and support options.
