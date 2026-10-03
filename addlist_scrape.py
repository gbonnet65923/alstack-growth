# -*- coding: utf-8 -*-
"""Scrape addlist.org catalog for AI channels (direct HTTP, no browser).
Output: addlist_channels.json [{title, username, subs, url}]
"""
import json, re, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def try_rss(cat_url):
    # addlist category pages often expose RSS
    for suffix in ["/rss", "?rss=1"]:
        try:
            xml = get(cat_url + suffix)
            if "<item>" in xml or "<entry" in xml:
                items = []
                root = ET.fromstring(xml)
                for it in root.iter("item"):
                    t = it.findtext("title") or ""
                    l = it.findtext("link") or ""
                    items.append({"title": t, "url": l})
                return items
        except Exception:
            continue
    return None

def parse_html_channels(html):
    out = []
    # addlist links look like https://addlist.org/channel/<slug> or t.me/<un>
    for m in re.finditer(r'href="(https?://(?:addlist\.org/channel/[^"]+|t\.me/([A-Za-z][\w]{3,31})))"[^>]*>([^<]{3,80})<', html):
        url, un, title = m.group(1), m.group(2), m.group(3).strip()
        out.append({"title": title, "url": url, "username": un})
    # also title-attribute cards
    for m in re.finditer(r't\.me/([A-Za-z][\w]{3,31})["\'][^>]*>\s*([^<]{3,80})', html):
        out.append({"title": m.group(2).strip(), "url": "https://t.me/" + m.group(1), "username": m.group(1)})
    return out

def main():
    results = []
    seen = set()
    targets = [
        "https://addlist.org/",
        "https://addlist.org/channels",
        "https://addlist.org/catalog",
        "https://addlist.org/search?q=" + urllib.parse.quote("нейросети"),
        "https://addlist.org/search?q=" + urllib.parse.quote("чат ai"),
    ]
    for url in targets:
        try:
            html = get(url)
            print(f"OK {url} ({len(html)} bytes)")
            items = try_rss(url) or parse_html_channels(html)
            for it in items:
                key = it.get("username") or it["url"]
                if key in seen: continue
                seen.add(key)
                it["src"] = url
                results.append(it)
            print(f"  parsed {len(items)} items")
        except Exception as e:
            print(f"FAIL {url}: {str(e)[:80]}")
        time.sleep(2)
    json.dump(results, open(r"C:/Users/User/tmp/tg_chat_grow/addlist_channels.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"TOTAL: {len(results)}")

main()
