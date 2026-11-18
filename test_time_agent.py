import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import time_agent as a

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name)/'test.db')
        self.db = a.connect(self.path)
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def test_first_interaction(self):
        self.assertIsNone(a.clock(self.db)['last_user_at'])
    def test_cross_session(self):
        with patch('time_agent.time.time', return_value=1000):
            a.remember_user(self.db,'hello')
        self.db.close()
        self.db = a.connect(self.path)
        with patch('time_agent.time.time', return_value=1060):
            self.assertEqual(a.clock(self.db)['seconds_since_last_user'],60)
    def test_restart_overdue_and_dedup(self):
        with patch('time_agent.time.time', return_value=1000):
            a.add_job(self.db,10,'test')
        self.db.close()
        self.db = a.connect(self.path)
        with patch('time_agent.time.time', return_value=1020):
            self.assertEqual(len(a.tick(self.db)),1)
            self.assertEqual(len(a.tick(self.db)),0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM notifications').fetchone()[0],1)
    def test_invalid_delay(self):
        with self.assertRaises(ValueError):
            a.add_job(self.db,-1,'bad')

if __name__=='__main__':
    unittest.main()
