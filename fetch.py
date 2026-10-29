#!/usr/bin/env python3
"""Daily read-only snapshot of public subreddits for personal summaries.

Uses Reddit's official Data API with application-only OAuth
(client_credentials grant). It only reads: no posting, voting,
messaging or moderation. Snapshots are saved locally and never
redistributed.

Credentials come from an env file (default ~/.config/reddit-digest.env):
    REDDIT_CLIENT_ID=...
    REDDIT_CLIENT_SECRET=...
    REDDIT_USERNAME=...
"""
import argparse
import base64
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

VERSION = "1.0"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"
PAUSE_S = 1.0  # one request per second, well under the 100/min limit


def load_env(path):
    env = {}
    for line in pathlib.Path(path).expanduser().read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    missing = [k for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME") if not env.get(k)]
    if missing:
        sys.exit(f"Missing in {path}: {', '.join(missing)}")
    return env


def user_agent(env):
    # Format required by Reddit's API rules: platform:app id:version (by /u/username)
    return f"macos:cesar-digest:v{VERSION} (by /u/{env['REDDIT_USERNAME']})"


def get_token(env):
    auth = base64.b64encode(f"{env['REDDIT_CLIENT_ID']}:{env['REDDIT_CLIENT_SECRET']}".encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={"Authorization": f"Basic {auth}", "User-Agent": user_agent(env)},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def api_get(path, params, token, env):
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"bearer {token}", "User-Agent": user_agent(env)})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    time.sleep(PAUSE_S)
    return data


def snapshot(sub, cfg, token, env, out_dir):
    out = {"subreddit": sub, "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "listings": {}, "comments": {}}
    for name, (path, params) in {
        "top_month": (f"/r/{sub}/top", {"t": "month", "limit": cfg["limit"]}),
        "hot": (f"/r/{sub}/hot", {"limit": cfg["limit"]}),
    }.items():
        out["listings"][name] = api_get(path, params, token, env)
    # Top comments of the most discussed posts in this month's top listing
    posts = [c["data"] for c in out["listings"]["top_month"]["data"]["children"]]
    for p in sorted(posts, key=lambda p: -p["num_comments"])[: cfg["comment_posts"]]:
        out["comments"][p["id"]] = api_get(f"/r/{sub}/comments/{p['id']}", {"limit": cfg["comments_per_post"], "depth": 2, "sort": "top"}, token, env)
    day = datetime.date.today().isoformat()
    dest = out_dir / sub / f"{day}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out))
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="~/.config/reddit-digest.env")
    ap.add_argument("--config", default=pathlib.Path(__file__).with_name("subreddits.json"))
    ap.add_argument("--out", default="data")
    args = ap.parse_args()
    env = load_env(args.env)
    cfg = json.loads(pathlib.Path(args.config).read_text())
    token = get_token(env)
    for sub in cfg["subreddits"]:
        print("saved", snapshot(sub, cfg, token, env, pathlib.Path(args.out).expanduser()))


if __name__ == "__main__":
    main()
