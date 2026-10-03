# -*- coding: utf-8 -*-
"""Global search for LIVE AI megagroups (chats) directly.
contacts.Search -> megagroups -> filter members>=50 -> activity check (msgs last 3 days).
Output appended to ai_groups_live.json with direct=True flag.
Usage: python search_live_groups.py
"""
import asyncio, json, os, random, shutil, time, datetime

from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Chat, Channel

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "searchers")
os.makedirs(WORK, exist_ok=True)

QUERIES = [
    "чат заработок нейросети", "чат фриланс ии", "чат копирайт нейросети",
    "чат маркетинг нейросети", "нейросети для бизнеса чат", "чат удаленка ии",
    "чат блогеры нейросети", "чат контент мейкеры", "телеграм чат ai ru",
    "чат grok 4", "чат gpt 5", "чат gemini 3", "чат claude opus",
    "чат генерация музыки ai", "чат нейровизуал", "чат 3d генерация",
    "чат монтаж видео ai", "чат автоворонки ии", "чат товарка нейросети",
    "чат арбитраж ии", "чат крипт нейросети", "чат трейдинг ai",
    "нейросети чат украина", "нейросети чат казахстан", "нейросети чат беларусь",
    "чат студенты ии", "чат школьники нейросети", "домашка нейросети чат",
    "чат преподаватели ии", "чат юристы нейросети",
]

def session(n=2):
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    files = [f for f in os.listdir(SRC) if f.endswith(".session") and f[:-8] in clean]
    random.shuffle(files)
    out = []
    for f in files:
        if len(out) >= n: break
        stem = f[:-8]
        if any(x in stem for x in ("7448683285", "809951394")): continue
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(os.path.join(SRC, f), dst + ".session")
            except Exception: continue
        out.append(dst)
    return out

async def main():
    st_f = os.path.join(BASE, "live_groups_found.json")
    found = json.load(open(st_f, encoding="utf-8")) if os.path.exists(st_f) else []
    known = {g["linked_id"] for g in found}
    paths = session(2)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)
    for p in paths:
        c = TelegramClient(p, API_ID, API_HASH, connection_retries=2)
        await c.connect()
        if not await c.is_user_authorized():
            await c.disconnect(); continue
        print("searcher:", os.path.basename(p))
        for q in QUERIES:
            try:
                r = await c(SearchRequest(q=q, limit=20))
            except errors.FloodWaitError as e:
                print(f"  FLOOD {e.seconds}s — stop searcher"); break
            except Exception as e:
                print(f"  ERR {q}: {str(e)[:60]}"); continue
            for ch in r.chats:
                if not isinstance(ch, Channel): continue
                if not getattr(ch, "megagroup", False): continue
                if getattr(ch, "broadcast", False): continue
                if ch.id in known: continue
                cnt = getattr(ch, "participants_count", 0) or 0
                if cnt < 30: continue
                known.add(ch.id)
                # activity check
                try:
                    ent = await c.get_input_entity(ch)
                    msgs = await c.get_messages(ent, limit=30)
                    recent = [m for m in msgs if m.date >= cutoff and m.sender_id and m.sender_id > 0 and m.text]
                    senders = len({m.sender_id for m in recent})
                except Exception as e:
                    print(f"  {ch.title[:30]}: act err {str(e)[:40]}"); continue
                status = "LIVE" if (len(recent) >= 5 and senders >= 3) else "dead"
                print(f"  [{status}] {cnt:>5} | {len(recent):>2}msg/{senders:>2}snd 3d | {ch.title[:45]} | @{ch.username}")
                if status == "LIVE":
                    found.append({
                        "channel": ch.username, "title": ch.title,
                        "linked_id": ch.id, "members": cnt,
                        "recent_human": len(recent), "recent_senders": senders,
                        "direct": True,
                    })
                    json.dump(found, open(st_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            await asyncio.sleep(random.uniform(2, 6))
        await c.disconnect()
        break  # one searcher is enough for first pass
    print(f"TOTAL LIVE FOUND: {len(found)}")

asyncio.run(main())
