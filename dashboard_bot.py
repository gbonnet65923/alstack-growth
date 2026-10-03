# -*- coding: utf-8 -*-
"""@shilldashbord_bot — пульт управления шилл-кампанией @AlStack.
Дашборд: процессы, шарды, каналы, хантер, реакции, аккаунты, логи.
Управление: запуск/остановка шилла, хантера, джойна, реакций.
Запуск: env -u PYTHONPATH python dashboard_bot.py
"""
import aiohttp.connector
aiohttp.connector.DefaultResolver = aiohttp.ThreadedResolver  # aiodns broken on Windows

import asyncio, json, os, re, subprocess, sys, time, glob
import psutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup,
                           InlineKeyboardButton)

OWNER = 7448683285  # ReformBoss (Vlad)
BASE = r"C:/Users/User/tmp/tg_chat_grow"
os.chdir(BASE)

ALSTACK = "AlStack"
ALSTACK_ID = 4420835850

TOKEN=open(".dash_token", encoding="utf-8").read().strip()

PROC_MAP = {
    "shard_worker.py": "🧩 шард шилла",
    "mass_seed.py": "🧩 mass_seed",
    "chat_hunter_loop.py": "🔍 хантер чатов",
    "join_channels.py": "🚪 джойн каналов",
    "react_new.py": "❤️ реакции (посты)",
    "react_latest.py": "❤️ реакции (авто)",
    "harvest_atlas_loop.py": "🌾 атлас-харвест",
    "wave_chain.py": "🌊 wave_chain",
    "merge_pool.py": "🔀 merge_pool",
    "sub_alstack.py": "👥 подписки",
    "responder.py": "💬 респондер",
}

router = Router()


# ───────────────────────── helpers ─────────────────────────

def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def jload(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def log_tail(name, n=12):
    try:
        with open(name, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-n:])
    except Exception:
        return "(лог не найден)"


def live_procs():
    """Живые python-процессы кампании (без самого бота)."""
    me = os.getpid()
    out = []
    for p in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
        try:
            if (p.info["name"] or "").lower().find("python") < 0:
                continue
            cl = " ".join(p.info["cmdline"] or [])
            if p.pid == me or "dashboard_bot" in cl:
                continue
            for script, label in PROC_MAP.items():
                if script in cl:
                    age = int(time.time() - p.info["create_time"])
                    out.append({"pid": p.pid, "script": script,
                                "label": label, "age": age})
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return out


def fmt_age(sec):
    if sec < 60:
        return f"{sec}с"
    if sec < 3600:
        return f"{sec//60}м"
    if sec < 86400:
        return f"{sec//3600}ч{(sec%3600)//60}м"
    return f"{sec//86400}д{(sec%86400)//3600}ч"


def shard_files():
    return sorted(glob.glob("mass_state_*.json"))


def collect_shards():
    today = time.strftime("%Y-%m-%d")
    rows = []
    tot = {"pairs": 0, "replies": 0, "done": 0, "fails": 0, "today_ok": 0,
           "today_fail": 0, "banned": 0}
    for f in shard_files():
        d = jload(f, {})
        if not isinstance(d, dict):
            continue
        idx = re.search(r"mass_state_(\d+)", f).group(1)
        hist = d.get("history", []) or []
        log = d.get("log", []) or []
        t_ok = sum(1 for e in log if e.get("day") == today and e.get("ok"))
        t_no = sum(1 for e in log if e.get("day") == today and not e.get("ok"))
        last = hist[-1] if hist else None
        rows.append({
            "idx": idx, "pairs": d.get("pairs", 0), "replies": d.get("replies", 0),
            "done": len(d.get("done_groups", []) or []),
            "fails": d.get("fails", 0),
            "banned": len(d.get("banned_accs", []) or []),
            "today_ok": t_ok, "today_fail": t_no,
            "last_g": (last or {}).get("g"), "last_r": (last or {}).get("r"),
            "last_ts": (last or {}).get("ts"),
        })
        tot["pairs"] += d.get("pairs", 0)
        tot["replies"] += d.get("replies", 0)
        tot["done"] += len(d.get("done_groups", []) or [])
        tot["fails"] += d.get("fails", 0)
        tot["today_ok"] += t_ok
        tot["today_fail"] += t_no
        tot["banned"] += len(d.get("banned_accs", []) or [])
    return rows, tot


