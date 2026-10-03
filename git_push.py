# -*- coding: utf-8 -*-
"""Push tg_chat_grow project to a PRIVATE GitHub repo via Git Data API.
git-remote-https.exe is missing on this box -> blobs/trees/commits over REST.
EXCLUDES: *.session, *.log, state files with account ids/phones, __pycache__.
"""
import base64, json, os, re, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'C:/Users/User/tmp/tg_chat_grow'
OWNER = 'gbonnet65923'
REPO_NAME = 'alstack-growth'
TOK = json.load(open('C:/Users/User/tmp/pw_alive.json', encoding='utf-8'))[0][0]

# ---- state/data files that carry account ids/phones -> NEVER push
STATE_DENY = re.compile(r'(mass_state|react_progress|seed_state|sub_progress|dress2_progress|'
                        r'spambot_|peers\.json|alstack_reactions|tgstat_parked|enrich_parked|'
                        r'enrich_progress|inviter_state|handoff_stats|donor_members|dress_check)', re.I)

def gh(method, path, data=None, raw=False):
    url = 'https://api.github.com' + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        'Authorization': 'token ' + TOK, 'Accept': 'application/vnd.github+json',
        'User-Agent': 'push-api', 'Content-Type': 'application/json'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r) if not raw else r.read()
        except urllib.error.HTTPError as e:
            txt = e.read()[:300].decode(errors='ignore')
            if e.code == 422 and 'name already exists' in txt:
                return {'existed': True}
            if e.code in (403, 429) or e.code >= 500:
                wait = int(e.headers.get('Retry-After', 10))
                print('  retry %s in %ss: HTTP %d %s' % (path, wait, e.code, txt[:120]), flush=True)
                time.sleep(wait); continue
            raise RuntimeError('HTTP %d %s: %s' % (e.code, path, txt))
    raise RuntimeError('retries exhausted: ' + path)

# 1. create private repo (ignore 422 = exists)
r = gh('POST', '/user/repos', {'name': REPO_NAME, 'private': True,
                               'description': 'Telegram AI-channel growth engine: catalog parsers, pool enrichment, organic seeding waves'})
print('repo:', r.get('full_name') or r.get('existed'))

# 1b. empty repo rejects Data API blobs (409). If repo empty -> init via Contents API first.
info = gh('GET', '/repos/%s/%s' % (OWNER, REPO_NAME))
if info.get('size', 0) == 0:
    print('repo empty -> init via Contents API')
    init = gh('PUT', '/repos/%s/%s/contents/README.md' % (OWNER, REPO_NAME), {
        'message': 'init', 'content': base64.b64encode(
            b'# alstack-growth\nTelegram AI-channel growth engine.\n').decode()})
    print('init commit:', init.get('commit', {}).get('sha'))

# 2. collect files: top-level .py/.ps1/.md + safe .json; no sessions/logs/pycache/subdirs-with-sessions
files = []
for f in sorted(os.listdir(BASE)):
    p = os.path.join(BASE, f)
    if not os.path.isfile(p):
        continue
    ext = os.path.splitext(f)[1].lower()
    if ext in ('.session', '.log', '.tmp', '.flag') or ext == '.session-journal':
        continue
    if f == '__pycache__' or ext == '.pyc':
        continue
    if ext == '.json':
        if STATE_DENY.search(f):
            continue
        if os.path.getsize(p) > 400_000:   # skip giant dumps, API blob limit friendliness
            print('  skip big json:', f, os.path.getsize(p)); continue
    if ext in ('.py', '.ps1', '.md', '.json', '.txt') or f == '.gitignore':
        files.append(f)

# wave_*.json pool slices are safe (channel data only)
print('files to push:', len(files))

# 3. .gitignore content
gitignore = """# credentials / sessions / runtime state - NEVER commit
*.session
*.session-journal
mass/
mass_state_*.json
react_progress.json
seed_state.json
sub_progress.json
dress2_progress.json
spambot_*.json
peers.json
alstack_reactions.json
tgstat_parked.json
enrich_parked.json
enrich_progress.json
inviter_state.json
handoff_stats.json
donor_members.json
*.log
__pycache__/
*.pyc
"""
files_map = {f: os.path.join(BASE, f) for f in files}
files_map['.gitignore'] = None  # synthetic

# 4. blobs
sha_map = {}
for i, (f, p) in enumerate(files_map.items()):
    raw = gitignore.encode() if p is None else open(p, 'rb').read()
    res = gh('POST', '/repos/%s/%s/git/blobs' % (OWNER, REPO_NAME),
             {'content': base64.b64encode(raw).decode(), 'encoding': 'base64'})
    sha_map[f] = res.get('sha')
    if (i + 1) % 15 == 0:
        print('  blobs %d/%d' % (i + 1, len(files_map)), flush=True)
print('blobs done:', len(sha_map))

# 5. tree
tree = [{'path': f, 'mode': '100644', 'type': 'blob', 'sha': s} for f, s in sha_map.items() if s]
t = gh('POST', '/repos/%s/%s/git/trees' % (OWNER, REPO_NAME), {'tree': tree})
print('tree:', t.get('sha'))

# 6. commit (parent = current main tip if exists)
try:
    refinfo = gh('GET', '/repos/%s/%s/git/refs/heads/main' % (OWNER, REPO_NAME))
    parents = [refinfo['object']['sha']]
except Exception:
    parents = []
c = gh('POST', '/repos/%s/%s/git/commits' % (OWNER, REPO_NAME), {
    'message': 'AlStack growth engine v2.3: 205 new AI channels harvested (tg-me/hottg/lyzem/tgdr.io/tgram.io + 4 SSR catalogs), '
               '84 linked groups enriched, pool 1111 (242 seedable), LLM failover to MiniMax-M2.1, psutil wave_chain fix, '
               'ensure_in_group KeyError fix, state-save retry',
    'tree': t['sha'],
    'parents': parents,
    'author': {'name': 'Vlad Gothbreach', 'email': 'gothbreach@proton.me',
               'date': time.strftime('%Y-%m-%dT%H:%M:%S+03:00')},
    'committer': {'name': 'Vlad Gothbreach', 'email': 'gothbreach@proton.me',
                  'date': time.strftime('%Y-%m-%dT%H:%M:%S+03:00')}})
print('commit:', c.get('sha'))

# 7. ref main (create or force-update)
try:
    ref = gh('POST', '/repos/%s/%s/git/refs' % (OWNER, REPO_NAME), {'ref': 'refs/heads/main', 'sha': c['sha']})
    print('ref created:', ref.get('ref'))
except RuntimeError as e:
    if '422' in str(e):
        ref = gh('PATCH', '/repos/%s/%s/git/refs/heads/main' % (OWNER, REPO_NAME), {'sha': c['sha'], 'force': True})
        print('ref updated:', ref.get('ref'))
    else:
        raise

# 8. verify
info = gh('GET', '/repos/%s/%s' % (OWNER, REPO_NAME))
print('VERIFY repo:', info['full_name'], '| private:', info['private'], '| size KB:', info['size'])
cnt = gh('GET', '/repos/%s/%s/git/trees/main?recursive=0' % (OWNER, REPO_NAME))
print('VERIFY files on main:', len(cnt.get('tree', [])))
print('DONE https://github.com/%s/%s' % (OWNER, REPO_NAME))
