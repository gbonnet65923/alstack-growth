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
    dst=os.path.join(BASE,"verify",stem)
    if not os.path.exists(dst+".session"): shutil.copy(os.path.join(SRC,stem+".session"),dst+".session")
    c=TelegramClient(dst,API_ID,API_HASH)
    await c.connect()
    groups=[]
    for fn in ["ai_groups_live.json","live_groups_found.json"]:
        p=os.path.join(BASE,fn)
        if os.path.exists(p): groups+=json.load(open(p,encoding="utf-8"))
    total=0
    for g in groups:
        gid=g["linked_id"]
        try:
            if g.get("direct"):
                ent=await c.get_input_entity(g["channel"])
                uname=g["channel"]
            else:
                chan=await c.get_entity(g["channel"])
                try: await c(JoinChannelRequest(chan))
                except Exception: pass
                async for m in c.iter_messages(chan,limit=30):
                    if m.replies is not None and getattr(m.replies,"grouped_id",None):
                        await c(GetDiscussionMessageRequest(channel=chan,msg_id=m.id)); break
                ent=await c.get_input_entity(PeerChannel(channel_id=gid))
                uname=g.get("group_un") or None
                if uname is None:
                    e2=await c.get_entity(ent); uname=e2.username
            hits=[]
            async for m in c.iter_messages(ent,limit=100):
                if m.text and "alstack" in m.text.lower():
                    nm="?"
                    try:
                        u=await c.get_entity(m.sender_id); nm=u.first_name or "?"
                    except Exception: pass
                    if uname: link=f"https://t.me/{uname}/{m.id}"
                    else: link=f"id {gid} msg {m.id} (private)"
                    hits.append((nm,m.text[:70],link))
            if hits:
                total+=len(hits)
                print(f"### {g['title'][:40]} ({g.get('members')}) — {len(hits)} сообщений:")
                for nm,t,l in hits: print(f"  [{nm}] {t}\n    {l}")
        except Exception as e:
            pass
    print("TOTAL @AlStack mentions found:", total)
    await c.disconnect()
asyncio.run(main())
