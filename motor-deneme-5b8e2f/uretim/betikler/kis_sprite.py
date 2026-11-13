"""Winter / night versions for small sprites (old decorations) and ground snow for the snowy
building variants.

kar_sprite: thin cream snow like the ic2 props: a cap on every surface facing up (pixel above is
            empty or the outline), and about half of the upper part of each column covered with a
            broken edge. The old colours shimmer through a little (awning stripes stay readable).
gece_sprite: bina.gecele, brightness matched to the ic2 night versions (day/night ratio).
zemin_karla: green / olive / dirt ground tiles in the lower diamond of a building sprite -> snow.

  python kis_sprite.py sus            # 9 old decorations: <ad>_karli / <ad>_gece from the de-plinthed art
  python kis_sprite.py bina           # assets/kale/varyant/*_karli.png: ground tiles to snow
"""
import glob
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bina  # noqa: E402
import kaide as K  # noqa: E402

KALE = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"
OUT = "D:/AI/son-kale-cikti/kaide"
KREM = np.array([[236, 234, 224], [222, 222, 216], [200, 204, 210], [176, 184, 198]], np.float32)


def gurultu(H, W, tohum=5, s=1.3):
    g = ndimage.gaussian_filter(np.random.default_rng(tohum).standard_normal((H, W)), s)
    return g / (g.std() + 1e-6)


def kar_sprite(a, kapsam=0.5, bant=0.3, tohum=5):
    a = a.copy()
    H, W = a.shape[:2]
    dolu = a[..., 3] > 200
    f = a[..., :3].astype(np.float32)
    lum = f @ [0.299, 0.587, 0.114]
    kontur = dolu & (lum < 45)
    yuzey = dolu & ~kontur
    ust_bos = np.zeros_like(dolu); ust_bos[1:] = ~dolu[:-1] | kontur[:-1]; ust_bos[0] = True
    kap = yuzey & ust_bos                                   # first surface pixel under air / outline
    kap2 = np.zeros_like(kap); kap2[1:] = kap[:-1]
    g = gurultu(H, W, tohum)
    kap |= kap2 & yuzey & (g > -0.2)                        # 2nd row on most of the cap: broken edge
    # upper part of each column: about half covered, ragged
    ust_bant = np.zeros_like(dolu)
    for x in np.nonzero(dolu.any(0))[0]:
        ys = np.nonzero(dolu[:, x])[0]
        ust_bant[ys[0]:ys[0] + max(1, int(len(ys) * bant)), x] = True
    esik = np.quantile(g[ust_bant & yuzey], 1 - kapsam) if (ust_bant & yuzey).any() else 0
    alan = ust_bant & yuzey & (g > esik) & (lum > 60)
    kar = kap | alan
    # cream tones by the old brightness (lit parts lighter), stripes / shapes shimmer through
    t = np.clip((200 - lum) / 70, 0, 3)
    t = np.where(kap & ~alan, np.minimum(t, 1), t)
    idx = np.clip(np.round(t), 0, 3).astype(int)
    c = KREM[idx] * 0.85 + f * 0.15
    a[kar, :3] = np.clip(c[kar], 0, 255).astype(np.uint8)
    return a


_HEDEF = []


def ic2_gece_parlaklik():
    """Mean brightness of the ic2 night props (absolute: the old art is darker than the ic2 art)."""
    if not _HEDEF:
        v = []
        for p in glob.glob(f"{KALE}/sus/ic2/*_gece.png"):
            g = np.asarray(Image.open(p).convert("RGBA")).astype(np.float32)
            m = g[..., 3] > 200
            if m.sum() > 50:
                v.append((g[m][:, :3] @ [0.299, 0.587, 0.114]).mean())
        _HEDEF.append(float(np.median(v)))
    return _HEDEF[0]


def gece_sprite(a):
    """bina.gecele with a high light-source threshold (no glowing carrots), then lifted to the ic2
    night brightness; highlights keep their relative contrast."""
    g = np.asarray(bina.gecele(Image.fromarray(a, "RGBA"), isik_v=0.97, isik_s=0.75)).copy()
    dolu = a[..., 3] > 200
    lum = g[dolu][:, :3].astype(np.float32) @ [0.299, 0.587, 0.114]
    k = np.clip(ic2_gece_parlaklik() / max(lum.mean(), 1), 1.0, 1.8)
    g[..., :3] = np.clip(g[..., :3].astype(np.float32) * k, 0, 255).astype(np.uint8)
    return g


