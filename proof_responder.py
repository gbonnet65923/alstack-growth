# -*- coding: utf-8 -*-
"""Proof links for responder replies: find our accounts' messages in groups."""
import asyncio, json, os, shutil

from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.functions.channels import JoinChannelRequest

API_ID = 2040; API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"

async def main():
    stem = "igfhngp_633874480"
    dst = os.path.join(BASE, "verify", stem)
    if not os.path.exists(dst + ".session"):
        shutil.copy(os.path.join(SRC, stem + ".session"), dst + ".session")
    c = TelegramClient(dst, API_ID, API_HASH)
    await c.connect()
    rs = json.load(open(os.path.join(BASE, "responder_state.json"), encoding="utf-8"))
    ours = {h["acc"] for h in rs["history"]}
    groups = {}
    for fn in ["ai_groups_live.json", "live_groups_found.json"]:
        p = os.path.join(BASE, fn)
        if os.path.exists(p):
            for g in json.load(open(p, encoding="utf-8")):
                groups[g["channel"]] = g
    found_total = 0
    for gname in {h["g"] for h in rs["history"]}:
        g = groups.get(gname)
        if not g: continue
        try:
            if g.get("direct"):
                ent = await c.get_input_entity(gname)
                uname = gname
            else:
                chan = await c.get_entity(gname)
                try: await c(JoinChannelRequest(chan))
                except Exception: pass
                async for m in c.iter_messages(chan, limit=30):
                    if m.replies is not None and getattr(m.replies, "grouped_id", None):
                        await c(GetDiscussionMessageRequest(channel=chan, msg_id=m.id)); break
                ent = await c.get_input_entity(PeerChannel(channel_id=g["linked_id"]))
                e2 = await c.get_entity(ent)
                uname = e2.username
            hits = []
            async for m in c.iter_messages(ent, limit=120):
                if m.sender_id in ours and m.text:
                    link = f"https://t.me/{uname}/{m.id}" if uname else f"private id={g['linked_id']} msg={m.id}"
                    hits.append((str(m.date), m.text[:70], link))
            if hits:
                found_total += len(hits)
                print(f"### {g['title'][:42]} ({g.get('members')})")
                for d, t, l in hits[:4]:
                    print(f"  {t}\n    {l}")
        except Exception as e:
            print(f"{gname}: ERR {str(e)[:60]}")
        await asyncio.sleep(1)
    print("TOTAL responder msgs verified:", found_total)
    await c.disconnect()

asyncio.run(main())
