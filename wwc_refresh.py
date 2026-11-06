"""Determine when a WWC score refresh is warranted. No external writes."""
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
UTC = dt.timezone.utc


def read_games(path):
    if not Path(path).exists():
        return []
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    return list(data.values()) if isinstance(data, dict) else data


def game_window(game, timezone, now):
    if game.get('status', '').lower() in ('final', 'finished', 'cancelled', 'canceled'):
        return False
    start = dt.datetime.fromisoformat(game['date'] + 'T' + game['time']).replace(tzinfo=ZoneInfo(timezone)).astimezone(UTC)
    return start - dt.timedelta(hours=1) <= now <= start + dt.timedelta(hours=5)


def should_poll(games, timezone, now):
    return any(game_window(g, timezone, now) for g in games)


def should_enable_today(games, timezone, now):
    # Enable fast workflow the day before a game to tolerate GitHub schedule delays.
    local = now.astimezone(ZoneInfo(timezone)).date()
    for g in games:
        if g.get('status', '').lower() in ('final', 'finished', 'cancelled', 'canceled'):
            continue
        date = dt.date.fromisoformat(g['date'])
        if local - dt.timedelta(days=1) <= date <= local + dt.timedelta(days=1):
            return True
    return False


def load_all_games():
    sources = [(ROOT / 'docs' / 'games.json', 'Europe/Copenhagen')]
    # Future years can be added after their verified local time zones are configured.
    config = ROOT / 'wwc_future_config.json'
    if config.exists():
        zones = json.loads(config.read_text(encoding='utf-8')).get('timezones', {})
        for year, tz in zones.items():
            sources.append((ROOT / 'docs' / 'wwc' / str(year) / 'games.json', tz))
    return [(read_games(path), tz) for path, tz in sources if path.exists()]


def main():
    now = dt.datetime.now(UTC)
    mode = os.environ.get('WWC_REFRESH_MODE', 'poll')
    sources = load_all_games()
    decision = any((should_enable_today if mode == 'enable' else should_poll)(games, tz, now) for games, tz in sources)
    print(f'{mode}: {"yes" if decision else "no"}; sources={len(sources)}')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as f:
            f.write(f'active={str(decision).lower()}\n')

if __name__ == '__main__':
    main()
