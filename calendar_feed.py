"""IIHF 2026 Women's Worlds calendar feed. Python 3.11+."""
import argparse
import datetime as dt
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

SOURCE = 'https://stats.iihf.com/Hydra/773/index.html'
OFFICIAL = 'https://www.iihf.com/en/events/2026/ww/schedule'
ROOT = Path(__file__).resolve().parent
DENMARK = ZoneInfo('Europe/Copenhagen')
UTC = dt.timezone.utc
# Verified official schedule, keyed by IIHF game number. Date/time is Denmark local.
ROWS = [
('06','15:00','AUT','CZE','Esbjerg','PRE'),('06','15:00','SWE','CAN','Herning','PRE'),
('06','19:00','SUI','USA','Esbjerg','PRE'),('06','19:00','DEN','FIN','Herning','PRE'),
('07','19:00','GER','AUT','Esbjerg','PRE'),('07','19:00','JPN','DEN','Herning','PRE'),
('08','15:00','USA','GER','Esbjerg','PRE'),('08','15:00','FIN','SWE','Herning','PRE'),
('08','19:00','CZE','SUI','Esbjerg','PRE'),('08','19:00','CAN','JPN','Herning','PRE'),
('09','19:00','AUT','USA','Esbjerg','PRE'),('09','19:00','DEN','CAN','Herning','PRE'),
('10','15:00','CZE','GER','Esbjerg','PRE'),('10','15:00','FIN','JPN','Herning','PRE'),
('10','19:00','SUI','AUT','Esbjerg','PRE'),('10','19:00','SWE','DEN','Herning','PRE'),
('11','15:00','GER','SUI','Esbjerg','PRE'),('11','15:00','CAN','FIN','Herning','PRE'),
('11','19:00','USA','CZE','Esbjerg','PRE'),('11','19:00','JPN','SWE','Herning','PRE'),
('13','11:00','RL','RL','Herning','P9-10'),('13','15:00','QF','QF','Herning','QF'),
('13','15:00','QF','QF','Esbjerg','QF'),('13','19:00','QF','QF','Herning','QF'),
('13','19:00','QF','QF','Esbjerg','QF'),('15','15:00','SF','SF','Herning','SF'),
('15','19:00','SF','SF','Herning','SF'),('16','15:00','L(SF)','L(SF)','Herning','BMG'),
('16','19:00','W(SF)','W(SF)','Herning','GMG')]
TEAM = {'AUT':'Austria','CAN':'Canada','CZE':'Czechia','DEN':'Denmark','FIN':'Finland',
        'GER':'Germany','JPN':'Japan','SUI':'Switzerland','SWE':'Sweden','USA':'United States',
        'RL':'Relegation TBD','QF':'Quarterfinal TBD','SF':'Semifinal TBD',
        'L(SF)':'Semifinal losers TBD','W(SF)':'Semifinal winners TBD'}
PHASE = {'PRE':'Preliminary round','REL':'Relegation','P9-10':'Placement Round (9–10)','QF':'Quarterfinal',
         'SF':'Semifinal','BMG':'Bronze medal game','GMG':'Gold medal game'}

def seed():
    return {str(n): {'number':n,'date':f'2026-11-{day}', 'time':time,
        'home':home,'away':away,'city':city,'phase':phase,'status':'Scheduled',
        'score_home':None,'score_away':None} for n,(day,time,home,away,city,phase) in enumerate(ROWS,1)}

def normalize(text):
    return re.sub(r'\s+', ' ', text.replace('\xa0',' ')).strip()

