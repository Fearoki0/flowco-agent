import copy
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import flowco


class FlowCoTestCase(unittest.TestCase):
    """Every test owns its configuration, processes, files and accounting."""
    def setUp(self):
        super().setUp()
        self.storage = tempfile.TemporaryDirectory(prefix='flowco-test-')
        self.addCleanup(self.storage.cleanup)
        root = Path(self.storage.name)
        cfg = copy.deepcopy(flowco.SHARED_DEFAULTS)
        cfg.update(confirm_commands=False, sandbox='local')
        replacements = dict(CFG=cfg, WORK=root / 'work', CONFIG_DIR=root / 'config',
                            SANDBOX={'mode': 'local', 'note': 'test', 'python': ''},
                            BUDGET=flowco.BudgetManager(), TASK_GRAPH={'tasks': {}, 'order': []},
                            RUN_DATA={}, CAPABILITY_CACHE={}, CURRENT_CAPABILITIES=None,
                            CANCEL_EVENT=threading.Event(), TOOLS=[], BACKGROUND_TASKS={},
                            TASK_STATE={'steps': 0, 'tools': 0, 'errors': 0, 'fixes': 0,
                                        'verifications': 0, 'started': 0, 'paused': False, 'status': 'idle', 'touches': set()})
        for key, name in [('CONFIG_FILE', 'config.json'), ('LOG_FILE', 'flowco.log'), ('SESSION_DIR', 'sessions'),
                          ('BACKUP_DIR', 'backups'), ('HISTORY_FILE', 'history'), ('SKILLS_DIR', 'skills')]:
            replacements[key] = root / 'config' / name
        patch = mock.patch.multiple(flowco, **replacements)
        patch.start()
        self.addCleanup(patch.stop)
        flowco.WORK.mkdir()
        flowco.ensure_dirs()
        env = mock.patch.dict('os.environ', {'FLOWCO_YES': '0', 'FLOWCO_TEST_MODE': '0'})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(flowco.stop_background_tasks)
