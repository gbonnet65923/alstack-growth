# -*- coding: utf-8 -*-
"""Validate tgstat_all.json usernames via telethon: resolve, check megagroup,
members>=30, AI-relevant title. Output: tgstat_valid.json"""
import asyncio, json, os, random, shutil, sys

from telethon import TelegramClient, errors
from telethon.tl.types import Channel

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "validators")
os.makedirs(WORK, exist_ok=True)

AI_MUST = ["ai","ии","нейр","neuro","gpt","claude","gemini","grok","deepseek","gigachat","prompt","промт","промпт","midjourney","sora","suno","machine learning","data science","нейросет","вайбкод","vibe","zerocoder","зерокодер","no code","nocode","n8n","make.com","python","питон","код","code","dev","разраб","program","программ","it ","айти","tech","технолог","автомат","bot","бот","api","генер","digital","цифров","стартап","startup","фриланс","freelance","удален","заработ","маркетинг","marketing","smm","контент","content","дизайн","design","курс","course","обучен","qa","тест","sql","linux","devops","git","web","веб","frontend","backend","mobile","мобильн","android","андроид","ios","apple","яндекс","sber","vk","kaspersky","1c","excel","power bi","аналит","кибер","cyber","security","безопас","хак","hack","crypto","крипт","блокчейн","blockchain","web3","nft"," trading","трейд","инвест","финанс","fin"]

async def main():
    src = json.load(open(os.path.join(BASE, "tgstat_all.json"), encoding="utf-8"))
    outf = os.path.join(BASE, "tgstat_valid.json")
    valid = json.load(open(outf, encoding="utf-8")) if os.path.exists(outf) else []
    checked = {v["username"] for v in valid}
    todo = [s for s in src if s["username"] not in checked and not s["username"].startswith("http")]
    # dedupe by username
    seen = set(); uniq = []
    for s in todo:
        if s["username"].lower() in seen: continue
        seen.add(s["username"].lower()); uniq.append(s)
    print("to validate:", len(uniq))
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    random.shuffle(clean)
    stem = clean[0]
    dst = os.path.join(WORK, stem)
    if not os.path.exists(dst + ".session"):
        shutil.copy(os.path.join(SRC, stem + ".session"), dst + ".session")
    c = TelegramClient(dst, API_ID, API_HASH, connection_retries=2)
    await c.connect()
    ok = skip = 0
    for i, s in enumerate(uniq):
        un = s["username"]
        try:
            ent = await c.get_entity(un)
        except errors.FloodWaitError as e:
            print(f"FLOOD {e.seconds}s at {i} — stop"); break
        except Exception:
            skip += 1; continue
        if not isinstance(ent, Channel) or not getattr(ent, "megagroup", False):
            skip += 1; continue
        cnt = getattr(ent, "participants_count", 0) or 0
        title = ent.title or un
        hay = (title + " " + un).lower()
        if cnt < 30 or not any(k in hay for k in AI_MUST):
            skip += 1; continue
        valid.append({"username": un, "title": title, "members": cnt, "cat": s.get("cat"), "src": "tgstat"})
        ok += 1
        print(f"  OK {cnt:>6} | {title[:45]} | @{un}")
        if ok % 10 == 0:
            json.dump(valid, open(outf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        await asyncio.sleep(random.uniform(1.5, 4))
    json.dump(valid, open(outf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    await c.disconnect()
    print(f"VALID: {ok} skipped: {skip} total: {len(valid)}")

asyncio.run(main())
