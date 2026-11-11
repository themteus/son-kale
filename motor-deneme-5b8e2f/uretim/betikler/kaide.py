"""Remove the ground tile / plinth under the old inner-castle decorations (assets/kale/sus/*.png).

The new ic2 props stand straight on the ground; the old PixelLab ones sit on a small isometric
slab (grass top + dark sides). Per item:
  cimen  (odun, fici, kumes, agac1): the green slab goes (green hue below the object's crown line),
         plus the dark slab sides / outline touching it.
  koyu   (tezgah): the dark grey-green base goes.
  kenar  (bostan, camasir): the bed / deck is part of the object, only the raised slab sides go,
         so it lies flat on the ground.
Then: the object is moved down by the slab thickness (feet on the real ground), a 1 px dark outline
closes the cut, the old shadow is replaced by the ic2-style banded shadow. Canvas size and the
bottom-centre point stay the same, so kale.json placements do not move.

  python kaide.py [ad ...]     -> D:/AI/son-kale-cikti/kaide/<ad>.png + karsilastirma
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SUS = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale/sus"
ORJ = "D:/AI/araclar/orijinal/sus"
OUT = "D:/AI/son-kale-cikti/kaide"
KONTUR = np.array([22, 17, 20], np.uint8)

# kind, row from which the slab may be removed (above it: crown / object only), slab thickness
AYAR = {
    "odun": ("cimen", 0, 4),
    "fici": ("cimen", 0, 4),
    "kumes": ("cimen", 0, 4),
    "agac1": ("cimen", 68, 4),
    "tezgah": ("koyu", 0, 3),
    "bostan": ("kenar", 0, 5),
    "camasir": ("kenar", 0, 7),
}


def kaynak(ad):
    os.makedirs(ORJ, exist_ok=True)
    p = f"{ORJ}/{ad}.png"
    if not os.path.exists(p):
        Image.open(f"{SUS}/{ad}.png").save(p)
    return np.asarray(Image.open(p).convert("RGBA"))


def kaide_sil(ad):
    kind, ust_sinir, kal = AYAR[ad]
    a = kaynak(ad).copy()
    H, W = a.shape[:2]
    golge = (a[..., 3] > 0) & (a[..., 3] < 250)
    a[golge] = 0                                   # old shadow: replaced at the end
    dolu = a[..., 3] > 0
    f = a[..., :3].astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    lum = f @ [0.299, 0.587, 0.114]
    mx, mn = f.max(-1), f.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    alt = np.zeros((H, W), bool); alt[ust_sinir:] = True

    if kind in ("cimen", "koyu"):
        if kind == "cimen":
            ust = dolu & alt & (g > r * 1.0) & (g > b * 1.15)
        else:
            alt3 = np.zeros((H, W), bool); alt3[int(H * 0.6):] = True
            ust = dolu & alt3 & (lum < 72) & (sat < 0.38) & ~((r > g * 1.18) & (lum > 40))
        lab, n = ndimage.label(ust)
        if n:
            boy = np.bincount(lab.ravel()); boy[0] = 0
            ust &= (boy >= 25)[lab]
        # slab region: convex hull of its top face, pushed down by the side thickness (+1 outline)
        from scipy.spatial import ConvexHull
        yy, xx = np.nonzero(ust)
        pts = np.stack([xx, yy], 1)
        hull = pts[ConvexHull(pts).vertices]
        m = Image.new("L", (W, H), 0)
        for d in range(0, kal + 5):
            ImageDraw.Draw(m).polygon([(x, y + d) for x, y in hull], fill=255)
        S = ndimage.binary_dilation(np.asarray(m) > 0, iterations=2) & alt   # + the slab's outer outline
        # side colours: what is in S below the top face around the front corner (no object there)
        alt_bant = S & ~ndimage.binary_dilation(ust, iterations=0) & ~ust
        on_kose = np.zeros((H, W), bool)
        cx = int(np.median(xx)); yb = yy.max()
        on_kose[yb - 2:yb + kal + 3, max(0, cx - 30):cx + 30] = True
        yan_renk = {tuple(c) for c in a[alt_bant & on_kose & dolu][:, :3]}
        # a little wider: also colours within 6 of a sampled side colour
        renk = a[..., :3].astype(int)
        yan = np.zeros((H, W), bool)
        for c in yan_renk:
            yan |= np.abs(renk - np.array(c)).max(-1) <= 6
        # the slab's own bottom outline: dark pixels in the lowest band of S
        en_alt = S & ~np.roll(S, -3, axis=0)
        karo_alt = en_alt & dolu & (lum < 80)
        karo = karo_alt | S & dolu & (ust | yan | ((g > r * 1.0) & (g > b * 1.1)) | ((sat < 0.5) & (sat > 0.18) & (g >= r * 0.95) & (b < g * 0.8) & (lum > 120)))
        # side faces: per column, the band right under the lowest top-face pixel
        # light wood (stump), orange legs, white chickens are objects standing in front of the slab
        koru = (((lum >= 80) & (r > g * 1.15)) | (lum > 170)) if ad in ON_NESNE else np.zeros((H, W), bool)
        ustd = ndimage.binary_dilation(ust, iterations=1)
        for x in np.nonzero(ustd.any(0))[0]:
            y0 = np.nonzero(ustd[:, x])[0].max()
            karo[y0 + 1:y0 + kal + 3, x] |= dolu[y0 + 1:y0 + kal + 3, x] & ~koru[y0 + 1:y0 + kal + 3, x]
        a[karo] = 0
        KESIK[ad] = S
    else:
        # flat bed/deck: remove what hangs below the top face = the side band. The top face's lower
        # edges run from the left corner to the front corner to the right corner (2:1).
        xs = np.nonzero(dolu.any(0))[0]
        xl, xr = xs.min(), xs.max()
        yl = np.nonzero(dolu[:, xl])[0].min()          # top of the left corner
        yr = np.nonzero(dolu[:, xr])[0].min()
        xx = np.arange(W)
        cx = (xl + xr) / 2
        # lower edge of the top face (left half goes down to the front, right half goes up)
        kenar_y = np.where(xx <= cx, yl + (xx - xl) / 2, yr + (xr - xx) / 2) + 0.5
        yy = np.arange(H)[:, None]
        yan = dolu & (yy > kenar_y[None, :] + 1)
        a[yan] = 0
        KENAR[ad] = (xl, yl, xr, yr, cx)
    # drop crumbs left behind: <10 px anywhere, <30 px inside the cut slab region (not chickens: white)
    dolu = a[..., 3] > 0
    lab, n = ndimage.label(dolu)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        kirinti = (boy < 10)[lab] & dolu
        if ad in KESIK:
            beyaz = np.zeros(n + 1, bool)
            np.maximum.at(beyaz, lab.ravel(), (lum.ravel() > 170))
            kirinti |= ((boy < 30) & ~beyaz)[lab] & dolu & KESIK[ad]
        a[kirinti] = 0
    # move down by the slab thickness: the feet stood on the slab top
    a = np.roll(a, kal, axis=0)
    a[:kal] = 0
    # 1 px dark outline under the new bottom silhouette
    dolu = a[..., 3] > 0
    alt_k = np.zeros_like(dolu); alt_k[1:] = dolu[:-1]
    alt_k &= ~dolu
    yan_k = np.zeros_like(dolu); yan_k[:, 1:] |= dolu[:, :-1]; yan_k[:, :-1] |= dolu[:, 1:]
    yan_k &= ~dolu
    if ad in KESIK:
        kesik = np.roll(KESIK[ad], kal, axis=0)
    else:
        kesik = np.zeros_like(dolu); kesik[int(H * 0.5):] = True
    kon = (alt_k | yan_k) & kesik
    # do not thicken an outline that is still there
    kon &= ~ndimage.binary_dilation((a[..., :3].astype(int).sum(-1) < 120) & dolu, iterations=1)
    a[kon, :3] = KONTUR
    a[kon, 3] = 255
    NESNE[ad] = a.copy()
    return golge_ciz(a)


KENAR = {}
NESNE = {}   # object without shadow (for the winter / night versions)
KESIK = {}
ON_NESNE = {"odun", "kumes"}   # something stands in front of the slab (stump, chickens)


def golge_ciz(a, guc=78):
    """ic2-style banded elliptical shadow (light top left), inside the same canvas."""
    H, W = a.shape[:2]
    dolu = a[..., 3] > 0
    cols = np.nonzero(dolu.any(0))[0]
    rows = np.nonzero(dolu.any(1))[0]
    base_w = cols.max() - cols.min() + 1
    ew, eh = base_w * 0.55, max(3, base_w * 0.16)
    cx = (cols.min() + cols.max()) / 2 + base_w * 0.08
    cy = min(rows.max() - eh * 0.2, H - 1 - eh * 0.6)
    yy, xx = np.mgrid[0:H, 0:W]
    d = ((xx - cx) / ew) ** 2 + ((yy - cy) / eh) ** 2
    alpha = np.clip(1.0 - d, 0, 1) ** 0.8 * guc
    alpha = (np.round(alpha / 26) * 26).clip(0, guc)
    sh = np.zeros((H, W, 4), np.uint8)
    sh[..., :3] = (36, 28, 22)
    sh[..., 3] = alpha.astype(np.uint8)
    canvas = Image.fromarray(sh, "RGBA")
    canvas.alpha_composite(Image.fromarray(a, "RGBA"))
    return canvas


def karsilastir(adlar, yol):
    tiles = []
    for ad in adlar:
        eski = Image.fromarray(kaynak(ad), "RGBA")
        yeni = Image.open(f"{OUT}/{ad}.png")
        w, h = eski.size
        t = Image.new("RGBA", (2 * w + 12, h + 4), (96, 120, 64, 255))
        t.alpha_composite(eski, (0, 2)); t.alpha_composite(yeni, (w + 12, 2))
        tiles.append(t)
    W = max(t.width for t in tiles); H = sum(t.height + 6 for t in tiles)
    S = Image.new("RGBA", (W, H), (40, 40, 40, 255)); y = 0
    for t in tiles:
        S.alpha_composite(t, (0, y)); y += t.height + 6
    S.resize((S.width * 3, S.height * 3), Image.Resampling.NEAREST).save(yol)


TUM = ["agac1", "agac2", "bostan", "camasir", "fici", "kumes", "odun", "samanaraba", "tezgah"]


def varyantlar(ad):
    """_karli / _gece like the ic2 props (uyum.py): snow on top surfaces / night grade, then shadow."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bina
    if ad in AYAR:
        a = NESNE[ad]
    else:
        a = kaynak(ad).copy()
        a[(a[..., 3] > 0) & (a[..., 3] < 250)] = 0
    im = Image.fromarray(a, "RGBA")
    k = np.asarray(bina.karla_ust(im, 0.42 if ad.startswith("agac") else 0.35))
    golge_ciz(k).save(f"{OUT}/{ad}_karli.png")
    golge_ciz(np.asarray(bina.gecele(im, isik_v=0.9, isik_s=0.65)), 70).save(f"{OUT}/{ad}_gece.png")
    if ad not in AYAR:
        golge_ciz(a).save(f"{OUT}/{ad}.png")


if __name__ == "__main__":
    adlar = sys.argv[1:] or TUM
    os.makedirs(OUT, exist_ok=True)
    for ad in adlar:
        if ad in AYAR:
            kaide_sil(ad).save(f"{OUT}/{ad}.png")
        varyantlar(ad)
    karsilastir(adlar, f"{OUT}/_karsilastirma.png")
    print("ok")
