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


def kar_sprite(a, kapsam=0.5, bant=0.3, tohum=5, sadece_ust=False, kume=1.3, karisim=0.15, yumusak=0.0, kap_kalin=2):
    a = a.copy()
    H, W = a.shape[:2]
    dolu = a[..., 3] > 200
    f = a[..., :3].astype(np.float32)
    lum = f @ [0.299, 0.587, 0.114]
    kontur = dolu & (lum < 45)
    yuzey = dolu & ~kontur
    ust_bos = np.zeros_like(dolu); ust_bos[1:] = ~dolu[:-1] | kontur[:-1]; ust_bos[0] = True
    if sadece_ust:                                          # only the outer top silhouette (awnings)
        ust_bos = np.zeros_like(dolu); ust_bos[1:] = ~dolu[:-1]; ust_bos[0] = True
        ust_bos |= np.roll(ust_bos, 1, axis=0) & kontur      # just under the outer outline
    kap = yuzey & ust_bos                                   # first surface pixel under air / outline
    g = gurultu(H, W, tohum, kume)
    kap0 = kap.copy()
    for d in range(1, kap_kalin):                           # cap depth (2 = old behaviour)
        kd = np.zeros_like(kap); kd[d:] = kap0[:-d]
        kap |= kd & yuzey & ((g > -0.2) if d == 1 else (g > -0.6 + 0.3 * d))
    # upper part of each column: about half covered, ragged
    ust_bant = np.zeros_like(dolu)
    for x in np.nonzero(dolu.any(0))[0]:
        ys = np.nonzero(dolu[:, x])[0]
        ust_bant[ys[0]:ys[0] + max(1, int(len(ys) * bant)), x] = True
    if bant <= 0:
        ust_bant[:] = False
    esik = np.quantile(g[ust_bant & yuzey], 1 - kapsam) if (ust_bant & yuzey).any() else 0
    alan = ust_bant & yuzey & (g > esik) & (lum > 60)
    kar = kap | alan
    # cream tones by the old brightness (lit parts lighter), stripes / shapes shimmer through
    lum_t = ndimage.gaussian_filter(lum, yumusak) if yumusak > 0 else lum   # smoothed: big shade areas
    t = np.clip((200 - lum_t) / 70, 0, 3)
    t = np.where(kap & ~alan, np.minimum(t, 1), t)
    idx = np.clip(np.round(t), 0, 3).astype(int)
    c = KREM[idx] * (1 - karisim) + f * karisim
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
    son = a.shape[0] - 4                                    # the placement point is the image bottom
    for y in range(y_alt + 1, son):
        a[y, x0 - 1:x1 + 2] = satir
    # 1 px thicker trunk all the way down (dark bark on the right side)
    govde = dolu.copy(); govde[:y_alt - 10] = False
    for y in range(y_alt - 10, son):
        xs_ = np.nonzero(a[y, :, 3] > 200)[0]
        if len(xs_) and xs_.max() - xs_.min() < 10:
            a[y, xs_.max() + 1] = (40, 28, 24, 255)
    # small root flare + outline on the last row
    y = son
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
        if ad == "tezgah":
            kar = kar_sprite(a, bant=0, sadece_ust=True)          # awning stripes stay visible
        else:
            if ad == "agac1":                                       # big oak: a bit more on the crown
                kar = kar_sprite(a, kapsam=0.45, bant=0.26, kume=2.2)
            else:
                kar = kar_sprite(a, kapsam=0.3, bant=0.16 if ad.startswith("agac") else 0.2)   # sparse, like ic2
        K.golge_ciz(kar).save(f"{OUT}/{ad}_karli.png")
        K.golge_ciz(gece_sprite(a), 70).save(f"{OUT}/{ad}_gece.png")
        print(ad)


