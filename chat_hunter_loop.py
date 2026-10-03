# -*- coding: utf-8 -*-
"""Continuous chat hunter — runs forever, cycles through query sets,
sleeps between rounds, appends new live groups to live_groups_found.json.
Usage: python chat_hunter_loop.py (background)
"""
import asyncio, json, os, random, shutil, sys, time, datetime

from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "hunters")
OUT = os.path.join(BASE, "live_groups_found.json")
os.makedirs(WORK, exist_ok=True)

QUERY_SETS = [
    ["чат нейросети", "chatgpt чат", "ии чат", "нейросети 2026 чат", "ai чат ру"],
    ["чат промпты", "midjourney чат", "генерация картинок чат", "nano banana чат", "sora чат"],
    ["чат вайбкодинг", "zerocoder чат", "no code чат", "чат разработка", "python чат"],
    ["заработок ии чат", "фриланс нейросети", "удаленка чат", "чат крипто ии", "arbitrage чат"],
    ["чат маркетинг ai", "smm нейросети чат", "контент мейкеры чат", "блогеры чат", "копирайт ии"],
    ["нейросети обучение чат", "курсы ии чат", "чат студенты ai", "machine learning чат", "data science ру"],
    ["grok чат", "claude чат", "gemini чат", "deepseek чат", "gigachat чат"],
    ["чат дизайн ии", "freepik чат", "photoshop нейросети", "видео монтаж ai чат", "музыка suno чат"],
    ["нейросети чат украина", "ии чат казахстан", "нейросети чат узбекистан", "ai chat belarus", "нейросети чат россия"],
    ["чат автоматизация", "n8n чат", "make.com чат", "api нейросети чат", "боты телеграм чат"],
    ["абузы чат", "раздачи ключей чат", "триалы чат", "chatgpt plus абуз", "подписки раздача чат"],
    ["курсор чат", "codex чат", "copilot чат", "ollama чат", "llama чат"],
    ["нейрофотограф чат", "ai аватар чат", "генерация видео чат", "kling чат", "runway чат"],
    ["чат ии помощник", "агенты ии чат", "автоджепт чат", "langchain чат", "rag чат"],
    ["курсы нейросетей чат", "обучение chatgpt чат", "промпт инженер чат", "нейроклуб чат", "ии сообщество чат"],
]

DROP_KW = ["mlbb", "mobile legends", "млнр", "winx", "savage", "sorare", "blox", "roblox", "minecraft", "cs2", "dota", "pubg", "billie", "airbnb", "wildberries", "wb ", "ozon", "купли-продаж", "недвижим", "авто ", "знакомств"]

# STRICT AI relevance: title/username must contain at least one of these
AI_MUST = ["ai", "ии", "нейр", "neuro", "gpt", "chatgpt", "claude", "gemini", "grok", "deepseek", "gigachat",
           "prompt", "промт", "промпт", "midjourney", "sora", "suno", "nano banana", "ml ", "machine learning",
           "data science", "ds ", "нейросет", "вайбкодинг", "vibe", "zerocoder", "зерокодер", "no code", "nocode",
           "n8n", "make.com", "python", "питон", "code", "код", "dev", "разраб", "program", "программ",
           "it ", "айти", "tech", "технолог", "automat", "автоматиз", "бот ", "bot", "api", "ml", "neuroset",
           "генер", "generate", "цифров", "digital", "стартап", "startup", "freelance", "фриланс", "удален",
           "заработ", "маркетинг", "marketing", "smm", "контент", "content", "дизайн", "design", "курсы", "course",
           "обучен", "education", "школ", "student", "студент"]

def pick_hunters(n=3):
    clean = set(json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"])
    files = [f for f in os.listdir(SRC) if f.endswith(".session") and f[:-8] in clean]
    random.shuffle(files)
    out = []
    for f in files:
        if len(out) >= n: break
        stem = f[:-8]
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(os.path.join(SRC, f), dst + ".session")
            except Exception: continue
        out.append(dst)
    return out

def load_found():
    if os.path.exists(OUT):
        return json.load(open(OUT, encoding="utf-8"))
    return []

def save_found(f):
    tmp = OUT + ".tmp"
    json.dump(f, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)

async def hunt_round(paths):
    found = load_found()
    known = {(g.get("channel") or "").lower() for g in found}
    known |= {g.get("linked_id") for g in found}
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)
    new_total = 0
    qs = random.sample(QUERY_SETS, 3)
    for p in paths:
        c = TelegramClient(p, API_ID, API_HASH, connection_retries=2)
        await c.connect()
        if not await c.is_user_authorized():
            await c.disconnect(); continue
        for qset in qs:
            for q in qset:
                try:
                    r = await c(SearchRequest(q=q, limit=25))
                except errors.FloodWaitError as e:
                    print(f"FLOOD {e.seconds}s", flush=True)
                    await c.disconnect()
                    return new_total
                except Exception:
                    continue
                for ch in r.chats:
                    if not isinstance(ch, Channel) or not getattr(ch, "megagroup", False): continue
                    if getattr(ch, "broadcast", False): continue
                    hay = ((ch.title or "") + " " + (ch.username or "")).lower()
                    if any(k in hay for k in DROP_KW): continue
                    if not any(k in hay for k in AI_MUST): continue
                    cnt = getattr(ch, "participants_count", 0) or 0
                    if cnt < 30: continue
                    if (ch.username or "").lower() in known or ch.id in known: continue
                    try:
                        ent = await c.get_input_entity(ch)
                        msgs = await c.get_messages(ent, limit=30)
                        recent = [m for m in msgs if m.date >= cutoff and m.sender_id and m.sender_id > 0 and m.text]
                        senders = len({m.sender_id for m in recent})
                    except Exception:
                        continue
                    if len(recent) >= 5 and senders >= 3:
                        known.add((ch.username or "").lower()); known.add(ch.id)
                        found.append({
                            "channel": ch.username, "title": ch.title,
                            "linked_id": ch.id, "members": cnt,
                            "recent_human": len(recent), "recent_senders": senders,
                            "direct": True, "src": "hunter",
                        })
                        new_total += 1
                        print(f"NEW [{cnt:>6}] {len(recent)}msg/{senders}snd | {ch.title[:45]} | @{ch.username}", flush=True)
                        save_found(found)
                    await asyncio.sleep(random.uniform(1, 3))
                await asyncio.sleep(random.uniform(3, 8))
        await c.disconnect()
        break  # one hunter per round to save quota
    return new_total

async def main():
    round_n = 0
    while True:
        round_n += 1
        paths = pick_hunters(2)
        print(f"=== ROUND {round_n} ({datetime.datetime.now().strftime('%H:%M')}) ===", flush=True)
        try:
            n = await hunt_round(paths)
            print(f"round {round_n}: +{n} new groups", flush=True)
        except Exception as e:
            print(f"round err: {str(e)[:100]}", flush=True)
        total = len(load_found())
        print(f"pool total: {total}", flush=True)
        if total > 120:
            print("pool big enough, sleeping 6h", flush=True)
            await asyncio.sleep(6 * 3600)
        else:
            await asyncio.sleep(random.uniform(45 * 60, 90 * 60))

asyncio.run(main())
