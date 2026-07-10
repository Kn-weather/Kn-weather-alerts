import os, json, requests, re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# --- Webhooks ---
OUTLOOK_WEBHOOK = os.getenv("OUTLOOK_WEBHOOK")
MCD_WEBHOOK = os.getenv("MCD_WEBHOOK")
SVR_WEBHOOK = os.getenv("SVR_WEBHOOK")
TORNADO_WEBHOOK = os.getenv("TORNADO_WEBHOOK")
TROPICAL_WEBHOOK = os.getenv("TROPICAL_WEBHOOK")
FLOOD_WEBHOOK = os.getenv("FLOOD_WEBHOOK")
HURRICANE_WEBHOOK = os.getenv("HURRICANE_WEBHOOK")
WINTER_WEBHOOK = os.getenv("WINTER_WEBHOOK")

NWS_BASE = "https://api.weather.gov"
SPC_BASE = "https://www.spc.noaa.gov"
UA = "MyWxBot/1.0 (your_email@example.com)"
HEADERS = {"User-Agent": UA, "Accept": "application/geo+json"}

def send_discord(webhook_url, content, embed):
    if not webhook_url:
        return # Skip if no webhook URL is provided
    data = {"content": content, "embeds": [embed]}
    try:
        requests.post(webhook_url, json=data, timeout=10)
    except Exception as e:
        print(f"Failed to send webhook: {e}")

# --- NWS Alerts ---
def check_nws():
    r = requests.get(f"{NWS_BASE}/alerts/active", headers=HEADERS, timeout=20)
    if r.status_code != 200: return
    alerts = r.json().get("features", [])
    
    # Only look at alerts issued in the last 10 minutes
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    
    for alert in alerts:
        props = alert["properties"]
        event = props.get("event", "")
        target_webhook = None
        color = 0x3498DB # Default blue
        
        # 1. Severe Thunderstorm Warnings
        if event == "Severe Thunderstorm Warning":
            target_webhook = SVR_WEBHOOK
            color = 0xFFA500 # Orange
            
        # 2. Tornado Warnings
        elif event in ["Tornado Warning", "Tornado Emergency"]:
            target_webhook = TORNADO_WEBHOOK
            color = 0xFF0000 # Red
            
        # 3. Tropical Storm & Storm Surge
        elif event in ["Tropical Storm Warning", "Storm Surge Warning"]:
            target_webhook = TROPICAL_WEBHOOK
            color = 0x8E44AD # Purple
            
        # 4. Flood Watches & Warnings
        elif event in ["Flood Watch", "Flood Warning", "Flash Flood Watch", "Flash Flood Warning", "Areal Flood Watch", "Areal Flood Warning", "Coastal Flood Watch", "Coastal Flood Warning"]:
            target_webhook = FLOOD_WEBHOOK
            color = 0x00FF00 # Green
            
        # 5. Hurricane Warnings
        elif event in ["Hurricane Warning", "Hurricane Force Wind Warning"]:
            target_webhook = HURRICANE_WEBHOOK
            color = 0xC0392B # Dark Red
            
        # 6. Winter Weather
        elif event in ["Blizzard Warning", "Winter Storm Warning", "Ice Storm Warning", "Snow Squall Warning", "Extreme Cold Warning", "Extreme Cold Watch"]:
            target_webhook = WINTER_WEBHOOK
            color = 0xFFFFFF # White
            
        else:
            # Skip events we didn't ask for
            continue
            
        if not target_webhook:
            continue
            
            sent_time = datetime.fromisoformat(props["sent"].replace("Z","+00:00"))
        if sent_time < cutoff:
            continue
            
        embed = {
            "title": props.get("headline", event),
            "color": color,
            "fields": [
                {"name": "Areas", "value": props.get("areaDesc","?")[:1024], "inline": False},
                {"name": "Expires", "value": props.get("expires","?"), "inline": True}
            ],
            "description": (props.get("description") or "")[:2048]
        }
        send_discord(target_webhook, f"⚠️ **{event}**", embed)

# --- SPC MCDs ---
def check_mcd():
    if not MCD_WEBHOOK:
        return
        
    r = requests.get(f"{SPC_BASE}/products/md/", headers={"User-Agent": UA}, timeout=20)
    soup = BeautifulSoup(r.text, "lxml")
    links = soup.find_all("a", href=re.compile(r"^md\d{4}\.html$"))
    if not links: return
    
    number = re.search(r"md(\d{4})", links[0]["href"]).group(1)
    mcd_url = f"{SPC_BASE}/products/md/md{number}.html"
    
    # Fetch the actual MCD text to check its issue time
    mcd_r = requests.get(mcd_url, headers={"User-Agent": UA}, timeout=20)
    mcd_soup = BeautifulSoup(mcd_r.text, "lxml")
    text = mcd_soup.get_text(" ", strip=True)
    
    # Look for a time like "1630Z" in the text
    time_match = re.search(r"(\d{2})(\d{2})Z", text)
    if time_match:
        hr, mn = int(time_match.group(1)), int(time_match.group(2))
        now = datetime.now(timezone.utc)
        issue_time = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
        # If issue time is in the future, it was likely issued yesterday
        if issue_time > now:
            issue_time -= timedelta(days=1)
            
        cutoff = now - timedelta(minutes=15)
        if issue_time < cutoff:
            return # MCD is old, don't post it
            
    embed = {
        "title": f"SPC Mesoscale Discussion #{number}",
        "url": mcd_url,
        "color": 0x9B59B6,
        "description": text[:2048]
    }
    send_discord(MCD_WEBHOOK, f"🌀 **New SPC MCD #{number}**", embed)

# --- SPC Day 1 Convective Outlook ---
def check_outlook():
    if not OUTLOOK_WEBHOOK:
        return
        
    # We check the text page to see when it was issued
    r = requests.get(f"{SPC_BASE}/products/outlook/day1otlk.html", headers={"User-Agent": UA}, timeout=20)
    soup = BeautifulSoup(r.text, "lxml")
    text = soup.get_text(" ", strip=True)
    
    # Look for the issue time (e.g., "0100Z", "1300Z", "1630Z", "2000Z")
    time_match = re.search(r"(\d{2})(\d{2})Z", text)
    if not time_match:
        return
        
    hr, mn = int(time_match.group(1)), int(time_match.group(2))
    now = datetime.now(timezone.utc)
    issue_time = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
    
    # If issue time is in the future, it was likely issued yesterday
    if issue_time > now:
        issue_time -= timedelta(days=1)
        
    # Only post if the outlook was issued in the last 30 minutes
    cutoff = now - timedelta(minutes=30)
    if issue_time < cutoff:
        return # Outlook is old
        
    # SPC updates this map image every time a new outlook is issued
    map_url = f"{SPC_BASE}/products/outlook/day1otlk.gif"
    
    embed = {
        "title": "SPC Day 1 Convective Outlook",
        "url": f"{SPC_BASE}/products/outlook/day1otlk.html",
        "color": 0x1ABC9C,
        "image": {"url": map_url},
        "description": text[:1024] # Include the first bit of the text summary
    }
    send_discord(OUTLOOK_WEBHOOK, "🗺️ **New SPC Day 1 Convective Outlook**", embed)

if __name__ == "__main__":
    print("Checking weather...")
    check_nws()
    check_mcd()
    check_outlook()
    print("Done.")
