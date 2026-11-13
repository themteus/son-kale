"""Collect the exact ComfyUI settings used for Son Kale from the PNG metadata ComfyUI stores
in every output (the API workflow), one sample per (folder, recipe tag).

  python uretim_topla.py <repo>/motor-deneme-5b8e2f/uretim
Writes is-akislari/api/<name>.json, is-akislari/ui/<name>.json (drag-and-drop format, built
with ComfyUI's /object_info) and ayarlar_png.json (settings read from each workflow).
"""
import glob
import json
import os
import re
import sys
import urllib.request

from PIL import Image

OUT_ROOT = "D:/AI/ComfyUI/output"
URL = "http://127.0.0.1:8188"


def ornekler():
    """{name: png path} - first PNG of each recipe tag in each output folder."""
    seen = {}
    for p in sorted(glob.glob(f"{OUT_ROOT}/son-kale-*/**/*.png", recursive=True)):
        rel = os.path.relpath(p, OUT_ROOT).replace("\\", "/")
        base = os.path.basename(p)
        tag = re.sub(r"_\d{5}_\.png$", "", base)
        tag = re.sub(r"_\d{2}$", "", tag)                     # frame index (units)
        tag = re.sub(r"_\d+_\d+$", "", tag)                   # tile x_y (background)
        tag = re.sub(r"(ciftlik|demirci|duvarci|ev|maden|oduncu|tasocagi|yayci)\d", r"\1", tag)
        name = (os.path.dirname(rel).replace("/", "__") + "__" + tag).replace("__ham", "")
        if name not in seen:
            seen[name] = p
    return seen


def api_of(p):
    try:
        info = Image.open(p).info
    except Exception:
        return None
    return json.loads(info["prompt"]) if "prompt" in info else None


def ayarlar(wf):
    s = {}
    for n in wf.values():
        c, i = n["class_type"], n["inputs"]
        if c == "CheckpointLoaderSimple":
            s["checkpoint"] = i["ckpt_name"]
        elif c == "LoraLoader":
            s["lora"] = i["lora_name"]; s["lora_guc"] = [i["strength_model"], i["strength_clip"]]
        elif c == "VAELoader":
            s["vae"] = i["vae_name"]
        elif c == "ControlNetLoader":
            s["controlnet"] = i["control_net_name"]
        elif c.startswith("ControlNetApply"):
            s["controlnet_guc"] = i.get("strength"); s["controlnet_basla_bitir"] = [i.get("start_percent"), i.get("end_percent")]
        elif c == "Canny":
            s["canny_esik"] = [i["low_threshold"], i["high_threshold"]]
        elif c == "KSampler":
            for k in ("seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"):
                s[k] = i[k]
        elif c == "EmptyLatentImage":
            s["cozunurluk"] = [i["width"], i["height"]]
        elif c == "LoadImage":
            s.setdefault("giris_gorselleri", []).append(i["image"])
    def metin(ref, yon):
        n = wf[ref[0]]
        while n["class_type"] != "CLIPTextEncode":  # follow through ControlNetApply
            n = wf[n["inputs"][yon][0]]
        return n["inputs"]["text"]
    ks = next((v for v in wf.values() if v["class_type"] == "KSampler"), None)
    if ks:
        s["pozitif"] = metin(ks["inputs"]["positive"], "positive")
        s["negatif"] = metin(ks["inputs"]["negative"], "negative")
    if "cozunurluk" not in s:
        s["cozunurluk"] = [1024, 1024]
    return s


def object_info():
    with urllib.request.urlopen(URL + "/object_info", timeout=60) as r:
        return json.load(r)


def ui_of(api, oi):
    """API prompt -> LiteGraph UI workflow (loads by drag and drop)."""
    ids = {k: i + 1 for i, k in enumerate(api)}
    nodes, links, lid = [], [], 0
    out_links = {}
    for k, n in api.items():
        info = oi[n["class_type"]]
        req = info["input"].get("required", {}); opt = info["input"].get("optional", {})
        order = list(req) + list(opt)
        inputs, widgets = [], []
        for name in order:
            if name not in n["inputs"]:
                continue
            v = n["inputs"][name]
            spec = (req.get(name) or opt.get(name))
            typ = spec[0] if isinstance(spec[0], str) else "COMBO"
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and v[0] in api:
                lid += 1
                src = api[v[0]]["class_type"]
                otype = oi[src]["output"][v[1]]
                links.append([lid, ids[v[0]], v[1], ids[k], len(inputs), otype])
                out_links.setdefault((v[0], v[1]), []).append(lid)
                inputs.append({"name": name, "type": otype, "link": lid})
            else:
                widgets.append(v)
                if name in ("seed", "noise_seed"):
                    widgets.append("fixed")
        nodes.append({"id": ids[k], "type": n["class_type"], "pos": [(ids[k] % 6) * 330, (ids[k] // 6) * 260],
                      "size": [300, 200], "flags": {}, "order": ids[k], "mode": 0, "inputs": inputs,
                      "outputs": [], "properties": {"Node name for S&R": n["class_type"]}, "widgets_values": widgets,
                      "_k": k})
    for nd in nodes:
        info = oi[nd["type"]]
        nd["outputs"] = [{"name": nm, "type": t, "links": out_links.get((nd["_k"], i), []), "slot_index": i}
                         for i, (nm, t) in enumerate(zip(info["output_name"], info["output"]))]
        del nd["_k"]
    return {"last_node_id": len(nodes), "last_link_id": lid, "nodes": nodes, "links": links,
            "groups": [], "config": {}, "extra": {}, "version": 0.4}


def main(hedef):
    oi = object_info()
    os.makedirs(f"{hedef}/is-akislari/api", exist_ok=True)
    os.makedirs(f"{hedef}/is-akislari/ui", exist_ok=True)
    tum = {}
    for name, p in ornekler().items():
        wf = api_of(p)
        if not wf:
            continue
        json.dump(wf, open(f"{hedef}/is-akislari/api/{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(ui_of(wf, oi), open(f"{hedef}/is-akislari/ui/{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        s = ayarlar(wf)
        s["ornek_cikti"] = os.path.relpath(p, OUT_ROOT).replace("\\", "/")
        tum[name] = s
    json.dump(tum, open(f"{hedef}/ayarlar_png.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(tum), "is akisi")


if __name__ == "__main__":
    main(sys.argv[1])
