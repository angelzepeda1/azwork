#!/usr/bin/env python3
"""Poll the personal Telegram bot for new messages from Angel, answer via a headless
Claude Code call, and reply. Run every ~60s by com.angelzepeda.telegram-bot-poller.plist."""
import json
import os
import subprocess

ROOT = "/Users/angelzepeda/Documents/Claude/Projects/Personal Tasks"
CLAUDE_BIN = "/Users/angelzepeda/.local/bin/claude"
STATE_FILE = os.path.join(ROOT, "notifications/telegram-last-update.txt")

with open(os.path.join(ROOT, "notifications/telegram.json")) as f:
    config = json.load(f)
BOT_TOKEN = config["bot_token"]
CHAT_ID = str(config["chat_id"])


def api(method, **params):
    # Shells out to curl rather than urllib — this machine's Python SSL trust
    # store rejects a cert in the chain that curl (via the system keychain) accepts.
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    args = ["curl", "-s", "-X", "POST", url]
    for k, v in params.items():
        args += ["--data-urlencode", f"{k}={v}"]
    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    return json.loads(result.stdout)


def get_last_id():
    if os.path.exists(STATE_FILE):
        content = open(STATE_FILE).read().strip()
        return int(content) if content else 0
    return 0


def save_last_id(uid):
    with open(STATE_FILE, "w") as f:
        f.write(str(uid))


def send(text):
    # Telegram caps a single message at 4096 chars
    for i in range(0, max(len(text), 1), 3900):
        api("sendMessage", chat_id=CHAT_ID, text=text[i:i + 3900])


def main():
    last_id = get_last_id()
    resp = api("getUpdates", offset=last_id + 1, timeout=0)
    for update in resp.get("result", []):
        uid = update["update_id"]
        if uid > last_id:
            last_id = uid
        msg = update.get("message", {})
        if str(msg.get("chat", {}).get("id")) != CHAT_ID:
            continue  # only ever respond to the owner's own chat
        text = msg.get("text")
        if not text:
            continue
        try:
            result = subprocess.run(
                [CLAUDE_BIN, "-p", text,
                 "--allowedTools", "Bash Read Write Edit Glob Grep",
                 "--permission-mode", "acceptEdits"],
                cwd=ROOT, capture_output=True, text=True, timeout=170,
            )
            reply = (result.stdout or "").strip() or "(no output)"
        except subprocess.TimeoutExpired:
            reply = "That took too long and timed out (>170s)."
        except Exception as e:
            reply = f"Error running that: {e}"
        send(reply)
    save_last_id(last_id)


if __name__ == "__main__":
    main()
