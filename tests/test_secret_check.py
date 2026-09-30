"""Exercise the checks against real Git indexes, commits, and hooks."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts/check_secrets.py"
KEY = b"np" + b"_" + b"sandboxTest123"


class SecretCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agentbench-test-", dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Secret check tests")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", ".git/disabled-hooks")

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.repo, check=check,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stage(self, path, content):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        self.git("add", "-f", "--", path)

    def scan(self, mode="--staged"):
        return subprocess.run([sys.executable, str(SCANNER), mode], cwd=self.repo,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_clean_example_allowed(self):
        self.stage(".env.example", b"PROVIDER_API_KEY=replace-me\n")
        self.assertEqual(self.scan().returncode, 0)

    def test_environment_files_at_any_depth_blocked(self):
        for path in [".env", "nested/.env", "space dir/line\nbreak/.env.local"]:
            with self.subTest(path=path):
                self.stage(path, b"safe=true\n")
                self.assertEqual(self.scan().returncode, 1)
                self.git("rm", "--cached", "--", path)

    def test_staged_content_not_worktree_is_scanned(self):
        self.stage("settings.txt", KEY)
        (self.repo / "settings.txt").write_bytes(b"clean worktree")
        result = self.scan()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(KEY, result.stdout + result.stderr)

    def test_unstaged_key_does_not_block_clean_index(self):
        self.stage("settings.txt", b"clean index")
        (self.repo / "settings.txt").write_bytes(KEY)
        self.assertEqual(self.scan().returncode, 0)

    def test_binary_and_example_contents_checked(self):
        for path, content in [("file.bin", b"\0" + KEY + b"\0"),
                              (".env.example", KEY)]:
            with self.subTest(path=path):
                self.stage(path, content)
                self.assertEqual(self.scan().returncode, 1)
                self.git("rm", "--cached", "--", path)

    def test_filename_secret_redacted(self):
        self.stage(KEY.decode() + ".txt", b"safe")
        result = self.scan()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(KEY, result.stdout + result.stderr)

    def test_history_catches_added_then_deleted_secret_on_other_branch(self):
        self.stage("safe.txt", b"safe")
        self.git("commit", "-qm", "base")
        self.git("branch", "clean")
        self.stage("settings.txt", KEY)
        self.git("commit", "-qm", "add secret")
        self.git("rm", "settings.txt")
        self.git("commit", "-qm", "remove secret")
        self.git("checkout", "-q", "clean")
        self.assertEqual(self.scan().returncode, 0)
        self.assertEqual(self.scan("--all-history").returncode, 1)

    def test_commit_and_tag_messages_checked(self):
        self.stage("safe.txt", b"safe")
        self.git("commit", "-qm", KEY.decode())
        result = self.scan("--all-history")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(KEY, result.stdout + result.stderr)
        self.git("commit", "--amend", "-qm", "safe")
        self.git("tag", "-a", "agentbench-test", "-m", KEY.decode())
        self.assertEqual(self.scan("--all-history").returncode, 1)

    def test_installed_hooks_reject_real_commits(self):
        (self.repo / "scripts").mkdir()
        shutil.copy2(SCANNER, self.repo / "scripts/check_secrets.py")
        shutil.copytree(ROOT / ".githooks", self.repo / ".githooks")
        (self.repo / ".venv/bin").mkdir(parents=True)
        os.symlink(sys.executable, self.repo / ".venv/bin/python")
        self.git("config", "core.hooksPath", ".githooks")
        self.stage("safe.txt", b"safe")
        self.assertEqual(self.git("commit", "-qm", "safe", check=False).returncode, 0)
        self.stage("settings.txt", KEY)
        self.assertNotEqual(self.git("commit", "-qm", "bad", check=False).returncode, 0)
        self.stage("settings.txt", b"safe again")
        self.assertNotEqual(self.git("commit", "-qm", KEY.decode(), check=False).returncode, 0)
        self.assertEqual(self.git("commit", "-qm", "clean", check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