def collect_pool():
    pool = jload("pool_merged.json", []) or []
    done = set(jload("shill_done.json", []) or [])
    return pool, done


def acc_stats():
    cls = jload("spambot_classified.json", {}) or {}
    ok = len(cls.get("ok", []))
    spam = len(cls.get("spam", []))
    ban = len(cls.get("banned", []))
    unk = len(cls.get("unknown", []))
    sess = {}
    for d in ["mass", "seeders", "subs", "reactors", "harvesters",
              "validators", "checkers", "dressers", "joiners", "hunters",
              "responders"]:
        sess[d] = len(glob.glob(f"{d}/*.session"))
    return ok, spam, ban, unk, sess


def start_bg(script, args, logname):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    lf = open(logname, "ab")
    p = subprocess.Popen([sys.executable, script, *args], cwd=BASE, env=env,
                         stdout=lf, stderr=subprocess.STDOUT,
                         creationflags=subprocess.DETACHED_PROCESS |
                         subprocess.CREATE_NEW_PROCESS_GROUP)
    return p.pid


def running(script):
    return any(x["script"] == script for x in live_procs())


def kill_script(script):
    killed = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if (p.info["name"] or "").lower().find("python") < 0:
                continue
            cl = " ".join(p.info["cmdline"] or [])
            if script in cl and "dashboard_bot" not in cl:
                p.terminate()
                killed.append(p.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed


# ───────────────────────── texts ─────────────────────────

def txt_status():
    procs = live_procs()
    rows, tot = collect_shards()
    pool, done = collect_pool()
    found = jload("live_groups_found.json", []) or []
    react = jload("react_progress.json", {}) or {}
    sub = jload("sub_progress.json", {}) or {}
    alive = {s for s in rows if s["last_ts"] and time.time() - s["last_ts"] < 600}

    L = ["<b>📊 СТАТУС КАМПАНИИ @AlStack</b>", ""]
    L.append(f"<b>Процессы ({len(procs)}):</b>")
    if procs:
        for p in procs:
            L.append(f"  • {p['label']} — pid {p['pid']}, {fmt_age(p['age'])}")
    else:
        L.append("  ⛔ ничего не запущено")
    L.append("")
    L.append("<b>Шилл:</b>")
    L.append(f"  • шардов в файлах: {len(rows)}, активных (действие &lt;10мин): {len(alive)}")
    L.append(f"  • пар отправлено: {tot['pairs']} | реплаев: {tot['replies']}")
    L.append(f"  • сегодня: ✅ {tot['today_ok']} / ❌ {tot['today_fail']}")
    L.append(f"  • зашилено групп всего: {len(done)} | фейлов: {tot['fails']} | бан акков: {tot['banned']}")
    L.append("")
    L.append("<b>Пулы:</b>")
    L.append(f"  • pool_merged: {len(pool)} каналов | шилл-очередь: {len(pool)-len(done)}")
    L.append(f"  • найдено хантером: {len(found)}")
    L.append("")
    ok, spam, ban, unk, sess = acc_stats()
    L.append("<b>Аккаунты:</b>")
    L.append(f"  • чистых: {ok} | спам-блок: {spam} | бан: {ban} | неизв: {unk}")
    L.append(f"  • сессий mass/: {sess.get('mass',0)}")
    L.append("")
    L.append("<b>Канал @AlStack:</b>")
    L.append(f"  • акков с реакциями: {len(react)} | подписаны: {len(sub)}")
    L.append("  • /live — живые метрики канала (посты+реакции)")
    return "\n".join(L)


def txt_shards():
    rows, tot = collect_shards()
    L = ["<b>🧩 ШАРДЫ (mass_state_*)</b>", ""]
    for s in rows:
        act = "🟢" if s["last_ts"] and time.time() - s["last_ts"] < 600 else "⚪"
        L.append(f"{act} <b>shard {s['idx']}</b>: пар {s['pairs']}, реплаев {s['replies']}, "
                 f"групп {s['done']}, сегодня ✅{s['today_ok']}/❌{s['today_fail']}, бан {s['banned']}")
        if s["last_g"]:
            ago = fmt_age(int(time.time() - s["last_ts"])) if s["last_ts"] else "?"
            L.append(f"    └ @{esc(s['last_g'])} ({ago} назад): «{esc((s['last_r'] or '')[:70])}»")
    L.append("")
    L.append(f"<b>ИТОГО:</b> пар {tot['pairs']} | реплаев {tot['replies']} | "
             f"сегодня ✅{tot['today_ok']}/❌{tot['today_fail']}")
    return "\n".join(L)


def txt_channels(page=0):
    pool, done = collect_pool()
    pool = sorted(pool, key=lambda g: -(g.get("members") or 0))
    per = 20
    pages = max(1, (len(pool) + per - 1) // per)
    page = max(0, min(page, pages - 1))
    chunk = pool[page * per:(page + 1) * per]
    L = [f"<b>📺 КАНАЛЫ ПУЛА</b> ({len(pool)} всего, зашилено {len(done)})",
         f"стр. {page+1}/{pages} — топ по подписчикам", ""]
    for g in chunk:
        ch = g.get("channel") or "?"
        m = g.get("members") or 0
        mark = "✅" if ch in done else "⬜"
        linked = "💬" if g.get("linked_id") else ("📢" if g.get("direct") else "❔")
        L.append(f"{mark} {linked} <b>@{esc(ch)}</b> — {m:,}".replace(",", " "))
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️", callback_data=f"ch:{page-1}" if page > 0 else "noop"),
        InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"),
        InlineKeyboardButton(text="➡️", callback_data=f"ch:{page+1}" if page < pages-1 else "noop"),
    ], [InlineKeyboardButton(text="🔙 меню", callback_data="menu")]])
    return "\n".join(L), kb


