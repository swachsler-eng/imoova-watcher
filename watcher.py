"""
Imoova relocation watcher.

Scrapes https://www.imoova.com/relocations/table/usa , filters listings
by the cities you care about (matching either the "From" or "To" column),
and emails you when a NEW matching listing shows up (it won't re-email
you about the same listing twice).

HOW TO USE
----------
1. Edit the CONFIG section below (your cities, and your email address).
2. Set two GitHub repo secrets (see README.md) so the script can send email:
     GMAIL_ADDRESS   - the gmail account sending the alert
     GMAIL_APP_PASSWORD - a 16-character Gmail "app password" (not your real password)
3. GitHub Actions runs this automatically on a schedule (see .github/workflows/watch.yml)
"""

import json
import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ======================= CONFIG - EDIT THIS PART =======================

# Cities you want to be alerted about. Matching is case-insensitive and
# matches if the city name appears in either the "From" or "To" column.
# Example: ["Denver", "Salt Lake City", "Chicago"]
WATCH_CITIES = [
    # "Denver",
    # "Chicago",
]

# Where to send the alert email
TO_EMAIL = "you@example.com"

# The page we're watching
URL = "https://www.imoova.com/relocations/table/usa"

# File used to remember which listings we've already alerted on,
# so we don't email you about the same one every run.
SEEN_FILE = Path(__file__).parent / "seen_listings.json"

# =========================================================================


def fetch_listings():
    resp = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ImoovaWatcher/1.0)"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if table is None:
        raise RuntimeError("Could not find a table on the page — site layout may have changed.")

    # Map header name -> column index, so this survives minor layout changes
    header_cells = table.find("thead").find_all("th") if table.find("thead") else table.find_all("th")
    headers = [h.get_text(strip=True).lower() for h in header_cells]

    def col(name):
        for i, h in enumerate(headers):
            if name in h:
                return i
        return None

    idx_ref = col("ref")
    idx_from = col("from")
    idx_to = col("to")
    idx_depart = col("depart")
    idx_deliver = col("deliver")
    idx_vehicle = col("vehicle")

    body = table.find("tbody") or table
    rows = body.find_all("tr")

    listings = []
    for row in rows:
        cells = row.find_all("td")
        if not cells or len(cells) < 3:
            continue

        def cell_text(i):
            if i is None or i >= len(cells):
                return ""
            return cells[i].get_text(strip=True)

        link_tag = row.find("a", href=True)
        link = link_tag["href"] if link_tag else ""
        if link and link.startswith("/"):
            link = "https://www.imoova.com" + link

        ref = cell_text(idx_ref) or (link_tag.get_text(strip=True) if link_tag else "")
        from_city = cell_text(idx_from)
        to_city = cell_text(idx_to)
        depart = cell_text(idx_depart)
        deliver = cell_text(idx_deliver)
        vehicle = cell_text(idx_vehicle)

        if not ref or not from_city:
            continue

        listings.append(
            {
                "ref": ref,
                "from": from_city,
                "to": to_city,
                "depart": depart,
                "deliver": deliver,
                "vehicle": vehicle,
                "link": link,
            }
        )

    return listings


def matches_watch_list(listing):
    if not WATCH_CITIES:
        return False
    from_l = listing["from"].lower()
    to_l = listing["to"].lower()
    for city in WATCH_CITIES:
        c = city.lower().strip()
        if c and (c in from_l or c in to_l):
            return True
    return False


def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(sorted(seen)))


def send_email(new_matches):
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_app_password:
        print("GMAIL_ADDRESS / GMAIL_APP_PASSWORD not set — skipping email, printing instead:")
        for m in new_matches:
            print(m)
        return

    lines = []
    for m in new_matches:
        lines.append(
            f"{m['from']} -> {m['to']}  |  Depart: {m['depart']}  Deliver by: {m['deliver']}\n"
            f"Vehicle: {m['vehicle']}\n"
            f"{m['link']}\n"
        )
    body = "New Imoova relocation listings matching your cities:\n\n" + "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = f"Imoova: {len(new_matches)} new matching listing(s)"
    msg["From"] = gmail_address
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.sendmail(gmail_address, [TO_EMAIL], msg.as_string())

    print(f"Emailed {len(new_matches)} new match(es) to {TO_EMAIL}")


def main():
    if not WATCH_CITIES:
        print("WATCH_CITIES is empty in watcher.py — nothing to match against. Edit the CONFIG section.")
        sys.exit(0)

    listings = fetch_listings()
    print(f"Fetched {len(listings)} listings from site.")

    seen = load_seen()
    matches = [l for l in listings if matches_watch_list(l)]
    new_matches = [m for m in matches if m["ref"] not in seen]

    print(f"{len(matches)} total matches, {len(new_matches)} are new.")

    if new_matches:
        send_email(new_matches)
        seen.update(m["ref"] for m in new_matches)
        save_seen(seen)
    else:
        print("No new matches this run.")


if __name__ == "__main__":
    main()
