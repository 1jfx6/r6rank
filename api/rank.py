import os, json, urllib.request
from flask import Flask

app = Flask(__name__)

def fetch():
    req = urllib.request.Request(
        os.environ["ARENYZE_URL"],
        headers={"api-key": os.environ["ARENYZE_KEY"], "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.load(r)

def find(obj, test):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if test(k, v):
                return v
        for v in obj.values():
            r = find(v, test)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find(v, test)
            if r is not None:
                return r
    return None

def is_rank(k, v):
    return "rank" in k.lower() and isinstance(v, str) and "http" not in v

def is_rp(k, v):
    return k.lower() in ("rankpoints", "rank_points", "rp", "mmr") and isinstance(v, (int, float, str))

@app.route("/")
@app.route("/api/rank")
def rank():
    name = os.environ.get("PLAYER_NAME", "Player")
    try:
        data = fetch()
        r = find(data, is_rank)
        rp = find(data, is_rp)
        if r is None:
            return "Couldn't read rank. Raw: " + json.dumps(data)[:300], 200, {"Cache-Control": "no-store"}
        text = f"{name} is {r} ({rp} RP)" if rp is not None else f"{name} is {r}"
        return text, 200, {
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "public, s-maxage=1800",
        }
    except Exception as e:
        return f"Error: {e!r}", 200, {"Cache-Control": "no-store"}