def txt_hunter():
    found = jload("live_groups_found.json", []) or []
    pool, done = collect_pool()
    pool_names = {(g.get("channel") or "") for g in pool}
    found = sorted(found, key=lambda g: -(g.get("members") or 0))
    new = [g for g in found if g.get("channel") not in pool_names]
    L = [f"<b>🔍 ХАНТЕР — найденные чаты</b> (всего {len(found)}, новых вне пула {len(new)})", ""]
    for g in found[:25]:
        ch = g.get("channel") or "?"
        m = g.get("members") or 0
        rh = g.get("recent_human", "?")
        inn = "🆕" if g in new else "▪️"
        L.append(f"{inn} <b>@{esc(ch)}</b> — {m:,} | людей/7д: {rh} | «{esc((g.get('title') or '')[:30])}»".replace(",", " "))
    if len(found) > 25:
        L.append(f"... ещё {len(found)-25}")
    return "\n".join(L)


def txt_react():
    react = jload("react_progress.json", {}) or {}
    sub = jload("sub_progress.json", {}) or {}
    L = ["<b>❤️ РЕАКЦИИ / ПОДПИСКИ @AlStack</b>", ""]
    L.append(f"  • акков с реакциями: {len(react)}")
    L.append(f"  • акков подписаны: {len(sub)}")
    L.append("")
    tail = log_tail("react_new.log", 10)
    L.append("<b>react_new.log (хвост):</b>")
    L.append(f"<pre>{esc(tail[-900:])}</pre>")
    L.append("")
    L.append("Канал принимает ТОЛЬКО кастомные эмодзи (прем-пак).")
    L.append("/live — текущие реакции по постам")
    return "\n".join(L)


def txt_accounts():
    ok, spam, ban, unk, sess = acc_stats()
    L = ["<b>👥 АККАУНТЫ</b>", ""]
    L.append(f"  • ✅ чистых: {ok}")
    L.append(f"  • ⚠️ спам-блок: {spam}")
    L.append(f"  • ⛔ бан: {ban}")
    L.append(f"  • ❔ не проверено: {unk}")
    L.append("")
    L.append("<b>Сессии по workdir:</b>")
    for d, n in sess.items():
        if n:
            L.append(f"  • {d}/: {n}")
    rows, tot = collect_shards()
    L.append("")
    L.append(f"<b>Баны в шардах:</b> {tot['banned']}")
    return "\n".join(L)


LIVE_LOGS = ["mass_0.log", "mass_1.log", "mass_2.log", "mass_3.log",
             "hunter_run.log", "join_run.log", "react_new.log",
             "harvest_atlas_loop.log", "merge_pool.log", "wave_1.log"]


def txt_logs_menu():
    kb = []
    row = []
    for name in LIVE_LOGS:
        if not os.path.exists(name):
            continue
        age = int(time.time() - os.path.getmtime(name))
        live = "🟢" if age < 300 else "⚪"
        row.append(InlineKeyboardButton(text=f"{live} {name[:18]}",
                                        callback_data=f"log:{name}"))
        if len(row) == 2:
            kb.append(row); row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton(text="🔙 меню", callback_data="menu")])
    return ("<b>📜 ЛОГИ</b> (🟢 = обновлялся &lt;5мин)\n\nВыбери лог:"), \
        InlineKeyboardMarkup(inline_keyboard=kb)


