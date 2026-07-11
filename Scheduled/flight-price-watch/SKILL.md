---
name: flight-price-watch
description: Checks every watched flight route/date in flight-tracker/watches.json and iMessages an alert when the price drops enough
---

This runs LOCALLY (launchd), not as a cloud routine — iMessage delivery requires the real
Messages.app on this Mac, which a cloud sandbox does not have.

## Step 1 — Load the watch list
Read `flight-tracker/watches.json` (relative to this project root). Skip any watch with
`enabled: false`. For each remaining watch, do Steps 2–5.

## Step 2 — Get the current lowest price (Otto Travel)
Call `mcp__claude_ai_Otto_Travel__read_skill` with `skill_name: "flight_search"` once per
run (not per watch — the returned `skill_keys` are reusable for every watch this run).
For each watch:
- Call `search_flights` with `origin`, `destination`, `departure_date`, `return_date`
  (omit if the watch has none — one-way), `cabin_class`, and the `skill_keys` from above.
- Poll `task_status` until `status: "completed"`.
- Call `query_flights` on the returned handle:
  `SELECT fo.price, fo.cabin FROM flights f JOIN fare_options fo ON f.physical_flight_key = fo.physical_flight_key WHERE f.leg='outbound' ORDER BY fo.price ASC LIMIT 1`
  For round-trip watches this price is already the combined round-trip total (see
  `price_type='round_trip'` in the schema) — do not add outbound + return separately.
- This is the cheapest bookable fare regardless of cabin (including Basic Economy), matching
  what most fare trackers quote as "the price." Record it as `current_price`.
- If the search errors or returns nothing, skip this watch for this run — do not write a
  fake price, and do not send an alert. Note the failure when posting the summary (Step 6).

## Step 3 — Compare against the last check
Read `flight-tracker/price-history.json`. Look up this watch's `id` array.
- If the array is empty (first-ever check for this watch), there is nothing to compare
  against — this run is a baseline only. No alert, regardless of price.
- Otherwise, `last_price` = the price from the most recent (last) entry in that array.
  Compute the drop `last_price - current_price`.

## Step 4 — Decide whether to alert
Per the watch's `alert_type`:
- `"percent"`: alert if `(last_price - current_price) / last_price * 100 >= alert_threshold`.
- `"amount"`: alert if `last_price - current_price >= alert_threshold`.
Only alert on a genuine drop (current_price < last_price) — a price increase or unchanged
price is never an alert, no matter the math above.

## Step 5 — Send the iMessage (only if Step 4 says to)
Use Bash with `osascript` — no MCP tool needed:
```
osascript -e 'tell application "Messages" to send "MESSAGE_TEXT" to buddy "RECIPIENT" of (service 1 whose service type = iMessage)'
```
Message format: "✈️ Fare drop: [label] is now $[current_price] (was $[last_price], down
[X]% / $[Y]) — [alert_threshold]%/$ threshold hit. Route: [origin]→[destination], depart
[departure_date]" + return date if round-trip.
Substitute the watch's own `recipient` for RECIPIENT. Escape any double quotes in the
message text for the shell.

## Step 6 — Record this check and report
Regardless of whether an alert fired, append `{ "checked_at": <UTC ISO timestamp now>,
"price": current_price, "cabin": <cabin from Step 2> }` to this watch's array in
`flight-tracker/price-history.json` and write the file back. Do this even for the
baseline-only first run.

After all watches are processed, if running interactively, give a one-line summary per
watch (current price, change since last check, alert sent or not). If any watch's search
failed this run, mention it. This runs unattended most of the time — there is no chat to
post to when launchd fires it, so this summary is for the log file / a manual test run.
