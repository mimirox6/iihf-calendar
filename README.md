# IIHF Women's Worlds – Google Calendar sync

This is an **add-on** to your existing `mimirox6/iihf-calendar` repository. It does not replace the IIHF scraper, existing games, or public `.ics` feed.

## Files to upload to the existing repository

- `google_calendar_sync.py` → repository root
- `.github/workflows/update.yml` → **replace** existing file at this path

Do not upload `games.sample.json` or the tests unless you want them for reference. Keep your existing `docs/games.json`, `calendar_feed.py`, and `requirements.txt` unchanged.

## 1. Create a Google Calendar

On a desktop, open Google Calendar → Settings → Add calendar → Create new calendar. Name it `IIHF Women's Worlds 2026`. Initially keep it private. Under that calendar's **Integrate calendar**, copy **Calendar ID** (often ends in `@group.calendar.google.com`).

## 2. Create a Google Cloud service account

1. In Google Cloud Console, create/select a project you control.
2. Enable **Google Calendar API** for that project.
3. Go to **IAM & Admin → Service Accounts** and create a service account (no project-wide roles needed).
4. Open the service account → **Keys → Add key → Create new key → JSON**. Download the JSON securely. Treat it like a password. Google Cloud organization policies may disable service-account key creation; if so, stop rather than weakening policies.
5. Back in Google Calendar, open the new calendar's **Share with specific people or groups** and share it with the service account email (from the JSON `client_email`), granting **Make changes to events**. Do not grant access to your main calendar.

## 3. Add GitHub secrets

Repository → Settings → Secrets and variables → Actions → Secrets → New repository secret:

- `GOOGLE_CALENDAR_ID`: the ID from step 1
- `GOOGLE_SERVICE_ACCOUNT_JSON`: paste the **entire** JSON key file contents, including braces

Never commit the JSON key to GitHub or send it in a screenshot.

Repository → Settings → Secrets and variables → Actions → Variables → New repository variable:

- Name: `GOOGLE_SYNC_DRY_RUN`
- Value: `true`

The sync workflow skips Google entirely if secrets are missing. When secrets exist, it checks the 29 game records and prints what would be created or changed without writing.

## 4. Upload files and test

1. Upload `google_calendar_sync.py` to repository root.
2. Replace `.github/workflows/update.yml` with the supplied version. In GitHub, open that file → pencil icon → replace content → commit.
3. Go to Actions → Update IIHF calendar → Run workflow.
4. Open the **Sync to Google Calendar** step. Expect `DRY RUN: 29 changes` for a new calendar. If it errors, do not enable writes; check service account permissions, calendar ID and API access.
5. Set `GOOGLE_SYNC_DRY_RUN` to `false` under Actions Variables.
6. Run the workflow again. Confirm `SYNC: 29 changes` (create) and verify the 29 games in the new Google Calendar.
7. Run a third time. Expect `SYNC: 0 changes` (unless the official data changed).

## 5. Make the Google Calendar public and share it

After verifying the events, in Google Calendar → Settings → your IIHF calendar → Access permissions for events → Make available to public. Choose **See all event details** if you want everyone to see teams and scores. Google may warn that anyone can find this calendar; confirm only if you're comfortable with that. Under **Integrate calendar**, copy its **Public URL to this calendar** for viewers. If your organization restricts public sharing, you may need to use a personal Google account or retain the public `.ics` link instead.

**Time zone:** Every game uses `Europe/Copenhagen`; Google displays the correct local time for each viewer. Google may take time to refresh displays.

## Safeguards and limitations

- Only the 29 known numbered games are synchronized. If the IIHF parser fails, the existing workflow stops before Google sync.
- The script creates deterministic Google event IDs and updates only events with matching private source markers. It **never deletes events**.
- The first run is read-only by default. An explicit variable change is required to write.
- The GitHub workflow is scheduled every 30 minutes, but GitHub Actions may delay runs. A green run proves execution, not necessarily an IIHF score change.
- Google Calendar service accounts may be restricted by Workspace policies; use an account you control.
- A calendar made public is accessible to anyone with the link and may be indexed.
- Scores update only when the upstream IIHF feed exposes them and the existing parser recognizes them.
