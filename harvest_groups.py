"""Harvest linked discussion groups of AI channels (crosspromo.db + donors_ai.json).
Uses ONE session (Abex37). Output: ai_groups.json [{channel, title, linked_id, members}]"""
import asyncio, json, os, random, sqlite3

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
import shutil
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
def fresh_session():
    import json as _j
    clean = _j.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    random.shuffle(clean)
    for stem in clean:
        src_f = os.path.join(SRC, stem + ".session")
        dst = os.path.join(BASE, "harvesters", stem)
        if not os.path.exists(dst + ".session") and os.path.exists(src_f):
            shutil.copy(src_f, dst + ".session")
            return dst
        if os.path.exists(dst + ".session"):
            return dst
    return None
PATH = fresh_session()

def channel_usernames():
    db = r"C:/Users/User/tmp/insideads_clone/crosspromo.db"
    con = sqlite3.connect(db)
    rows = con.execute("SELECT username, title, subs FROM channels WHERE username != '' ORDER BY subs DESC").fetchall()
    con.close()
    ai = json.load(open(os.path.join(BASE, "donors_ai.json"), encoding="utf-8"))
    ai_un = {a["un"] for a in ai if a.get("un")}
    out = []
    for un, title, subs in rows:
        if un in ai_un or un == "ai_python":
            out.append(un)
    return out

async def main():
    c = TelegramClient(PATH, API_ID, API_HASH, connection_retries=2)
    await c.connect()
    groups = []
    prev_f = os.path.join(BASE, "ai_groups.json")
    if os.path.exists(prev_f):
        groups = json.load(open(prev_f, encoding="utf-8"))
    known = {g["channel"] for g in groups}
    cands = [u for u in channel_usernames() if u not in known]
    random.shuffle(cands)
    print("candidates:", len(cands))
    for un in cands:
        if len(groups) >= 150: break
        try:
            ent = await c.get_entity(un)
            try:
                await c(JoinChannelRequest(ent))
            except Exception:
                pass
            full = await c(GetFullChannelRequest(channel=ent))
            linked = full.full_chat.linked_chat_id
            if not linked:
                print(f"  {un}: no linked group"); continue
            try:
                g = await c.get_entity(linked)
                title = g.title
                members = getattr(g, "participants_count", None)
                if members is None:
                    gf = await c(GetFullChannelRequest(channel=g))
                    members = gf.full_chat.participants_count
            except Exception as e:
                title = "?"; members = -1
            gun = getattr(g, "username", None)
            groups.append({"channel": un, "title": title, "linked_id": linked, "members": members, "group_un": gun})
            print(f"  {un} -> group {linked} '{title}' ({members} members)")
            json.dump(groups, open(prev_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            await asyncio.sleep(random.uniform(3, 7))
        except errors.FloodWaitError as e:
            print(f"FLOOD {e.seconds}s — stopping"); break
        except Exception as e:
            print(f"  {un}: ERR {str(e)[:80]}")
    await c.disconnect()
    print("TOTAL groups:", len(groups))

asyncio.run(main())