def agac2_govde(a):
    """The sapling's trunk stops in the air above its shadow: carry it down to the ground."""
    a = a.copy()
    dolu = a[..., 3] > 200
    ys = np.nonzero(dolu.any(1))[0]
    y_alt = ys.max()
    xs = np.nonzero(dolu[y_alt])[0]
    x0, x1 = xs.min(), xs.max()
    satir = a[y_alt, x0 - 1:x1 + 2].copy()
    for k in range(1, 8):
        y = y_alt + k
        if y >= a.shape[0] - 3:
            break
        a[y, x0 - 1:x1 + 2] = satir
    # small root flare + outline on the last row
    y = min(y_alt + 7, a.shape[0] - 4)
    a[y, x0 - 2:x1 + 3] = satir[len(satir) // 2]
    a[y, x0 - 3] = a[y, x1 + 3] = (22, 17, 20, 255)
    a[y + 1, x0 - 2:x1 + 3] = (22, 17, 20, 255)
    return a


def sus():
    for ad in K.TUM:
        if ad in K.AYAR:
            K.kaide_sil(ad).save(f"{OUT}/{ad}.png")
            a = K.NESNE[ad]
        else:
            a = K.kaynak(ad).copy()
            a[(a[..., 3] > 0) & (a[..., 3] < 250)] = 0
            if ad == "agac2":
                a = agac2_govde(a)
            K.golge_ciz(a).save(f"{OUT}/{ad}.png")
        K.golge_ciz(kar_sprite(a, bant=0.22 if ad.startswith("agac") else 0.3)).save(f"{OUT}/{ad}_karli.png")
        K.golge_ciz(gece_sprite(a), 70).save(f"{OUT}/{ad}_gece.png")
        print(ad)


def zemin_karla(a):
    """Ground tiles in the lower diamond of a building sprite -> snow (grass, olive, dirt, fields)."""
    a = a.copy()
    H, W = a.shape[:2]
    dolu = a[..., 3] > 200
    f = a[..., :3].astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    lum = f @ [0.299, 0.587, 0.114]
    mx, mn = f.max(-1), f.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    # lower diamond: from the leftmost / rightmost opaque columns, 2:1
    xs = np.nonzero(dolu.any(0))[0]
    xl, xr = xs.min(), xs.max()
    yl = np.nonzero(dolu[:, xl])[0].min(); yr = np.nonzero(dolu[:, xr])[0].min()
    cx = (xl + xr) / 2
    yy, xx = np.mgrid[0:H, 0:W]
    ust_kenar = np.where(xx <= cx, yl - (xx - xl) / 2, yr - (xr - xx) / 2)
    elmas = dolu & (yy >= ust_kenar - 2)
    yesil = (g > r * 1.04) & (g > b * 1.25) & (sat > 0.25)
    zeytin = (sat < 0.55) & (sat > 0.15) & (np.abs(r - g) < 22) & (b < g * 0.85)
    toprak = (r > g * 1.1) & (g > b * 1.05) & (sat > 0.25) & (lum > 50) & (lum < 170)
    mo = ndimage.uniform_filter(lum, 5)
    sd = np.sqrt(np.maximum(ndimage.uniform_filter(lum ** 2, 5) - mo ** 2, 0))
    # only grass-like ground: green or olive green, fairly smooth (walls, plaster, wood are not)
    zeytin = (g >= r * 1.0) & (b < g * 0.78) & (sat > 0.27)
    zemin = elmas & (yesil | zeytin) & (sd < 18) & (lum > 40)
    zemin = ndimage.binary_opening(zemin, np.ones((2, 2)))
    lab, n = ndimage.label(zemin)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        zemin &= (boy >= 25)[lab]
    t = np.clip((185 - lum) / 45, 0, 3) + 0.4 * gurultu(H, W, 7, 1.2)
    idx = np.clip(np.round(t), 0, 3).astype(int)
    a[zemin, :3] = np.clip(KREM[idx] * 0.9 + f * 0.1, 0, 255)[zemin].astype(np.uint8)
    return a, zemin


def bina_varyant():
    orj = "D:/AI/araclar/orijinal/varyant"
    os.makedirs(orj, exist_ok=True)
    for p in sorted(glob.glob(f"{KALE}/varyant/*_karli.png")):
        ad = os.path.basename(p)
        y = f"{orj}/{ad}"
        if not os.path.exists(y):
            Image.open(p).save(y)
        a = np.asarray(Image.open(y).convert("RGBA"))
        k, z = zemin_karla(a)
        Image.fromarray(k, "RGBA").save(p)
        print(ad, int(z.sum()))


if __name__ == "__main__":
    if sys.argv[1] == "sus":
        sus()
    else:
        bina_varyant()