def txt_help():
    return """<b>🎛 ПУЛЬТ @AlStack</b>

<b>Команды:</b>
/status — общая сводка
/shards — шарды шилла
/channels — пул каналов (пагинация)
/hunter — найденные чаты
/react — реакции/подписки
/accounts — аккаунты
/logs — логи процессов
/live — живые метрики канала

<b>Запуски:</b>
/start_shill — mass_seed (4 шарда)
/start_hunter — охота за новыми чатами
/start_join — вход в каналы
/start_react — реакции на слабые посты

<b>Остановки:</b>
/stop_shill /stop_hunter /stop_join /stop_react
/stop_all — всё

<b>Правила кампании (зашиты в софт):</b>
• 1 шилл на чат навсегда
• задержка вопрос→ответ 210-330с
• в сам @AlStack не комментируем — только реакции/подписки
• защищённые ID: 7448683285, 809951394"""


def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статус", callback_data="m:status"),
         InlineKeyboardButton(text="🧩 Шарды", callback_data="m:shards")],
        [InlineKeyboardButton(text="📺 Каналы", callback_data="ch:0"),
         InlineKeyboardButton(text="🔍 Хантер", callback_data="m:hunter")],
        [InlineKeyboardButton(text="❤️ Реакции", callback_data="m:react"),
         InlineKeyboardButton(text="👥 Аккаунты", callback_data="m:accs")],
        [InlineKeyboardButton(text="📜 Логи", callback_data="m:logs"),
         InlineKeyboardButton(text="📡 Live канал", callback_data="m:live")],
        [InlineKeyboardButton(text="▶️ Запуски", callback_data="m:runs"),
         InlineKeyboardButton(text="🛑 Остановки", callback_data="m:stops")],
    ])
    return kb


def runs_menu():
    procs = {p["script"] for p in live_procs()}
    def st(s):
        return "🟢" if s in procs else "⚪"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{st('mass_seed.py')} Шилл (mass_seed)", callback_data="run:shill")],
        [InlineKeyboardButton(text=f"{st('chat_hunter_loop.py')} Хантер", callback_data="run:hunter")],
        [InlineKeyboardButton(text=f"{st('join_channels.py')} Джойн", callback_data="run:join")],
        [InlineKeyboardButton(text=f"{st('react_latest.py')} Реакции", callback_data="run:react")],
        [InlineKeyboardButton(text="🔙 меню", callback_data="menu")],
    ])
    return "<b>▶️ ЗАПУСКИ</b>\n🟢 = уже работает\n", kb


def stops_menu():
    procs = {p["script"] for p in live_procs()}
    def st(s):
        return "🟢" if s in procs else "⚪"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{st('mass_seed.py')}+{st('shard_worker.py')} Шилл", callback_data="stop:shill"),
         InlineKeyboardButton(text=f"{st('chat_hunter_loop.py')} Хантер", callback_data="stop:hunter")],
        [InlineKeyboardButton(text=f"{st('join_channels.py')} Джойн", callback_data="stop:join"),
         InlineKeyboardButton(text=f"{st('react_new.py')} Реакции", callback_data="stop:react")],
        [InlineKeyboardButton(text="⛔ СТОП ВСЁ", callback_data="stop:all")],
        [InlineKeyboardButton(text="🔙 меню", callback_data="menu")],
    ])
    return "<b>🛑 ОСТАНОВКИ</b>\n", kb


# ───────────────────────── live probe ─────────────────────────

