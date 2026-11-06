# WWC adaptive score refresh – review package

**Not deployed.** Adds game-day-aware polling to `mimirox6/iihf-calendar` without replacing the existing 2026 scripts or touching Google Calendar during installation. Six local unit tests passed. GitHub API, IIHF live fetch, and Google API writes have not been end-to-end tested.

## Included

- `wwc_refresh.py`: decides whether the current time falls within a game window using `docs/games.json` and `Europe/Copenhagen` for the existing 2026 tournament. Future-year files are supported at `docs/wwc/YYYY/games.json` only when their verified time zones are entered in `wwc_future_config.json`.
- `.github/workflows/wwc-refresh-controller.yml`: runs once per day, enabling the fast workflow near game days and disabling it otherwise.
- `.github/workflows/wwc-fast-scores.yml`: when enabled, starts every five minutes, checks for active game windows, and only then runs the existing IIHF parser and Google sync. It commits refreshed `docs` files when changed.
- `tests/test_wwc_refresh.py`: six local timing tests.

## What it does and doesn't do

The controller checks daily. It enables fast polling from the day before through the day after scheduled unfinished games. The fast workflow only fetches scores from one hour before a scheduled game until five hours afterward, stopping sooner if the stored game status becomes Final. This is a conservative **time-window approximation**, not a direct live-status probe. Very long delays, overtime beyond the window, or missing Final status may require an additional catch-up run. GitHub Actions can delay or skip scheduled runs. It may not refresh at five-minute intervals exactly.

**Monthly discovery is not implemented in this patch.** Future WWC tournament discovery remains a separate preview-only feature, and its outputs must be connected to the documented future-year file path and a verified venue time zone before this scheduler can poll those games. The current `update.yml` still runs every 30 minutes unless its schedule is explicitly removed during the approved migration.

## Review and installation checklist (approval required)

1. **Do not upload yet** until you approve replacing the existing schedule. Review this package first.
2. Back up `.github/workflows/update.yml`. Keep its `workflow_dispatch` trigger, but remove its `schedule` trigger **only after** the new workflows have been tested. Otherwise the old 30-minute checks will continue. Keep the original workflow available for manual recovery.
3. Add the three code/workflow files at their exact relative paths and add the test file. Do not overwrite `calendar_feed.py`, `google_calendar_sync.py`, `docs/games.json`, or `docs/calendar.ics`.
4. Set `GOOGLE_SYNC_DRY_RUN=true` before any test runs. Confirm existing `GOOGLE_CALENDAR_ID` and `GOOGLE_SERVICE_ACCOUNT_JSON` secrets remain configured; do not copy credentials into source files.
5. Run `python -m unittest discover -s tests -p 'test_wwc_refresh.py' -v` and manually run **WWC refresh controller**. Check whether the fast workflow was enabled/disabled as expected. Repository policy must allow `GITHUB_TOKEN` to use `actions: write` for enabling/disabling workflows.
6. Manually run **WWC fast scores** during a known game window and inspect its output in dry-run mode. Confirm existing Google events are proposed as updates, not creations. Outside a window it should skip the fetch entirely.
7. Once approved, set `GOOGLE_SYNC_DRY_RUN=false`, verify one real sync, and remove the old 30-minute cron schedule from `update.yml`. Do not disable the old workflow entirely; retain manual recovery.
8. Monitor the first real game day and the next idle day to verify that the controller correctly manages the fast workflow. If a controller run fails, inspect GitHub Actions rather than assuming the fast workflow has been disabled.

## Important cautions

- The controller can change the enabled/disabled state of the **new fast workflow**, not the Google Calendar. It does not disable itself.
- If the new fast workflow is disabled, manually starting it may first require enabling it through GitHub's Actions UI.
- Two concurrent sync workflows can race; avoid running the old scheduled workflow and new fast workflow simultaneously. The fast workflow has its own concurrency group, but the original workflow does not share that group.
- No automatic deletions are implemented here. Existing stable Google event IDs are controlled by the unchanged `google_calendar_sync.py`.
- GitHub private-repository Actions minutes and scheduling delays depend on your plan and service load.
