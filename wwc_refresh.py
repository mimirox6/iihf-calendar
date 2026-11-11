"""WWC game-window and recovery decisions. No network calls or calendar writes."""
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
UTC = dt.timezone.utc
FINAL = {'final','finished','after ot','after so','cancelled','canceled'}
STATE = ROOT / 'docs' / 'wwc_refresh_state.json'

def read_games(path):
    if not Path(path).exists(): return []
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    return list(data.values()) if isinstance(data, dict) else data

def start_time(game, timezone):
    return dt.datetime.fromisoformat(game['date']+'T'+game['time']).replace(tzinfo=ZoneInfo(timezone)).astimezone(UTC)

def unfinished(game):
    return str(game.get('status','')).strip().lower() not in FINAL

def game_key(game):
    return str(game.get('date','')[:4])+':'+str(game.get('number',''))

def fast_window(game, timezone, now):
    if not unfinished(game) or str(game.get('status','')).lower() == 'postponed': return False
    start = start_time(game, timezone)
    return start-dt.timedelta(minutes=15) <= now < start+dt.timedelta(hours=12)

def game_window(game, timezone, now):
    return fast_window(game, timezone, now)

def should_poll(games, timezone, now):
    return any(fast_window(g,timezone,now) for g in games)

def should_enable_today(games, timezone, now):
    # Keep the fast workflow enabled from the day before until the last fast window ends.
    for g in games:
        if not unfinished(g) or str(g.get('status','')).lower() == 'postponed': continue
        start = start_time(g,timezone)
        if start-dt.timedelta(days=1) <= now < start+dt.timedelta(hours=12): return True
    return False

def recovery_interval(age):
    if age < dt.timedelta(hours=12): return None
    if age < dt.timedelta(hours=24): return dt.timedelta(hours=1)
    if age < dt.timedelta(hours=72): return dt.timedelta(hours=6)
    return dt.timedelta(days=1)

def due_recovery(games, timezone, now, state):
    for g in games:
        if not unfinished(g): continue
        age = now-start_time(g,timezone)
        interval = recovery_interval(age)
        if interval is None: continue
        last = state.get(game_key(g))
        if not last: return True
        try: checked = dt.datetime.fromisoformat(last.replace('Z','+00:00'))
        except (ValueError,TypeError): return True
        if checked.tzinfo is None or now-checked >= interval: return True
    return False

def load_all_games():
    sources = [(ROOT/'docs'/'games.json','Europe/Copenhagen')]
    config = ROOT/'wwc_future_config.json'
    if config.exists():
        zones = json.loads(config.read_text(encoding='utf-8')).get('timezones',{})
        for year,tz in zones.items(): sources.append((ROOT/'docs'/'wwc'/str(year)/'games.json',tz))
    return [(read_games(path),tz) for path,tz in sources if path.exists()]

def read_state():
    return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}

def mark_success(sources, now, mode):
    # Record checks only for games eligible in the successful run.
    state = read_state()
    for games,tz in sources:
        for g in games:
            if (fast_window(g,tz,now) if mode == 'fast' else recovery_interval(now-start_time(g,tz)) is not None and unfinished(g)):
                state[game_key(g)] = now.isoformat()
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def main():
    now = dt.datetime.now(UTC)
    mode = os.getenv('WWC_REFRESH_MODE','poll')
    sources = load_all_games()
    if mode == 'mark-success':
        mark_success(sources,now,os.getenv('WWC_CHECK_KIND','fast'))
        print('Recorded successful check timestamps'); return
    state = read_state()
    if mode == 'enable': decision = any(should_enable_today(g,tz,now) for g,tz in sources)
    elif mode == 'recovery': decision = any(due_recovery(g,tz,now,state) for g,tz in sources)
    else: decision = any(should_poll(g,tz,now) for g,tz in sources)
    print(f'{mode}: {"yes" if decision else "no"}; sources={len(sources)}')
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f: f.write(f'active={str(decision).lower()}\n')

if __name__ == '__main__': main()
