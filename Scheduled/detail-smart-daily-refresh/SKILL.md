---
name: detail-smart-daily-refresh
description: Daily morning refresh of the Detail Smart dashboard — rebuilds full week view each Monday
---

Every morning, pull fresh data for the Detail Smart dashboard and update the artifact + post a brief chat summary.

## Owner preferences (standing — do not deviate without being asked)
- BOOKINGS = Square Appointments calendar ONLY. In weeks where the owner books jobs via invoices instead, the calendar may be empty — that is expected; show 0 bookings rather than substituting invoices.
- REVENUE = COLLECTED ONLY. Count money actually captured. This includes (a) COMPLETED Square orders dated by closed_at, AND (b) MANUAL PAYMENTS noted by the owner in the booking details (see cash/manual rule below). Do NOT count DRAFT/OPEN/quoted invoices or FAILED payment attempts.
- MANUAL-PAYMENT RULE: The owner records off-invoice payments by writing them in the appointment's seller_note (e.g. "paid cash", "paid cash to Abdul", "paid via Venmo", "Zelle", "Cash App"). If a booking has NO matching completed invoice/order but its note indicates it was paid by cash OR any manual method (Venmo, Zelle, Cash App, etc.), mark that appointment PAID (blue chip) and COUNT its price in collected revenue. Use the booking's service-variation price as the amount. Add a short tag in the note like "· paid cash" or "· paid via Venmo". Treat Venmo/Zelle/Cash App the same as cash.
- ALWAYS INCLUDE THE CLIENT'S NAME first in each appointment's notes (resolve customer_id → given_name + family_name via customers.get — method is "get", not "retrieve"). Then service, vehicle, address, detailer, payment tag.
- The dashboard appointment feed must MATCH the Square Appointments calendar exactly (same count, same people). Bucket each booking by its start_at in PT — a 7:00 PM PT appointment has a start_at after midnight UTC, so always compare against the -07:00 week boundaries, not raw UTC dates.
- Always keep the dashboard up to date each run, even if every number is zero (a genuinely quiet week is valid data).
- BACKLOG INTEGRITY: every run also repairs past weeks, not just the current one — see Step 3.5. A "—" placeholder or a null `calls` field on a past week means an earlier run failed partway through; it is not a real value and should never be left standing if it can be filled in.

## Step 0 — Calculate the week window (LA time, UTC-7)
Determine today's date in LA time. Find the most recent Monday (if today IS Monday, that's the start).
- weekStart = this Monday at 00:00:00-07:00 (ISO string)
- weekEnd   = this Sunday at 23:59:59-07:00 (ISO string)
- weekLabel = e.g. "May 18 – May 24, 2026"
- shortLabel = e.g. "May 18–24"

## Step 1 — Square bookings & revenue
A) Bookings (Appointments calendar only) — Call mcp__bbff3468-c4bf-4bf7-850f-0f8418158337__make_api_request:
- service: "bookings", method: "list"
- location_id: "LNBSAEM57WH24"
- start_at_min: weekStart, start_at_max: weekEnd  (full week end, NOT now; window must be ≤ 31 days)
- Keep only bookings with status "ACCEPTED" (exclude CANCELLED_BY_CUSTOMER / CANCELLED_BY_SELLER / DECLINED / NO_SHOW). You may mention notable cancellations in the briefing.
- For EACH accepted booking: resolve client name (customers.get); read seller_note for the vehicle, detailer, and any manual-payment flag (cash/Venmo/Zelle).
- Build the appointment note as: "<given_name> <family_name> · <service/variation> · <vehicle> · <address> · Detailer: <name> · <payment tag if manual>".
- Determine PAID vs ACCEPTED: PAID if there is a matching COMPLETED order (by customer_id) OR the note has a manual-payment flag; otherwise ACCEPTED. Set chip "chip-b" for PAID, "chip-g" for ACCEPTED. Revenue cell = exact paid amount for PAID, "~$price" estimate for ACCEPTED.
- If zero bookings come back, set bookings: 0 and appointments: [].

B) Revenue (COLLECTED ONLY) — Call mcp__bbff3468-c4bf-4bf7-850f-0f8418158337__make_api_request:
- service: "orders", method: "search"
- location_ids: ["LNBSAEM57WH24", "LA6WYZETKKQB1", "LPR49Q5X82EA2", "LZR4WANPF0XA2"]
- query.filter.state_filter.states: ["COMPLETED"]
- query.filter.date_time_filter.closed_at: { start_at: weekStart, end_at: min(weekEnd, now) }   ← filter by CLOSED_AT (payment date), not created_at
- query.sort: { sort_field: "CLOSED_AT", sort_order: "DESC" }
- Only COMPLETED orders; ignore DRAFT/OPEN/CANCELED and FAILED tenders.
- Match each completed order to its booking by customer_id so the appointment shows the real paid amount.
- TOTAL collected revenue = (sum of completed-order total_money/100, includes tips) + (sum of manual/cash-paid booking prices from Step 1A that have no completed order). Avoid double-counting a job that has both an order and a note. orders/paid-job count = number of distinct paid jobs. avgPerJob = total / count (or "—" if 0).

