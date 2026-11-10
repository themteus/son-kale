"""Re-draw the inner-castle background (arka.png / on.png) at 1x pixel density.

The original is drawn at 1.5x in the game. Here it is NEAREST-upscaled 1.5x (same layout),
cut into overlapping tiles, each tile upscaled to 1024 and redrawn with SDXL + pixel-art LoRA
+ ControlNet canny (edges from a softened copy, so only the big shapes are locked),
BOX-downscaled back, feather-blended and quantized to the original palette.
on.png keeps its alpha mask exactly (1.5x NEAREST of the original mask).

  python arka_hd.py deneme arka --x 495 --y 570 --t 512 768 --denoise 0.4 0.5 --seed 7
  python arka_hd.py tam arka --t 512 --denoise 0.45 --cn 0.5 [--kis]
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import birim as B  # noqa: E402

KALE = f"{B.REPO}/assets/kale"
KAYNAK = "D:/AI/araclar/orijinal/kale"  # frozen originals (repo copies get replaced)
OUT = f"{B.OUT}/arka_hd"
BG = (128, 128, 128)

POS = ("pixel art, isometric medieval castle courtyard seen from above, stone castle walls made of many small "
       "bricks, round stone towers with conical roofs, dirt ground, grass, pine trees, crisp tiny pixels, "
       "detailed, clean dark outlines, warm sunlight from top left, PixelLab style")
POS_KIS = ("pixel art, isometric medieval castle courtyard in winter seen from above, everything covered in white "
           "snow, snow on the ground, snow on top of the stone castle walls and on the battlements, snowy roofs, "
           "snow covered pine trees, stone walls made of many small bricks, crisp tiny pixels, clean dark outlines, "
           "cold light from top left, PixelLab style")
NEG = ("blurry, photo, 3d render, realistic, text, watermark, big blocky pixels, low detail, smooth gradient, "
       "jpeg artifacts, people, characters, frame, border")
NEG_KIS = NEG + ", green grass, summer, autumn"


def kaynak(ad):
    os.makedirs(KAYNAK, exist_ok=True)
    p = f"{KAYNAK}/{ad}.png"
    if not os.path.exists(p):
        Image.open(f"{KALE}/{ad}.png").save(p)
    return Image.open(p).convert("RGBA")


def buyuk(ad, kis=False):
    im = kaynak(ad)
    W, H = round(im.width * 1.5), round(im.height * 1.5)
    big = im.resize((W, H), Image.Resampling.NEAREST)
    hd = f"{OUT}/{ad}.png"
    if kis and os.path.exists(hd):  # winter starts from the finished 1x summer image (same layout)
        alfa = big.getchannel("A")
        big = Image.open(hd).convert("RGBA")
        big.putalpha(alfa)
    rgb = Image.new("RGBA", (W, H), BG + (255,))
    rgb.alpha_composite(big)
    return rgb.convert("RGB"), big.getchannel("A")


def workflow(inp, ctrl, prefix, seed, denoise, cn, pos, neg, steps=25):
    wf = B.workflow(inp, prefix, seed, denoise, cn, pos, neg, steps)
    wf["15"] = {"class_type": "LoadImage", "inputs": {"image": ctrl}}
    wf["12"]["inputs"]["image"] = ["15", 0]
    wf["12"]["inputs"].update(low_threshold=0.4, high_threshold=0.8)
    wf["2"]["inputs"].update(strength_model=0.8, strength_clip=0.8)
    # plain VAE decode asks for ~9.6 GB on the RX 6700 XT, spills and slows every later job ~10x
    wf["8"] = {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["7", 0], "vae": ["3", 0], "tile_size": 512,
                                                          "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}}
    wf["11"] = {"class_type": "VAEEncodeTiled", "inputs": {"pixels": ["10", 0], "vae": ["3", 0], "tile_size": 512,
                                                           "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}}
    return wf


def parca(rgb, x, y, t, ad):
    """Tile (x,y,t) -> 1024 input + softened control image, saved into ComfyUI/input."""
    c = rgb.crop((x, y, x + t, y + t))
    inp = c.resize((1024, 1024), Image.Resampling.NEAREST)
    ctrl = c.filter(ImageFilter.GaussianBlur(1.2)).resize((1024, 1024), Image.Resampling.BILINEAR)
    a, b = f"hd_{ad}_{x}_{y}_{t}.png", f"hdc_{ad}_{x}_{y}_{t}.png"
    inp.save(f"{B.COMFY}/input/{a}")
    ctrl.save(f"{B.COMFY}/input/{b}")
    return a, b


def palet(ad, kis=False):
    """Palette image (max 256 colours) from the original, plus snow colours for winter."""
    src = [np.asarray(kaynak(ad))]
    if kis:
        for f in ("demirci1_karli", "ev2_karli", "oduncu2_karli", "kisla_karli"):
            for d in (f"{KALE}/varyant", f"{KALE}/sus/ic2"):
                if os.path.exists(f"{d}/{f}.png"):
                    src.append(np.asarray(Image.open(f"{d}/{f}.png").convert("RGBA")))
    px = np.concatenate([s.reshape(-1, 4) for s in src])
    px = px[px[:, 3] > 200][:, :3]
    strip = Image.fromarray(px.reshape(1, -1, 3).astype(np.uint8))
    q = strip.quantize(colors=96 if kis else 64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return q


def kuantala(im, pal):
    return im.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")


def izgara(W, H, t, ov):
    st = t - ov
    xs = list(range(0, max(W - t, 0) + 1, st))
    ys = list(range(0, max(H - t, 0) + 1, st))
    if xs[-1] != W - t:
        xs.append(W - t)
    if ys[-1] != H - t:
        ys.append(H - t)
    return [(x, y) for y in ys for x in xs]


def agirlik(t, ov):
    r = np.ones(t, np.float32)
    ramp = np.linspace(0.02, 1, ov, dtype=np.float32)
    r[:ov] = ramp
    r[-ov:] = ramp[::-1]
    return np.outer(r, r)


def deneme(a):
    rgb, _ = buyuk(a.ad, a.kis)
    pal = palet(a.ad, a.kis)
    jobs, meta = [], []
    for t in a.t:
        x, y = a.x, a.y
        inp, ctrl = parca(rgb, x, y, t, a.ad + ("_kis" if a.kis else ""))
        for d in a.denoise:
            for cn in a.cn:
                pre = f"son-kale-v2/arka_hd/deneme_{a.ad}{'_kis' if a.kis else ''}_t{t}_d{int(d*100)}_c{int(cn*100)}_s{a.seed}"
                jobs.append((pre, workflow(inp, ctrl, pre, a.seed, d, cn, POS_KIS if a.kis else POS, NEG_KIS if a.kis else NEG)))
                meta.append((pre, t, d, cn))
    out = B.run_jobs(jobs)
    tiles = []
    for pre, t, d, cn in meta:
        g = Image.open(out[pre]).convert("RGB").resize((t, t), Image.Resampling.BOX)
        tiles.append((kuantala(g, pal), f"t{t} d{d} c{cn}"))
    # side by side, cropped to the smallest tile, x2 for viewing
    m = min(a.t)
    orig = rgb.crop((a.x, a.y, a.x + m, a.y + m))
    row = [orig] + [im.crop((0, 0, m, m)) for im, _ in tiles]
    W = Image.new("RGB", (len(row) * (m + 8), m), (30, 30, 30))
    for i, im in enumerate(row):
        W.paste(im, (i * (m + 8), 0))
    W = W.resize((W.width * 2, W.height * 2), Image.Resampling.NEAREST)
    p = f"D:/AI/son-kale-cikti/deneme_{a.ad}{'_kis' if a.kis else ''}_{a.x}_{a.y}_s{a.seed}.png"
    W.save(p)
    print(p, [lab for _, lab in tiles])


def tam(a):
    rgb, alfa = buyuk(a.ad, a.kis)
    W, H = rgb.size
    t, ov = a.t[0], a.ov
    d, cn = a.denoise[0], a.cn[0]
    kis = "_kis" if a.kis else ""
    jobs, meta = [], []
    for (x, y) in izgara(W, H, t, ov):
        if alfa.crop((x, y, x + t, y + t)).getbbox() is None:
            continue  # fully transparent (on.png)
        inp, ctrl = parca(rgb, x, y, t, a.ad + kis)
        pre = f"son-kale-v2/arka_hd/{a.ad}{kis}_{x}_{y}"
        jobs.append((pre, workflow(inp, ctrl, pre, a.seed, d, cn, POS_KIS if a.kis else POS, NEG_KIS if a.kis else NEG)))
        meta.append((pre, x, y))
    print(f"{len(jobs)} parca", flush=True)
    out = B.run_jobs(jobs)
    acc = np.zeros((H, W, 3), np.float32)
    wsum = np.zeros((H, W, 1), np.float32)
    w = agirlik(t, ov)[..., None]
    for pre, x, y in meta:
        g = np.asarray(Image.open(out[pre]).convert("RGB").resize((t, t), Image.Resampling.BOX), np.float32)
        acc[y:y + t, x:x + t] += g * w
        wsum[y:y + t, x:x + t] += w
    base = np.asarray(rgb, np.float32)
    res = np.where(wsum > 0, acc / np.maximum(wsum, 1e-6), base)
    im = kuantala(Image.fromarray(res.clip(0, 255).astype(np.uint8)), palet(a.ad, a.kis))
    im = im.convert("RGBA")
    im.putalpha(alfa)
    adi = a.ad + ("_karli" if a.kis else "")
    p = f"{OUT}/{adi}.png"
    os.makedirs(OUT, exist_ok=True)
    (im if a.ad == "on" else im.convert("RGB")).save(p)
    print(p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mod", choices=["deneme", "tam"])
    ap.add_argument("ad", choices=["arka", "on"])
    ap.add_argument("--x", type=int, default=495)
    ap.add_argument("--y", type=int, default=570)
    ap.add_argument("--t", type=int, nargs="+", default=[512])
    ap.add_argument("--ov", type=int, default=128)
    ap.add_argument("--denoise", type=float, nargs="+", default=[0.45])
    ap.add_argument("--cn", type=float, nargs="+", default=[0.5])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--kis", action="store_true")
    a = ap.parse_args()
    deneme(a) if a.mod == "deneme" else tam(a)
