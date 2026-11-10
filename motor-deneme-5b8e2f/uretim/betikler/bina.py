"""Variants of the inner-castle buildings (PixelLab isometric art) with SDXL + ControlNet canny.

Usage:
  python bina.py demirci3 --varyant karli gece yikik --seeds 11 22
  python bina.py hepsi --varyant karli gece yikik --seed 22
Output: D:/AI/ComfyUI/output/son-kale-v2/bina/<varyant>/<bina>.png (same size as the original)
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import birim as B  # noqa: E402  (workflow, run_jobs, build_palette, apply_palette)

KALE = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"
ORJ = "D:/AI/araclar/orijinal/kale"
OUT = f"{B.OUT}/bina"
BG = (200, 200, 200)
BINALAR = ["ciftlik", "demirci", "duvarci", "ev", "maden", "oduncu", "tasocagi", "yayci"]
AD = {"ciftlik": "farmhouse with barn", "demirci": "blacksmith workshop with forge and anvil",
      "duvarci": "stonemason workshop", "ev": "medieval house", "maden": "mine entrance with wooden supports",
      "oduncu": "lumberjack hut with log piles", "tasocagi": "stone quarry with cut blocks", "yayci": "bowyer workshop"}
BASE = "pixel art, isometric 2:1 view, a medieval {ad}, {v}, single building, centered, plain flat light gray background, crisp pixels, clean dark outline, cozy medieval city builder style"
NEG = "blurry, photo, 3d render, realistic, text, watermark, multiple buildings, cropped, top-down, side view, people"
VARYANT = {
    # denoise, controlnet strength, prompt part, silhouette from (old|new)
    "karli": (0.42, 0.75, "winter, roofs covered in thick fresh white snow, snow piles on the ground, small icicles hanging from eaves, frosty cold blue shadows", "old"),
    "gece": (0.5, 0.8, "at night, dark blue moonlit colors, warm glowing yellow lit windows and doorway, lantern light, deep night shadows", "old"),
    "yikik": (0.9, 0.35, "roofless burned ruin after a siege, roof completely collapsed into the house, only broken walls and charred beams standing, big holes in the walls, rubble piles, collapsed broken roof with exposed charred beams, cracked crumbling walls, rubble and debris, scorch marks", "new"),
}


def ref_image(name):
    p = f"{ORJ}/{name}.png"
    return Image.open(p).convert("RGBA")


def hsv(arr):
    f = arr[..., :3].astype(np.float32) / 255
    mx, mn = f.max(-1), f.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, sat, mx


UST_BOLGE = {"ciftlik1": 0.5, "demirci1": 0.55, "ev1": 0.58, "yayci1": 0.55, "oduncu1": 0.4, "oduncu2": 0.4, "oduncu3": 0.4, "ciftlik3": 0.42}


def karla_ust(im, oran=0.42):
    """Snow for thatch/log buildings: every warm-or-cool surface in the upper part of each
    column (the roof), plus a thin cap on every top edge; walls lower down stay as they are."""
    a = np.asarray(im).copy()
    h, sat, val = hsv(a)
    vis = a[..., 3] > 0
    H, W = vis.shape
    zone = np.zeros_like(vis)
    cap = np.zeros_like(vis)
    for x in range(W):
        ys = np.nonzero(vis[:, x])[0]
        if len(ys) < 4:
            continue
        y0, y1 = ys[0], ys[-1]
        zone[y0:y0 + int(oran * (y1 - y0)) + 1, x] = True
        # top-edge caps: pixels whose pixel above is empty (eaves, ledges, ridges)
    above = np.zeros_like(vis); above[1:] = vis[:-1]
    top = vis & ~above
    for k in range(3):
        cap |= np.roll(top, k, axis=0)
    fire = (sat > 0.6) & (val > 0.8) & (h < 60)
    outline = val < 0.18
    roofish = vis & zone & (sat > 0.12) & (val > 0.22) & ~fire & ~outline
    core = ndimage.binary_opening(roofish, structure=np.ones((3, 3)))
    roof = ndimage.binary_dilation(core, iterations=1) & roofish
    snow_mask = (roof | (cap & vis & ~fire & ~outline))
    lum = (0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]) / 255
    snow = np.stack([200 + 55 * lum, 212 + 43 * lum, 228 + 27 * lum], -1)
    a[..., :3] = np.where(snow_mask[..., None], np.clip(snow, 0, 255), a[..., :3]).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def karla(im):
    """Paint roof tiles (orange-brown, warm, fairly saturated) and flat ground as snow,
    keeping the original light/shade so the shapes still read."""
    a = np.asarray(im).copy()
    h, sat, val = hsv(a)
    vis = a[..., 3] > 0
    cand = vis & (h > 4) & (h < 34) & (sat > 0.3) & (val > 0.28) & ~((val > 0.8) & (sat > 0.7))  # warm tiles, not fire
    # roofs are wide tile areas; timber beams are thin lines: an opening removes the beams
    core = ndimage.binary_opening(cand, structure=np.ones((4, 4)))
    roof = ndimage.binary_dilation(core, iterations=2) & cand
    lum = (0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]) / 255
    snow = np.stack([200 + 55 * lum, 212 + 43 * lum, 228 + 27 * lum], -1)
    a[..., :3] = np.where(roof[..., None], np.clip(snow, 0, 255), a[..., :3]).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def gecele(im, isik_v=0.75, isik_s=0.45):
    """Night grade of the original art: dark blue moonlight, warm emissive pixels stay lit
    and get a soft 1px glow."""
    a = np.asarray(im).astype(np.float32)
    h, sat, val = hsv(a.astype(np.uint8))
    vis = a[..., 3] > 0
    emissive = vis & (h < 60) & (sat > isik_s) & (val > isik_v)  # fire, embers, lit windows
    lum = (0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2])
    night = np.stack([lum * 0.28 + a[..., 0] * 0.12, lum * 0.34 + a[..., 1] * 0.12, lum * 0.52 + a[..., 2] * 0.2], -1)
    out = np.where(emissive[..., None], a[..., :3], night)
    # warm glow around emissive pixels (only on the building)
    glow = ndimage.binary_dilation(emissive, iterations=2) & ~emissive & vis
    out[glow] = out[glow] * 0.5 + np.array([255, 170, 70]) * 0.35
    res = np.dstack([np.clip(out, 0, 255), a[..., 3]]).astype(np.uint8)
    return Image.fromarray(res, "RGBA")


ON_ISLEM = {"karli": karla}
KROMA = {"aktif": False}
SURUM = {"karli": 4, "yikik": 3}
YIKIK_OZEL = {
    "ciftlik": "ruined burned farmstead after a siege, thatched roof partly burned away exposing charred rafters, broken wooden fence, scattered hay bales, trampled crop field, the farmhouse and barn still recognizable",
    "maden": "abandoned damaged mine after a siege, dark mine tunnel entrance with broken wooden support beams, rail tracks and an overturned ore cart, fallen rocks, the mine entrance still recognizable",
    "tasocagi": "damaged stone quarry after a siege, cut stone blocks scattered and broken, a toppled wooden crane, cracked quarry walls, rubble, the quarry still recognizable",
    "oduncu": "burned damaged lumberjack hut after a siege, roof partly collapsed with charred beams, scattered log piles, a broken saw horse and axe in a stump, the hut still recognizable",
}
OZEL_SURUM = 2  # bump to redraw a variant after changing its recipe


def make_input(name, varyant=None):
    im = ref_image(name)
    if varyant == "karli" and name in UST_BOLGE:
        im = karla_ust(im, UST_BOLGE[name])
    elif varyant in ON_ISLEM:
        im = ON_ISLEM[varyant](im)
    bb = im.getchannel("A").getbbox()
    k = max(1, 860 // max(bb[2] - bb[0], bb[3] - bb[1]))
    big = im.resize((im.width * k, im.height * k), Image.Resampling.NEAREST)
    ox = int(512 - (bb[0] + bb[2]) / 2 * k)
    oy = int(512 - (bb[1] + bb[3]) / 2 * k)
    canvas = Image.new("RGBA", (1024, 1024), BG + (255,))
    layer = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    layer.paste(big, (ox, oy))
    canvas.alpha_composite(layer)
    fn = f"v2_bina_{name}{'_' + varyant if varyant else ''}.png"
    canvas.convert("RGB").save(f"{B.COMFY}/input/{fn}")
    return fn, (ox, oy, k)


def back(gen_path, name, place, sil):
    old = ref_image(name)
    ox, oy, k = place
    g = Image.open(gen_path).convert("RGB")
    box = g.crop((ox, oy, ox + old.width * k, oy + old.height * k)).resize(old.size, Image.Resampling.BOX)
    oa = np.asarray(old.getchannel("A")) >= 128
    rgb = np.asarray(box).astype(np.int16)
    near_bg = np.abs(rgb - np.array(BG)).max(axis=2) <= 22
    if sil == "old":
        mask = oa
    else:
        # ruined: shape may lose parts (collapsed roof), never grow far beyond the old one
        mask = ndimage.binary_dilation(oa, iterations=2) & ~near_bg
        mask = ndimage.binary_opening(mask, structure=np.ones((2, 2)))
        lab, n = ndimage.label(mask)
        if n > 1:
            sizes = np.bincount(lab.ravel()); sizes[0] = 0
            mask = (sizes >= 0.02 * sizes.max())[lab]
    if sil == "old" and KROMA.get("aktif"):
        o_rgb = np.asarray(old.convert("RGB")).astype(np.float32)
        n_rgb = np.asarray(box).astype(np.float32)
        _, ns, nv = hsv(n_rgb.astype(np.uint8))
        oh, osat, oval = hsv(o_rgb.astype(np.uint8))
        fire = (osat > 0.5) & (oval > 0.75) & (oh < 60)
        snow = (nv > 0.72) & (ns < 0.18) & ~fire
        yo = np.asarray(Image.fromarray(o_rgb.astype(np.uint8)).convert("YCbCr")).astype(np.float32)
        yn = np.asarray(box.convert("YCbCr")).astype(np.float32)
        ycc = yn.copy()
        ycc[..., 1:] = np.where(snow[..., None], yn[..., 1:], yo[..., 1:])
        box = Image.fromarray(ycc.astype(np.uint8), "YCbCr").convert("RGB")
    out = box.convert("RGBA")
    out.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bina", nargs="+")
    ap.add_argument("--varyant", nargs="+", default=list(VARYANT))
    ap.add_argument("--seeds", nargs="+", type=int, default=[22])
    ap.add_argument("--renk", type=int, default=24)
    a = ap.parse_args()
    names = [f"{b}{s}" for b in BINALAR for s in (1, 2, 3)] if a.bina == ["hepsi"] else a.bina

    jobs, meta = [], {}
    for name in names:
        base = "".join(c for c in name if not c.isdigit())
        for v in a.varyant:
            if v == "gece":
                os.makedirs(f"{OUT}/gece", exist_ok=True)
                gecele(ref_image(name)).save(f"{OUT}/gece/{name}.png")
                continue
            inp, place = make_input(name, v)
            d, cn, part, sil = VARYANT[v]
            ozel = v == "yikik" and base in YIKIK_OZEL
            if ozel:
                d, cn, part = 0.78, 0.6, YIKIK_OZEL[base]
            pos = BASE.format(ad=AD[base], v=part)
            for s in a.seeds:
                ver = SURUM.get(v, 3)
                if (v == "karli" and name in UST_BOLGE) or ozel:
                    ver = f"{ver}x{OZEL_SURUM}"
                prefix = f"son-kale-v2/bina/ham/{v}{ver}_{name}_s{s}"
                done = sorted(glob.glob(f"{B.COMFY}/output/{prefix}_*.png"))
                meta[prefix] = (name, v, s, place, sil, done[-1] if done else None)
                if not done:
                    wf = B.workflow(inp, prefix, s, d, cn, pos, NEG)
                    if v == "yikik":
                        wf["14"]["inputs"]["end_percent"] = 0.7 if ozel else 0.45  # identity vs free shape
                    jobs.append((prefix, wf))
    print(f"{len(jobs)} cizim kuyruga alindi ({len(meta) - len(jobs)} hazir)", flush=True)
    paths = B.run_jobs(jobs) if jobs else {}

    for prefix, (name, v, s, place, sil, done) in meta.items():
        KROMA["aktif"] = v == "karli"
        frame = back(paths.get(prefix, done), name, place, sil)
        pal = B.build_palette([frame], a.renk)
        frame = B.apply_palette(frame, pal)
        d = f"{OUT}/{v}"
        os.makedirs(d, exist_ok=True)
        suffix = "" if len(a.seeds) == 1 else f"_s{s}"
        frame.save(f"{d}/{name}{suffix}.png")
    print("kaydedildi:", OUT)


if __name__ == "__main__":
    main()
