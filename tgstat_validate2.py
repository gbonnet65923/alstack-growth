# -*- coding: utf-8 -*-
"""Validate tgstat usernames with SESSION ROTATION.
On FloodWait: park session, switch to next. Small batches per session.
Output: tgstat_valid.json + tgstat_parked.json"""
import asyncio, json, os, random, shutil, time

from telethon import TelegramClient, errors
from telethon.tl.types import Channel

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "validators")
os.makedirs(WORK, exist_ok=True)

AI_MUST = ["ai","ии","нейр","neuro","gpt","claude","gemini","grok","deepseek","gigachat","prompt","промт","промпт","midjourney","sora","suno","machine learning","data science","нейросет","вайбкод","vibe","zerocoder","зерокодер","no code","nocode","n8n","make.com","python","питон","код","code","dev","разраб","program","программ","it ","айти","tech","технолог","автомат","bot","бот","api","генер","digital","цифров","стартап","startup","фриланс","freelance","удален","заработ","маркетинг","marketing","smm","контент","content","дизайн","design","курс","course","обучен","qa","тест","sql","linux","devops","git","web","веб","frontend","backend","mobile","мобильн","android","андроид","ios","apple","яндекс","sber","vk","kaspersky","1c","excel","аналит","кибер","cyber","security","безопас","хак","hack","crypto","крипт","блокчейн","blockchain","web3","nft","трейд","инвест","финанс","fin","тон ","ton","работа","ваканс","job","hr","бизнес","business","предприним","товарк","дроп","e-com","ecom","продаж","tilda","тильда","notion","figma","excel"]

def load(fn, default):
    p = os.path.join(BASE, fn)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

def save(fn, data):
    p = os.path.join(BASE, fn)
    tmp = p + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)

async def main():
    src = load("tgstat_all.json", [])
    valid = load("tgstat_valid.json", [])
    parked = load("tgstat_parked.json", {})
    skipf = load("tgstat_skip.json", [])
    vset = {v["username"].lower() for v in valid}
    sset = {s.lower() for s in skipf}
    todo, seen = [], set()
    for s in src:
        un = s["username"].lower()
        if un in vset or un in sset or un in seen or un.startswith("http"): continue
        seen.add(un); todo.append(s)
    print("to validate:", len(todo), flush=True)

    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    random.shuffle(clean)
    clean = [c for c in clean if c not in parked]

    ci = 0
    c = None
    stem = None
    ok = 0
    for i, s in enumerate(todo):
        if c is None:
            if ci >= len(clean):
                print("sessions exhausted"); break
            stem = clean[ci]; ci += 1
            dst = os.path.join(WORK, stem)
            if not os.path.exists(dst + ".session"):
                try: shutil.copy(os.path.join(SRC, stem + ".session"), dst + ".session")
                except Exception: continue
            c = TelegramClient(dst, API_ID, API_HASH, connection_retries=2)
            await c.connect()
            if not await c.is_user_authorized():
                await c.disconnect(); c = None; continue
            print(f"session: {stem}", flush=True)
        un = s["username"]
        try:
            ent = await c.get_entity(un)
        except errors.FloodWaitError as e:
            print(f"FLOOD {e.seconds}s on {stem} — park, rotate", flush=True)
            await c.disconnect(); c = None
            parked[stem] = time.time() + e.seconds
            save("tgstat_parked.json", parked)
            clean = [x for x in clean if x not in parked]
            continue
        except errors.UsernameNotOccupiedError:
            sset.add(un.lower()); continue
        except Exception:
            sset.add(un.lower()); continue
        if not isinstance(ent, Channel) or not getattr(ent, "megagroup", False):
            sset.add(un.lower())
        else:
            cnt = getattr(ent, "participants_count", 0) or 0
            if cnt < 30:
                try:
                    from telethon.tl.functions.channels import GetFullChannelRequest
                    full = await c(GetFullChannelRequest(channel=ent))
                    cnt = full.full_chat.participants_count or cnt
                except Exception:
                    pass
            title = ent.title or un
            hay = (title + " " + un).lower()
            if cnt < 30 or not any(k in hay for k in AI_MUST):
                sset.add(un.lower())
            else:
                valid.append({"username": un, "title": title, "members": cnt, "cat": s.get("cat"), "src": "tgstat", "direct": True, "linked_id": ent.id, "recent_human": 10, "recent_senders": 5})
                vset.add(un.lower()); ok += 1
                print(f"  OK {cnt:>6} | {title[:45]} | @{un}", flush=True)
        if (i + 1) % 25 == 0:
            save("tgstat_valid.json", valid)
            save("tgstat_skip.json", sorted(sset))
            print(f"progress {i+1}/{len(todo)} valid={len(valid)}", flush=True)
        await asyncio.sleep(random.uniform(2.5, 6))
    if c: await c.disconnect()
    save("tgstat_valid.json", valid)
    save("tgstat_skip.json", sorted(sset))
    print(f"DONE valid={len(valid)} skipped={len(sset)} parked={len(parked)}", flush=True)

asyncio.run(main())
