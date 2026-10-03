# alstack_views_boost.py — накрутка просмотров постов @AlStack
# Метод: embed-view через t.me/<ch>/<post>?embed=1 + &view=<key> (MarkSnaile/telegram-channel-views-boost, GPL-3.0)
# Без платных сервисов — только бесплатные прокси из наших пулов.
# Usage: env -u PYTHONPATH python alstack_views_boost.py [N_POSTS] [TARGET_VIEWS]
import requests, threading, sys, os, json, time, random

HOME = os.path.expanduser("~")
CHANNEL = "AlStack"
PROXY_FILES = [
    HOME + "/tmp/live_http_proxies.txt",
    HOME + "/tmp/fresh_proxies_now.txt",
    HOME + "/tmp/bpproxies_fresh.txt",
    HOME + "/tmp/smm_proxy.txt",
]
N_POSTS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
TARGET = int(sys.argv[2]) if len(sys.argv) > 2 else 500

def load_proxies():
    out, seen = [], set()
    for f in PROXY_FILES:
        try:
            for line in open(f, encoding="utf-8", errors="ignore"):
                p = line.strip().split()[0] if line.strip() else ""
                if p and ":" in p and " " not in p and p not in seen:
                    seen.add(p)
                    out.append(p if p.startswith("http") else "http://" + p)
        except Exception:
            pass
    return out

def last_post_ids(n):
    """Get last n post ids via t.me/s/AlStack preview (no auth)."""
    r = requests.get(f"https://t.me/s/{CHANNEL}", timeout=25,
                     headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    import re
    ids = re.findall(r'data-post="' + CHANNEL + r'/(\d+)"', r.text)
    uniq = list(dict.fromkeys(ids))
    return uniq[-n:] if len(uniq) >= n else uniq

stats = {"ok": 0, "fail": 0}
lock = threading.Lock()
sem = threading.Semaphore(60)

def boost(post, proxy):
    sem.acquire()
    try:
        px = {"http": proxy, "https": proxy}
        r = requests.get(f"https://t.me/{CHANNEL}/{post}?embed=1", timeout=15, proxies=px)
        cookie = r.headers.get("set-cookie", "").split(";")[0]
        key = r.text.split('data-view="')[1].split('"')[0]
        if "stel_ssid" not in cookie:
            return
        r2 = requests.get(f"https://t.me/{CHANNEL}/{post}?embed=1&view={key}", timeout=15,
                          headers={"x-requested-with": "XMLHttpRequest",
                                   "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                   "referer": f"https://t.me/{CHANNEL}/{post}?embed=1",
                                   "cookie": cookie}, proxies=px)
        with lock:
            stats["ok" if r2.status_code == 200 else "fail"] += 1
    except Exception:
        with lock:
            stats["fail"] += 1
    finally:
        sem.release()

def main():
    proxies = load_proxies()
    print(f"proxies: {len(proxies)}")
    if not proxies:
        print("NO PROXIES"); sys.exit(1)
    posts = last_post_ids(N_POSTS)
    print(f"posts: {posts}")
    if not posts:
        print("NO POSTS"); sys.exit(1)
    threads = []
    per_post = max(1, TARGET // max(1, len(posts)))
    for post in posts:
        for i in range(min(per_post, len(proxies))):
            t = threading.Thread(target=boost, args=(post, proxies[i]))
            threads.append(t); t.start()
            if len(threads) % 200 == 0:
                for tt in threads[-200:]: tt.join(timeout=30)
    for t in threads: t.join(timeout=45)
    print(json.dumps({"ok": stats["ok"], "fail": stats["fail"], "posts": posts}))

if __name__ == "__main__":
    main()
