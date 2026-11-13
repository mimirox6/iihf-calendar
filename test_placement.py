import unittest
from calendar_feed import parse_stats, seed, merge, PHASE
from google_calendar_sync import event_body, event_id
class PlacementTests(unittest.TestCase):
    def test_official_phase_and_completed_result(self):
        html='<table><tr><td>13 Nov 2026</td><td>11:00</td><td>Herning</td><td>21 P9-10</td><td>JPN - AUT</td><td>2 - 1</td><td>Game Completed</td></tr></table>'
        game=parse_stats(html)['21']
        self.assertEqual((game['home'],game['away'],game['phase'],game['status']),('JPN','AUT','P9-10','Final'))
        self.assertEqual((game['score_home'],game['score_away']),(2,1))
        merged=merge(seed(),{'21':game})['21']
        self.assertEqual(event_body(merged)['id'],event_id(21))
        self.assertIn('Placement Round (9–10)',event_body(merged)['summary'])
        self.assertEqual(event_body(merged)['start']['timeZone'],'Europe/Copenhagen')
    def test_no_invented_result(self):
        html='<tr><td>13 Nov 2026 11:00 Herning 21 P9-10 JPN - AUT Scheduled</td></tr>'
        game=parse_stats(html)['21']
        self.assertIsNone(game['score_home'])
        self.assertEqual(game['status'],'Scheduled')
    def test_existing_phase_still_supported(self):
        html='<tr><td>13 Nov 2026 11:00 Herning 21 REL JPN - AUT 0 - 0 Live</td></tr>'
        self.assertEqual(parse_stats(html)['21']['phase'],'REL')
    def test_other_games_unchanged(self):
        games=seed()
        self.assertEqual(len(games),29)
        self.assertEqual(games['22']['phase'],'QF')
        self.assertEqual(games['21']['phase'],'P9-10')
if __name__=='__main__':unittest.main()