def parse_stats(html):
    """Extract numbered game records from IIHF Hydra schedule table rows.

    Fail closed if the site layout changes: never publish partial or uncertain scores.
    """
    soup = BeautifulSoup(html, 'html.parser')
    found = {}
    for tr in soup.select('tr'):
        text = normalize(tr.get_text(' ', strip=True))
        # Each official row contains date, time, venue, game number, phase, teams, result, status.
        date = re.search(r'\b(\d{1,2})\s+Nov\s+2026\b', text, re.I)
        time = re.search(r'\b(\d{1,2}:\d{2})\b', text)
        game = re.search(r'\b(\d{1,2})\s+(P9-10|PRE|REL|QF|SF|BMG|GMG)\b', text)
        if not (date and time and game):
            continue
        number = int(game.group(1))
        if not 1 <= number <= 29:
            continue
        phase = game.group(2)
        tail = text[game.end():]
        teams = re.search(r'\b(AUT|CAN|CZE|DEN|FIN|GER|JPN|SUI|SWE|USA|L\(SF\)|W\(SF\)|RL|QF|SF)\s*[-–:]\s*(AUT|CAN|CZE|DEN|FIN|GER|JPN|SUI|SWE|USA|L\(SF\)|W\(SF\)|RL|QF|SF)(?![A-Za-z])', tail)
        if not teams:
            continue
        home, away = teams.groups()
        # Score is accepted only when between the team pairing and a status token.
        remainder = tail[teams.end():]
        if re.search(r'\bGame\s+Completed\b', remainder, re.I):
            status = 'Final'
        elif re.search(r'\b(Final|Finished|After OT|After SO)\b', remainder, re.I):
            status = 'Final'
        elif re.search(r'\bLive\b|\bPeriod\s+\d+\s+Ended\b|\bIn Progress\b', remainder, re.I):
            status = 'Live'
        elif re.search(r'\bPostponed\b', remainder, re.I):
            status = 'Postponed'
        elif re.search(r'\b(Cancelled|Canceled)\b', remainder, re.I):
            status = 'Cancelled'
        else:
            status = 'Scheduled'
        score_home = score_away = None
        score = re.search(r'\b(\d{1,2})\s*[-–:]\s*(\d{1,2})\b', remainder)
        if score and status in ('Final', 'Live'):
            score_home,score_away = map(int,score.groups())
        city = 'Esbjerg' if 'Esbjerg' in text else 'Herning' if 'Herning' in text else None
        found[str(number)] = {'number':number,'date':f'2026-11-{int(date.group(1)):02d}',
            'time':time.group(1).zfill(5),'home':home,'away':away,'city':city,
            'phase':phase,'status':status,'score_home':score_home,'score_away':score_away}
    return found

def merge(previous, updates):
    result = {k:dict(v) for k,v in previous.items()}
    for key, update in updates.items():
        if key not in result: continue
        old = result[key]
        for field in ('date','time','home','away','city','phase'):
            if update.get(field) is not None: old[field] = update[field]
        # Never downgrade a confirmed Final because the upstream table is stale.
        if str(old.get('status','')).lower() in ('final','finished','after ot','after so') and str(update.get('status','')).lower() not in ('final','finished','after ot','after so'):
            pass
        elif update.get('status') is not None: old['status'] = update['status']
        # Never erase a previously confirmed score when IIHF temporarily omits it.
        old_final = str(previous[key].get('status','')).lower() in ('final','finished','after ot','after so')
        new_final = str(update.get('status','')).lower() in ('final','finished','after ot','after so')
        if update.get('score_home') is not None and update.get('score_away') is not None and (not old_final or new_final):
            old['score_home'],old['score_away'] = update['score_home'],update['score_away']
    return result

def esc(value):
    return str(value).replace('\\','\\\\').replace('\n','\\n').replace(',','\\,').replace(';','\\;')

def fold(line):
    """Fold RFC5545 content lines at 75 UTF-8 octets."""
    out=[]; current=''
    for ch in line:
        if len((current+ch).encode('utf-8')) > 75:
            out.append(current);current=' '+ch
        else: current+=ch
    out.append(current)
    return '\r\n'.join(out)

