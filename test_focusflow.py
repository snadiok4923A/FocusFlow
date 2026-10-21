import tempfile
import unittest
from pathlib import Path
from focusflow import connect_db, add_task, list_tasks, complete_task, add_habit, log_habit, habit_summary, dashboard, export_csv

class FocusFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect_db(Path(self.tmp.name) / "test.db")
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def test_task_lifecycle(self):
        task_id = add_task(self.db, "Build portfolio", priority="high")
        self.assertEqual("Build portfolio", list_tasks(self.db)[0]["title"])
        self.assertTrue(complete_task(self.db, task_id))
        self.assertFalse(complete_task(self.db, task_id))
        self.assertEqual(1, dashboard(self.db)["completed_tasks"])
    def test_reject_empty_task(self):
        with self.assertRaises(ValueError): add_task(self.db, " ")
    def test_habit_logging_and_duplicate(self):
        habit_id = add_habit(self.db, "Read")
        log_habit(self.db, habit_id)
        self.assertTrue(habit_summary(self.db)[0]["done_today"])
        with self.assertRaises(ValueError): log_habit(self.db, habit_id)
    def test_csv_export(self):
        add_task(self.db, "Export test")
        path = Path(self.tmp.name) / "tasks.csv"
        self.assertEqual(1, export_csv(self.db, path))
        self.assertIn("Export test", path.read_text(encoding="utf-8"))

if __name__ == "__main__": unittest.main()
