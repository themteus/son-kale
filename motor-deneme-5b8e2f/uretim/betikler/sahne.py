"""Offline render of the inner-castle scene like kale.js + varyant.js draw it (for comparison shots
when the game cannot be run in a visible browser).

Layers: background, path layer, buildings (depth (disari ? 30 : 10) + dipY*O/2000), decorations
(same rule with their y), front walls at depth 20. Textures / tints follow varyant.js:
winter -> *_karli (else tint 0xcfdbec), winter + damage -> kv_*_yikik_karli, winter night -> *_karli
+ tint 0x56648c, summer night -> *_gece (+ 0x... ) or tint.

  python sahne.py <out.png> [seviye=3]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

K = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"
O = 3
TON = {"karli": (0xcf, 0xdb, 0xec), "gece": (0x56, 0x64, 0x8c)}


def tint(im, rgb):
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    a[..., :3] *= np.array(rgb) / 255.0
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def yukle(p):
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None


def sahne(seviye=3, kis=True, hasar=False, gece=False):
    M = json.load(open(f"{K}/kale.json", encoding="utf-8"))
    L = json.load(open(f"{K}/kale_ic2.json", encoding="utf-8"))
    hal = "yikik" if hasar else ("gece" if gece else ("karli" if kis else None))

    def doku(temel_yol, var_yol_fn, is_bina):
        temel = yukle(temel_yol)
        if hal == "gece":
            if kis and var_yol_fn("karli") and yukle(var_yol_fn("karli")):
                return tint(yukle(var_yol_fn("karli")), TON["gece"])
            g = var_yol_fn("gece") and yukle(var_yol_fn("gece"))
            return g if g is not None else tint(temel, TON["gece"])
        if hal == "yikik":
            if kis and var_yol_fn("yikik_karli") and yukle(var_yol_fn("yikik_karli")):
                return yukle(var_yol_fn("yikik_karli"))
            y = var_yol_fn("yikik") and yukle(var_yol_fn("yikik"))
            if is_bina:
                return y if y is not None else temel
            k = var_yol_fn("karli") and yukle(var_yol_fn("karli"))
            return k if (kis and k is not None) else temel
        if hal == "karli":
            k = var_yol_fn("karli") and yukle(var_yol_fn("karli"))
            return k if k is not None else tint(temel, TON["karli"])
        return temel

    arka = yukle(f"{K}/arka_karli.png" if kis else f"{K}/arka.png")
    if gece:
        arka = tint(arka, TON["gece"])
    tuval = arka.copy()
    z = yukle(f"{K}/sus/ic2/zemin.png")
    if z is not None:
        z = tint(z, TON["gece"] if gece else TON["karli"]) if kis or gece else z
        tuval.alpha_composite(z)
    nesneler = []
    for k_, m in M["binalar"].items():
        if not k_.endswith(str(seviye)):
            continue
        im = doku(f"{K}/{k_}.png", lambda h, k_=k_: f"{K}/varyant/{k_}_{h}.png", True)
        im = im.resize((round(im.width * (m.get("piksel") or O)), round(im.height * (m.get("piksel") or O))), Image.NEAREST) if (m.get("piksel") or O) != 1 else im
        nesneler.append(((30 if m.get("disari") else 10) + m["dipY"] * O / 2000, im, (round(m["x"] * O), round(m["y"] * O))))
    sus = [dict(s) for s in M.get("susler", [])] + [dict(s, ad="ic2/" + s["ad"]) for s in L.get("susler", [])]
    for s in sus:
        p = f"{K}/sus/{s['ad']}.png"
        im = doku(p, lambda h, s=s: f"{K}/sus/{s['ad']}_{h}.png", False)
        if im is None:
            continue
        pk = s.get("piksel") or 1
        if pk != 1:
            im = im.resize((round(im.width * pk), round(im.height * pk)), Image.NEAREST)
        if s.get("ayna"):
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        nesneler.append(((30 if s.get("disari") else 10) + s["y"] / 2000, im, (round(s["x"] - im.width / 2), round(s["y"] - im.height))))
    on = yukle(f"{K}/on_karli.png" if kis else f"{K}/on.png")
    if gece:
        on = tint(on, TON["gece"])
    nesneler.append((20, on, (round(M["on"]["x"] * O), round(M["on"]["y"] * O))))
    for _, im, (x, y) in sorted(nesneler, key=lambda t: t[0]):
        tuval.alpha_composite(im, (x, y))
    return tuval.convert("RGB")


if __name__ == "__main__":
    out = sys.argv[1]
    sv = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    hal = [("kis seviye 3", dict(kis=True)), ("kis + hasar", dict(kis=True, hasar=True)), ("kis gecesi", dict(kis=True, gece=True))]
    ims = [sahne(sv, **kw) for _, kw in hal]
    W = Image.new("RGB", (960 * 3 + 20, 540), (30, 30, 30))
    for i, im in enumerate(ims):
        W.paste(im.resize((960, 540), Image.BOX), (i * 970, 0))
        im.save(out.replace(".png", f"_{i}.png"))
    W.save(out)
    print(out)
