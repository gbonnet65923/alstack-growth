import asyncio, os, shutil
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.functions.channels import JoinChannelRequest

API_ID = 2040; API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
# content_kuhnya group id from ai_groups.json
import json
groups = json.load(open(os.path.join(BASE,"ai_groups.json"),encoding="utf-8"))
g = next(x for x in groups if x["channel"]=="content_kuhnya")
gid = g["linked_id"]
print("group:", g["title"], gid)

async def main():
    stem = "igfhngp_633874480"
    dst = os.path.join(BASE,"seeders",stem)
    if not os.path.exists(dst+".session"): shutil.copy(os.path.join(SRC,stem+".session"), dst+".session")
    c = TelegramClient(dst, API_ID, API_HASH)
    await c.connect()
    chan = await c.get_entity(g["channel"])
    try: await c(JoinChannelRequest(chan))
    except Exception: pass
    async for m in c.iter_messages(chan, limit=25):
        if m.replies is not None and getattr(m.replies,"grouped_id",None):
            await c(GetDiscussionMessageRequest(channel=chan, msg_id=m.id))
            break
    ent = await c.get_input_entity(PeerChannel(channel_id=gid))
    msgs = await c.get_messages(ent, limit=10)
    for m in msgs:
        print(f"[{m.date}] {m.sender_id}: {str(m.text)[:90]}")
    await c.disconnect()
asyncio.run(main())
