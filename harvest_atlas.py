# -*- coding: utf-8 -*-
"""harvest_atlas.py — harvest linked discussion groups from gramgpt atlas (3496 AI channels).
Output: atlas_groups.json [{channel, title, linked_id, members}] — merge_pool picks it up."""
import asyncio, json, os, random, shutil, sys

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.types import Chat, Channel, ChannelFull

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
ATLAS = r"C:/Users/User/tmp/insideads_clone/atlas_ai_public.json"
OUT = os.path.join(BASE, "atlas_groups.json")
WORK = os.path.join(BASE, "atlas_harvesters")
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, BASE)
from pool_filter import is_ai

SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"

def session_paths(n=3):
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    random.shuffle(clean)
    out = []
    for stem in clean:
        if len(out) >= n: break
        src_f = os.path.join(SRC, stem + ".session")
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session") and os.path.exists(src_f):
            try: shutil.copy(src_f, dst + ".session")
            except Exception: continue
        if os.path.exists(dst + ".session"):
            out.append(dst)
    return out

def load_out():
    try: return json.load(open(OUT, encoding="utf-8"))
    except Exception: return []

def save_out(g):
    tmp = OUT + ".tmp"
    json.dump(g, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)

async def harvest(client, cands, groups, known, per_client=400):
    n = 0
    for un in cands:
        if n >= per_client: break
        try:
            ent = await client.get_entity(un)
        except Exception:
            continue
        try:
            await client(JoinChannelRequest(ent))
        except errors.FloodWaitError as e:
            print(f"FLOOD {e.seconds}s — client done", flush=True)
            return n
        except Exception:
            pass
        try:
            full = await client(GetFullChannelRequest(channel=ent))
        except errors.FloodWaitError as e:
            print(f"FLOOD {e.seconds}s — client done", flush=True)
            return n
        except Exception:
            continue
        f = full.full_chat
        linked = getattr(f, "linked_chat_id", None)
        if not linked or linked in known:
            n += 1
            continue
        gtitle = ""
        gmembers = 0
        for ch in full.chats:
            if ch.id == linked:
                gtitle = getattr(ch, "title", "") or ""
                gmembers = getattr(ch, "participants_count", 0) or 0
                break
        entry = {"channel": str(ent.username or un), "title": gtitle or (getattr(ent, "title", "") or ""),
                 "linked_id": linked, "members": gmembers}
        if not is_ai(entry):
            n += 1
            continue
        groups.append(entry)
        known.add(linked)
        save_out(groups)
        print(f"  {entry['channel']} -> group {linked} '{gtitle}' ({gmembers} members)", flush=True)
        n += 1
        await asyncio.sleep(random.uniform(1.5, 4))
    return n

async def main():
    atlas = json.load(open(ATLAS, encoding="utf-8"))
    random.shuffle(atlas)
    groups = load_out()
    known = {g.get("linked_id") for g in groups}
    done_channels = {g.get("channel") for g in groups}
    cands = []
    for e in atlas:
        un = (e.get("username") or "").replace("@", "").strip()
        if not un or un in done_channels: continue
        probe = {"channel": un, "title": e.get("title") or ""}
        if not is_ai(probe): continue
        cands.append(un)
    print("atlas:", len(atlas), "| candidates (AI-filtered, new):", len(cands), flush=True)
    paths = session_paths(3)
    print("sessions:", len(paths), flush=True)
    tasks = []
    chunk = (len(cands) + len(paths) - 1) // max(len(paths), 1)
    clients = []
    for i, p in enumerate(paths):
        c = TelegramClient(p, API_ID, API_HASH, connection_retries=2, sequential_updates=True)
        await c.connect()
        if not await c.is_user_authorized():
            await c.disconnect(); continue
        clients.append((c, cands[i*chunk:(i+1)*chunk]))
    for c, sl in clients:
        tasks.append(harvest(c, sl, groups, known))
    await asyncio.gather(*tasks, return_exceptions=True)
    for c, _ in clients:
        try: await c.disconnect()
        except Exception: pass
    save_out(groups)
    print("TOTAL atlas groups:", len(groups), flush=True)

asyncio.run(main())
