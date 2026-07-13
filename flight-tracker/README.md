# flight-tracker

A general-purpose fare watcher. Add any route/date to `watches.json` and the
`flight-price-watch` skill (in `../Scheduled/flight-price-watch/SKILL.md`) checks it on a
schedule, tracks price history, and sends a Telegram message when the price drops enough
to matter.

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
| `enabled` | Set `false` to pause a watch without removing its history. |

There's no per-watch recipient field — alerts go to the single Telegram chat configured in
`../notifications/telegram.json`, shared across every watch.

## How it runs

This runs as a **cloud routine** (via RemoteTrigger, see `claude.ai/code/routines`) — a
fresh clone every 6 hours, no dependency on this Mac being on, awake, or charged. Alerts go
out via a personal Telegram bot (see `../notifications/README.md`) — a plain HTTPS call, no
MCP server or OAuth involved. Quo's SMS `send-message` was tried first but hit an unresolved
"API key required or invalid" error; Gmail was ruled out because its connector can only
create an unsent draft, not actually send. Each run pushes its own changes
(`price-history.json`, `index.html`) back to `origin main`, so pull locally to see the latest.
See the skill file for the full step-by-step.

## Otto Travel quota note

Otto Travel search is capped at 20 searches/day on this account. At a 6-hour check
interval, each watch uses ~4 searches/day — leaves room for a few more watches, but don't
add so many that 6-hourly checks blow past 20/day total.
