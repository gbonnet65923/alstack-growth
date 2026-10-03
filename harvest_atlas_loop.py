# -*- coding: utf-8 -*-
"""harvest_atlas_loop.py — endless atlas harvest with FloodWait rotation.
Rotates through clean sessions; on flood parks session until expiry; keeps going."""
import asyncio, json, os, random, shutil, time

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
ATLAS = r"C:/Users/User/tmp/insideads_clone/atlas_ai_public.json"
OUT = os.path.join(BASE, "atlas_groups.json")
WORK = os.path.join(BASE, "atlas_harvesters")
os.makedirs(WORK, exist_ok=True)
import sys
sys.path.insert(0, BASE)
from pool_filter import is_ai

SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"

def all_sessions():
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    out = []
    for stem in clean:
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

def candidates():
    atlas = json.load(open(ATLAS, encoding="utf-8"))
    groups = load_out()
    done = {g.get("channel") for g in groups}
    cands = []
    for e in atlas:
        un = (e.get("username") or "").replace("@", "").strip()
        if not un or un in done: continue
        if not is_ai({"channel": un, "title": e.get("title") or ""}): continue
        cands.append(un)
    random.shuffle(cands)
    return cands, groups

async def harvest_one(path, cands, groups, known, budget):
    """Harvest until budget or flood. Returns (done, flood_seconds)."""
    c = TelegramClient(path, API_ID, API_HASH, connection_retries=2, sequential_updates=True)
    await c.connect()
    if not await c.is_user_authorized():
        await c.disconnect()
        return 0, None
    n = 0
    flood = None
    for un in cands:
        if n >= budget: break
        try:
            ent = await c.get_entity(un)
        except errors.FloodWaitError as e:
            flood = e.seconds; break
        except Exception:
            continue
        try:
            await c(JoinChannelRequest(ent))
        except errors.FloodWaitError as e:
            flood = e.seconds; break
        except Exception:
            pass
        try:
            full = await c(GetFullChannelRequest(channel=ent))
        except errors.FloodWaitError as e:
            flood = e.seconds; break
        except Exception:
            n += 1; continue
        f = full.full_chat
        linked = getattr(f, "linked_chat_id", None)
        n += 1
        if linked and linked not in known:
            gtitle = ""; gmembers = 0
            for ch in full.chats:
                if ch.id == linked:
                    gtitle = getattr(ch, "title", "") or ""
                    gmembers = getattr(ch, "participants_count", 0) or 0
                    break
            entry = {"channel": str(ent.username or un),
                     "title": gtitle or (getattr(ent, "title", "") or ""),
                     "linked_id": linked, "members": gmembers}
            if is_ai(entry):
                groups.append(entry)
                known.add(linked)
                save_out(groups)
                print(f"  {entry['channel']} -> group {linked} '{gtitle[:40]}' ({gmembers})", flush=True)
        await asyncio.sleep(random.uniform(3, 7))
    try: await c.disconnect()
    except Exception: pass
    return n, flood

async def main():
    paths = all_sessions()
    random.shuffle(paths)
    print("sessions:", len(paths), flush=True)
    parked = {}  # path -> resume_ts
    pi = 0
    while True:
        cands, groups = candidates()
        if not cands:
            print("atlas exhausted, sleep 1h", flush=True)
            await asyncio.sleep(3600)
            continue
        known = {g.get("linked_id") for g in groups}
        # pick next non-parked session
        picked = None
        for _ in range(len(paths)):
            p = paths[pi % len(paths)]; pi += 1
            if parked.get(p, 0) <= time.time():
                picked = p; break
        if not picked:
            wait = min(parked.values()) - time.time()
            print(f"all sessions parked, sleep {int(wait)}s", flush=True)
            await asyncio.sleep(max(wait, 30))
            continue
        try:
            n, flood = await harvest_one(picked, cands, groups, known, budget=60)
        except Exception as e:
            print("session err:", str(e)[:80], flush=True)
            parked[picked] = time.time() + 600
            continue
        if flood:
            parked[picked] = time.time() + flood + 60
            print(f"[park] {os.path.basename(picked)} flood {flood}s -> total groups {len(groups)}", flush=True)
        else:
            print(f"[done] {os.path.basename(picked)} n={n} total groups {len(groups)}", flush=True)
        await asyncio.sleep(random.uniform(20, 60))

asyncio.run(main())
