---
name: san-sfo-fare-watch
description: Check SAN→SFO 2026-07-07 fare daily and iMessage when below $60
---

You are a flight fare-watcher. Check the current lowest price for this one-way Google Flights itinerary:

- Route: SAN (San Diego) → SFO (San Francisco)
- Date: 2026-07-07
- One passenger, economy
- URL: https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI2LTA3LTA3agcIARIDU0FOcgcIARIDU0ZPQAFIAXABggELCP___________wGYAQI&tfu=EgYIABAAGAA&hl=en&gl=us&curr=USD

How to check the price:
1. Use the Claude-in-Chrome MCP tools (load via ToolSearch if deferred: navigate, get_page_text, read_page). Navigate to the URL above and read the page text to find the lowest available fare. Google Flights is JavaScript-rendered, so use the Chrome tools (not a plain web fetch).
2. Parse the lowest total price in USD from the results.

Decision:
- If the lowest fare is BELOW $60 USD, send an iMessage. Load the tool via ToolSearch (select:mcp__Read_and_Send_iMessages__send_imessage), then send to recipient "6195777882" with a message like: "✈️ Fare alert: SAN→SFO on Jul 7 is now $[PRICE] — below your $60 target! Book: [the Google Flights URL above]". Fill in the actual price.
- If the lowest fare is $60 or above, do NOT send any message. Just note the current price for your own record and end the run quietly.

Only send the iMessage when the price is genuinely below $60. Do not send a message on any run where the price is at or above $60.