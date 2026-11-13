"""Copy finished units into the game repo.

For each unit: back up the old sheet to assets/gorsel/eski/<unit>.png (only the first time),
copy the new sheet, and replace only that unit's entry in kareler.json.
Usage: python aktar.py zombi kosucu iskelet ...
"""
import json
import os
import shutil
import sys

REPO = "D:/AI/son-kale/motor-deneme-5b8e2f"
G = f"{REPO}/assets/gorsel"
OUT = "D:/AI/ComfyUI/output/son-kale-v2"
YAYCILAR = ("okcu", "asker")

path = f"{G}/kareler.json"
raw = open(path, encoding="utf-8").read()
K = json.loads(raw)
os.makedirs(f"{G}/eski", exist_ok=True)
for u in sys.argv[1:]:
    new_png, new_json = f"{OUT}/{u}/{u}.png", f"{OUT}/{u}/kareler_{u}.json"
    if not (os.path.exists(new_png) and os.path.exists(new_json)):
        print(f"{u}: hazir degil, atlandi"); continue
    if not os.path.exists(f"{G}/eski/{u}.png"):
        shutil.copy2(f"{G}/{u}.png", f"{G}/eski/{u}.png")
    shutil.copy2(new_png, f"{G}/{u}.png")
    entry = json.load(open(new_json, encoding="utf-8"))
    if u in YAYCILAR:
        K[u] = entry
    else:
        entry.pop("rows", None)
        K["birimler"][u] = {**K["birimler"][u], **{k: entry[k] for k in ("fw", "fh", "footY", "centerX", "olcek")}}
    print(f"{u}: aktarildi ({entry['fw']}x{entry['fh']}, olcek {entry['olcek']})")
# keep the original compact one-line style
open(path, "w", encoding="utf-8", newline="").write(json.dumps(K, ensure_ascii=False, separators=(",", ":")))
