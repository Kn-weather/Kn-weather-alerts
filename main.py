import os, json, requests, re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
NWS_BASE = "https://api.weather.gov"
SPC_BASE = "https://www.spc.noaa.gov"
UA = "MyWxBot/1.0 (your_email@example.com)"
HEADERS = {"User-Agent": UA, "Accept": "application/geo+json"}

def send_discord(content, embed):
    data = {"content": content, "embeds": [embed]}
    try:
        requests.post(WEBHOOK_URL, json=data, timeout=10)
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
        
        # Filter for Severe stuff
        if event not in ["Tornado Warning", "Tornado Emergency", "Severe Thunderstorm Warning", "Tornado Watch", "Severe Thunderstorm Watch"]:
            continue
            
        sent_time = datetime.fromisoformat(props["sent"].replace("Z","+00:00"))
        if sent_time < cutoff:
            continue
            
        embed = {
            "title": props.get("headline", event),
            "color": 0xFF0000 if "Tornado" in event else 0xFFA500,
            "fields": [
                {"name": "Areas", "value": props.get("areaDesc","?")[:1024], "inline": False},
                {"name": "Expires", "value": props.get("expires","?"), "inline": True}
            ],
            "description": (props.get("description") or "")[:2048]
        }
        send_discord(f"⚠️ **{event}**", embed)

# --- SPC MCDs ---
def check_mcd():
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
        # Assume it was issued today
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
        "color": 0x9932CC,
        "description": text[:2048]
    }
    send_discord(f"🌀 **New SPC MCD #{number}**", embed)

if __name__ == "__main__":
    print("Checking weather...")
    check_nws()
    check_mcd()
    print("Done.")
