import subprocess, json, glob, os, re
os.chdir(r"C:/Users/User/tmp/tg_chat_grow")
ps = 'Get-CimInstance Win32_Process -Filter "Name=\'python.exe\'" | Select-Object ProcessId,CommandLine | Format-List'
out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                     capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout
procs = re.findall(r"CommandLine\s*:\s*(.+)", out)
tags = ["shard_worker", "mass_seed", "chat_hunter", "harvest", "merge_pool", "wave_chain", "responder"]
counts = {t: sum(1 for c in procs if t in c) for t in tags}
print("PROCS:", counts, "| python total:", len(procs))
sd = json.load(open("shill_done.json", encoding="utf-8"))
print("shill_done:", len(sd))
pairs = resp = 0
for f in glob.glob("mass_state_*.json"):
    s = json.load(open(f, encoding="utf-8"))
    for g, v in s.items():
        if isinstance(v, dict):
            pairs += v.get("pairs", 0)
            resp += v.get("replies", 0) + v.get("resp", 0)
print("state pairs:", pairs, "replies:", resp)
pm = json.load(open("pool_merged.json", encoding="utf-8"))
print("pool:", len(pm))
