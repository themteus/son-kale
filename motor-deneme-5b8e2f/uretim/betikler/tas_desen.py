"""Code-stamped regular stone pattern for the castle walls and towers (1x HD background).

Each wall face is a 2:1 isometric plane: rows follow the wall's slope in 2 px steps, stones are
BW px long and BH px high, every other row shifted half a stone. Every stone: 1 px light top-left
edge, 1 px dark joint bottom-right, a small random tone step. Colours are the building stone ramp
(duvarci / demirci / kisla); brightness comes from the old art (light from the top left), so the
face keeps its shading. Towers are cylinders: rows bend with the ellipse, stones get narrower and
darker towards the edges. Dark details (outline, windows, doors), wood, vines and red cloth are not
touched; only stone-coloured pixels inside a face polygon get the pattern.

Faces are polygons in ORIGINAL coords (on.png 1240x482 / arka.png 1280x720) -> scaled 1.5x.

  python tas_desen.py deneme      # left front wall + its tower, before/after
  python tas_desen.py on|arka     # whole image
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

KALE = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"
ORJ = "D:/AI/araclar/orijinal/kale"
HD = "D:/AI/ComfyUI/output/son-kale-v2/arka_hd"
CIKTI = "D:/AI/son-kale-cikti"
S = 1.5
BW, BH = 7, 4   # stone length / height in screen px

# boxes (original coords) the pattern must not touch: small red-roofed tower and door in front of the keep
HARIC = {"on": [], "arka": [(1000, 380, 1056, 450)]}

# face: (kind, polygon in original coords, params)
#   "duz": flat wall face, params = slope (+0.5 wall goes down to the right, -0.5 up to the right)
#   "kule": cylinder, params = (cx, r) in original coords
YUZLER = {
    "on": [
        ("duz", [(46, 78), (346, 214), (346, 292), (46, 150)], 0.5),          # incl. merlons          # left front wall
        ("kule", [(344, 231), (397, 231), (397, 312), (344, 312)], (370.5, 26)),
        ("kule", [(4, 60), (51, 60), (51, 150), (4, 150)], (27.5, 22.5)),            # left end tower
        ("duz", [(397, 245), (672, 372), (672, 456), (397, 320)], 0.5),             # wall to the corner
        ("kule", [(668, 382), (739, 382), (739, 482), (668, 482)], (703.5, 33.5)),  # corner tower
        ("duz", [(737, 366), (922, 288), (922, 372), (737, 464)], -0.42),           # right front wall
        ("duz", [(965, 214), (1039, 178), (1039, 328), (965, 362)], -0.5),          # gate block
        ("kule", [(918, 242), (969, 242), (969, 358), (918, 358)], (943.75, 23.75)),  # left gate tower
        ("kule", [(985, 210), (1037, 210), (1037, 264), (985, 264)], (1011, 26)),     # right gate tower
        ("duz", [(1037, 222), (1172, 152), (1172, 242), (1037, 334)], -0.5),        # wall to the end tower
        ("kule", [(1171, 125), (1233, 125), (1233, 232), (1171, 232)], (1202, 30)),   # end tower
    ],
    "arka": [
        ("duz", [(85, 246), (262, 170), (262, 244), (85, 336)], -0.45),             # NW wall, left part
        ("kule", [(258, 150), (302, 150), (302, 247), (258, 247)], (280, 20)),       # NW mid tower
        ("duz", [(298, 150), (530, 50), (530, 132), (298, 238)], -0.45),            # NW wall, right part
        ("kule", [(518, 0), (577, 0), (577, 120), (518, 120)], (547, 27)),          # top tower
        ("duz", [(573, 56), (800, 168), (800, 224), (573, 142)], 0.45),             # NE wall
        ("kule", [(795, 145), (852, 145), (852, 262), (795, 262)], (823.5, 26.5)),  # NE corner tower
        ("duz", [(850, 193), (962, 248), (962, 302), (850, 247)], 0.5),             # wall to the keep
        ("kule", [(948, 285), (1002, 285), (1002, 432), (948, 432)], (975, 25)),     # keep: round tower
        ("duz", [(1000, 296), (1100, 343), (1100, 442), (1000, 442)], 0.5),         # keep: long face
        ("duz", [(1100, 300), (1145, 280), (1145, 412), (1100, 434)], -0.5),        # keep: side face
        ("kule", [(1144, 280), (1191, 280), (1191, 412), (1144, 412)], (1167, 22)),  # keep: right tower
    ],
}


def tas_rampasi(n=9, ad="on"):
    """Stone colours, light to dark: median colour per brightness bin. Source: the old wall art itself
    (its warm beige) plus the stonemason / smith buildings."""
    px = []
    o = np.asarray(Image.open(f"{ORJ}/{ad}.png").convert("RGBA"))
    a = o.reshape(-1, 4)[tas_maskesi(o).reshape(-1)][:, :3].astype(np.float32)
    px.append(a)
    for f in ("duvarci1", "duvarci2", "demirci1", "demirci2"):
        p = f"{KALE}/{f}.png"
        if os.path.exists(p):
            a = np.asarray(Image.open(p).convert("RGBA")).reshape(-1, 4)
            a = a[a[:, 3] > 200][:, :3].astype(np.float32)
            mx, mn = a.max(1), a.min(1)
            sat = (mx - mn) / np.maximum(mx, 1)
            lum = a @ [0.299, 0.587, 0.114]
            px.append(a[(sat < 0.32) & (lum > 45) & (lum < 215)])
    px = np.concatenate(px)
    lum = px @ [0.299, 0.587, 0.114]
    kes = np.quantile(lum, np.linspace(0, 1, n + 1))
    ramp = [np.median(px[(lum >= kes[i]) & (lum <= kes[i + 1])], 0) for i in range(n)]
    return np.array(ramp[::-1])          # index 0 = lightest


def tas_maskesi(o):
    """Stone-coloured pixels of the old art (not outline, not wood, not vines, not red cloth)."""
    a = o[..., :3].astype(np.float32)
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    lum = a @ [0.299, 0.587, 0.114]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    yesil = (g > r * 0.98) & (g > b * 1.1)
    kirmizi = (r > g * 1.5) & (r > b * 1.5)
    # dark pixels: keep solid blobs (windows, gate, arrow slits, outline runs 3+ px thick), but thin
    # dark lines are the old mortar and get the new pattern
    koyu = lum <= 52
    blob = ndimage.binary_dilation(ndimage.binary_opening(koyu, np.ones((4, 4))), iterations=1) & koyu
    m = ((lum > 52) | (koyu & ~blob & (lum > 18))) & (sat < 0.55) & ~yesil & ~kirmizi
    if o.shape[-1] == 4:
        m &= o[..., 3] > 0
    return m


def desen(H, W, poli, kind, par, isik, ramp, tohum=1):
    """Pattern (colour per pixel) + mask for one face, in HD coords."""
    rng = np.random.default_rng(tohum)
    yy, xx = np.mgrid[0:H, 0:W]
    if kind == "duz":
        # rows parallel to the wall: v = y - slope * x, in 2:1 pixel steps
        v = yy - np.floor(xx * par).astype(int) if par > 0 else yy + np.floor(xx * -par).astype(int)
        u = xx.astype(np.float64)
        isik_kenar = 0.0
    else:
        cx, r = par[0] * S, par[1] * S
        dx = np.clip((xx + 0.5 - cx) / r, -0.999, 0.999)
        v = (yy - np.round(0.5 * r * np.sqrt(1 - dx ** 2))).astype(int)   # rows bend with the ellipse
        u = np.arcsin(dx) * r                                              # arc length along the row
        isik_kenar = np.abs(dx)
    sira = np.floor_divide(v, BH)
    vi = v - sira * BH
    kay = (sira % 2) * (BW // 2)
    tas = np.floor((u + kay) / BW).astype(int)
    ui = (u + kay) - tas * BW
    # per-stone tone step (-1, 0, +1) from a hash of (row, stone)
    h = (sira * 73856093) ^ (tas * 19349663) ^ tohum
    adim = (np.abs(h) % 7)
    adim = np.where(adim < 2, -1, np.where(adim > 4, 1, 0))
    # base index from the old art's brightness (and darker towards a tower's edges)
    taban = isik + isik_kenar ** 3 * 2.2
    idx = np.round(taban).astype(int) + adim
    derz = (vi == BH - 1) | (ui >= BW - 1)
    kenar = ((vi == 0) | (ui < 1)) & ~derz
    idx = np.where(kenar, idx - 2, idx)
    idx = np.where(derz, idx + 4, idx)
    if kind == "kule":
        idx = np.where(np.abs(dx) > 0.96, len(ramp) + 2, idx)   # tower silhouette against the wall
    idx = np.clip(idx, 0, len(ramp) - 1)
    renk = ramp[idx]
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in poli], fill=255)
    return renk, np.asarray(m) > 0


def uygula(ad, hd_img, yuzler=None):
    o = np.asarray(Image.open(f"{ORJ}/{ad}.png").convert("RGBA"))
    o = np.asarray(Image.fromarray(o).resize(hd_img.size, Image.Resampling.NEAREST))
    H, W = o.shape[:2]
    ramp = tas_rampasi(ad=ad)
    rl = ramp @ [0.299, 0.587, 0.114]
    # brightness of the old art -> ramp index (blurred: face shading, not the old stones)
    lum = ndimage.gaussian_filter(o[..., :3].astype(np.float32) @ [0.299, 0.587, 0.114], 3.0)
    isik = np.interp(-lum, -rl, np.arange(len(ramp)))
    tas_m = tas_maskesi(o)
    for x0, y0, x1, y1 in HARIC.get(ad, []):
        tas_m[int(y0 * S):int(y1 * S), int(x0 * S):int(x1 * S)] = False
    out = np.asarray(hd_img.convert("RGBA")).copy()
    for i, (kind, poli, par) in enumerate(yuzler if yuzler is not None else YUZLER[ad]):
        renk, m = desen(H, W, poli, kind, par, isik, ramp, tohum=i + 1)
        m &= tas_m
        # same average brightness as the old stones of this face
        if m.any():
            eski = o[m, :3].astype(np.float32).mean(0)
            renk = np.clip(renk + (eski - renk[m].mean(0)) * 0.9, 0, 255)
        out[m, :3] = renk[m].astype(np.uint8)
        # 1 px dark outline where the patterned stone meets sky / ground / transparency (merlons, edges)
        acik = ~tas_m if o.shape[-1] != 4 else (~tas_m | (o[..., 3] == 0))
        ust = np.zeros_like(m); ust[1:] = acik[:-1] & (o[:-1, :, 3] == 0 if o.shape[-1] == 4 else ~tas_m[:-1])
        sol = np.zeros_like(m); sol[:, 1:] = (o[:, :-1, 3] == 0) if o.shape[-1] == 4 else ~tas_m[:, :-1]
        sag = np.zeros_like(m); sag[:, :-1] = (o[:, 1:, 3] == 0) if o.shape[-1] == 4 else ~tas_m[:, 1:]
        kontur = m & (ust | sol | sag)
        out[kontur, :3] = np.clip(ramp[-1] * 0.55, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def palete_indir(ad, im):
    """Shared 48-colour palette (old art + buildings), no dithering; small bright reds stay exact."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import arka_hd as A
    a = np.asarray(im.convert("RGBA"))
    q = np.asarray(A.kuantala(Image.fromarray(a[..., :3]), A.palet(ad))).copy()
    f = a[..., :3].astype(np.float32)
    kir = (f[..., 0] > 100) & (f[..., 0] > f[..., 1] * 1.6) & (f[..., 0] > f[..., 2] * 1.6)
    lab, n = ndimage.label(kir)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        kir &= (boy < 1500)[lab]
    q[kir] = a[kir, :3]
    if ad == "arka" and ALEV:
        q[ALEV[0]] = a[ALEV[0], :3]
    out = np.dstack([q, a[..., 3]])
    return Image.fromarray(out.astype(np.uint8), "RGBA" if ad == "on" else None).convert("RGBA" if ad == "on" else "RGB")


