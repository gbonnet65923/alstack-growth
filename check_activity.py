# -*- coding: utf-8 -*-
"""Activity check: count human messages in last 7 days per harvested group.
Writes ai_groups_live.json (only groups with >= MIN_HUMAN human msgs).
Usage: python check_activity.py
"""
import asyncio, json, os, random, shutil, time, datetime

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.types import PeerChannel

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "activitycheck")
MIN_HUMAN = 4
os.makedirs(WORK, exist_ok=True)

async def resolve(client, g):
    try:
        chan = await client.get_entity(g["channel"])
        try: await client(JoinChannelRequest(chan))
        except Exception: pass
        async for m in client.iter_messages(chan, limit=25):
            if m.replies is not None and getattr(m.replies, "grouped_id", None):
                try:
                    await client(GetDiscussionMessageRequest(channel=chan, msg_id=m.id)); break
                except Exception: continue
        return await client.get_input_entity(PeerChannel(channel_id=g["linked_id"]))
    except Exception:
        return None

async def main():
    stem = "igfhngp_633874480"
    dst = os.path.join(WORK, stem)
    if not os.path.exists(dst + ".session"):
        shutil.copy(os.path.join(SRC, stem + ".session"), dst + ".session")
    c = TelegramClient(dst, API_ID, API_HASH, connection_retries=2)
    await c.connect()
    groups = json.load(open(os.path.join(BASE, "ai_groups.json"), encoding="utf-8"))
    out_f = os.path.join(BASE, "ai_groups_live.json")
    live = []
    if os.path.exists(out_f):
        live = json.load(open(out_f, encoding="utf-8"))
    done = {g["channel"] for g in live} | set(json.load(open(os.path.join(BASE, "seed_state.json"), encoding="utf-8")).get("dead", []))
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    for g in groups:
        if g["channel"] in done: continue
        if (g.get("members") or 0) < 10:
            print(f"  {g['channel']}: SKIP small ({g.get('members')})"); continue
        ent = await resolve(c, g)
        if ent is None:
            print(f"  {g['channel']}: SKIP unresolved"); continue
        try:
            msgs = await c.get_messages(ent, limit=60, offset_date=int(time.time()))
        except Exception as e:
            print(f"  {g['channel']}: ERR {str(e)[:50]}"); continue
        human = [m for m in msgs if m.text and m.sender_id and m.sender_id > 0 and m.date >= cutoff]
        senders = len({m.sender_id for m in human})
        print(f"  {g['channel']}: {len(human)} msgs / {senders} senders (7d)")
        if len(human) >= MIN_HUMAN and senders >= 2:
            g2 = dict(g); g2["recent_human"] = len(human); g2["recent_senders"] = senders
            live.append(g2)
            json.dump(live, open(out_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        await asyncio.sleep(random.uniform(3, 8))
    await c.disconnect()
    print(f"LIVE GROUPS: {len(live)}")

asyncio.run(main())
