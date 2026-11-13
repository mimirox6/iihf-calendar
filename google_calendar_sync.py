"""Sync official IIHF calendar JSON to a Google Calendar owned by the user.
Only events tagged with this integration's private extended property are modified.
"""
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
TIMEZONE = 'Europe/Copenhagen'
BASE = 'https://www.googleapis.com/calendar/v3/calendars'
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
SOURCE = 'https://www.iihf.com/en/events/2026/ww/schedule'
PHASE = {'PRE':'Preliminary round','REL':'Relegation','P9-10':'Placement Round (9–10)','QF':'Quarterfinal','SF':'Semifinal','BMG':'Bronze medal game','GMG':'Gold medal game'}
TEAM = {'AUT':'Austria','CAN':'Canada','CZE':'Czechia','DEN':'Denmark','FIN':'Finland','GER':'Germany','JPN':'Japan','SUI':'Switzerland','SWE':'Sweden','USA':'United States','RL':'Relegation TBD','QF':'Quarterfinal TBD','SF':'Semifinal TBD','L(SF)':'Semifinal losers TBD','W(SF)':'Semifinal winners TBD'}
MARKER = 'iihf2026ww'

def event_id(n):
    # Google Calendar event IDs allow lowercase a-v and 0-9 only.
    return f'iihf2026game{int(n):02d}'

def event_body(game):
    n = int(game['number'])
    start = dt.datetime.fromisoformat(game['date']+'T'+game['time']).replace(tzinfo=ZoneInfo(TIMEZONE))
    end = start + dt.timedelta(hours=2, minutes=30)
    home = TEAM.get(game['home'],game['home'])
    away = TEAM.get(game['away'],game['away'])
    final = game['status'].lower() in ('final','finished','after ot','after so')
    scored = game.get('score_home') is not None and game.get('score_away') is not None
    title = (f'{home} {game["score_home"]} - {game["score_away"]} {away} ({ "Final" if final else "Live" })' if scored else f'{home} vs {away}')
    if game['phase'] != 'PRE':
        title = f'{PHASE.get(game["phase"],game["phase"])}: {title}'
    return {'id':event_id(n),'summary':title,
            'description':f'IIHF 2026 Women\'s World Championship | Game {n} | {PHASE.get(game["phase"],game["phase"])}\nStatus: {game["status"]}\nOfficial results: {SOURCE}',
            'location':f'{game.get("city") or "Denmark"}, Denmark',
            'start':{'dateTime':start.isoformat(),'timeZone':TIMEZONE},
            'end':{'dateTime':end.isoformat(),'timeZone':TIMEZONE},
            'status':'cancelled' if 'cancel' in game['status'].lower() else 'confirmed',
            'extendedProperties':{'private':{'source':MARKER,'gameNumber':str(n)}}}

def is_owned(remote,n):
    return remote.get('extendedProperties',{}).get('private',{}).get('source') == MARKER and remote.get('extendedProperties',{}).get('private',{}).get('gameNumber') == str(n)

def check_response(response):
    if response.status_code >= 400:
        raise RuntimeError(f'Google Calendar API HTTP {response.status_code}: {response.text[:500]}')
    return response.json() if response.content else {}

def sync(session, calendar_id, games, dry_run=True):
    from urllib.parse import quote
    endpoint = f'{BASE}/{quote(calendar_id,safe="")}/events'
    actions = []
    if len(games) != 29 or {str(i) for i in range(1,30)} != set(games):
        raise ValueError('Expected exactly 29 numbered IIHF games; refusing partial sync')
    for n in range(1,30):
        body = event_body(games[str(n)])
        url = endpoint+'/'+event_id(n)
        r = session.get(url,timeout=30)
        if r.status_code == 404:
            actions.append(('create',n))
            if not dry_run:
                check_response(session.post(endpoint,json=body,timeout=30))
        else:
            remote = check_response(r)
            if not is_owned(remote,n):
                raise RuntimeError(f'Event ID collision or unowned event for game {n}; refusing overwrite')
            keys = ('summary','description','location','start','end','status')
            if any(remote.get(k) != body[k] for k in keys):
                actions.append(('update',n))
                if not dry_run:
                    patch = {k:body[k] for k in keys}
                    check_response(session.patch(url,json=patch,timeout=30))
    return actions

def main():
    calendar_id = os.environ['GOOGLE_CALENDAR_ID']
    info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_info(info,scopes=SCOPES)
    session = AuthorizedSession(creds)
    games = json.loads((ROOT/'docs'/'games.json').read_text(encoding='utf-8'))
    dry_run = os.getenv('GOOGLE_SYNC_DRY_RUN','true').lower() != 'false'
    actions = sync(session,calendar_id,games,dry_run=dry_run)
    print(f'{"DRY RUN" if dry_run else "SYNC"}: {len(actions)} changes; '+', '.join(f'{a} #{n}' for a,n in actions))
    print('No deletions performed. Google controls downstream sharing and refresh.')

if __name__=='__main__':
    main()
