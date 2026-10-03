# -*- coding: utf-8 -*-
"""Subscribe all clean accounts to @AlStack channel (real subscriber growth).
Usage: python sub_alstack.py [N]  (N = accounts to process this run, default 40)
"""
import asyncio, json, os, random, shutil, sys, time

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "subs")
PROG = os.path.join(BASE, "sub_progress.json")
os.makedirs(WORK, exist_ok=True)

def load_prog():
    if os.path.exists(PROG): return set(json.load(open(PROG, encoding="utf-8")))
    return set()

def save_prog(s):
    json.dump(sorted(s), open(PROG, "w", encoding="utf-8"))

async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    done = load_prog()
    todo = [s for s in clean if s not in done][:n]
    print("to sub:", len(todo), "| already:", len(done))
    ok = 0
    for stem in todo:
        src_f = os.path.join(SRC, stem + ".session")
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(src_f, dst + ".session")
            except Exception: continue
        try:
            c = TelegramClient(dst, API_ID, API_HASH, connection_retries=1)
            await c.connect()
            if not await c.is_user_authorized():
                await c.disconnect(); done.add(stem); continue
            ent = await c.get_entity("AlStack")
            try:
                await c(JoinChannelRequest(ent))
                ok += 1
                print(f"  {stem}: JOINED @AlStack")
            except errors.FloodWaitError as e:
                print(f"  {stem}: FLOOD {e.seconds}s — stop run"); await c.disconnect(); break
            except errors.ChannelPrivateError:
                print("  channel private?! stop"); await c.disconnect(); break
            except Exception as e:
                if "already" in str(e).lower(): ok += 1
                else: print(f"  {stem}: ERR {str(e)[:60]}")
            done.add(stem)
            save_prog(done)
            await c.disconnect()
            await asyncio.sleep(random.uniform(3, 9))
        except Exception as e:
            print(f"  {stem}: CRASH {str(e)[:60]}")
    save_prog(done)
    print(f"SUBBED: {ok} (progress {len(done)}/{len(clean)})")

asyncio.run(main())
