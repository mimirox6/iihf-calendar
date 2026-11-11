import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from google_calendar_sync import event_body, event_id, is_owned, sync, MARKER

class FakeResponse:
    def __init__(self,status_code=200,payload=None):
        self.status_code=status_code; self._payload=payload or {}; self.content=b'{}'; self.text='{}'
    def json(self):return self._payload
class FakeSession:
    def __init__(self):self.remote={};self.writes=[]
    def get(self,url,timeout):
        eid=url.rsplit('/',1)[-1]
        return FakeResponse(200,self.remote[eid]) if eid in self.remote else FakeResponse(404)
    def post(self,url,json,timeout):
        self.writes.append(('post',json['id']));self.remote[json['id']]=json
        return FakeResponse(200,json)
    def patch(self,url,json,timeout):
        eid=url.rsplit('/',1)[-1];self.writes.append(('patch',eid));self.remote[eid].update(json)
        return FakeResponse(200,self.remote[eid])

def games():
    return {str(n):{'number':n,'date':'2026-11-06','time':'15:00','home':'USA','away':'CAN','phase':'PRE','status':'Scheduled','city':'Herning','score_home':None,'score_away':None} for n in range(1,30)}

class TestSync(unittest.TestCase):
    def test_stable_ids(self):self.assertEqual(event_id(1),'iihf2026game01')
    def test_denmark_time(self):
        self.assertEqual(event_body(games()['1'])['start']['dateTime'],'2026-11-06T15:00:00+01:00')
    def test_dry_run_never_writes(self):
        s=FakeSession();self.assertEqual(len(sync(s,'abc',games(),True)),29);self.assertEqual(s.writes,[])
    def test_create_then_no_changes(self):
        s=FakeSession();self.assertEqual(len(sync(s,'abc',games(),False)),29)
        self.assertEqual(sync(s,'abc',games(),False),[])
    def test_score_updates(self):
        s=FakeSession();g=games();sync(s,'abc',g,False)
        g['1'].update(status='Final',score_home=3,score_away=2)
        self.assertEqual(sync(s,'abc',g,False),[('update',1)])
        self.assertIn('(Final)',s.remote[event_id(1)]['summary'])
    def test_refuse_unowned_event(self):
        s=FakeSession();s.remote[event_id(1)]={'id':event_id(1)}
        with self.assertRaises(RuntimeError):sync(s,'abc',games(),False)
    def test_reject_incomplete(self):
        with self.assertRaises(ValueError):sync(FakeSession(),'abc',{'1':games()['1']},False)

if __name__=='__main__':unittest.main()
