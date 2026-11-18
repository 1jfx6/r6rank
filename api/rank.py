import os, json, urllib.request
from flask import Flask

app = Flask(__name__)

TIERS = ["Copper", "Bronze", "Silver", "Gold", "Platinum", "Emerald", "Diamond", "Champion"]
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}

def rank_name(rank_id):
    if rank_id <= 0:
        return "Unranked"
    rank_id = min(rank_id, 40)
    tier = TIERS[(rank_id - 1) // 5]
    division = 5 - ((rank_id - 1) % 5)
    return f"{tier} {ROMAN[division]}"

def rank_name_from_rp(rp):
    if rp < 1000:
        return "Unranked"
    return rank_name(min((rp - 1000) // 100 + 1, 40))

def fetch():
    req = urllib.request.Request(
        os.environ["ARENYZE_URL"],
        headers={"api-key": os.environ["ARENYZE_KEY"], "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=9) as r:
        return json.load(r)

@app.route("/")
@app.route("/api/rank")
def rank():
    name = os.environ.get("PLAYER_NAME", "Unavailable")
    display = os.environ.get("DISPLAY_NAME", "Player")
    try:
        fs = fetch()["fullStats"]

        # current rank
        latest = None
        for fam in fs["platform_families_full_profiles"]:
            for board in fam["board_ids_full_profiles"]:
                for fp in board["full_profiles"]:
                    if latest is None or fp.get("season_id", 0) > latest.get("season_id", 0):
                        latest = fp
        cur = latest["profile"]

        # peak
        peak_rp = cur["max_rank_points"]
        for seg in fs["data"]["segments"]:
            if seg.get("type") != "season":
                continue
            if seg.get("metadata", {}).get("rankType") != "rp":
                continue
            v = seg.get("stats", {}).get("maxRankPoints", {}).get("value", 0)
            peak_rp = max(peak_rp, v)

        text = (f"{display}'s current rank: {rank_name(cur['rank'])} ({cur['rank_points']:,} RP), "
                f"{display}'s peak rank: {rank_name_from_rp(peak_rp)}, (Tracker: {name})")
        return text, 200, {
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "no-store",
        }
    except Exception as e:
        return f"Error: {e!r}", 200, {"Cache-Control": "no-store"}
