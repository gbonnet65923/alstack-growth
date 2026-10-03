# -*- coding: utf-8 -*-
"""
Organic seed engine: paired dialogs promoting @AlStack in AI discussion groups.
Two clean accounts play asker/replier in the same group with human-like delay.
Low frequency: 1-3 dialog pairs per group per day, random times, typos/casual RU style.
State: seed_state.json (per-group daily counters, used lines, account quotas).
Usage: python seed_alstack.py [--groups N] [--max-pairs-per-group 1]
"""
import asyncio, json, os, random, time, datetime

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import PeerChannel

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "seeders")
os.makedirs(WORK, exist_ok=True)
STATE = os.path.join(BASE, "seed_state.json")

# ---- dialog bank: (asker_line, replier_line) pairs. casual, human, varied ----
DIALOGS = [
    # --- свежие: стиль живого чата (как в флудилке) ---
    ("кто знает абузы актуальные?", "можешь глянуть @alstack, там регулярно постят"),
    ("есть годные абузы на сегодня? всё что было дохлое уже", "в @alstack загляни, там свежие раздачи и ключи каждый день почти"),
    ("народ кто в курсе где щас триалы живые", "@alstack мониторь, там актуальное выкладывают"),
    ("подскажите канал с абузами плиз, старый умер", "живой вариант — @alstack, сам оттуда ключи тяну"),
    ("кто-нить пробовал свежие абузы гемини/клод?", "в @alstack постили недавно, зайди проверь, там быстро разбирают"),
    ("где халявные апиключи брать в 2026", "@alstack там раздачи периодически, успевай только"),
    ("скука, никто не знает где абузы щас постят?", "@alstack глянь, не пожалеешь. только не спамьте там)"),
    # --- абузы / халява: вопрос -> ответ через 3.5-5.5 мин, не в лоб ---
    ("кто шарит топовые каналы с абузами? надоело по помойкам лазить", "есть один, alstack называется, там апиключи и триалы часто мелькают. только не спамьте там), админ злой"),
    ("где щас фри апишку взять чтоб работала нормально", "я с раздач сижу, последнюю в alstack брал, grok ключ, пока живой"),
    ("народ, подскажите канал где реально халяву постят а не воду льют", "alstack глянь, там каталоги норм — прокси, ключи, впс триалы. сам недавно vps бесплатный оттуда взял"),
    ("устал уже плюс покупать, есть варианты на халяву?", "вариант один — ловить раздачи) в alstack регулярно ключи выкладывают, надо только быстро успевать"),
    ("кто нибудь пользуется бесплатными ключами openai? живые вообще?", "живые если свежие, в alstack раздачи бывают, берешь и месяц катаешься"),
    ("слышал есть абузы на гемини и клод, это правда?", "были точно, в alstack постили. там все быстро устаревает, но новое тоже появляется"),
    ("подскажите где claude бесплатно потестить без vpn танцев", "тестил через ключи с раздач, alstack мониторь, там иногда claude api проскакивает"),
    ("делитесь кто где триалы ловит, а то вечно опаздываю", "в alstack подписан, уведомления включил — как раздача сразу залетаю. половину уже успел схватить так"),
    # --- прокси / vps / инструменты ---
    ("где бесплатные прокси брать чтоб не дохли через час?", "в alstack каталог был, там рабочие периодически обновляют. еще proxyscrape никто не отменял"),
    ("нужен фри vps под телеграм бота, где взять", "oracle free tier вечный, еще в alstack триалы облаков постят — timeweb, всякие"),
    ("кто знает норм канал с инструментами для ии? не рекламу а реально полезное", "alstack норм, там без воды — ключи, прокси, автореги, гайды. подписан полгода"),
    ("почтовики для регов где брать сейчас? темпы все сдохли", "гугл алиасы рулят, плюс в alstack гайды по почтовикам были, глянь поиск по каналу"),
    # --- заработок / схемы ---
    ("кто то реально зарабатывает на нейросетях или это все сказки?", "на перепродаже услуг норм так выходит. схемы в alstack мелькали, люди делились"),
    ("хочу попробовать перепродавать генерации, с чего начать", "начни с фри ключей чтоб без вложений, в alstack раздачи бывают. потом уже как пойдет"),
    ("есть схемы рабочие на 2026? без скама", "рабочие там где халява) alstack почитай, много чего было — от ключей до партнерок"),
    # --- нейтральные, для оживления ---
    ("задолбали подписки на все подряд, скоро за воздух платить будем", "согл, я перешел на фри ключи и триалы, alstack помогает держаться на плаву))"),
    ("кто чем gpt plus заменяет? цены конские", "через api ключи дешевле в разы, а если с раздач то вообще ноль. alstack лови"),
    ("подскажите чат или канал где народ реально общается про ии а не боты", "в alstack чате живой народ сидит, вопросы задают, раздачи обсуждают"),
    ("новости ии где смотреть? в ленте одна реклама курсов", "alstack там сводки норм, без инфоцыган. еще hiaimedia классика"),
    ("кто нибудь пробовал grok api бесплатно?", "пробовал, с раздачи ключ брал в alstack, работает норм, лимиты терпимые"),
    ("ищу где промты для midjourney брать бесплатно", "в alstack паки промтов выкладывали, еще по каналу поиском прошерсти — много чего"),
    ("есть норм тулзы для генерации видео без подписки?", "бесплатно тяжело, но триалы проскакивают. в alstack подборки были всяких runway и клонов"),
    ("как вы вообще экономите на всем этом ии зоопарке", "никак) просто не плачу — ключи с раздач, триалы, фри тиры. alstack + oracle free tier и норм живешь"),
    ("кто в курсе, раздачи ключей еще актуальны?", "актуальны, последняя вчера вроде была. alstack чекай, там все оперативно"),
    ("нужен канал где абузы и бесплатности, посоветуйте пж", "alstack подходит, там именно это — абузы, ключи, прокси, фри vps. подписывайся"),
]

