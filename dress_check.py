"""Check dress state (photo/username/bio) of clean sessions + find linked AI discussion groups."""
import asyncio, json, os, random, shutil

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"

async def main():
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    print("clean sessions:", len(clean))
    # sample 8 for dress check
    sample = random.sample(clean, min(8, len(clean)))
    work = os.path.join(BASE, "dresscheck")
    os.makedirs(work, exist_ok=True)
    undressed = 0
    for stem in sample:
        src_f = os.path.join(SRC, stem + ".session")
        if not os.path.exists(src_f): continue
        dst = os.path.join(work, stem)
        if not os.path.exists(dst + ".session"):
            shutil.copy(src_f, dst + ".session")
        try:
            c = TelegramClient(dst, API_ID, API_HASH, connection_retries=1)
            await c.connect()
            if not await c.is_user_authorized():
                print(f"  {stem}: NOT AUTH"); await c.disconnect(); continue
            me = await c.get_me()
            has_photo = bool(me.photo)
            print(f"  {stem}: name={me.first_name!r} photo={has_photo} username={me.username}")
            if not has_photo: undressed += 1
            await c.disconnect()
        except Exception as e:
            print(f"  {stem}: ERR {str(e)[:80]}")
    print("undressed in sample:", undressed, "/", len(sample))

asyncio.run(main())