async def alstack_live():
    """Подпроцесс: копия сессии → метрики канала (не блокирует рабочие)."""
    probe = "live_probe.py"
    code = '''
import asyncio, json, glob, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(r"C:/Users/User/tmp/tg_chat_grow")
async def main():
    from telethon import TelegramClient
    src = None
    for f in sorted(glob.glob("reactors/*.session")):
        b = f[:-len(".session")]
        if not os.path.exists(b+"-journal") and not os.path.exists(b+"-wal"):
            src = f; break
    if not src:
        print(json.dumps({"error": "no free session"})); return
    p = "reactors/_probe_live.session"
    shutil.copyfile(src, p)
    c = TelegramClient(p[:-len(".session")], 2040, "b18441a1ff607e10a989891a5462e627")
    await c.start()
    ent = await c.get_entity("AlStack")
    out = {"subs": ent.participants_count, "posts": []}
    async for m in c.iter_messages("AlStack", limit=8):
        tot = sum(r.count for r in m.reactions.results) if m.reactions else 0
        views = m.views or 0
        out["posts"].append({"id": m.id, "reactions": tot, "views": views,
                             "date": m.date.strftime("%d.%m %H:%M"),
                             "text": (m.message or "")[:60]})
    await c.disconnect()
    for x in (p, p+"-journal"):
        try: os.remove(x)
        except OSError: pass
    print(json.dumps(out, ensure_ascii=False))
asyncio.run(main())
'''
    with open(probe, "w", encoding="utf-8") as f:
        f.write(code)
    env = dict(os.environ); env.pop("PYTHONPATH", None)
    proc = await asyncio.create_subprocess_exec(
        sys.executable, probe, cwd=BASE, env=env,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=90)
    except asyncio.TimeoutError:
        proc.kill()
        return {"error": "timeout 90s"}
    txt = out.decode("utf-8", "replace").strip().splitlines()
    for line in reversed(txt):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass
    return {"error": (err.decode("utf-8", "replace")[-200:] or "no json")}


def txt_live(data):
    if data.get("error"):
        return f"<b>📡 LIVE @AlStack</b>\n\n⛔ {esc(data['error'])}"
    L = [f"<b>📡 LIVE @AlStack</b> — {data['subs']:,} подписчиков".replace(",", " "), ""]
    for p in data["posts"]:
        L.append(f"msg <b>{p['id']}</b> ({p['date']}): ❤️{p['reactions']} 👁{p['views']:,} — «{esc(p['text'])}»".replace(",", " "))
    weak = [p["id"] for p in data["posts"] if p["reactions"] < 30]
    L.append("")
    if weak:
        L.append(f"⚠️ слабые посты (&lt;30 реакций): {weak} — /start_react")
    else:
        L.append("✅ все посты &gt;30 реакций")
    return "\n".join(L)


# ───────────────────────── handlers ─────────────────────────

def owner_only(fn):
    async def wrapper(event, *a, **kw):
        uid = event.from_user.id if hasattr(event, "from_user") else event.chat.id
        if uid != OWNER:
            try:
                if isinstance(event, CallbackQuery):
                    await event.answer("⛔ только для Влада", show_alert=True)
                else:
                    await event.answer("⛔")
            except Exception:
                pass
            return
        return await fn(event, *a, **kw)
    return wrapper


@router.message(CommandStart())
@owner_only
async def cmd_start(m: Message):
    await m.answer(txt_help(), reply_markup=main_menu())


@router.message(Command("menu"))
@owner_only
async def cmd_menu(m: Message):
    await m.answer("🎛 <b>Меню</b>", reply_markup=main_menu())


@router.message(Command("status"))
@owner_only
async def cmd_status(m: Message):
    await m.answer(txt_status())


@router.message(Command("shards"))
@owner_only
async def cmd_shards(m: Message):
    await m.answer(txt_shards())


@router.message(Command("channels"))
@owner_only
async def cmd_channels(m: Message):
    t, kb = txt_channels(0)
    await m.answer(t, reply_markup=kb)


@router.message(Command("hunter"))
@owner_only
async def cmd_hunter(m: Message):
    await m.answer(txt_hunter())


@router.message(Command("react"))
@owner_only
async def cmd_react(m: Message):
    await m.answer(txt_react())


@router.message(Command("accounts"))
@owner_only
async def cmd_accounts(m: Message):
    await m.answer(txt_accounts())


@router.message(Command("logs"))
@owner_only
async def cmd_logs(m: Message):
    t, kb = txt_logs_menu()
    await m.answer(t, reply_markup=kb)


@router.message(Command("help"))
@owner_only
async def cmd_help(m: Message):
    await m.answer(txt_help())


@router.message(Command("live"))
@owner_only
async def cmd_live(m: Message):
    msg = await m.answer("📡 probe... (до 90с)")
    data = await alstack_live()
    await msg.edit_text(txt_live(data))


