"""Check @SpamBot restriction status across CLEAN_ALIVE_SESSIONS.
Copies sessions to checkers/ to avoid touching originals.
Usage: python check_spambot.py [N]
Outputs spambot_status.json {stem: 'ok'|'restricted:<text>'|err}
"""
import asyncio, json, os, random, shutil, sys

from telethon import TelegramClient
from telethon.tl.functions.messages import StartBotRequest

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = r"C:/Users/User/tmp/tg_chat_grow/checkers"
OUT = r"C:/Users/User/tmp/tg_chat_grow/spambot_status.json"

os.makedirs(WORK, exist_ok=True)

def load_prev():
    if os.path.exists(OUT):
        return json.load(open(OUT, encoding="utf-8"))
    return {}

async def check(path, bot_ent_cache):
    client = TelegramClient(path, API_ID, API_HASH, connection_retries=1, device_model="iPhone 13")
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect(); return "NOT AUTH"
    me = await client.get_me()
    try:
        bot = await client.get_entity("SpamBot")
    except Exception as e:
        await client.disconnect(); return f"resolve bot: {str(e)[:50]}"
    try:
        await client(StartBotRequest(bot=bot, peer=bot, start_param="start"))
    except Exception:
        pass
    await asyncio.sleep(3)
    msgs = await client.get_messages(bot, limit=3)
    texts = [m.text or "" for m in msgs if m.text]
    await client.disconnect()
    joined = " ".join(texts).lower()
    if not texts:
        return "no reply"
    if "no restrictions" in joined or "account is not limited" in joined or "свободен от ограничений" in joined or "your account is free" in joined:
        return "ok"
    return "restricted: " + texts[0][:120].replace("\n", " ")

async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    prev = load_prev()
    files = [f for f in os.listdir(SRC) if f.endswith(".session")]
    random.shuffle(files)
    done = 0
    for f in files:
        if done >= n: break
        stem = f[:-8]
        if stem in prev: continue
        if any(x in stem for x in ("7448683285", "809951394")): continue
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(os.path.join(SRC, f), dst + ".session")
            except Exception: continue
        try:
            r = await check(dst, None)
        except Exception as e:
            r = f"ERR {str(e)[:80]}"
        prev[stem] = r
        done += 1
        print(f"[{done}/{n}] {stem}: {r[:90]}")
        if done % 5 == 0:
            json.dump(prev, open(OUT, "w", encoding="utf-8"))
        await asyncio.sleep(random.uniform(1, 3))
    json.dump(prev, open(OUT, "w", encoding="utf-8"))
    ok = sum(1 for v in prev.values() if v == "ok")
    print(f"SUMMARY: checked={len(prev)} ok={ok}")

asyncio.run(main())
