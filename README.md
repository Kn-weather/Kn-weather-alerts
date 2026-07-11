```markdown
# 🌪️ NWS & SPC Discord Weather Alerts

A lightweight, 100% free, serverless Discord bot that fetches live severe weather alerts from the National Weather Service (NWS) and the Storm Prediction Center (SPC) and posts them directly to categorized Discord channels using Webhooks.

Because this runs entirely on **GitHub Actions**, there are no servers to pay for, no bots to keep online 24/7, and no local infrastructure required.

## ✨ Features
- **100% Free Hosting:** Runs automatically every 5 minutes via GitHub Actions.
- **Categorized Routing:** Sends different alert types (Tornado, Flood, Winter, etc.) to their own specific Discord channels.
- **Nationwide Coverage:** Monitors the entire United States.
- **SPC Integration:** Posts SPC Mesoscale Discussions (MCDs) and the Day 1 Convective Outlook map.
- **Smart Spam Control:** Uses a 10-minute issuance cutoff to ensure alerts aren't posted repeatedly every 5 minutes.
- **Webhook Powered:** No Discord Bot account or `discord.py` gateway connection required.

## 🗂️ Alert Categories & Routing
The script routes alerts to 8 separate Discord channels based on the official NWS/SPC product types.

| Category | NWS / SPC Events Routed | GitHub Secret Name |
| :--- | :--- | :--- |
| **SPC Outlooks** | SPC Day 1 Convective Outlook (Map + Text) | `OUTLOOK_WEBHOOK` |
| **Mesoscale Discussions** | SPC Mesoscale Discussions (MCDs) | `MCD_WEBHOOK` |
| **Severe T-Storm Warnings** | Severe Thunderstorm Warning | `SVR_WEBHOOK` |
| **Tornado Warnings** | Tornado Warning, Tornado Emergency | `TORNADO_WEBHOOK` |
| **Tropical Alerts** | Tropical Storm Warning, Storm Surge Warning | `TROPICAL_WEBHOOK` |
| **Flood Alerts** | Flood Watch/Warning, Flash Flood Watch/Warning, Areal/Coastal Flood | `FLOOD_WEBHOOK` |
| **Hurricane Alerts** | Hurricane Warning, Hurricane Force Wind Warning | `HURRICANE_WEBHOOK` |
| **Winter Weather** | Blizzard, Winter Storm, Ice Storm, Snow Squall, Extreme Cold | `WINTER_WEBHOOK` |

## 🚀 Setup Guide

### Step 1: Create Discord Webhooks
1. In your Discord server, create 8 channels for the categories listed above.
2. Go to **Channel Settings** > **Integrations** > **Webhooks** for each channel.
3. Create a webhook, name it (e.g., "Weather Bot"), and **Copy the Webhook URL**. Do this for all 8 channels.

### Step 2: Add GitHub Secrets
1. Go to your repository **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret**.
3. Add 8 secrets using the exact names from the table above (e.g., `TORNADO_WEBHOOK`), pasting the corresponding Discord Webhook URL as the value.

### Step 3: Enable GitHub Actions
1. Go to the **Actions** tab in your repository.
2. If prompted, click "I understand my workflows, go ahead and enable them."
3. Click on **Weather Alerts Poller** on the left.
4. Click the green **Run workflow** button on the right to test the script manually.

If there are active alerts that were issued in the last 10 minutes, they will immediately post to your Discord channels!

## ⚙️ How It Works
- **Polling:** The GitHub Action runs on a cron schedule of `*/5 * * * *` (every 5 minutes).
- **NWS API:** It fetches all active alerts from `api.weather.gov/alerts/active`.
- **SPC Scraping:** It fetches the SPC MCD index and Day 1 Outlook pages to check for new products.
- **Deduplication:** Because GitHub Actions is stateless (it forgets everything after it runs), the script checks the `sentTime` of the alert. It will only post alerts that were issued within the last 10 minutes. This prevents spam while allowing a buffer for GitHub delays.

## ⏱️ Delay Expectations
Because this runs on a 5-minute cron schedule, the delay between the NWS issuing an alert and it appearing in Discord will be anywhere from **0 to 5 minutes**. 

## 🛠️ Customization
- **To change polling frequency:** Edit `.github/workflows/weather.yml` and change `*/5 * * * *` to your desired cron schedule.
- **To add new alert types:** Edit `main.py`, find the `check_nws()` function, and add a new `elif event in ["..."]` block with your desired events and webhook variable.
- **To move to a new Discord server:** Simply update the 8 GitHub Secrets with the new Discord channel Webhook URLs. No code changes required!

## 📄 License
This project is open source and available for anyone to use or modify.
``` 

