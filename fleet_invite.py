"""
Fleet inviter for иишко Chat (id 4430207146).
Each worker account harvests donor group members INTO ITS OWN SESSION
(otherwise get_input_entity fails with PeerIdInvalid), then invites.
Donor: DLeX AI Python linked group (1033207416).
Rate: max N adds/account/run, 8-20s pause, retire on ban/flood.
State: inviter_state.json. Usage: python fleet_invite.py [--limit-per-acc 10] [--workers 5]
"""
import asyncio, json, os, random, shutil, sys, time

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest, GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsRecent, InputPeerChannel, PeerChannel
from telethon.tl.functions.messages import ImportChatInviteRequest

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
CHAT_ID = 4430207146
DONOR_GROUP = 1033207416  # linked chat of @ai_python
TARGET_HASH = 3093626362748681171
DONOR_HASH = 1228602166823654129
INVITE_HASH = "h3Su0z0zl-M3NWNi"

BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC_SESSIONS = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORKERS = os.path.join(BASE, "inviters")
STATE_FILE = os.path.join(BASE, "inviter_state.json")
EXCLUDED = {"8348347899", "7068444489", "7448683285", "809951394"}

os.makedirs(WORKERS, exist_ok=True)

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE, encoding="utf-8"))
    return {"invited": [], "per_acc": {}, "retired": {}, "log": []}

def save_state(st):
    tmp = STATE_FILE + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, STATE_FILE)

def pick_workers(n):
    # only sessions verified clean by check_spambot.py
    clean = set()
    cf = os.path.join(BASE, "spambot_classified.json")
    if os.path.exists(cf):
        clean = set(json.load(open(cf, encoding="utf-8")).get("ok", []))
    files = [f for f in os.listdir(SRC_SESSIONS) if f.endswith(".session") and f[:-8] in clean]
    random.shuffle(files)
    out = []
    for f in files:
        if len(out) >= n: break
        stem = f[:-8]
        if any(x in stem for x in EXCLUDED): continue
        if any(stem.endswith("_" + x) for x in EXCLUDED): continue
        dst = os.path.join(WORKERS, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(os.path.join(SRC_SESSIONS, f), dst + ".session")
            except Exception: continue
        out.append(dst)
    return out

async def run_account(path, limit, global_invited):
    stem = os.path.basename(path)
    client = TelegramClient(path, API_ID, API_HASH, connection_retries=2)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect(); return {"stem": stem, "err": "NOT AUTH"}
    me = await client.get_me()
    result = {"stem": stem, "id": me.id, "added": 0, "privacy": 0, "flood": None, "retired": False}
    try:
        # join donor group (caches members into THIS session)
        # join target chat via invite link (needed to invite others)
        try:
            await client(ImportChatInviteRequest(hash=INVITE_HASH))
        except errors.FloodWaitError as e:
            result["flood"] = e.seconds; await client.disconnect(); return result
        except errors.UserAlreadyParticipantError:
            pass
        except Exception:
            pass
        # each worker resolves the linked donor group itself (access_hash is per-session)
        try:
            chan = await client.get_entity("ai_python")
            full = await client(GetFullChannelRequest(channel=chan))
            linked = full.full_chat.linked_chat_id
            if linked:
                dent = await client.get_input_entity(PeerChannel(channel_id=linked))
            else:
                result["err"] = "donor has no linked group"; await client.disconnect(); return result
        except errors.FloodWaitError as e:
            result["flood"] = e.seconds; await client.disconnect(); return result
        except Exception as e:
            result["err"] = f"donor resolve: {str(e)[:70]}"; await client.disconnect(); return result
        part = await client(GetParticipantsRequest(dent, ChannelParticipantsRecent(), 0, 200, 0))
        cands = [u.id for u in part.users if not getattr(u,'bot',False) and not getattr(u,'deleted',False) and u.id not in global_invited and u.id != me.id]
        random.shuffle(cands)
        result["pool"] = len(cands)
        # resolve target from own session cache (joined above)
        tgt = None
        async for dlg in client.iter_dialogs():
            if dlg.entity.id == CHAT_ID:
                tgt = await client.get_input_entity(dlg.entity); break
        if tgt is None:
            try: tgt = await client.get_input_entity(PeerChannel(channel_id=CHAT_ID))
            except Exception:
                result["err"] = "target not resolved (join failed?)"; await client.disconnect(); return result
        for uid in cands:
            if result["added"] >= limit: break
            try:
                ue = await client.get_input_entity(uid)
                await client(InviteToChannelRequest(tgt, [ue]))
                result["added"] += 1
                global_invited.add(uid)
                await asyncio.sleep(random.uniform(8, 18))
            except errors.InviteRequestSentError:
                result["added"] += 1
                global_invited.add(uid)
                await asyncio.sleep(random.uniform(8, 18))
            except errors.FloodWaitError as e:
                result["flood"] = e.seconds; break
            except errors.UserPrivacyRestrictedError:
                result["privacy"] += 1
            except errors.UserNotMutualContactError:
                result["privacy"] += 1
            except (errors.UserAlreadyParticipantError, errors.UserChannelsTooMuchError, errors.PeerIdInvalidError):
                continue
            except errors.ChatAdminRequiredError:
                result["retired"] = True; result["err"] = "admin required"; break
            except errors.UserBannedInChannelError:
                result["retired"] = True; result["err"] = "spam-limited"; break
            except Exception as e:
                result.setdefault("other_err", str(e)[:80]); break
    except Exception as e:
        result["err"] = str(e)[:120]
    try: await client.disconnect()
    except Exception: pass
    return result

async def main():
    limit = 10; nworkers = 5
    args = sys.argv[1:]
    if "--limit-per-acc" in args: limit = int(args[args.index("--limit-per-acc") + 1])
    if "--workers" in args: nworkers = int(args[args.index("--workers") + 1])

    st = load_state()
    global_invited = set(st["invited"])
    workers = pick_workers(nworkers)
    print(f"workers={len(workers)} limit={limit} already_invited={len(global_invited)}")
    for wp in workers:
        stem = os.path.basename(wp)
        if stem in st["retired"]:
            print(f"  {stem}: retired, skip"); continue
        if st["per_acc"].get(stem, 0) >= 40:
            print(f"  {stem}: daily cap (40), skip"); continue
        print(f"  running {stem} ...")
        r = await run_account(wp, limit, global_invited)
        st["per_acc"][stem] = st["per_acc"].get(stem, 0) + r.get("added", 0)
        if r.get("retired") or r.get("flood"):
            st["retired"][stem] = {"ts": time.time(), "why": r.get("err") or f"flood {r.get('flood')}"}
        st["log"].append({**r, "ts": time.time()})
        st["invited"] = list(global_invited)
        save_state(st)
        print(f"    -> added={r.get('added',0)} pool={r.get('pool','-')} privacy={r.get('privacy',0)} flood={r.get('flood')} err={r.get('err')}")
        await asyncio.sleep(random.uniform(15, 40))
    save_state(st)
    print(f"RUN TOTAL invited: {len(global_invited)}")

asyncio.run(main())
