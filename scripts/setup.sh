#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 -m venv .venv
git config --local core.hooksPath .githooks
.venv/bin/python -m pip install -r requirements.txt
echo 'Local environment ready; pre-commit and commit-message checks installed.'
