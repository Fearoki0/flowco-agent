"""
test_agent.py - Offline unit tests for FlowCo v5.0 agent architecture, DAG, and verification
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add work directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flowco


class TestAgentArchitecture(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.test_root = Path(self.td.name).resolve()
        self.orig_work = flowco.WORK
        self.orig_backup = flowco.BACKUP_DIR
        flowco.WORK = (self.test_root / "workspace").resolve()
        flowco.WORK.mkdir(parents=True, exist_ok=True)
        flowco.BACKUP_DIR = (self.test_root / "backups").resolve()
        flowco.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        flowco.WORK = self.orig_work
        flowco.BACKUP_DIR = self.orig_backup
        self.td.cleanup()

    def test_task_graph_dag_and_cycles(self):
        """Verify DAG scheduling, dependency enforcement, and cycle detection."""
        flowco.tool_task_graph("init")
        flowco.tool_task_graph("add", task_id="t1", title="Research codebase")
        flowco.tool_task_graph("add", task_id="t2", title="Implement feature", depends_on="t1")

        # Cycle creation must be rejected
        cycle_res = flowco.tool_task_graph("add", task_id="t3", title="Cyclic task", depends_on="t2")
        self.assertNotIn("Error", cycle_res)
        cycle_res2 = flowco.tool_task_graph("update", task_id="t1", depends_on="t3")
        self.assertIn("Circular dependency", cycle_res2)

        # Before t1 is DONE, t2 must be PENDING/BLOCKED
        show = flowco.tool_task_graph("show")
        self.assertIn("[READY] t1", show)
        self.assertIn("[PENDING] t2", show)

        # Mark t1 DONE -> t2 becomes READY
        flowco.tool_task_graph("update", task_id="t1", status="DONE")
        show2 = flowco.tool_task_graph("show")
        self.assertIn("[DONE] t1", show2)
        self.assertIn("[READY] t2", show2)

    def test_atomic_file_write_and_undo(self):
        """Verify atomic writes leave no temp files and undo restores previous content."""
        target = flowco.safe_path("example.txt")
        res1 = flowco.tool_write_file("example.txt", "Initial content v1")
        self.assertIn("Wrote", res1)
        self.assertEqual(target.read_text(encoding="utf-8"), "Initial content v1")

        # Edit file
        res2 = flowco.tool_write_file("example.txt", "Updated content v2")
        self.assertIn("Wrote", res2)
        self.assertEqual(target.read_text(encoding="utf-8"), "Updated content v2")

        # Restore via undo
        res_undo = flowco.tool_undo("example.txt")
        self.assertIn("restored", res_undo.lower())
        self.assertEqual(target.read_text(encoding="utf-8"), "Initial content v1")

    def test_verification_gate_exit_codes(self):
        """Verify tool_verify validates real process return codes and file invariants."""
        # Check command success
        res_pass = flowco.tool_verify(command="echo OK_PASS")
        self.assertIn("[VERIFICATION PASSED]", res_pass)

        # Check command failure exit code
        res_fail = flowco.tool_verify(command="exit 42")
        self.assertIn("[VERIFICATION FAILED]", res_fail)
        self.assertIn("code 42", res_fail)

        # Check Python syntax validation
        py_bad = flowco.WORK / "bad.py"
        py_bad.write_text("def broken_syntax(:\n", encoding="utf-8")
        res_syntax = flowco.tool_verify(syntax_check="bad.py")
        self.assertIn("[VERIFICATION FAILED]", res_syntax)
        self.assertIn("syntax error", res_syntax.lower())

    def test_task_graph_delete_and_missing_deps(self):
        """Verify duplicate tasks rejected, missing dependencies mark task BLOCKED, and delete action cleans graph."""
        flowco.tool_task_graph("init")
        flowco.tool_task_graph("add", task_id="t1", title="Task 1")

        # Duplicate ID should be rejected
        dup_res = flowco.tool_task_graph("add", task_id="t1", title="Task 1 again")
        self.assertIn("already exists", dup_res)

        # Task with missing dependency must be BLOCKED
        flowco.tool_task_graph("add", task_id="t2", title="Task 2", depends_on="non_existent_dep")
        show = flowco.tool_task_graph("show")
        self.assertIn("[BLOCKED] t2", show)

        # Delete action
        del_res = flowco.tool_task_graph("delete", task_id="t1")
        self.assertIn("Deleted task 't1'", del_res)
        self.assertNotIn("t1", flowco.TASK_GRAPH["tasks"])

    def test_local_model_switch_and_sandbox(self):
        """Verify /local use and /sandbox commands configure profiles cleanly."""
        flowco.cmd_local("use ollama qwen2.5-coder")
        self.assertEqual(flowco.CFG["active_provider"], "ollama")
        self.assertIn("11434", flowco.CFG["base_url"])

        flowco.cmd_sandbox("off")
        self.assertEqual(flowco.SANDBOX["mode"], "off")

        flowco.cmd_sandbox("local")
        self.assertEqual(flowco.SANDBOX["mode"], "local")


if __name__ == "__main__":
    unittest.main()
