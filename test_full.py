import asyncio, os, shutil
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
API_ID=2040; API_HASH="b18441a1ff607e10a989891a5462e627"
BASE=r"C:/Users/User/tmp/tg_chat_grow"; SRC=r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
async def main():
    stem="igfhngp_633874480"
    dst=os.path.join(BASE,"verify",stem)
    if not os.path.exists(dst+".session"): shutil.copy(os.path.join(SRC,stem+".session"),dst+".session")
    c=TelegramClient(dst,API_ID,API_HASH)
    await c.connect()
    for un in ["aigeneration_chat","webprogrammists","itdogchat","neuralforum"]:
        try:
            ent=await c.get_entity(un)
            full=await c(GetFullChannelRequest(channel=ent))
            fc=full.full_chat
            print(f"@{un}: title={ent.title!r} members={fc.participants_count} linked={fc.linked_chat_id} megagroup={ent.megagroup}")
        except Exception as e:
            print(f"@{un}: ERR {str(e)[:70]}")
    await c.disconnect()
asyncio.run(main())
