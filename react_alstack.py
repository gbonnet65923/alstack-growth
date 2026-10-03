# -*- coding: utf-8 -*-
"""
Reactions on @AlStack posts from farm accounts. NO comments — reactions only.
Each account reacts to the last few posts with a random emoji (🔥 👍 ❤️ etc).
Usage: python react_alstack.py [N] (accounts per run, default 30)
"""
import asyncio, json, os, random, shutil, sys

from telethon import TelegramClient, errors
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "reactors")
PROG = os.path.join(BASE, "react_progress.json")
os.makedirs(WORK, exist_ok=True)

EMOJIS = ["🔥", "👍", "❤", "🎉", "👏", "💯"]

def load_prog():
    if os.path.exists(PROG): return set(json.load(open(PROG, encoding="utf-8")))
    return set()

def save_prog(s): json.dump(sorted(s), open(PROG, "w", encoding="utf-8"))

async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    done = load_prog()
    todo = [s for s in clean if s not in done][:n]
    print("to react:", len(todo), "| already:", len(done))
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
            msgs = await c.get_messages(ent, limit=3)
            n_re = 0
            for m in msgs:
                if m.id is None: continue
                try:
                    await c(SendReactionRequest(peer=ent, msg_id=m.id, reaction=[ReactionEmoji(emoticon=random.choice(EMOJIS))], big=False))
                    n_re += 1
                except errors.FloodWaitError as e:
                    print(f"  {stem}: FLOOD {e.seconds}s — stop run")
                    await c.disconnect(); save_prog(done); return
                except Exception as e:
                    print(f"  {stem}: react err {str(e)[:50]}")
                await asyncio.sleep(random.uniform(4, 12))
            if n_re:
                ok += 1
                print(f"  {stem}: {n_re} reactions")
            done.add(stem)
            save_prog(done)
            await c.disconnect()
            await asyncio.sleep(random.uniform(3, 10))
        except Exception as e:
            print(f"  {stem}: CRASH {str(e)[:60]}")
    save_prog(done)
    print(f"REACTED: {ok} accounts (progress {len(done)}/{len(clean)})")

asyncio.run(main())
