# IIHF 2026 Women's World Championship - Live Calendar

An **unofficial** 29-game iCalendar feed, backed by the IIHF Hydra statistics schedule. It updates start times, teams (including playoff matchups), statuses and final scores when those fields appear in the official source. Event IDs remain stable by IIHF game number.

## Set up on GitHub (free)

1. Create a **public** GitHub repository, e.g. `iihf-womens-calendar`.
2. Upload the **contents** of this folder to the repository root, including `.github/workflows/update.yml`.
3. In **Settings → Actions → General → Workflow permissions**, choose **Read and write permissions** and save. (Some organizations restrict this.)
4. In **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/docs`, then save.
5. In **Actions → Update IIHF calendar**, choose **Run workflow**. Check that it completes successfully.
6. Wait for GitHub Pages to publish. The subscription URL is:
   `https://YOUR-USERNAME.github.io/iihf-womens-calendar/calendar.ics`
   Replace both the username and repo name if yours differs.
7. Verify that `calendar.ics` loads and shows 29 `VEVENT` entries.

The scheduled workflow attempts updates every 30 minutes; GitHub Actions schedules are best-effort and can be delayed. A source parsing error fails the workflow rather than silently replacing correct data. Check Actions for failures. GitHub Pages propagation and client refresh add further delay.

## Subscribe (do not import if you want updates)

- **Google Calendar (desktop web):** Other calendars → + → From URL → paste the HTTPS `.ics` link → Add calendar. Google determines its own refresh frequency.
- **Outlook on the web:** Calendar → Add calendar → Subscribe from web → paste the HTTPS `.ics` link → Import/Save. Menu wording may vary by Outlook version.
- **Apple Calendar (Mac):** File → New Calendar Subscription → paste the HTTPS `.ics` link → choose refresh interval.
- **iPhone/iPad:** Settings → Apps → Calendar → Calendar Accounts → Add Account → Other → Add Subscribed Calendar (menu path varies by iOS version).

Use the HTTPS URL for subscriptions; downloading/importing `calendar.ics` once creates a static copy.

## Technical details

- Game dates and times are preserved as **Denmark local time (`Europe/Copenhagen`)** in the ICS, with a `VTIMEZONE` definition for portability. Calendar applications generally display these events in each subscriber’s local time zone automatically. In November 2026 Denmark observes CET (UTC+1).
- Events are allocated 2.5 hours; IIHF schedule supplies start times, not guaranteed end times.
- `UID` is fixed for each of games 1-29, so playoff placeholders can become actual team matchups.
- Final scores are placed in the event title **only if the official source explicitly supplies a score and final status**. The parser deliberately does not treat `0-0` placeholders as results.
- The parser depends on the current structure of IIHF's public Hydra HTML. If the site changes, updates will stop and require a parser adjustment. The code does not use an official documented API.
- The initial `docs/calendar.ics` is a static seed. The feed becomes auto-updating **only after you host it and enable the workflow**.
- Tournament is November 6-16, 2026. You can disable the workflow after results are final.

## Local checks

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python calendar_feed.py --offline  # regenerate from saved games.json
python calendar_feed.py            # fetch and validate IIHF live data
```

This is not affiliated with IIHF. Follow IIHF's website access rules and keep polling reasonable.
