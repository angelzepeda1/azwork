---
name: spending-gut-check
description: Weekly harsh spending gut-check from Copilot data; posts in chat and creates a 9am Monday Google Calendar event with the recommendation in the details.
---

Deliver a harsh, no-sugar-coating weekly "spending gut-check" based on the user's Copilot budgeting app data, then log it to Google Calendar.

STEP 1 — Get the data from Copilot (a native macOS app, accessed via computer-use screen control):
- Call request_access for the app "Copilot" (bundle id com.copilot.production), then open_application "Copilot", then screenshot.
- The app should open without a passcode (the user disabled the in-app lock). If it shows a passcode/Face ID lock screen, or if the Mac is at the login/lock screen, STOP and tell the user: "Copilot (or your Mac) is locked — unlock it and re-run this." Never attempt to enter any passcode or password.
- On the Dashboard, read the "Monthly spending" panel (amount left vs budgeted, and the over/under-pace figure) and the "Top categories" panel (each category's spent amount, budget amount, and over/under status). Zoom in on the Top categories panel to read exact numbers. If useful, also check "Transactions to review" for large or recurring uncategorized charges.

STEP 2 — Write the message. Tone: harsh, direct, accountability-driven — like a blunt friend who's tired of excuses. Ask pointed "why did you spend so much on X?" questions. BUT stay factually honest: only call out categories that are actually over budget or above peer norms. If a category is disciplined, say so plainly rather than inventing a problem. Never fabricate numbers — use only what's on screen.
Benchmark against mid-20s / Gen Z U.S. peer averages: restaurants/dining ~$572/mo, entertainment ~$284/mo, travel ~$883/mo (sporadic). Use these for comparison and call out where the user exceeds their OWN budget (the sharpest critique) and where they exceed peers.
Format: exactly three short bullets, each = one category, a dollar figure, and a single sub-5-minute action or pointed question. Then one closing line naming the overall pattern (e.g. budgets set too loose so "under budget" is meaningless). Keep it tight — no preamble, no postamble. Lead with the worst offender.

STEP 3 — Output the message directly in chat.

STEP 4 — Create a Google Calendar event with the recommendation in the details, using the create_event tool (mcp__3e5cf226-330e-47bd-b8b2-b24b52116a6f__create_event):
- summary: "Weekly Budget Gut-Check"
- Determine TODAY's date at runtime (the task runs Monday morning). Set startTime to today at 09:00:00 and endTime to today at 09:30:00, local time.
- timeZone: "America/Los_Angeles"
- calendarId: "angelzepeda.1010@gmail.com" (the user's primary calendar)
- description: the FULL gut-check message from Step 2 (the three bullets plus the closing line). This is the key part — the recommendation must live in the event's details/description field.
- Do not add any attendees (this is a personal reminder, not a meeting invite).
After creating it, confirm to the user in chat that the event was added for 9am today.

Do not move money, change anything in Copilot, or take any other side-effectful action beyond posting the message and creating this one personal calendar event.