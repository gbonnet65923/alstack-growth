# -*- coding: utf-8 -*-
"""enrich_new.py — resolve 205 new catalog channels -> linked discussion groups.
Output: ai_groups_new3.json (ai_groups.json format) + ai_channels_enriched.json.
Session rotation, FloodWait parking, budget per session. NEVER touch 7448683285 / 809951394."""
import asyncio, json, os, random, shutil, sys, time

BASE = r"C:/Users/User/tmp/tg_chat_grow"
RECON = r"C:/Users/User/tmp/tg_api_recon"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "enrichers")
os.makedirs(WORK, exist_ok=True)
os.chdir(BASE)

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PROTECT = {7448683285, 809951394}
BUDGET = 40  # resolves per session before rotate

OUT_GROUPS = os.path.join(BASE, "ai_groups_new3.json")
OUT_FULL = os.path.join(RECON, "ai_channels_enriched.json")
PROGRESS = os.path.join(BASE, "enrich_progress.json")

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetFullChannelRequest

def load_json(p, d):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d

def save_json(p, d):
    tmp = p + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, p)

# collect targets: phase1 (190) + phase2 (15), drop bots
targets = []
seen = set()
for f in ("ai_channels_new.json", "ai_channels_new2.json"):
    for r in load_json(os.path.join(RECON, f), []):
        ch = r.get("channel", "")
        if not ch or ch.startswith("+") or ch in seen:
            continue
        if r.get("type") == "bot":
            continue
        seen.add(ch)
        targets.append(r)
random.shuffle(targets)

progress = load_json(PROGRESS, {})  # channel -> result dict
groups = load_json(OUT_GROUPS, [])
group_keys = {(g.get("linked_id") or g.get("channel")) for g in groups}

def pending():
    return [t for t in targets if t["channel"] not in progress]

def clean_sessions():
    ok = set(load_json(os.path.join(BASE, "spambot_classified.json"), {}).get("ok", []))
    out = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".session"):
            continue
        name = fn[:-8]
        if ok and name not in ok:
            continue
        out.append(name)
    return out

parked = set(load_json(os.path.join(BASE, "enrich_parked.json"), []))

async def run_session(sess_name, queue):
    sf = os.path.join(SRC, sess_name + ".session")
    wf = os.path.join(WORK, sess_name + ".session")
    if not os.path.exists(wf):
        shutil.copy(sf, wf)
        for ext in ("-journal", "-wal", "-shm"):
            p = sf + ext
            if os.path.exists(p):
                shutil.copy(p, wf + ext)
    client = TelegramClient(wf, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        parked.add(sess_name)
        return "unauth", 0
    me = await client.get_me()
    if me.id in PROTECT:
        await client.disconnect()
        return "protect", 0
    done = 0
    while queue and done < BUDGET:
        t = queue[0]
        ch = t["channel"]
        try:
            ent = await client.get_entity(ch)
            full = await client(GetFullChannelRequest(ent))
            fc = full.full_chat
            linked = getattr(fc, "linked_chat_id", None)
            members = getattr(fc, "participants_count", None) or t.get("members")
            rec = {
                "channel": ch, "title": t.get("title") or getattr(ent, "title", "") or "",
                "members": members, "linked_id": linked,
                "type": "supergroup" if getattr(ent, "megagroup", False) else "channel",
            }
            progress[ch] = rec
            queue.pop(0)
            done += 1
            if linked and linked not in group_keys:
                groups.append({"channel": ch, "title": rec["title"], "linked_id": linked, "members": members})
                group_keys.add(linked)
            elif rec["type"] == "supergroup" and (rec["members"] or 0) >= 20 and ch not in group_keys:
                groups.append({"channel": ch, "title": rec["title"], "members": members, "direct": True})
                group_keys.add(ch)
            if done % 10 == 0:
                save_json(PROGRESS, progress)
                save_json(OUT_GROUPS, groups)
                save_json(os.path.join(BASE, "enrich_parked.json"), sorted(parked))
                print(f"[{sess_name}] {done} resolves, queue {len(queue)}", flush=True)
            await asyncio.sleep(random.uniform(1.0, 2.5))
        except errors.FloodWaitError as e:
            print(f"[{sess_name}] FloodWait {e.seconds}s -> park", flush=True)
            parked.add(sess_name)
            save_json(os.path.join(BASE, "enrich_parked.json"), sorted(parked))
            break
        except (errors.UsernameNotOccupiedError, errors.UsernameInvalidError):
            progress[ch] = {"channel": ch, "error": "not_found"}
            queue.pop(0)
        except errors.ChannelPrivateError:
            progress[ch] = {"channel": ch, "error": "private"}
            queue.pop(0)
        except Exception as e:
            print(f"[{sess_name}] {ch} ERR {type(e).__name__}: {str(e)[:80]}", flush=True)
            progress[ch] = {"channel": ch, "error": type(e).__name__}
            queue.pop(0)
    save_json(PROGRESS, progress)
    save_json(OUT_GROUPS, groups)
    try:
        await client.disconnect()
    except Exception:
        pass
    return "ok", done

async def main():
    queue = pending()
    print(f"targets total={len(targets)} pending={len(queue)}", flush=True)
    sess_list = [s for s in clean_sessions() if s not in parked]
    random.shuffle(sess_list)
    print(f"sessions available: {len(sess_list)}", flush=True)
    for s in sess_list:
        if not queue:
            break
        st, n = await run_session(s, queue)
        print(f"[main] {s}: {st}, {n} resolves, queue {len(queue)}", flush=True)
        if st == "unauth":
            continue
        await asyncio.sleep(random.uniform(3, 8))
    # final save
    save_json(PROGRESS, progress)
    save_json(OUT_GROUPS, groups)
    enriched = list(progress.values())
    save_json(OUT_FULL, enriched)
    with_linked = sum(1 for r in enriched if r.get("linked_id"))
    with_direct = sum(1 for r in enriched if r.get("type") == "supergroup")
    print(f"DONE enriched={len(enriched)} linked_groups={with_linked} supergroups={with_direct} groups_file={len(groups)}", flush=True)

asyncio.run(main())