ALEV = []


def arka_son(im):
    """Background only: vines and red cloth of the keep come back from the old art; the light halo
    around the front walls' silhouette (the redraw drew those towers a bit wider) becomes old art."""
    a = np.asarray(im).copy()
    H, W = a.shape[:2]
    o = np.asarray(Image.open(f"{ORJ}/arka.png").convert("RGB").resize((W, H), Image.Resampling.NEAREST))
    of = o.astype(np.float32)
    r, g, b = of[..., 0], of[..., 1], of[..., 2]
    kale = np.zeros((H, W), bool)
    kale[int(270 * S):int(445 * S), int(945 * S):int(1195 * S)] = True
    yesil = (g > r * 1.05) & (g > b * 1.2)
    kirmizi = (r > 100) & (r > g * 1.6) & (r > b * 1.6)
    geri = kale & (yesil | kirmizi)
    a[geri] = o[geri]
    # torch / lamp flames: small bright yellow spots of the old art
    alev = (r > 170) & (g > 140) & (b < 120) & (r - b > 90)
    lab, n = ndimage.label(ndimage.binary_dilation(alev, iterations=1))
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        alev &= (boy < 120)[lab]
    a[alev] = o[alev]
    # the courtyard torch by the NE wall: the redraw turned it into a glowing doorway; old pole + flame back
    x0, y0, x1, y1 = [int(v * S) for v in (671, 146, 684, 190)]
    kut = np.zeros((H, W), bool); kut[y0:y1, x0:x1] = True
    lum = of @ [0.299, 0.587, 0.114]
    mesale = kut & ((lum < 75) | ((g > 150) & (lum > 140)) | ((r > 150) & (g > 120) & (b < 120)))
    a[mesale] = o[mesale]
    alev |= mesale
    ALEV[:] = [alev]
    # front walls (on.png) as placed over the background: 1.5x at screen (30, 327)
    on = Image.open(f"{ORJ}/on.png").getchannel("A")
    on = on.resize((round(on.width * S), round(on.height * S)), Image.Resampling.NEAREST)
    m = Image.new("L", (W, H), 0)
    m.paste(on, (30, 327))
    m = np.asarray(m) > 0
    hale = ndimage.binary_dilation(m, iterations=6) & ~m
    a[hale] = o[hale]
    return Image.fromarray(a)


