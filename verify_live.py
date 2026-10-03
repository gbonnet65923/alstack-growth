import asyncio, json, os, shutil
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.functions.channels import JoinChannelRequest

API_ID=2040; API_HASH="b18441a1ff607e10a989891a5462e627"
BASE=r"C:/Users/User/tmp/tg_chat_grow"
SRC=r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"

async def main():
    stem="igfhngp_633874480"
    dst=os.path.join(BASE,"verify",stem); os.makedirs(os.path.dirname(dst),exist_ok=True)
    if not os.path.exists(dst+".session"): shutil.copy(os.path.join(SRC,stem+".session"),dst+".session")
    c=TelegramClient(dst,API_ID,API_HASH)
    await c.connect()
    live=json.load(open(os.path.join(BASE,"ai_groups_live.json"),encoding="utf-8"))
    for g in live[:6]:
        try:
            chan=await c.get_entity(g["channel"])
            try: await c(JoinChannelRequest(chan))
            except Exception: pass
            async for m in c.iter_messages(chan,limit=30):
                if m.replies is not None and getattr(m.replies,"grouped_id",None):
                    await c(GetDiscussionMessageRequest(channel=chan,msg_id=m.id)); break
            ent=await c.get_input_entity(PeerChannel(channel_id=g["linked_id"]))
            msgs=await c.get_messages(ent,limit=8)
            print(f"\n=== {g['channel']} ({g['title'][:35]}) ===")
            for m in msgs:
                if m.text:
                    nm=""
                    if m.sender_id and m.sender_id>0:
                        try:
                            u=await c.get_entity(m.sender_id); nm=u.first_name or ""
                        except Exception: nm=str(m.sender_id)
                    mark=" <<< MY REPLY" if "alstack" in m.text.lower() else ""
                    print(f"  [{m.date.strftime('%H:%M')}] {nm}: {m.text[:85]}{mark}")
        except Exception as e:
            print(f"\n=== {g['channel']}: ERR {str(e)[:60]}")
    await c.disconnect()
asyncio.run(main())
