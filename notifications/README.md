# notifications

Shared credentials for any scheduled skill (local or cloud) that needs to actually notify
Angel — as opposed to just logging or leaving a draft.

## telegram.json

A personal Telegram bot ("Porky", @Terminator4000bot) that only messages Angel's own chat.
Any skill can send a message with a single `curl` call, no MCP server or extra auth needed:

```bash
BOT_TOKEN=$(python3 -c "import json;print(json.load(open('notifications/telegram.json'))['bot_token'])")
CHAT_ID=$(python3 -c "import json;print(json.load(open('notifications/telegram.json'))['chat_id'])")
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "text=Your message here"
```

Works identically from a local shell or a cloud routine — it's a plain HTTPS call, not a
local-only integration like iMessage.

**This file is git-tracked and contains a live bot token.** That's a deliberate tradeoff
(chosen over gitignoring it) so cloud routines — which work off a fresh clone with no other
way to receive secrets — can use it too. If this repo is ever made public, revoke and
regenerate the token first (via BotFather → `/mybots` → this bot → API Token → Revoke).

## Why Telegram over Quo SMS or Gmail

- Quo's `send-message` MCP tool was hitting an unresolved "API key required or invalid"
  error as of 2026-07-12 — reads (messages/calls/contacts) worked, sending did not.
- Gmail's connector only exposes `create_draft`, not an actual send.
- A Telegram bot sends for real, works from anywhere, and has no account-approval process.
