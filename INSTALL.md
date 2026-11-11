# WWC refresh – deployment package

Source baseline: user-provided `iihf-calendar-main.zip` (Nov 10, 2026). This ZIP is an overlay: upload its file contents to the matching repository paths. It does NOT include or overwrite your current calendar data, Google secrets, or existing event IDs.

## Changes
- 15-minute pregame window; fast monitoring until 12 hours after scheduled start for unfinished games.
- New hourly recovery workflow. It checks an unfinished game only when due: hourly after 12 hours, every six hours after 24 hours, and daily after 72 hours. A successful recovery check is persisted in `docs/wwc_refresh_state.json`.
- Existing daily controller remains unchanged. It enables fast workflow near games and disables it after the fast window.
- Shared concurrency group for fast, recovery, and manual update workflows; no new Google event IDs or deletions.
- Protects Final status and score from being overwritten by stale nonfinal upstream records. Verified Final score corrections remain allowed.

## Before installing
1. Back up the current repository (GitHub Code > Download ZIP) and save its current commit SHA.
2. Set `GOOGLE_SYNC_DRY_RUN=true` under Settings > Secrets and variables > Actions > Variables. The original 2026 manual update also respects this variable.
3. Upload the patch files to the exact paths. Do NOT upload the whole ZIP as a file, and do NOT replace `docs/games.json`, `docs/calendar.ics`, `google_calendar_sync.py`, `games.json`, or credentials.
4. Leave `.github/workflows/wwc-refresh-controller.yml` unchanged. The new logic in `wwc_refresh.py` controls its decision.
5. Run `python -m unittest discover -s tests` and `python -m unittest test_google_sync` locally if desired. The packaged tests were run before delivery.

## Preview verification
1. Run `WWC result recovery` manually from Actions. Inspect `recovery: yes/no` and if yes, `DRY RUN: ... update #...`. Expect **no unexpected create actions**. A recovery run may be `no` if no game is due.
2. Run `WWC fast scores` manually during a game window. Inspect `poll: yes/no`, and any `DRY RUN` updates.
3. Run `WWC refresh controller` manually. Check its enable/disable decision; controller does change GitHub workflow enabled state even while Google dry-run is on.
4. Check that the `docs/wwc_refresh_state.json` file appears after a successful recovery check. Check the GitHub commit for the state file.
5. After reviewing expected updates, set `GOOGLE_SYNC_DRY_RUN=false` and run a single approved live workflow. Verify the Google Calendar has no duplicate events and scores match IIHF.

## Rollback
- Restore previous versions of the six production files from your saved GitHub commit, and remove `.github/workflows/wwc-recovery.yml`.
- Do not delete `docs/games.json`, Google Calendar events, or service-account secrets.
- You can leave `docs/wwc_refresh_state.json` in place; it is not an event record.

## Limitations
- GitHub Actions schedules may be delayed or skipped. This patch improves polling decisions but does not guarantee five-minute updates.
- The hourly recovery workflow still starts hourly even when there are no active games, but exits quickly without external calls when nothing is due.
- The current `calendar_feed.py` and `google_calendar_sync.py` are specific to 2026. **Monthly discovery and future WWC auto-creation are not part of this deployment**. Do not assume future-year calendar sync works yet.
- An IIHF source layout change can cause fail-closed parsing. No live GitHub/Google API deployment tests were performed.
- A postponed game with a changed start time is followed after the official parser publishes the revised schedule; the fast path skips records explicitly marked Postponed.
