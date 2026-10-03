# -*- coding: utf-8 -*-
"""TGStat scraper via Firecrawl API with key rotation. Fetches category ratings,
extracts chats, outputs tgstat_all.json [{title, username, members, cat}]"""
import json, os, re, time
import urllib.request

BASE = r"C:/Users/User/tmp/tg_chat_grow"
KEYS = [l.strip() for l in open(r"C:/Users/User/tmp/firecrawl_keys_full.txt", encoding="utf-8") if l.strip().startswith("fc-")]
CATS = ["tech", "marketing", "business", "courses", "education", "career", "design", "apps", "edutainment", "news", "blogs"]
ki = [0]

def scrape(url):
    for attempt in range(len(KEYS)):
        key = KEYS[ki[0] % len(KEYS)]; ki[0] += 1
        body = json.dumps({"url": url, "formats": ["markdown"], "onlyMainContent": True}).encode()
        req = urllib.request.Request("https://api.firecrawl.dev/v2/scrape", data=body, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            if d.get("success"):
                return d["data"]["markdown"]
            print("  api err:", str(d)[:100])
        except Exception as e:
            print("  req err:", str(e)[:80])
        time.sleep(2)
    return None

LINK_RE = re.compile(r"tgstat\.ru/chat/(@?[A-Za-z][A-Za-z0-9_\-]{4,})/stat")
MEMBERS_RE = re.compile(r"([\d\s\xa0]+)\s*участников")

def parse(md, cat):
    out = []
    for m in LINK_RE.finditer(md):
        un = m.group(1).lstrip("@")
        back = md[max(0, m.start() - 800):m.start()]
        title = un
        tm = re.findall(r"\\\\n\\\\n([^\\\\\n]{4,90}?)\\\\n\\\\n", back)
        if tm: title = tm[-1].strip()
        members = 0
        mm = MEMBERS_RE.search(back)
        if mm:
            try: members = int(mm.group(1).replace(" ", "").replace("\xa0", ""))
            except Exception: members = 0
        out.append({"title": title, "username": un, "members": members, "cat": cat})
    return out

def main():
    results = []
    seen = set()
    for cat in CATS:
        url = f"https://tgstat.ru/ratings/chats/{cat}?sort=msgs"
        print(f"=== {cat} (sort=msgs) ===", flush=True)
        md = scrape(url)
        if not md:
            print("  FAIL"); continue
        got = parse(md, cat)
        for g in got:
            if g["username"].lower() in seen: continue
            seen.add(g["username"].lower()); results.append(g)
        print(f"  parsed {len(got)} (new total {len(results)})", flush=True)
        json.dump(results, open(os.path.join(BASE, "tgstat_all.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(3)
    print("TOTAL:", len(results))

main()