@router.message(Command("start_shill"))
@owner_only
async def cmd_start_shill(m: Message):
    if running("mass_seed.py"):
        await m.answer("🟢 mass_seed уже работает")
        return
    pid = start_bg("mass_seed.py", ["--shards", "4", "--pairs-per-group", "2",
                                    "--replies-per-group", "2"], "mass_dash.log")
    await m.answer(f"▶️ mass_seed запущен (pid {pid}, 4 шарда). Лог: mass_dash.log")


@router.message(Command("start_hunter"))
@owner_only
async def cmd_start_hunter(m: Message):
    if running("chat_hunter_loop.py"):
        await m.answer("🟢 хантер уже работает")
        return
    pid = start_bg("chat_hunter_loop.py", [], "hunter_dash.log")
    await m.answer(f"▶️ хантер запущен (pid {pid}). Лог: hunter_dash.log")


@router.message(Command("start_join"))
@owner_only
async def cmd_start_join(m: Message):
    if running("join_channels.py"):
        await m.answer("🟢 джойн уже работает")
        return
    pid = start_bg("join_channels.py", ["--accounts", "8", "--per-acc", "12"], "join_dash.log")
    await m.answer(f"▶️ джойн запущен (pid {pid}, 8 акков × 12). Лог: join_dash.log")


@router.message(Command("start_react"))
@owner_only
async def cmd_start_react(m: Message):
    if running("react_latest.py") or running("react_new.py"):
        await m.answer("🟢 реакции уже крутятся")
        return
    pid = start_bg("react_latest.py", ["--n", "40", "--min", "30"], "react_dash.log")
    await m.answer(f"▶️ реакции на слабые посты запущены (pid {pid}, 40 акков). Лог: react_dash.log")


@router.message(Command("stop_shill"))
@owner_only
async def cmd_stop_shill(m: Message):
    k1 = kill_script("mass_seed.py")
    k2 = kill_script("shard_worker.py")
    await m.answer(f"🛑 шилл остановлен: mass_seed {k1 or '—'}, шарды {k2 or '—'}")


@router.message(Command("stop_hunter"))
@owner_only
async def cmd_stop_hunter(m: Message):
    k = kill_script("chat_hunter_loop.py")
    await m.answer(f"🛑 хантер: {k or 'не работал'}")


@router.message(Command("stop_join"))
@owner_only
async def cmd_stop_join(m: Message):
    k = kill_script("join_channels.py")
    await m.answer(f"🛑 джойн: {k or 'не работал'}")


@router.message(Command("stop_react"))
@owner_only
async def cmd_stop_react(m: Message):
    k = kill_script("react_new.py") + kill_script("react_latest.py")
    await m.answer(f"🛑 реакции: {k or 'не работали'}")


@router.message(Command("stop_all"))
@owner_only
async def cmd_stop_all(m: Message):
    allk = []
    for s in ["mass_seed.py", "shard_worker.py", "chat_hunter_loop.py",
              "join_channels.py", "react_new.py", "react_latest.py",
              "wave_chain.py", "merge_pool.py", "harvest_atlas_loop.py"]:
        allk += kill_script(s)
    await m.answer(f"⛔ остановлено всё: {allk or 'ничего не работало'}")


@router.callback_query(F.data == "menu")
@owner_only
async def cb_menu(cq: CallbackQuery):
    await cq.message.edit_text("🎛 <b>Меню</b>", reply_markup=main_menu())
    await cq.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(cq: CallbackQuery):
    await cq.answer()


@router.callback_query(F.data.startswith("m:"))
@owner_only
async def cb_menu_items(cq: CallbackQuery):
    what = cq.data.split(":", 1)[1]
    await cq.answer()
    if what == "status":
        await cq.message.edit_text(txt_status(), reply_markup=main_menu())
    elif what == "shards":
        await cq.message.edit_text(txt_shards(), reply_markup=main_menu())
    elif what == "hunter":
        await cq.message.edit_text(txt_hunter(), reply_markup=main_menu())
    elif what == "react":
        await cq.message.edit_text(txt_react(), reply_markup=main_menu())
    elif what == "accs":
        await cq.message.edit_text(txt_accounts(), reply_markup=main_menu())
    elif what == "logs":
        t, kb = txt_logs_menu()
        await cq.message.edit_text(t, reply_markup=kb)
    elif what == "runs":
        t, kb = runs_menu()
        await cq.message.edit_text(t, reply_markup=kb)
    elif what == "stops":
        t, kb = stops_menu()
        await cq.message.edit_text(t, reply_markup=kb)
    elif what == "live":
        await cq.message.edit_text("📡 probe... (до 90с)")
        data = await alstack_live()
        await cq.message.edit_text(txt_live(data), reply_markup=main_menu())