def ical(games, generated=None):
    generated = generated or dt.datetime.now(UTC)
    stamp=generated.strftime('%Y%m%dT%H%M%SZ')
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//IIHF Women Worlds 2026//Community Calendar//EN',
           'CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:IIHF Women Worlds 2026 - Live Results',
           'X-WR-TIMEZONE:Europe/Copenhagen','REFRESH-INTERVAL;VALUE=DURATION:PT30M',
           'X-PUBLISHED-TTL:PT30M',
           'BEGIN:VTIMEZONE','TZID:Europe/Copenhagen','X-LIC-LOCATION:Europe/Copenhagen',
           'BEGIN:DAYLIGHT','TZOFFSETFROM:+0100','TZOFFSETTO:+0200',
           'TZNAME:CEST','DTSTART:19700329T020000','RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU',
           'END:DAYLIGHT','BEGIN:STANDARD','TZOFFSETFROM:+0200','TZOFFSETTO:+0100',
           'TZNAME:CET','DTSTART:19701025T030000','RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU',
           'END:STANDARD','END:VTIMEZONE']
    for n in range(1,30):
        g=games[str(n)]
        start=dt.datetime.fromisoformat(g['date']+'T'+g['time']).replace(tzinfo=DENMARK)
        end=start+dt.timedelta(hours=2,minutes=30)
        scores=g.get('score_home') is not None and g.get('score_away') is not None
        finished=bool(re.search(r'Final|Finished|After OT|After SO',g['status'],re.I))
        title=(f"{TEAM.get(g['home'],g['home'])} {g['score_home']} - {g['score_away']} {TEAM.get(g['away'],g['away'])} (Final)"
               if scores and finished else f"{TEAM.get(g['home'],g['home'])} vs {TEAM.get(g['away'],g['away'])}")
        if g['phase']!='PRE':title=f"{PHASE.get(g['phase'],g['phase'])}: {title}"
        description=(f"IIHF Women's World Championship 2026\\nGame {n} - {PHASE.get(g['phase'],g['phase'])}\\n"
                     f"Status: {g['status']}\\nOfficial schedule/results: {OFFICIAL}")
        lines+=['BEGIN:VEVENT',f'UID:iihf-2026-ww-game-{n}@community-calendar',f'DTSTAMP:{stamp}',
                f'DTSTART;TZID=Europe/Copenhagen:{start.strftime("%Y%m%dT%H%M%S")}',f'DTEND;TZID=Europe/Copenhagen:{end.strftime("%Y%m%dT%H%M%S")}',
                f'SUMMARY:{esc(title)}',f'DESCRIPTION:{description}',
                f'LOCATION:{esc("Hockey Arena "+(g.get("city") or "Denmark")+", Denmark")}',
                f'URL:{OFFICIAL}',f'STATUS:{"CANCELLED" if re.search("Cancel",g["status"],re.I) else "CONFIRMED"}',
                'END:VEVENT']
    lines.append('END:VCALENDAR')
    return '\r\n'.join(fold(line) for line in lines)+'\r\n'

def run(offline=False):
    data_path=ROOT/'docs'/'games.json'
    games=seed()
    if data_path.exists():
        saved=json.loads(data_path.read_text(encoding='utf-8'))
        games=merge(games,saved)
    if not offline:
        response=requests.get(SOURCE,timeout=30,headers={'User-Agent':'IIHF-WW-Calendar/1.0 (personal calendar feed)'})
        response.raise_for_status()
        updates=parse_stats(response.text)
        if len(updates)<25:
            raise RuntimeError(f'IIHF schedule parsing returned only {len(updates)} of 29 games. Existing feed preserved.')
        games=merge(games,updates)
    (ROOT/'docs').mkdir(exist_ok=True)
    data_path.write_text(json.dumps(games,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (ROOT/'docs'/'calendar.ics').write_bytes(ical(games).encode('utf-8'))
    print('Wrote 29 games to docs/calendar.ics')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true',help='Use saved schedule without fetching IIHF')
    args=parser.parse_args()
    run(args.offline)
