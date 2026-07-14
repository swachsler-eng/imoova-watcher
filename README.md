# Imoova Relocation Watcher

Checks https://www.imoova.com/relocations/table/usa a few times a day and
emails you when a listing shows up for a city you're watching. Free to run
using GitHub Actions.

## One-time setup (about 10 minutes)

### 1. Create a Gmail "app password" (this is what lets the script send email as you)
1. Go to https://myaccount.google.com/security
2. Turn on **2-Step Verification** if it isn't already on (required for app passwords).
3. Go to https://myaccount.google.com/apppasswords
4. Create a new app password (name it anything, e.g. "imoova-watcher").
5. Copy the 16-character password it gives you — you'll need it in step 3 below.

You can use your normal Gmail address, or make a free throwaway Gmail account
just for this if you'd rather not use your main one.

### 2. Put this code in a GitHub repo
1. Create a free GitHub account if you don't have one: https://github.com/signup
2. Create a new **private** repository (e.g. "imoova-watcher").
3. Upload all the files in this folder to that repo (drag-and-drop works fine
   on github.com, or use `git push` if you're comfortable with git).

### 3. Add your secrets to the repo
In your new repo: **Settings → Secrets and variables → Actions → New repository secret**
Add two secrets:
- `GMAIL_ADDRESS` → the Gmail address from step 1
- `GMAIL_APP_PASSWORD` → the 16-character app password from step 1

### 4. Edit your filters
Open `watcher.py` and fill in `DELIVER_AFTER_DATE`, `MIN_DAYS`, and
`TO_EMAIL` near the top, e.g.:

```python
DELIVER_AFTER_DATE = date(2026, 8, 2)   # only alert if Deliver date is after this
MIN_DAYS = 6                             # only alert if rental is at least this many days

TO_EMAIL = "yourname@gmail.com"
```

A listing only triggers an alert if **both** conditions are true — Deliver
date after `DELIVER_AFTER_DATE`, and at least `MIN_DAYS` rental days (using
just the first number when the site shows something like "6 + 1"). Fuel
refund status is shown in the email for every match, but doesn't filter
anything.

Commit/save the change. That's it — the workflow in
`.github/workflows/watch.yml` will now run automatically on your schedule
and email you when a new matching listing appears. It only emails about
*new* listings it hasn't seen before, so you won't get repeat alerts for
the same one.

## Testing it right now (don't want to wait for the schedule)
In your repo, go to the **Actions** tab → click "Imoova Watcher" on the left →
click **Run workflow** → **Run workflow**. It'll run within a minute or two;
click into the run to see the logs (it prints what it found either way).

## Adjusting the schedule
Edit the `cron:` lines in `.github/workflows/watch.yml`. Cron times are in
UTC. Each `cron:` line is one run time per day.

## Notes / limits
- This relies on the site's HTML structure staying roughly the same. If
  Imoova redesigns the page, the script may need small tweaks — if it ever
  stops finding listings, that's the most likely cause and I can help fix it.
- GitHub Actions' free tier is generous (2,000 minutes/month for private
  repos) — this script takes seconds per run, so 3x/day is nowhere close to
  the limit.

