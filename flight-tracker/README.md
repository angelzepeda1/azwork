# flight-tracker

A general-purpose fare watcher. Add any route/date to `watches.json` and the
`flight-price-watch` skill (in `../Scheduled/flight-price-watch/SKILL.md`) checks it on a
schedule, tracks price history, and texts you when the price drops enough to matter.

## Files

- `watches.json` — the list of routes being watched. Add a new object to the array to
  track another trip. Set `enabled: false` to pause one without deleting it.
- `price-history.json` — one array per watch id, appended to on every run. This is how
  "drop from last check" gets computed, and how real 5-week/N-week high/low will exist
  once enough runs have accumulated.

## watches.json fields

| Field | Meaning |
|---|---|
| `id` | Stable identifier — also the key in `price-history.json`. Don't change once created. |
| `label` | Human-readable description for messages/logs. |
| `origin` / `destination` | IATA airport codes. |
| `departure_date` / `return_date` | `YYYY-MM-DD`. Omit `return_date` for a one-way watch. |
| `passengers`, `cabin_class` | Passed straight to Otto Travel's flight search. |
| `alert_type` | `"percent"` or `"amount"`. |
| `alert_threshold` | Number — e.g. `10` for percent means "alert on a 10%+ drop from the last check"; for amount, a dollar figure. |
| `recipient` | Phone number/contact the iMessage alert goes to. |
| `enabled` | Set `false` to pause a watch without removing its history. |

## How it runs

Every check needs a real macOS Messages.app session to send iMessage, so this runs as a
**local** launchd job (`~/Library/LaunchAgents/com.angelzepeda.flight-price-watch.plist`),
not a cloud routine — cloud sandboxes can't send iMessages. See the skill file for the
full step-by-step.

## Otto Travel quota note

Otto Travel search is capped at 20 searches/day on this account. At a 6-hour check
interval, each watch uses ~4 searches/day — leaves room for a few more watches, but don't
add so many that 6-hourly checks blow past 20/day total.