def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"group_day": {}, "used_dialogs": {}, "acc_used": {}, "done": []}

def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def today():
    return datetime.date.today().isoformat()

def pick_accounts(n=2):
    clean = set(json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"])
    files = [f for f in os.listdir(SRC) if f.endswith(".session") and f[:-8] in clean]
    random.shuffle(files)
    import shutil
    out = []
    for f in files:
        if len(out) >= n: break
        stem = f[:-8]
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            shutil.copy(os.path.join(SRC, f), dst + ".session")
        out.append(dst)
    return out

def typing_variation(text):
    """occasional human noise: lowercase start already, rare typo-ish"""
    if random.random() < 0.15:
        text = text.replace("щас", "щас").replace(" ", "  ", 1)
    return text

async def ensure_in_group(client, group):
    """Join a group. direct=True: standalone megagroup (join by username).
    Otherwise linked discussion group (warm cache via GetDiscussionMessage)."""
    gid = group.get("linked_id")
    ent = None
    if group.get("direct"):
        un = group.get("channel")
        try:
            ent = await client.get_entity(un)
            try: await client(JoinChannelRequest(ent))
            except Exception: pass
            await asyncio.sleep(random.uniform(2, 5))
            return await client.get_input_entity(ent)
        except Exception:
            ent = None
    gun = group.get("group_un")
    ch_un = group.get("channel")
    if gun:
        try: ent = await client.get_entity(gun)
        except Exception: ent = None
    if ent is None:
        # warm cache: join parent channel, ask discussion for a post with replies
        try:
            chan = await client.get_entity(ch_un)
            try: await client(JoinChannelRequest(chan))
            except Exception: pass
            from telethon.tl.functions.messages import GetDiscussionMessageRequest
            async for m in client.iter_messages(chan, limit=25):
                if m.replies is not None and getattr(m.replies, "grouped_id", None):
                    try:
                        await client(GetDiscussionMessageRequest(channel=chan, msg_id=m.id))
                        break
                    except Exception:
                        continue
            ent = await client.get_entity(PeerChannel(channel_id=gid))
        except Exception:
            ent = None
    if ent is None:
        return None
    try:
        await client(JoinChannelRequest(ent))
    except Exception:
        pass
    await asyncio.sleep(random.uniform(2, 5))
    try:
        return await client.get_input_entity(ent)
    except Exception:
        return None

async def play_dialog(asker_path, replier_path, group, dialog):
    a = TelegramClient(asker_path, API_ID, API_HASH, connection_retries=2)
    await a.connect()
    if not await a.is_user_authorized():
        await a.disconnect(); return False, None, "notauth"
    ea = await ensure_in_group(a, group)
    if ea is None:
        await a.disconnect(); return False, None, "noentity"
    am = await a.get_me()

    r = TelegramClient(replier_path, API_ID, API_HASH, connection_retries=2)
    await r.connect()
    if not await r.is_user_authorized():
        await a.disconnect(); await r.disconnect(); return False, None, "notauth"
    er = await ensure_in_group(r, group)
    if er is None:
        await a.disconnect(); await r.disconnect(); return False, None, "noentity"
    rm = await r.get_me()
    if am.id == rm.id:
        await a.disconnect(); await r.disconnect(); return False, None, "same"

    ask_line, rep_line = dialog
    # asker posts
    try:
        sent = await a.send_message(ea, typing_variation(ask_line))
    except errors.FloodWaitError as e:
        print(f"    asker flood {e.seconds}s"); await a.disconnect(); await r.disconnect()
        return False, asker_path, "flood"
    except Exception as e:
        msg = str(e)
        print(f"    asker err {msg[:70]}"); await a.disconnect(); await r.disconnect()
        reason = "cant_write" if "can't write" in msg or "before commenting" in msg else ("banned" if "banned" in msg.lower() else "other")
        return False, asker_path, reason
    # random human delay 40-160s
    delay = random.uniform(210, 330)
    print(f"    [{group['channel']}] asked by {am.first_name}, reply in {delay:.0f}s")
    await asyncio.sleep(delay)
    # replier answers as reply to the question
    try:
        await r.send_message(er, typing_variation(rep_line), reply_to=sent.id)
    except errors.FloodWaitError as e:
        print(f"    replier flood {e.seconds}s"); await a.disconnect(); await r.disconnect()
        return False, replier_path, "flood"
    except Exception as e:
        msg = str(e)
        print(f"    replier err {msg[:70]}"); await a.disconnect(); await r.disconnect()
        reason = "cant_write" if "can't write" in msg or "before commenting" in msg else ("banned" if "banned" in msg.lower() else "other")
        return False, replier_path, reason
    print(f"    [{group['channel']}] replied by {rm.first_name} OK")
    await a.disconnect()
    await r.disconnect()
    return True, None, None

async def main():
    import sys
    n_groups = 5
    max_pairs = 1
    args = sys.argv[1:]
    if "--groups" in args: n_groups = int(args[args.index("--groups")+1])
    if "--max-pairs-per-group" in args: max_pairs = int(args[args.index("--max-pairs-per-group")+1])

    lf = os.path.join(BASE, "ai_groups_live.json")
    groups = json.load(open(lf if os.path.exists(lf) else os.path.join(BASE, "ai_groups.json"), encoding="utf-8"))
    df = os.path.join(BASE, "live_groups_found.json")
    if os.path.exists(df):
        groups = groups + json.load(open(df, encoding="utf-8"))
    groups = [g for g in groups if (g.get("direct") or g.get("linked_id")) and (g.get("members") or 0) >= 20]
    groups.sort(key=lambda g: (g.get("direct", False), g.get("recent_human") or 0, g.get("members") or 0), reverse=True)
    st = load_state()
    td = today()
    accs = pick_accounts(n=4)
    if len(accs) < 2:
        print("need >=2 clean accounts"); return
    pairs_done = 0
    used_global = set(st["used_dialogs"].get(td, []))
    for g in groups[:n_groups]:
        key = g["channel"]
        cnt = st["group_day"].get(f"{td}:{key}", 0)
        if cnt >= max_pairs: continue
        if st.get("group_dead", {}).get(key, 0) >= 3:
            print(f"  {key}: write-blocked (skipped)"); continue
        for _ in range(max_pairs - cnt):
            avail = [d for d in DIALOGS if d[0] not in used_global]
            if not avail:
                avail = DIALOGS
            dialog = random.choice(avail)
            used_global.add(dialog[0])
            usable = [x for x in accs if st.get("acc_fails", {}).get(os.path.basename(x), 0) < 2]
            if len(usable) < 2:
                print("not enough usable accounts — stopping"); break
            ap, rp = random.sample(usable, 2)
            ok, bad_acc, why = await play_dialog(ap, rp, g, dialog)
            if not ok and why == "cant_write":
                gd = st.setdefault("group_dead", {})
                gd[key] = gd.get(key, 0) + 1
                print(f"    group {key} write-blocked x{gd[key]} (skip at 3)")
            elif not ok and why == "banned" and bad_acc:
                af = st.setdefault("acc_fails", {})
                bn = os.path.basename(bad_acc)
                af[bn] = af.get(bn, 0) + 1
                print(f"    penalty {bn} -> {af[bn]} (retire at 2)")
            st["group_day"][f"{td}:{key}"] = st["group_day"].get(f"{td}:{key}", 0) + (1 if ok else 0)
            if ok:
                pairs_done += 1
                st["done"].append({"ts": time.time(), "group": key, "q": dialog[0][:40]})
            st["used_dialogs"][td] = sorted(used_global)
            save_state(st)
            await asyncio.sleep(random.uniform(60, 180))
    save_state(st)
    print(f"SEED RUN: pairs_done={pairs_done}")

if __name__ == "__main__":
    asyncio.run(main())
