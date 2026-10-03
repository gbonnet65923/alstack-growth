# -*- coding: utf-8 -*-
"""One-shot: react N farm accounts to specific new @AlStack msg ids.
Usage: python react_new.py <msg_id> <msg_id> ... [--n 40]
"""
import asyncio, json, os, random, shutil, sys

from telethon import TelegramClient, errors
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji, ReactionCustomEmoji

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "reactors")
EMOJIS = ["🔥", "👍", "❤", "🎉", "👏", "💯"]
CUSTOM = json.load(open(os.path.join(BASE, "alstack_reactions.json"), encoding="utf-8")) if os.path.exists(os.path.join(BASE, "alstack_reactions.json")) else []

def main_args():
    ids, n = [], 40
    a = sys.argv[1:]
    if "--n" in a:
        n = int(a[a.index("--n")+1]); a.remove(str(n)); a.remove("--n")
    ids = [int(x) for x in a]
    return ids, n

async def run():
    ids, n = main_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    random.shuffle(clean)
    todo = clean[:n]
    print(f"reacting {len(todo)} accounts to msg ids {ids}")
    ok = 0
    for stem in todo:
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(os.path.join(SRC, stem + ".session"), dst + ".session")
            except Exception: continue
        try:
            c = TelegramClient(dst, API_ID, API_HASH, connection_retries=1)
            await c.connect()
            if not await c.is_user_authorized():
                await c.disconnect(); continue
            ent = await c.get_entity("AlStack")
            nre = 0
            for mid in ids:
                try:
                    if CUSTOM:
                        re = ReactionCustomEmoji(document_id=random.choice(CUSTOM))
                    else:
                        re = ReactionEmoji(emoticon=random.choice(EMOJIS))
                    await c(SendReactionRequest(peer=ent, msg_id=mid,
                        reaction=[re], big=random.random() < 0.15))
                    nre += 1
                except errors.FloodWaitError as e:
                    print(f"  {stem}: FLOOD {e.seconds}s"); await c.disconnect(); return
                except Exception as e:
                    print(f"  {stem}: err {str(e)[:50]}")
                await asyncio.sleep(random.uniform(4, 12))
            if nre:
                ok += 1
                print(f"  {stem}: {nre} reactions")
            await c.disconnect()
            await asyncio.sleep(random.uniform(3, 10))
        except Exception as e:
            print(f"  {stem}: CRASH {str(e)[:60]}")
    print(f"DONE: {ok}/{len(todo)} accounts reacted")

asyncio.run(run())
