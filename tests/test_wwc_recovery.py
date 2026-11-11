import datetime as dt
import unittest
from wwc_refresh import fast_window, due_recovery, should_enable_today, mark_success, recovery_interval, game_key
from calendar_feed import merge
UTC=dt.timezone.utc
G={'date':'2026-11-06','time':'15:00','status':'Live','number':1}
def when(hours): return dt.datetime(2026,11,6,14,0,tzinfo=UTC)+dt.timedelta(hours=hours)
class RecoveryTests(unittest.TestCase):
    def test_pregame_15_minutes(self):
        self.assertFalse(fast_window(G,'Europe/Copenhagen',when(-.3)))
        self.assertTrue(fast_window(G,'Europe/Copenhagen',when(-.2)))
    def test_fast_after_12_hours_stops(self):
        self.assertFalse(fast_window(G,'Europe/Copenhagen',when(12)))
    def test_recovery_due_after_12(self):
        self.assertTrue(due_recovery([G],'Europe/Copenhagen',when(12),{}))
    def test_recovery_not_due_with_recent_check(self):
        self.assertFalse(due_recovery([G],'Europe/Copenhagen',when(13),{'2026:1':when(12.5).isoformat()}))
    def test_recovery_catches_missed_runs(self):
        self.assertTrue(due_recovery([G],'Europe/Copenhagen',when(25),{'2026:1':when(12).isoformat()}))
    def test_stale_games_do_not_enable_fast(self):
        self.assertFalse(should_enable_today([G],'Europe/Copenhagen',when(100)))
    def test_final_not_due(self):
        self.assertFalse(due_recovery([{**G,'status':'Final'}],'Europe/Copenhagen',when(100),{}))
    def test_postponed_no_fast(self):
        self.assertFalse(fast_window({**G,'status':'Postponed'},'Europe/Copenhagen',when(1)))
    def test_final_no_downgrade(self):
        old={'1':{**G,'status':'Final','score_home':2,'score_away':1}}
        new={'1':{**G,'status':'Live','score_home':1,'score_away':1}}
        result=merge(old,new)
        self.assertEqual(result['1']['status'],'Final')
    def test_final_score_correction(self):
        old={'1':{**G,'status':'Final','score_home':2,'score_away':1}}
        new={'1':{**G,'status':'Final','score_home':3,'score_away':1}}
        self.assertEqual(merge(old,new)['1']['score_home'],3)
    def test_intervals(self):
        self.assertEqual(recovery_interval(dt.timedelta(hours=12)),dt.timedelta(hours=1))
        self.assertEqual(recovery_interval(dt.timedelta(hours=24)),dt.timedelta(hours=6))
        self.assertEqual(recovery_interval(dt.timedelta(hours=72)),dt.timedelta(days=1))
if __name__=='__main__':unittest.main()
