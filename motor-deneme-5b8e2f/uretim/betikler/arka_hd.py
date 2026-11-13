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
import glob
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
        import kar
        yaz = Image.open(hd).convert("RGB")
        big = kar.karla(yaz, np.asarray(alfa) > 0).convert("RGBA")  # code-painted snow, then a light redraw
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
    for b in ("ev", "demirci", "duvarci", "oduncu"):  # shared palette with the buildings
        for n in (1, 2, 3):
            if os.path.exists(f"{KALE}/{b}{n}.png"):
                src.append(np.asarray(Image.open(f"{KALE}/{b}{n}.png").convert("RGBA")))
    if kis:
        for f in ("demirci1_karli", "ev2_karli", "oduncu2_karli", "kisla_karli"):
            for d in (f"{KALE}/varyant", f"{KALE}/sus/ic2"):
                if os.path.exists(f"{d}/{f}.png"):
                    src.append(np.asarray(Image.open(f"{d}/{f}.png").convert("RGBA")))
    px = np.concatenate([s.reshape(-1, 4) for s in src])
    px = px[px[:, 3] > 200][:, :3]
    strip = Image.fromarray(px.reshape(1, -1, 3).astype(np.uint8))
    q = strip.quantize(colors=96 if kis else 48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return q


def kuantala(im, pal):
    return im.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")


def tek_piksel(im, koru_m=None):
    """3x3 mode filter only for lone pixels: a pixel whose colour has no 8-neighbour of the same colour
    takes the colour most of its neighbours share (salt-and-pepper dots, 1 px brick crumbs)."""
    a = np.asarray(im.convert("RGB")).astype(np.int32)
    kod = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    H, W = kod.shape
    p = np.pad(kod, 1, mode="edge")
    komsu = [p[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
    komsu = np.stack(komsu)                                   # 8 x H x W
    yalniz = ~(komsu == kod).any(0)
    say = (komsu[None] == komsu[:, None]).sum(1)              # how many neighbours share each neighbour's colour
    en = komsu[say.argmax(0), np.arange(H)[:, None], np.arange(W)[None]]
    cogunluk = say.max(0) >= 4
    yer = yalniz & cogunluk
    if koru_m is not None:
        from scipy import ndimage
        yer &= ~ndimage.binary_dilation(koru_m, iterations=2)
    kod = np.where(yer, en, kod)
    out = np.stack([(kod >> 16) & 255, (kod >> 8) & 255, kod & 255], -1).astype(np.uint8)
    return Image.fromarray(out)


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


# small props baked into the background, original (1280x720) coords: they melt at the tile settings,
# so each gets its own pass: 4x zoom, low denoise, sharp canny
KORU = {
    "arka": {"kuyu_tezgah": (486, 296, 548, 380), "tezgah2": (558, 334, 606, 382),
             "fici": (566, 292, 594, 322), "araba": (774, 314, 828, 372), "fener": (700, 340, 726, 392),
             "saman": (770, 496, 884, 560),
             # second round (review): keep, left back tower and the two back-wall banners, lower denoise,
             # stronger ControlNet
             "burc2": ((936, 214, 1256, 456), 0.25, 0.9), "kule_sol": ((250, 105, 315, 200), 0.25, 0.9),
             "bayrak_sol": ((342, 100, 378, 145), 0.25, 0.9), "bayrak_sag": ((745, 100, 781, 145), 0.25, 0.9),
             "yol": ((488, 370, 556, 412), 0.25, 0.9), "mesale": ((660, 140, 692, 192), 0.25, 0.9)},
    "on": {},
}


def koru(res, rgb, a):
    kutular = KORU.get(a.ad, {}) if not a.koruma_yok else {}
    if not kutular:
        return res
    kis = "_kis" if a.kis else ""
    jobs, meta = [], []
    for ad, kutu in kutular.items():
        (x0, y0, x1, y1), kd, kcn = kutu if len(kutu) == 3 else (kutu, a.koru_d, 0.8)
        X0, Y0, X1, Y1 = [round(v * 1.5) for v in (x0 - 6, y0 - 6, x1 + 6, y1 + 6)]
        s = max(X1 - X0, Y1 - Y0)
        k = max(2, 1024 // s)
        if len(kutu) == 3:
            k = min(4, k)  # small boxes: do not zoom past 4x (first-round boxes keep their cached scale)
        c = rgb.crop((X0, Y0, X0 + s, Y0 + s))
        inp = Image.new("RGB", (1024, 1024), BG)
        inp.paste(c.resize((s * k, s * k), Image.Resampling.NEAREST), (0, 0))
        fa = f"hdk_{a.ad}{kis}_{ad}.png"
        inp.save(f"{B.COMFY}/input/{fa}")
        pre = f"son-kale-v2/arka_hd/koru_{a.ad}{kis}_{ad}_d{int(kd * 100)}"
        wf = workflow(fa, fa, pre, a.seed, kd, kcn, POS_KIS if a.kis else POS, NEG_KIS if a.kis else NEG)
        wf["12"]["inputs"].update(low_threshold=0.3, high_threshold=0.6)
        jobs.append((pre, wf))
        meta.append((pre, X0, Y0, s, k))
    out = {}
    for pre, _ in jobs:
        done = sorted(glob.glob(f"{B.COMFY}/output/{pre}_*.png"))
        if done:
            out[pre] = done[-1]
    todo = [(p, w) for p, w in jobs if p not in out]
    out.update(B.run_jobs(todo) if todo else {})
    res = res.copy()
    for pre, X0, Y0, s, k in meta:
        g = Image.open(out[pre]).convert("RGB").crop((0, 0, s * k, s * k)).resize((s, s), Image.Resampling.BOX)
        g = g.filter(ImageFilter.UnsharpMask(radius=1.0, percent=a.keskin, threshold=2))
        if not a.kis:  # keep the tone of the old art in this box (the redraw drifts to yellow-cream)
            o = np.asarray(rgb.crop((X0, Y0, X0 + s, Y0 + s)), np.float32)
            gg = np.asarray(g, np.float32)
            gg = (gg - gg.mean((0, 1))) / (gg.std((0, 1)) + 1e-3) * o.std((0, 1)) + o.mean((0, 1))
            g = Image.fromarray(gg.clip(0, 255).astype(np.uint8))
        m = Image.new("L", (s, s), 0)
        m.paste(255, (6, 6, s - 6, s - 6))
        res.paste(g, (X0, Y0), m.filter(ImageFilter.GaussianBlur(3)))
    return res


def tam(a):
    rgb, alfa = buyuk(a.ad, a.kis)
    W, H = rgb.size
    t, ov = a.t[0], a.ov
    d, cn = a.denoise[0], a.cn[0]
    kis = "_kis" if a.kis else ""
    # opaque image: mirror-pad P px on every side, so no tile touches the real border
    # (SDXL paints a dark rounded frame on tiles that touch it)
    P = a.pad if a.ad == "arka" else 0
    rgb0 = rgb
    if P:
        rgb = Image.fromarray(np.pad(np.asarray(rgb0), ((P, P), (P, P), (0, 0)), mode="reflect"))
        alfa_p = Image.new("L", rgb.size, 255)
    else:
        alfa_p = alfa
    Wp, Hp = rgb.size
    etk = f"_p{P}" if P else ""
    jobs, meta = [], []
    for (x, y) in izgara(Wp, Hp, t, ov):
        if alfa_p.crop((x, y, x + t, y + t)).getbbox() is None:
            continue  # fully transparent (on.png)
        inp, ctrl = parca(rgb, x, y, t, a.ad + kis + etk)
        pre = f"son-kale-v2/arka_hd/{a.ad}{kis}{etk}_{x}_{y}"
        jobs.append((pre, workflow(inp, ctrl, pre, a.seed, d, cn, POS_KIS if a.kis else POS, NEG_KIS if a.kis else NEG)))
        meta.append((pre, x, y))
    out = {}
    for pre, _ in jobs:  # resume: reuse tiles already drawn
        done = sorted(glob.glob(f"{B.COMFY}/output/{pre}_*.png"))
        if done:
            out[pre] = done[-1]
    todo = [(p, w) for p, w in jobs if p not in out]
    print(f"{len(todo)} parca kuyruga ({len(out)} hazir)", flush=True)
    out.update(B.run_jobs(todo) if todo else {})
    acc = np.zeros((Hp, Wp, 3), np.float32)
    wsum = np.zeros((Hp, Wp, 1), np.float32)
    # steep weights: the tile whose centre is nearest wins, ~24 px cross-fade at seams
    # (wide averaging of two different drawings gives ghosted, muddy stones)
    w = (agirlik(t, ov) ** 6)[..., None]
    for pre, x, y in meta:
        g = np.asarray(Image.open(out[pre]).convert("RGB").resize((t, t), Image.Resampling.BOX), np.float32)
        # match the tile's colour spread to the original tile, so neighbouring tiles share one tone
        o = np.asarray(rgb.crop((x, y, x + t, y + t)), np.float32)
        if not a.kis:  # winter must move away from the summer tones
            g = (g - g.mean((0, 1))) / (g.std((0, 1)) + 1e-3) * o.std((0, 1)) + o.mean((0, 1))
        acc[y:y + t, x:x + t] += g * w
        wsum[y:y + t, x:x + t] += w
    base = np.asarray(rgb, np.float32)
    res = np.where(wsum > 0, acc / np.maximum(wsum, 1e-6), base)
    res = res[P:P + H, P:P + W]
    rgb = rgb0
    res = Image.fromarray(res.clip(0, 255).astype(np.uint8))
    res = res.filter(ImageFilter.UnsharpMask(radius=1.0, percent=a.keskin, threshold=2))
    res = koru(res, rgb, a)
    kirmizi = None
    if True:  # summer and winter (winter input = summer image + painted snow, its reds are the summer ones)
        o = np.asarray(rgb, np.float32)
        r = np.asarray(res, np.float32)
        from scipy import ndimage
        if not a.kis:
            # large-scale tone: follow the old art's local brightness/colour (dark north wall, dark forest,
            # cream blotches), keep the new small-scale detail. Off in winter: it would pull back to summer.
            yum = lambda x: np.stack([ndimage.gaussian_filter(x[..., c], 18) for c in range(3)], -1)
            r = r + (yum(o) - yum(r))
        # strong reds of the old art (banners, doors, roofs' red trims) come back pixel for pixel
        kirmizi = (o[..., 0] > 100) & (o[..., 0] > o[..., 1] * 1.6) & (o[..., 0] > o[..., 2] * 1.6)
        lab, n = ndimage.label(kirmizi)
        if n:  # only small red parts (banners, flags, doors); roofs are redrawn, not pasted back
            boy = np.bincount(lab.ravel()); boy[0] = 0
            kirmizi = (boy < 1500)[lab] & kirmizi
        r[kirmizi] = o[kirmizi]
        res = Image.fromarray(r.clip(0, 255).astype(np.uint8))
    if alfa.getextrema()[0] < 255:
        # silhouette band: where the redraw painted the grey padding inside the kept mask, use the old pixel
        from scipy import ndimage
        m = np.asarray(alfa) > 0
        band = m & ~ndimage.binary_erosion(m, iterations=8)
        r = np.asarray(res).astype(np.int16)
        gri = np.abs(r - np.array(BG)).max(axis=2) <= 22
        koyu = (r.max(axis=2) < 40) & ~(np.asarray(rgb).astype(np.int16).max(axis=2) < 60)
        yer = band & (gri | koyu)
        r = r.astype(np.uint8)
        r[yer] = np.asarray(rgb)[yer]
        res = Image.fromarray(r)
    else:
        # SD paints a dark frame along the outer edge of edge tiles: take the outer band from the
        # input (old pixels)
        K = 0 if P else 12
        yy, xx = np.mgrid[0:H, 0:W]
        kenar = np.minimum(np.minimum(yy, H - 1 - yy), np.minimum(xx, W - 1 - xx)).astype(np.float32)
        w2 = (kenar < K).astype(np.float32)  # hard cut: a soft band reads as a frame
        w2 = w2[..., None]
        res = Image.fromarray((np.asarray(res, np.float32) * (1 - w2) + np.asarray(rgb, np.float32) * w2).astype(np.uint8))
    im = kuantala(res, palet(a.ad, a.kis))
    if kirmizi is not None:
        im = tek_piksel(im, kirmizi)
        # the shared palette has no bright banner red: put those pixels back exactly
        ia = np.asarray(im).copy()
        ia[kirmizi] = np.asarray(rgb)[kirmizi]
        im = Image.fromarray(ia)
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
    ap.add_argument("--keskin", type=int, default=80, help="UnsharpMask yuzdesi (0 = kapali)")
    ap.add_argument("--koru-d", type=float, default=0.3, help="gomulu esyalar icin denoise")
    ap.add_argument("--koruma-yok", action="store_true")
    ap.add_argument("--pad", type=int, default=64, help="arka: kenarlara aynalanmis dolgu (px)")
    a = ap.parse_args()
    deneme(a) if a.mod == "deneme" else tam(a)
