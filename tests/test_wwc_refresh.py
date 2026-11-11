import datetime as dt
import unittest
from wwc_refresh import should_poll, should_enable_today

UTC = dt.timezone.utc
G = {'date': '2026-11-06', 'time': '15:00', 'status': 'Scheduled'}

class RefreshTests(unittest.TestCase):
    def test_before_window(self):
        self.assertFalse(should_poll([G], 'Europe/Copenhagen', dt.datetime(2026, 11, 6, 12, 0, tzinfo=UTC)))
    def test_during_window(self):
        self.assertTrue(should_poll([G], 'Europe/Copenhagen', dt.datetime(2026, 11, 6, 14, 0, tzinfo=UTC)))
    def test_after_window(self):
        self.assertFalse(should_poll([G], 'Europe/Copenhagen', dt.datetime(2026, 11, 7, 4, 0, tzinfo=UTC)))
    def test_final_stops_poll(self):
        self.assertFalse(should_poll([{**G, 'status':'Final'}], 'Europe/Copenhagen', dt.datetime(2026, 11, 6, 14, 0, tzinfo=UTC)))
    def test_controller_day_before(self):
        self.assertTrue(should_enable_today([G], 'Europe/Copenhagen', dt.datetime(2026, 11, 5, 14, 0, tzinfo=UTC)))
    def test_controller_idle(self):
        self.assertFalse(should_enable_today([G], 'Europe/Copenhagen', dt.datetime(2026, 10, 1, 14, 0, tzinfo=UTC)))

if __name__ == '__main__':
    unittest.main()