def zemin_karla(a, toprak_da=False, plaka=False):
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
    if toprak_da:
        # mine / quarry: the dirt yard too, but only in the front band of the diamond (not the walls)
        alt_y = np.array([np.nonzero(dolu[:, x])[0].max() if dolu[:, x].any() else 0 for x in range(W)])
        bant = (yy >= alt_y[None, :] - 0.42 * (alt_y.max() - ust_kenar.min())) & (yy <= alt_y[None, :])
        topr = (r > g * 1.08) & (g > b * 1.02) & (sat > 0.22) & (lum > 55) & (lum < 175) & (sd < 32)
        zemin |= elmas & bant & topr
    zemin = ndimage.binary_opening(zemin, np.ones((2, 2)))
    lab, n = ndimage.label(zemin)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        zemin &= (boy >= 25)[lab]
    t = np.clip((185 - lum) / 45, 0, 3) + 0.4 * gurultu(H, W, 7, 1.2)
    idx = np.clip(np.round(t), 0, 3).astype(int)
    a[zemin, :3] = np.clip(KREM[idx] * 0.9 + f * 0.1, 0, 255)[zemin].astype(np.uint8)
    if plaka:
        # the ground plate's front faces (lowest ~6 px of every column under a snowed top): shaded snow,
        # so the plate melts into the snowy ground instead of standing like a block
        alt_y = np.array([np.nonzero(dolu[:, x])[0].max() if dolu[:, x].any() else -1 for x in range(W)])
        yan = np.zeros((H, W), bool)
        for x in range(W):
            if alt_y[x] < 0:
                continue
            y0 = max(0, alt_y[x] - 6)
            if zemin[max(0, y0 - 6):y0 + 1, x].any():
                yan[y0:alt_y[x] + 1, x] = True
        yan &= dolu & ~zemin
        a[yan, :3] = np.where((np.arange(H)[:, None] >= alt_y[None, :])[yan][:, None],
                              np.array([150, 160, 182]), KREM[3]).astype(np.uint8)
        zemin |= yan
    # leftover summer green (moss in a window, tufts): cooled grey-blue
    yes = (a[..., 3] > 200) & (g > r * 1.05) & (g > b * 1.2) & ~zemin
    gri = f[yes] @ [0.299, 0.587, 0.114]
    a[yes, :3] = np.clip(np.stack([gri * 0.95, gri * 0.99, gri * 1.08], -1), 0, 255).astype(np.uint8)
    return a, zemin


def bina_varyant():
    orj = "D:/AI/araclar/orijinal/varyant"
    os.makedirs(orj, exist_ok=True)
    for p in sorted(q for q in glob.glob(f"{KALE}/varyant/*_karli.png") if "_yikik_" not in q):
        ad = os.path.basename(p)
        y = f"{orj}/{ad}"
        if not os.path.exists(y):
            Image.open(p).save(y)
        a = np.asarray(Image.open(y).convert("RGBA"))
        yazdan = ad in ("maden3_karli.png", "tasocagi3_karli.png")
        if yazdan:   # the old SDXL winter version changed the shape: snow the summer sprite itself
            a = kar_sprite(np.asarray(Image.open(f"{KALE}/{ad.replace('_karli', '')}").convert("RGBA")),
                           kapsam=0.6, bant=0.35, tohum=17, kume=3.0)
        # variants where the old snow pass did not take (maden1, tasocagi1/2...): thin snow on top
        m = a[..., 3] > 200
        f = a[m][:, :3].astype(int)
        beyaz = ((f.min(1) > 195) & (f.max(1) - f.min(1) < 30)).mean()
        if beyaz < 0.03 and not yazdan:
            a = kar_sprite(a, kapsam=0.5, bant=0.3, tohum=13, kume=2.5)
        k, z = zemin_karla(a, toprak_da=ad.startswith(("maden", "tasocagi")), plaka=ad.startswith(("maden", "tasocagi")))
        Image.fromarray(k, "RGBA").save(p)
        if beyaz < 0.03:
            print("  +kar", ad, round(beyaz, 3))
        print(ad, int(z.sum()))


