"""
test_security.py - Offline unit tests for FlowCo v5.0 security and sandbox boundaries
"""
import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

# Add work directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flowco


class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.test_root = Path(self.td.name).resolve()
        self.orig_work = flowco.WORK
        self.orig_backup = flowco.BACKUP_DIR
        self.orig_sandbox = dict(flowco.SANDBOX)

        flowco.WORK = (self.test_root / "workspace").resolve()
        flowco.WORK.mkdir(parents=True, exist_ok=True)
        flowco.BACKUP_DIR = (self.test_root / "backups").resolve()
        flowco.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        flowco.WORK = self.orig_work
        flowco.BACKUP_DIR = self.orig_backup
        flowco.SANDBOX.clear()
        flowco.SANDBOX.update(self.orig_sandbox)
        self.td.cleanup()

    def test_safe_path_traversal_prevention(self):
        """Verify directory traversal attempts raise PermissionError."""
        with self.assertRaises(PermissionError):
            flowco.safe_path("../../etc/passwd")

        with self.assertRaises(PermissionError):
            flowco.safe_path("/etc/passwd")

    def test_symlink_escape_prevention(self):
        """Verify symlinks pointing outside workspace are rejected."""
        outside_file = self.test_root / "outside.txt"
        outside_file.write_text("secret", encoding="utf-8")

        symlink_path = flowco.WORK / "escape_link"
        try:
            symlink_path.symlink_to(outside_file)
            with self.assertRaises(PermissionError):
                flowco.safe_path("escape_link")
        except OSError:
            # Android filesystems without symlink support
            pass

    def test_wipe_boundary_protection(self):
        """Verify is_safe_workspace rejects root, home, and sensitive Android folders."""
        self.assertFalse(flowco.is_safe_workspace(Path("/")))
        self.assertFalse(flowco.is_safe_workspace(flowco.HOME))
        self.assertFalse(flowco.is_safe_workspace(Path("/storage/emulated/0")))
        self.assertFalse(flowco.is_safe_workspace(Path("/sdcard")))
        self.assertFalse(flowco.is_safe_workspace(Path("/storage/emulated/0/DCIM")))
        self.assertFalse(flowco.is_safe_workspace(Path("/storage/emulated/0/Download")))
        self.assertFalse(flowco.is_safe_workspace(Path("/storage/emulated/0/Documents")))

        # Dedicated subfolder workspace must be allowed
        self.assertTrue(flowco.is_safe_workspace(flowco.WORK))

    def test_command_confirmation_default(self):
        """Verify confirm_commands defaults to True."""
        self.assertTrue(flowco.SHARED_DEFAULTS.get("confirm_commands"))

    def test_failsafe_sandbox_behavior(self):
        """Verify auto/proot falls back safely to 'off' rather than silent local execution."""
        flowco.CFG["sandbox"] = "proot"
        flowco.setup_sandbox()
        # On termux without proot setup, proot_selftest fails -> mode must be 'off'
        self.assertIn(flowco.SANDBOX["mode"], ("proot", "off"))
        if flowco.SANDBOX["mode"] == "off":
            self.assertIn("unavailable", flowco.SANDBOX["note"].lower())

    def test_noninteractive_command_rejection(self):
        """Verify commands are rejected when confirm_commands is True and session is non-interactive."""
        flowco.CFG["confirm_commands"] = True
        flowco.SANDBOX["mode"] = "local"
        with mock.patch("sys.stdin.isatty", return_value=False):
            res_cmd = flowco.tool_run_command("echo hello")
            self.assertIn("Command requires user confirmation", res_cmd)

            res_bg = flowco.tool_run_background("echo bg_task")
            self.assertIn("Command requires user confirmation", res_bg)

            # Destructive git operations also rejected
            res_git = flowco.tool_git("reset --hard HEAD")
            self.assertIn("Command requires user confirmation", res_git)

    def test_interactive_command_rejection_on_no(self):
        """Verify command rejection when user responds 'n' to confirmation prompt."""
        flowco.CFG["confirm_commands"] = True
        flowco.SANDBOX["mode"] = "local"
        with mock.patch("sys.stdin.isatty", return_value=True), \
             mock.patch("builtins.input", return_value="n"):
            res_cmd = flowco.tool_run_command("echo rejected_command")
            self.assertIn("rejected by user", res_cmd.lower())

    def test_null_byte_rejection(self):
        """Verify safe_path immediately rejects paths with null bytes."""
        with self.assertRaises(PermissionError):
            flowco.safe_path("evil\0payload.txt")

    def test_local_guard_traversal_and_banned(self):
        """Verify local_guard catches traversal, elevated binaries, and escaping paths."""
        self.assertIsNotNone(flowco.local_guard("cat ../outside.txt"))
        self.assertIsNotNone(flowco.local_guard("sudo apt update"))
        self.assertIsNotNone(flowco.local_guard("su - root"))
        self.assertIsNotNone(flowco.local_guard("termux-setup-storage"))
        self.assertIsNotNone(flowco.local_guard("cat /etc/shadow"))

    def test_broken_symlink_deletion(self):
        """Verify tool_delete_path can delete broken symlinks."""
        broken = flowco.WORK / "broken_link"
        try:
            broken.symlink_to(flowco.WORK / "non_existent_file_target.xyz")
            res = flowco.tool_delete_path("broken_link")
            self.assertIn("Deleted", res)
            self.assertFalse(broken.is_symlink())
        except OSError:
            pass


if __name__ == "__main__":
    unittest.main()
