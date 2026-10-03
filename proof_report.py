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
    live=json.load(open(os.path.join(BASE,"ai_groups_live.json"),encoding="utf-8"))
    proof=[]
    for g in live:
        try:
            chan=await c.get_entity(g["channel"])
            try: await c(JoinChannelRequest(chan))
            except Exception: pass
            async for m in c.iter_messages(chan,limit=30):
                if m.replies is not None and getattr(m.replies,"grouped_id",None):
                    await c(GetDiscussionMessageRequest(channel=chan,msg_id=m.id)); break
            ent=await c.get_input_entity(PeerChannel(channel_id=g["linked_id"]))
            found=[]
            async for m in c.iter_messages(ent,limit=60):
                if m.text and ("alstack" in m.text.lower() or "абузы" in m.text.lower() or "халявн" in m.text.lower()):
                    nm=""
                    try:
                        u=await c.get_entity(m.sender_id); nm=u.first_name or ""
                    except Exception: nm=str(m.sender_id)
                    found.append({"id":m.id,"date":str(m.date),"who":nm,"text":m.text[:90]})
            if found:
                proof.append({"channel":g["channel"],"title":g["title"],"members":g["members"],"msgs":found})
                print(f"\n=== {g['channel']} | {g['title'][:40]} | {g['members']} members ===")
                for f in found:
                    print(f"  msg_id={f['id']} [{f['date']}] {f['who']}: {f['text']}")
        except Exception as e:
            print(f"{g['channel']}: ERR {str(e)[:60]}")
        await asyncio.sleep(1)
    json.dump(proof,open(os.path.join(BASE,"proof_report.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("\nTOTAL groups with proof:",len(proof))
    await c.disconnect()
asyncio.run(main())