def yikik_karli():
    """Snowy versions of the ruined building variants (winter + wall damage): thin cream snow on top
    surfaces + snow on the ground tiles. Registered in varyantlar.json as 'yikik_karli'."""
    import json
    V = f"{KALE}/varyant"
    J = json.load(open(f"{V}/varyantlar.json", encoding="utf-8"))
    for p in sorted(glob.glob(f"{V}/*_yikik.png")):
        ad = os.path.basename(p)[:-len("_yikik.png")]
        a = np.asarray(Image.open(p).convert("RGBA"))
        k = kar_sprite(a, kapsam=0.6, bant=0.3, tohum=11, sadece_ust=True, kume=3.0)
        k, _ = zemin_karla(k, toprak_da=ad.startswith(("maden", "tasocagi")), plaka=ad.startswith(("maden", "tasocagi")))
        # outer outline: cold dark instead of near-black, so it does not read as a halo on the snow
        m = k[..., 3] > 0
        e = m & ~ndimage.binary_erosion(m)
        k = k.copy(); k[e, :3] = (54, 56, 70)
        Image.fromarray(k, "RGBA").save(f"{V}/{ad}_yikik_karli.png")
        J["dosyalar"].setdefault(ad, {})["yikik_karli"] = {"dosya": f"{ad}_yikik_karli.png", "kalite": "iyi"}
        print(ad)
    json.dump(J, open(f"{V}/varyantlar.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def soguk(a, maske, oran=0.6, mavi=(0.94, 0.99, 1.1)):
    """Desaturate the masked pixels towards a cold grey."""
    f = a[..., :3].astype(np.float32)
    lum = f @ [0.299, 0.587, 0.114]
    gri = np.stack([lum * mavi[0], lum * mavi[1], lum * mavi[2]], -1)
    a[maske, :3] = np.clip(f[maske] * (1 - oran) + gri[maske] * oran, 0, 255).astype(np.uint8)
    return a


def taban_kar(a):
    """Ground plate of a building sprite: pale green / beige ground in the lower band -> snow, the
    old flat grey shadow ellipse softer and lighter."""
    a = a.copy()
    H, W = a.shape[:2]
    dolu = a[..., 3] > 200
    f = a[..., :3].astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    lum = f @ [0.299, 0.587, 0.114]
    mx, mn = f.max(-1), f.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    alt_y = np.array([np.nonzero(dolu[:, x])[0].max() if dolu[:, x].any() else 0 for x in range(W)])
    yy = np.arange(H)[:, None]
    yuk = alt_y.max() - np.nonzero(dolu.any(1))[0].min()
    bant = dolu & (yy >= alt_y[None, :] - 0.3 * yuk)
    soluk = bant & (sat < 0.42) & (lum > 85) & (g >= b * 1.02) & ~((mn > 190) & (sat < 0.12))
    soluk = ndimage.binary_opening(soluk, np.ones((2, 2)))
    t = np.clip((200 - ndimage.gaussian_filter(lum, 1.0)) / 40, 0, 3) + 0.3 * gurultu(H, W, 41, 2.0)
    idx = np.clip(np.round(t), 0, 3).astype(int)
    a[soluk, :3] = np.clip(KREM[idx] * 0.92 + f * 0.08, 0, 255)[soluk].astype(np.uint8)
    # shadow ellipse (semi-transparent): lighter, cold and with a blurred edge
    gol = (a[..., 3] > 0) & (a[..., 3] < 200)
    if gol.any():
        al = a[..., 3].astype(np.float32)
        yum = ndimage.gaussian_filter(np.where(gol, al, 0), 1.5)
        yeni_al = np.where(gol | ((yum > 4) & (a[..., 3] == 0)), np.clip(yum * 0.75, 0, 199), al)
        a[..., 3] = yeni_al.astype(np.uint8)
        a[(a[..., 3] > 0) & (a[..., 3] < 200), :3] = (40, 44, 58)
    return a


def kozmetik():
    """Cosmetic winter fixes for level-3 mine, quarry, farm and the ruined winter roofs.
    Made from the summer sprites (same shape, footprint, size)."""
    V = f"{KALE}/varyant"
    ORJ = "D:/AI/araclar/orijinal/kozmetik"
    for ad in ("maden3", "tasocagi3", "ciftlik3"):
        for kind in ("karli", "yikik_karli"):
            kaynak = f"{KALE}/{ad}.png" if kind == "karli" else f"{V}/{ad}_yikik.png"
            a = np.asarray(Image.open(kaynak).convert("RGBA")).copy()
            f = a[..., :3].astype(np.float32)
            r, g, b = f[..., 0], f[..., 1], f[..., 2]
            dolu = a[..., 3] > 200
            if ad == "maden3":
                # dome: clean cream snow in big joined patches, cold shadows, little brown showing
                k = kar_sprite(a, kapsam=0.75, bant=0.45, tohum=51, kume=3.5, karisim=0.04, yumusak=1.5, kap_kalin=3)
            elif ad == "tasocagi3":
                # rock: continuous 3-4 px caps on every top surface, grey-green cooled
                a = soguk(a, dolu & (g >= r * 0.95) & (g > b * 1.02), 0.65)
                k = kar_sprite(a, kapsam=0.5, bant=0.3, tohum=52, kume=3.0, karisim=0.05, yumusak=1.0, kap_kalin=4)
            else:
                k = kar_sprite(a, kapsam=0.75, bant=0.34, tohum=53, kume=3.5, karisim=0.05, yumusak=1.2, kap_kalin=3)
            k, _ = zemin_karla(k, toprak_da=ad != "ciftlik3", plaka=ad != "ciftlik3")
            if ad == "ciftlik3":
                # olive field and ground under snow (as white as ciftlik1), furrows faintly visible
                f2 = k[..., :3].astype(np.float32)
                r2, g2, b2 = f2[..., 0], f2[..., 1], f2[..., 2]
                lum2 = f2 @ [0.299, 0.587, 0.114]
                sat2 = (f2.max(-1) - f2.min(-1)) / np.maximum(f2.max(-1), 1)
                H, W = lum2.shape
                d2 = k[..., 3] > 200
                alt_y = np.array([np.nonzero(d2[:, x])[0].max() if d2[:, x].any() else 0 for x in range(W)])
                yy = np.arange(H)[:, None]
                yuk = alt_y.max() - np.nonzero(d2.any(1))[0].min()
                bant = d2 & (yy >= alt_y[None, :] - 0.42 * yuk)
                bugday = (r2 > g2 * 1.02) & (g2 > b2 * 1.3) & (lum2 > 85)          # yellow wheat
                tarla = bant & (((g2 > b2 * 1.12) & (sat2 > 0.18) & (lum2 > 50) & ~((r2 > g2 * 1.35) & (lum2 < 90))) | bugday)
                mo = ndimage.uniform_filter(lum2, 5)
                sd = np.sqrt(np.maximum(ndimage.uniform_filter(lum2 ** 2, 5) - mo ** 2, 0))
                tarla &= sd < 45
                tarla = ndimage.binary_opening(tarla, np.ones((2, 2)))
                t = np.clip((170 - lum2) / 55, 0, 2)              # furrows stay a tone darker
                idx = np.clip(np.round(t), 0, 2).astype(int)
                k[tarla, :3] = np.clip(KREM[idx] * 0.94 + f2 * 0.06, 0, 255)[tarla].astype(np.uint8)
            if ad != "ciftlik3":
                k = taban_kar(k)
            if kind == "yikik_karli":
                m = k[..., 3] > 0
                e = m & ~ndimage.binary_erosion(m)
                k[e & (k[..., 3] > 200), :3] = (54, 56, 70)
            Image.fromarray(k, "RGBA").save(f"{V}/{ad}_{kind}.png")
            print(ad, kind)
    # ruined winter roofs: orange-yellow ember / tile spots -> cold brown-grey
    for ad in ("demirci3", "ev3", "ciftlik2"):
        p = f"{V}/{ad}_yikik_karli.png"
        a = np.asarray(Image.open(f"{ORJ}/{ad}_yikik_karli.png").convert("RGBA")).copy()
        f = a[..., :3].astype(np.float32)
        r, g, b = f[..., 0], f[..., 1], f[..., 2]
        sat = (f.max(-1) - f.min(-1)) / np.maximum(f.max(-1), 1)
        turuncu = (a[..., 3] > 200) & (r > g * 1.25) & (g > b * 1.05) & (sat > 0.45) & (r > 110)
        a = soguk(a, turuncu, 0.75, mavi=(0.98, 0.95, 0.98))
        Image.fromarray(a, "RGBA").save(p)
        print(ad, "yikik_karli turuncu", int(turuncu.sum()))


def sakin_cati(ad):
    """ic2 barn / barracks winter roofs: the old snow is a noisy checker; smooth it into 3 cream tones."""
    p = f"{KALE}/sus/ic2/{ad}_karli.png"
    y = f"D:/AI/araclar/orijinal/{ad}_karli_eski.png"
    if not os.path.exists(y):
        Image.open(p).save(y)
    a = np.asarray(Image.open(y).convert("RGBA")).copy()
    f = a[..., :3].astype(np.float32)
    lum = f @ [0.299, 0.587, 0.114]
    mx, mn = f.max(-1), f.min(-1)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    kar = (a[..., 3] > 200) & (lum > 165) & ((mx - mn) < 40)
    # roof = snow speckles + the tiles / thatch they sit on (the upper part of the sprite)
    sat = (mx - mn) / np.maximum(mx, 1)
    sicak = (r > g * 1.1) & (sat > 0.18)                     # tiles / thatch, not the grey-beige stone
    cati = ndimage.binary_closing(kar | sicak, np.ones((3, 3))) & (a[..., 3] > 200) & (lum > 60) & (kar | sicak | ndimage.binary_dilation(sicak, iterations=1))
    lab, n = ndimage.label(cati)
    if n:                                                  # the roof is the big connected piece
        boy = np.bincount(lab.ravel()); boy[0] = 0
        cati = lab == boy.argmax()
    cati[int(a.shape[0] * 0.55):] = False
    # blur inside the roof and bring it back to a few colours: no 1 px checker
    w = ndimage.gaussian_filter(cati.astype(np.float32), 1.0)
    yum = np.stack([ndimage.gaussian_filter(np.where(cati, f[..., c], 0), 1.0) for c in range(3)], -1) / np.maximum(w, 1e-3)[..., None]
    px = yum[cati]
    q = Image.fromarray(px.reshape(1, -1, 3).clip(0, 255).astype(np.uint8)).quantize(5, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    a[cati, :3] = np.asarray(q).reshape(-1, 3)
    Image.fromarray(a, "RGBA").save(p)


def sapel():
    """Chapel (ic2): the old snow covered the upper roof as a speckled cream texture and left the
    lower roof bare (hard tone break). Bare red roof tiles get the same speckled snow."""
    eski = "D:/AI/araclar/orijinal/sapel_karli_eski.png"
    a = np.asarray(Image.open(eski).convert("RGBA")).copy()
    f = a[..., :3].astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx, mn = f.max(-1), f.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    lum = f @ [0.299, 0.587, 0.114]
    kiremit = (a[..., 3] > 200) & (r > g * 1.25) & (sat > 0.3) & (lum > 45)
    kiremit = ndimage.binary_closing(kiremit, np.ones((3, 3))) & (a[..., 3] > 200) & (lum > 35)
    kiremit[int(kiremit.shape[0] * 0.62):] = False        # below the eaves: the wooden door, not roof
    # the snowy upper roof: about half the pixels near-white, the rest the tile colour lightened
    H, W = kiremit.shape
    desen = gurultu(H, W, 31, 0.7) > 0.0
    krem = np.array([236, 234, 226], np.float32)
    c = np.where(desen[..., None], krem * (0.9 + 0.1 * (lum[..., None] / 255)), f * 0.55 + krem * 0.45)
    a[kiremit, :3] = np.clip(c[kiremit], 0, 255).astype(np.uint8)
    Image.fromarray(a, "RGBA").save(f"{KALE}/sus/ic2/sapel_karli.png")


if __name__ == "__main__":
    if sys.argv[1] == "kozmetik":
        kozmetik()
    elif sys.argv[1] == "sapel":
        sapel()
    elif sys.argv[1] == "cati":
        for ad in ("ahir", "kisla"):
            sakin_cati(ad)
    elif sys.argv[1] == "sus":
        sus()
    elif sys.argv[1] == "yikik":
        yikik_karli()
    else:
        bina_varyant()