## Step 2 — Quo call stats
Call mcp__c35e4c24-70cb-47bc-9cf8-497397f9bf1c__fetch-call-transcripts:
- inboxPhoneNumber: "+14242168638", createdAfter: weekStart, maxResults: 200
Compute: totalCalls, inbound (direction="incoming"), outbound (direction="outgoing"), missed (duration ≤ 5s or status missed/no-answer), avgDuration "Xm Ys".
If this call fails with an API key error, skip it and keep the last known call stats.

## Step 3 — Google Reviews (via Gmail)
Call mcp__d2143c8c-3939-4b37-8191-472e5a9f5436__search_threads with:
- query: `from:businessprofile-noreply@google.com "left a review" after:YYYY/MM/DD` (Monday of current week, YYYY/MM/DD)
Parse:
- Each matching thread ("[Name] left a review for Detail Smart") = one new review
- newReviewsThisWeek = count; newReviewerNames = first names from subjects
- Keep last known overall rating & total from the dashboard's last WEEKS entry; total += newReviewsThisWeek
- If the Gmail search fails, skip and keep last known review data
Note: Gmail gets a notification from businessprofile-noreply@google.com per new review — most reliable auto-detection.

## Step 3.5 — Backfill incomplete historical weeks
Read the current HTML from `dashboards/detail-smart/index.html` and scan every WEEKS entry EXCEPT the
current (last) one for signs of a failed prior run:
- Square gap: revenue, orders, avgPerJob, or bookings is the placeholder string "—", or apptTag contains
  "unavailable" / "needs re-auth".
- Quo gap: calls is null.
For each incomplete week found, oldest first, cap at 3 weeks per run (bounds runtime; any remainder gets
picked up on a later day — do not try to clear a large backlog in one run):
- Parse that week's own label to reconstruct its weekStart/weekEnd (LA time, UTC-7), the same way Step 0
  does for the current week.
- Re-run Step 1 (Square bookings + revenue) and/or Step 2 (Quo calls), scoped to that historical window,
  for whichever half is missing.
- On success, overwrite ONLY the placeholder/null fields with the real values, rebuild that week's
  appointments array the same way Step 1 does, and clear the "unavailable"/"needs re-auth" note from
  apptTag (reset it to "Square Bookings").
- On failure, leave that week's placeholders untouched (don't invent numbers) and leave apptTag as-is so
  the next run retries it.
- Never touch a past week's `reviews` object — the review count/rating is a cumulative running total
  carried forward day to day, not independently recomputable per week, so already-recorded review data for
  prior weeks is left alone even if you can't verify it.
If any weeks are still incomplete after this run (either skipped due to the 3-week cap, or failed again),
list them by label in the morning briefing's "Heads up:" line so the owner knows the backlog isn't fully
clean yet.

## Step 4 — Rebuild the full dashboard HTML
Update the WEEKS array entry for the current week (the last entry) with all fresh data:
- revenue, orders (paid-job count), avgPerJob, bookings
- calls object (or keep last known if Quo failed)
- appointments array (one entry per accepted booking, CLIENT NAME FIRST, PAID/ACCEPTED set per rule above)
- reviews object: { count: newReviewsThisWeek, rating: lastKnownRating, total: lastKnownTotal + newReviewsThisWeek, names: newReviewerNames }
Also update weekLabel, shortLabel, and the last-updated timestamp at the bottom.
Write the updated HTML back to `dashboards/detail-smart/index.html` in place.

## Step 5 — Republish the Artifact
Read the saved URL from `dashboards/detail-smart/ARTIFACT_URL.txt`. Call the Artifact tool with
`file_path` set to `dashboards/detail-smart/index.html` and `url` set to that saved URL, so it redeploys
in place rather than minting a new link. (Only omit `url` if the file is missing/empty — a first-time
publish — in which case save the newly returned URL back to that file.)

## Step 6 — Post morning briefing
Post:
"☀️ Good morning! Detail Smart — [weekLabel]
• Revenue: $X collected (N paid jobs, avg $X/job)
• Bookings: N confirmed
• Calls: N inbound, N missed (N total), avg Xm Ys
• Google Reviews: N new this week · X ★ overall (N total)

[Open Dashboard](<the saved artifact URL>)"
If any metric is zero, still post it. If there are unpaid/quoted invoices, failed payments, or notable cancellations worth attention, add a one-line "Heads up:" note after the bullets.

## Step 7 — Commit and push
This skill runs in a fresh clone each time, so the local machine only sees today's numbers if they're
pushed. `git add dashboards/detail-smart/index.html dashboards/detail-smart/ARTIFACT_URL.txt`, commit with
a short message like "Daily refresh: [weekLabel]", and push to `origin main`. If the push is rejected
(diverged history), pull --rebase once and retry; do not force-push.