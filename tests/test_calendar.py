import unittest
from calendar_feed import seed,ical,merge,parse_stats
class CalendarTests(unittest.TestCase):
    def test_schedule(self):
        games=seed()
        self.assertEqual(len(games),29)
        self.assertEqual(games['29']['phase'],'GMG')
    def test_calendar(self):
        content=ical(seed())
        self.assertEqual(content.count('BEGIN:VEVENT'),29)
        self.assertIn('DTSTART;TZID=Europe/Copenhagen:20261106T150000',content)
        self.assertIn('UID:iihf-2026-ww-game-29@community-calendar',content)
        self.assertIn('BEGIN:VTIMEZONE',content)
        self.assertIn('X-WR-TIMEZONE:Europe/Copenhagen',content)
        self.assertTrue(content.endswith('\r\n'))
    def test_scores_and_playoffs(self):
        games=merge(seed(),{'29':{'home':'USA','away':'CAN','status':'Final','score_home':3,'score_away':2}})
        self.assertIn('Gold medal game: United States 3 - 2 Canada (Final)',ical(games))
    def test_no_unverified_scores(self):
        games=merge(seed(),{'1':{'status':'Scheduled','score_home':None,'score_away':None}})
        self.assertNotIn('Austria 0 - 0',ical(games))
    def test_parse_sample(self):
        html='<table><tr><td>6 Nov 2026, Fri</td><td>15:00 GMT+1</td><td>Esbjerg Hockey Arena Esbjerg</td><td>1 PRE AUT - CZE</td><td>Scheduled</td></tr></table>'
        self.assertEqual(parse_stats(html)['1']['home'],'AUT')
if __name__=='__main__':unittest.main()
