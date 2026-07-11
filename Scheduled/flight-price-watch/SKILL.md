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
  what most fare trackers quote as "the price." Record it as `current_price` and note its
  `cabin` value.
- Also run the same query with `AND fo.cabin != 'BASIC'` to get the cheapest standard-Economy
  fare — record as `alt_price` (used only for display on the dashboard, not for alert math).
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

## Step 6 — Record this check
Regardless of whether an alert fired, append `{ "checked_at": <UTC ISO timestamp now>,
"price": current_price, "cabin": <cabin from Step 2> }` to this watch's array in
`flight-tracker/price-history.json` and write the file back. Do this even for the
baseline-only first run. Do this for every watch BEFORE moving to Step 7, so the chart
rebuild below always reads fresh data.

## Step 7 — Regenerate and republish the chart page
`flight-tracker/index.html` embeds its own data in a `<script>` block as a `HISTORY` object
(one entry per watch id, each `{ label, color, cabinCurrent, points: [{t, p}, ...] }`),
plus an `ALT_PRICE` map and a `ROUTE_LABEL` map. All the layout/chart-drawing JS in that
file is generic — it re-derives axes, the line, dots, end-labels, and the table purely from
whatever is in `HISTORY`, so you only need to edit the embedded data, never the drawing code:
- For each watch, set `HISTORY[id].points` to the FULL array now in
  `flight-tracker/price-history.json` for that id (not just today's point — the chart plots
  the whole history every time).
- Update `HISTORY[id].cabinCurrent` to today's `cabin` from Step 2, and `ALT_PRICE[id]` to
  today's `alt_price`.
- `ROUTE_LABEL` only needs an entry when a new watch is added (it holds the human-readable
  departure/return date strings shown on the boarding-pass card) — leave existing entries
  alone.
- Do not touch the `<style>`, the SVG chart-building script, or any layout markup — only the
  `HISTORY` / `ALT_PRICE` / `ROUTE_LABEL` data at the top of the `<script>` block at the
  bottom of the file.
- Write the file back to `flight-tracker/index.html`.

Read the saved URL from `flight-tracker/ARTIFACT_URL.txt`. Call the Artifact tool with
`file_path` set to `flight-tracker/index.html` and `url` set to that saved URL, so it
redeploys in place. (Only omit `url` if that file is missing/empty — a first-time publish —
in which case save the newly returned URL back to that file.)

## Step 8 — Report
If running interactively, give a one-line summary per watch (current price, change since
last check, alert sent or not) plus the dashboard link. If any watch's search failed this
run, mention it. This runs unattended most of the time — there is no chat to post to when
launchd fires it, so this summary is for the log file / a manual test run.