@router.callback_query(F.data.startswith("ch:"))
@owner_only
async def cb_channels(cq: CallbackQuery):
    page = int(cq.data.split(":")[1])
    t, kb = txt_channels(page)
    await cq.message.edit_text(t, reply_markup=kb)
    await cq.answer()


@router.callback_query(F.data.startswith("log:"))
@owner_only
async def cb_log(cq: CallbackQuery):
    name = cq.data.split(":", 1)[1]
    if name not in LIVE_LOGS and not os.path.exists(name):
        await cq.answer("нет такого лога", show_alert=True)
        return
    tail = log_tail(name, 30)
    await cq.message.edit_text(
        f"<b>📜 {esc(name)}</b>\n<pre>{esc(tail[-3500:])}</pre>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 обновить", callback_data=f"log:{name}")],
            [InlineKeyboardButton(text="📜 логи", callback_data="m:logs")]]))
    await cq.answer()


@router.callback_query(F.data.startswith("run:"))
@owner_only
async def cb_run(cq: CallbackQuery):
    what = cq.data.split(":")[1]
    await cq.answer()
    if what == "shill":
        if running("mass_seed.py"):
            await cq.message.answer("🟢 mass_seed уже работает")
        else:
            pid = start_bg("mass_seed.py", ["--shards", "4", "--pairs-per-group", "2",
                                            "--replies-per-group", "2"], "mass_dash.log")
            await cq.message.answer(f"▶️ mass_seed запущен (pid {pid})")
    elif what == "hunter":
        if running("chat_hunter_loop.py"):
            await cq.message.answer("🟢 хантер уже работает")
        else:
            pid = start_bg("chat_hunter_loop.py", [], "hunter_dash.log")
            await cq.message.answer(f"▶️ хантер запущен (pid {pid})")
    elif what == "join":
        if running("join_channels.py"):
            await cq.message.answer("🟢 джойн уже работает")
        else:
            pid = start_bg("join_channels.py", ["--accounts", "8", "--per-acc", "12"], "join_dash.log")
            await cq.message.answer(f"▶️ джойн запущен (pid {pid})")
    elif what == "react":
        if running("react_latest.py") or running("react_new.py"):
            await cq.message.answer("🟢 реакции уже крутятся")
        else:
            pid = start_bg("react_latest.py", ["--n", "40", "--min", "30"], "react_dash.log")
            await cq.message.answer(f"▶️ реакции запущены (pid {pid})")


@router.callback_query(F.data.startswith("stop:"))
@owner_only
async def cb_stop(cq: CallbackQuery):
    what = cq.data.split(":")[1]
    await cq.answer()
    if what == "shill":
        k = kill_script("mass_seed.py") + kill_script("shard_worker.py")
    elif what == "hunter":
        k = kill_script("chat_hunter_loop.py")
    elif what == "join":
        k = kill_script("join_channels.py")
    elif what == "react":
        k = kill_script("react_new.py") + kill_script("react_latest.py")
    elif what == "all":
        k = []
        for s in ["mass_seed.py", "shard_worker.py", "chat_hunter_loop.py",
                  "join_channels.py", "react_new.py", "react_latest.py",
                  "wave_chain.py", "merge_pool.py", "harvest_atlas_loop.py"]:
            k += kill_script(s)
    else:
        k = []
    await cq.message.answer(f"🛑 остановлено: {k or 'ничего не работало'}")


async def auto_report(bot: Bot):
    """Автоотчёт владельцу каждые 30 минут, если что-то работает."""
    while True:
        await asyncio.sleep(1800)
        try:
            procs = live_procs()
            if not procs:
                continue
            rows, tot = collect_shards()
            await bot.send_message(
                OWNER,
                f"⏰ <b>Автоотчёт</b>\nПроцессов: {len(procs)} | "
                f"пар сегодня: {tot['today_ok']}✅/{tot['today_fail']}❌ | "
                f"всего пар {tot['pairs']}, реплаев {tot['replies']}")
        except Exception as e:
            print("auto_report err:", e)


async def main():
    bot = Bot(token=TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    asyncio.create_task(auto_report(bot))
    print("dashboard bot starting...", flush=True)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
