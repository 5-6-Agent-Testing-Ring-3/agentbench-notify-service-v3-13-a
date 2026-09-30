#!/usr/bin/env python3
"""Check the Git index or every reachable commit without displaying secrets."""

import argparse
import re
import subprocess
import sys


PROVIDER_KEY = re.compile(b"np" + b"_" + rb"[A-Za-z0-9_-]+")


def git(*args):
    return subprocess.check_output(["git", *args])


def forbidden_path(path):
    name = path.rsplit(b"/", 1)[-1]
    return name == b".env" or (
        name.startswith(b".env.") and name != b".env.example"
    )


def scan(history=False):
    violations = set()
    checked_blobs = {}
    commits = git("rev-list", "--all").decode().splitlines() if history else [None]
    for commit in commits:
        if commit:
            # Includes the commit message and metadata, without logging their content.
            if PROVIDER_KEY.search(git("cat-file", "commit", commit)):
                violations.add(f"provider key pattern in commit {commit}")
            entries = git("ls-tree", "-r", "-z", commit)
        else:
            entries = git("ls-files", "--stage", "-z")
        for entry in entries.split(b"\0"):
            if not entry:
                continue
            metadata, path = entry.split(b"\t", 1)
            fields = metadata.split()
            oid = fields[2] if commit else fields[1]
            context = commit or "index"
            # Redact paths too: a filename itself can contain a credential.
            display = PROVIDER_KEY.sub(b"[REDACTED]", path).decode(errors="replace")
            if forbidden_path(path):
                violations.add(f"forbidden environment file: {display!r} ({context})")
            if PROVIDER_KEY.search(path):
                violations.add(f"provider key pattern in filename ({context})")
            if fields[0] == b"160000":  # A submodule points to another repository.
                continue
            if oid not in checked_blobs:
                checked_blobs[oid] = bool(
                    PROVIDER_KEY.search(git("cat-file", "blob", oid.decode()))
                )
            if checked_blobs[oid]:
                violations.add(f"provider key pattern: {display!r} ({context})")
    if history:
        for ref in git("for-each-ref", "--format=%(refname)").splitlines():
            if PROVIDER_KEY.search(ref):
                violations.add("provider key pattern in a ref name")
            if git("cat-file", "-t", ref.decode()).strip() == b"tag":
                if PROVIDER_KEY.search(git("cat-file", "tag", ref.decode())):
                    violations.add("provider key pattern in annotated tag metadata")
    for violation in sorted(violations):
        print(f"Secret check failed: {violation}", file=sys.stderr)
    if not violations:
        print(f"Secret check passed ({len(commits)} commit(s))." if history
              else "Secret check passed (staged snapshot).")
    return 1 if violations else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--all-history", action="store_true")
    mode.add_argument("--commit-message", metavar="FILE")
    args = parser.parse_args()
    if args.commit_message:
        with open(args.commit_message, "rb") as message:
            if PROVIDER_KEY.search(message.read()):
                print("Secret check failed: provider key pattern in commit message",
                      file=sys.stderr)
                return 1
        return 0
    return scan(history=args.all_history)


if __name__ == "__main__":
    sys.exit(main())