if __name__ == "__main__":
    mod = sys.argv[1]
    if mod in ("on", "arka"):
        hd = Image.open(f"{HD}/{mod}.png")
        yeni = uygula(mod, hd)
        if mod == "arka":
            yeni = arka_son(yeni.convert("RGB"))
        yeni = palete_indir(mod, yeni)
        yeni.save(f"{HD}/{mod}_desen.png")
        print(f"{HD}/{mod}_desen.png")
    if mod == "deneme":
        hd = Image.open(f"{HD}/on.png")
        yeni = uygula("on", hd)
        x0, y0, x1, y1 = 40, 100, 640, 500
        def zemin(im):
            b = Image.new("RGBA", im.size, (90, 120, 70, 255)); b.alpha_composite(im.convert("RGBA")); return b.convert("RGB")
        o = Image.open(f"{ORJ}/on.png").convert("RGBA").resize(hd.size, Image.Resampling.NEAREST)
        parts = [zemin(i).crop((x0, y0, x1, y1)) for i in (o, hd, yeni)]
        w = x1 - x0
        sh = Image.new("RGB", (3 * w + 20, y1 - y0))
        for k, p in enumerate(parts):
            sh.paste(p, (k * (w + 10), 0))
        sh.resize((sh.width * 2, sh.height * 2), Image.Resampling.NEAREST).save(f"{CIKTI}/desen_deneme.png")
        yeni.save(f"{CIKTI}/desen_on.png")
        print("ok")
