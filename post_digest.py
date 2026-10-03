"""
AI digest poster for иишко Chat (4430207146).
Fetches fresh AI news from RSS/JSON sources, formats a compact digest,
posts via a dedicated session (poster.session copied once).
Usage: python post_digest.py [--dry]
"""
import asyncio, json, os, re, sys, html as htmlmod
import urllib.request
import xml.etree.ElementTree as ET

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
POSTER = os.path.join(BASE, "poster", "poster")
CHAT_ID = 4430207146
SEEN_FILE = os.path.join(BASE, "digest_seen.json")

SOURCES = [
    ("HN AI", "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+neural&points=50"),
    ("Habr AI", "https://habr.com/ru/rss/hubs/artificial_intelligence/articles/"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def parse_feed(xml_text, limit=6):
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for it in root.iter("item"):
        t = it.findtext("title") or ""
        l = it.findtext("link") or ""
        d = (it.findtext("description") or "")
        d = re.sub(r"<[^>]+>", " ", d)
        d = htmlmod.unescape(d).strip()[:160]
        if t and l:
            items.append((htmlmod.unescape(t).strip(), l.strip(), d))
        if len(items) >= limit: break
    # atom
    if not items:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for e in root.findall("a:entry", ns)[:limit]:
            t = e.findtext("a:title", default="", namespaces=ns)
            lk = e.find("a:link", ns)
            l = lk.get("href") if lk is not None else ""
            if t and l: items.append((t.strip(), l, ""))
    return items

def load_seen():
    if os.path.exists(SEEN_FILE):
        return set(json.load(open(SEEN_FILE, encoding="utf-8")))
    return set()

def save_seen(s):
    json.dump(sorted(s)[-2000:], open(SEEN_FILE, "w", encoding="utf-8"))

def build_digest():
    seen = load_seen()
    blocks = []
    new_seen = set(seen)
    for name, url in SOURCES:
        try:
            xml = fetch(url)
        except Exception as e:
            print(f"  {name}: FETCH FAIL {str(e)[:60]}"); continue
        picked = []
        for t, l, d in parse_feed(xml):
            if l in new_seen: continue
            picked.append((t, l, d)); new_seen.add(l)
            if len(picked) >= 3: break
        if picked:
            lines = [f"<b>{name}</b>"]
            for t, l, d in picked:
                lines.append(f'• <a href="{l}">{t}</a>')
            blocks.append("\n".join(lines))
    if not blocks:
        return None, new_seen
    body = "\n\n".join(blocks)
    import datetime
    date = datetime.datetime.now().strftime("%d.%m")
    text = f"<b>🤖 AI-ДАЙДЖЕСТ {date}</b>\n\n{body}\n\n<i>каждое утро свежее — stay tuned</i>"
    return text, new_seen

async def post(text, dry=False):
    from telethon import TelegramClient
    from telethon.tl.types import PeerChannel
    if dry:
        print(text[:2000]); return True
    client = TelegramClient(POSTER, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("poster NOT AUTH"); return False
    # join via invite if needed
    from telethon.tl.functions.messages import ImportChatInviteRequest
    try:
        await client(ImportChatInviteRequest(hash="h3Su0z0zl-M3NWNi"))
    except Exception:
        pass
    tgt = None
    async for dlg in client.iter_dialogs():
        if dlg.entity.id == CHAT_ID:
            tgt = await client.get_input_entity(dlg.entity); break
    if tgt is None:
        try: tgt = await client.get_input_entity(PeerChannel(channel_id=CHAT_ID))
        except Exception:
            print("target unresolved"); await client.disconnect(); return False
    await client.send_message(tgt, text, parse_mode="html", link_preview=False)
    await client.disconnect()
    return True

def main():
    dry = "--dry" in sys.argv
    text, new_seen = build_digest()
    if not text:
        print("nothing new"); return
    ok = asyncio.run(post(text, dry))
    if ok and not dry:
        save_seen(new_seen)
        print("POSTED")

if __name__ == "__main__":
    main()
