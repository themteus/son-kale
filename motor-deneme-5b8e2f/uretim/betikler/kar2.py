"""Winter, second approach: objects stay whole, snow only where it would lie.

1. Ground = smooth grass, dirt, grass in shadow, lit grass/field away from trees. Tiny leftovers of
   either class (< 30 px) are merged into the other, so no black splinters stay in the snow.
2. Ground snow: 4 tones taken from the snowy building variants (assets/kale/varyant/*_karli), small
   clustered texture, blue shadow on the lower-right side of every object (light from the top left),
   a lighter drift along object feet facing the light.
3. Objects keep their pixels. Snow caps where a pixel faces up: trees 1-2 px on branch tops, walls
   and towers 2-3 px on wall tops / merlons / tower caps (from the stone mask of the old art, so the
   new mortar lines do not count as edges), roofs 2 px on their top edge, a 1 px cold line under
   wall caps. Moss / summer greens on stone are cooled, tree trunks slightly cooled.

  python kar2.py arka on
"""
import glob
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arka_hd as A  # noqa: E402
import tas_desen as T  # noqa: E402

HD = "D:/AI/ComfyUI/output/son-kale-v2/arka_hd"
KALE = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"


def kar_tonlari(n=5):
    """Snow tones of the snowy building variants, light to dark."""
    px = []
    for p in glob.glob(f"{KALE}/varyant/*_karli.png"):
        a = np.asarray(Image.open(p).convert("RGBA")).reshape(-1, 4)
        a = a[a[:, 3] > 200][:, :3].astype(np.float32)
        mx, mn = a.max(1), a.min(1)
        sat = (mx - mn) / np.maximum(mx, 1)
        lum = a @ [0.299, 0.587, 0.114]
        px.append(a[(sat < 0.22) & (lum > 120) & (a[:, 2] >= a[:, 0] - 4)])
    px = np.concatenate(px)
    lum = px @ [0.299, 0.587, 0.114]
    # the variants' snow is nearly one colour: start from their lightest tone and step towards a cold
    # blue grey, so the ground has 3-4 readable tones and a shadow tone
    # same family as the cream snow on the roofs, cooler only in the shadow steps
    return np.array([[236, 236, 230], [224, 226, 226], [208, 214, 222], [188, 198, 214], [166, 178, 202]],
                    np.float32)[:n]


ZEMIN = []


def kaydir(m, dy, dx):
    out = np.zeros_like(m)
    H, W = m.shape
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = m[ys, xs]
    return out


def karla(ad, im):
    a = np.asarray(im.convert("RGBA"))
    H, W = a.shape[:2]
    alfa = a[..., 3] > 0
    f = a[..., :3].astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    lum = f @ [0.299, 0.587, 0.114]
    mx, mn = f.max(-1), f.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    mo = ndimage.uniform_filter(lum, 7)
    sd = np.sqrt(np.maximum(ndimage.uniform_filter(lum ** 2, 7) - mo ** 2, 0))

    # structures of the old art (stone mask inside the face polygons) and roofs
    o = np.asarray(Image.open(f"{T.ORJ}/{ad}.png").convert("RGBA").resize((W, H), Image.Resampling.NEAREST))
    tas = T.tas_maskesi(o)
    yuz = np.zeros((H, W), bool)
    for kind, poli, par in T.YUZLER[ad]:
        _, m = T.desen(H, W, poli, kind, par, np.zeros((H, W)), np.zeros((9, 3)), 1)
        yuz |= m
    # whole regions, not per-pixel classes: vines and mortar must not split a wall into "tops"
    yapi = ndimage.binary_fill_holes(ndimage.binary_closing(tas & yuz, np.ones((5, 5)))) & yuz
    cati0 = (r > g * 1.3) & (sat >= 0.4) & (g < r * 0.6)
    lab, n = ndimage.label(cati0)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        cati0 &= (boy >= 20)[lab]
    cati = ndimage.binary_fill_holes(ndimage.binary_closing(cati0, np.ones((5, 5))))

    yesil = (g >= r * 0.98) & (g > b * 1.1)
    # trees: dark-green cores of a fair size, grown into whole crowns (lit needles included)
    # crowns: dark green needles + the near-black outline around them close the shape, then fill it
    # needles are textured (smooth dark green = grass in shadow), and a crown is mostly green
    koyu = ((yesil & (lum <= 62) & (sd >= 7)) | (lum <= 40)) & ~yapi & ~cati
    lab, n = ndimage.label(koyu)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        yes = np.bincount(lab.ravel(), weights=(yesil & (lum <= 62)).ravel(), minlength=n + 1)
        # crowns have lit needle highlights around their dark core, grass in shadow does not
        parlak = ndimage.binary_dilation(yesil & (lum > 78), iterations=1)
        vur = np.bincount(lab.ravel(), weights=(parlak & (lab > 0)).ravel(), minlength=n + 1)
        koyu &= ((boy >= 25) & (yes >= 0.5 * np.maximum(boy, 1)) & ((vur >= 0.08 * boy) | (boy < 400) | (boy >= 3000)))[lab]
    agac = ndimage.binary_fill_holes(ndimage.binary_closing(koyu, np.ones((5, 5))))
    agac &= ~ndimage.binary_opening(cimen0 := ((g > r * 1.02) & (g > b * 1.12) & (lum > 55) & (lum < 125)), np.ones((9, 9)))
    agac = ndimage.binary_dilation(agac, iterations=1) & ~yapi & ~cati
    lab, n = ndimage.label(agac)
    if n:   # small green crumbs are not trees (they would stay green in the snow)
        boy = np.bincount(lab.ravel()); boy[0] = 0
        agac &= (boy >= 300)[lab]
    cimen = (g > r * 1.02) & (g > b * 1.12) & (lum > 55)
    toprak = (r > g * 1.25) & (g > r * 0.52) & (g > b * 1.05) & (lum > 42) & (lum < 175)
    zemin = (cimen & (sd < 30)) | (toprak & (sd < 18)) | (yesil & (lum <= 62) & (sd < 9))
    zemin &= ~agac
    if ad == "arka":
        # dark roof backs and trunks behind the keep are not dirt
        zemin[int(195 * 1.5):int(300 * 1.5), int(960 * 1.5):int(1150 * 1.5)] &= cimen[int(195 * 1.5):int(300 * 1.5), int(960 * 1.5):int(1150 * 1.5)] & ~agac[int(195 * 1.5):int(300 * 1.5), int(960 * 1.5):int(1150 * 1.5)]
        # north field: wheat and grass patch inside the courtyard corner is ground as well
        tarla = np.zeros((H, W), bool); tarla[220:292, 750:942] = True
        zemin |= tarla & (lum > 60) & ~yapi & (sat < 0.7)
    else:
        zemin &= cimen
    zemin &= alfa & ~yapi & ~cati
    zemin = ndimage.binary_closing(zemin, np.ones((3, 3))) & alfa & ~yapi & ~cati
    # tiny islands: object specks inside snow -> snow, snow specks inside objects -> object
    lab, n = ndimage.label(~zemin & alfa)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        zemin |= (boy < 30)[lab] & ~yapi & ~cati & ~agac & (lab > 0)
    lab, n = ndimage.label(zemin)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        zemin &= (boy >= 400)[lab]   # pockets inside tree crowns stay part of the tree
    # brown rims and old cart tracks: dirt-coloured pixels touching the snow join it
    kir = (r > g * 1.15) & (g > b * 1.0) & (lum > 28) & (lum < 175) & alfa & ~yapi & ~cati & ~agac
    for _ in range(3):
        zemin |= ndimage.binary_dilation(zemin, iterations=2) & kir
    # small leftovers inside the snow that are not trees / walls / roofs (green specks, crumbs) -> snow
    lab, n = ndimage.label(alfa & ~zemin)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        cekirdek = np.zeros(n + 1, bool)
        np.maximum.at(cekirdek, lab.ravel(), (koyu | yapi | cati).ravel())
        zemin |= (((boy < 250) & ~cekirdek) | (boy < 120))[lab] & (lab > 0) & ~yapi & ~cati
    if ad == "arka":
        # dark smooth shadow rings around props baked into the background (barrels, hay, stalls)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import arka_hd as AH
        for kutu_ in AH.KORU["arka"].values():
            (x0, y0, x1, y1) = kutu_[0] if len(kutu_) == 3 else kutu_
            kk = np.zeros((H, W), bool); kk[int(y0 * 1.5):int(y1 * 1.5), int(x0 * 1.5):int(x1 * 1.5)] = True
            halka = kk & (lum < 70) & (sd < 14) & ~yapi & ~cati & ndimage.binary_dilation(zemin, iterations=5)
            zemin |= halka
    # smoother snow edge: no 1 px teeth
    zemin = ndimage.binary_opening(ndimage.binary_closing(zemin, np.ones((3, 3))), np.ones((2, 2))) | (zemin & ~ndimage.binary_dilation(~zemin, iterations=1) )
    zemin &= alfa & ~yapi & ~cati
    nesne = alfa & ~zemin

    ton = kar_tonlari()           # 5 tones light -> dark (blue grey)
    out = f.copy()
    # ground texture: old brightness (bumps, tracks) + small clustered noise, 4 tones
    rng = np.random.default_rng(3)
    gur = ndimage.gaussian_filter(rng.standard_normal((H, W)), 4.0)   # large, calm clusters
    gur /= gur.std() + 1e-6
    yerel = ndimage.gaussian_filter(lum, 3.0)
    yerel = (yerel - ndimage.gaussian_filter(lum, 16)) / 25.0
    t = 0.7 - 0.45 * yerel - 0.4 * gur                     # mostly the two light tones
    # shadow: an object up-left of the pixel (light from the top left)
    # soft, sparse shadows: only objects of some size cast one, blurred and thresholded
    lab_n, nn = ndimage.label(nesne)
    buyuk = nesne.copy()
    if nn:
        bb = np.bincount(lab_n.ravel()); bb[0] = 0
        buyuk = (bb >= 200)[lab_n] & nesne
    gol = np.zeros((H, W), np.float32)
    for k in range(2, 11, 2):
        gol = np.maximum(gol, kaydir(buyuk, k // 2, k).astype(np.float32))
    golge = (ndimage.gaussian_filter(gol, 2.5) > 0.45) & zemin
    yakin = ndimage.binary_dilation(nesne, iterations=2) & zemin
    t = np.where(golge, t + 1.7, t)
    t = np.where(yakin & ~golge, t - 0.8, t)               # light-facing drift at object feet
    # soft edge: one tone step on the 1-2 px rim against objects
    kenar1 = zemin & ndimage.binary_dilation(nesne, iterations=1)
    kenar2 = zemin & ndimage.binary_dilation(nesne, iterations=2) & ~kenar1
    t = np.where(kenar1 & ~golge, np.maximum(t, 1), t)    # one light step only, no dark crumb rim
    idx = np.clip(np.round(t), 0, 4).astype(int)
    out[zemin] = ton[idx][zemin]

    # caps on objects
    acik = zemin | ~alfa                                   # open space above a cap
    # structures: top faces = stone pixels whose pixel above is not stone (old art mask, so the new
    # mortar does not count); 2-3 px deep
    ust = yapi & ~kaydir(yapi, 1, 0)
    # 3-4 px deep caps with a rounded lower edge (depth 3, 4 every other stone)
    derin = 3 + ((np.arange(W)[None, :] // 5) % 2)
    kap_y = ust.copy()
    sira = np.zeros((H, W), int)
    for d in (1, 2, 3):
        yeni = kaydir(ust, d, 0) & yapi & ((d < derin) | (d < 3))
        sira = np.where(yeni & ~kap_y, d, sira)
        kap_y |= yeni
    kap_y &= alfa
    out[kap_y] = ton[np.clip(sira, 0, 2)][kap_y]          # light on top, shaded towards the bottom
    alt = kaydir(kap_y, 1, 0) & ~kap_y & yapi
    out[alt] = np.array([88, 96, 122], np.float32)
    # snow piled at the wall feet: 2 px up onto the wall where snow lies below it
    dip = yapi & (kaydir(zemin, -1, 0) | kaydir(zemin, -2, 0)) & ~kap_y
    out[dip] = ton[1]
    # roofs: snow on the upper ~40 % of every roof column, broken lower edge
    kap_c = np.zeros((H, W), bool)
    for x in np.nonzero(cati.any(0))[0]:
        ys = np.nonzero(cati[:, x])[0]
        n_ = max(2, int(len(ys) * (0.36 + 0.08 * ((x // 3) % 2))))
        kap_c[ys[:n_], x] = True
    kap_c &= alfa
    out[kap_c] = ton[np.clip((lum[kap_c] < 70).astype(int) + (lum[kap_c] < 45).astype(int), 0, 2)]
    # trees: 1-2 px on branch tops facing open sky / snow
    agac_n = agac & nesne
    ust_a = agac_n & kaydir(acik, 1, 0)
    kap_a = ust_a | (kaydir(ust_a, 1, 0) & agac_n & (lum > 45))
    out[kap_a] = ton[np.where(ust_a, 0, 1)][kap_a]
    # rocks, carts, crates...: 2 px on top edges facing open snow / sky
    diger = nesne & ~agac & ~yapi & ~cati & ~kap_a
    ust_d = diger & kaydir(acik, 1, 0)
    kap_d = ust_d | (kaydir(ust_d, 1, 0) & diger)
    out[kap_d] = ton[np.where(ust_d, 0, 1)][kap_d]
    kap_a = kap_a | kap_d
    # cool what is left: moss on stone, summer greens, trunks; then a light winter cast on objects
    kalan = nesne & ~kap_y & ~kap_c & ~kap_a & ~alt
    yosun = kalan & yesil & ~agac
    gri = out[yosun] @ [0.299, 0.587, 0.114]
    out[yosun] = np.stack([gri * 0.92, gri * 0.97, gri * 1.08], -1)
    agac_k = kalan & agac
    out[agac_k] = out[agac_k] * np.array([0.9, 0.95, 1.06])
    out[kalan] = out[kalan] * 0.92 + np.array([168, 182, 210], np.float32) * 0.08
    ZEMIN[:] = [zemin, kap_y | kap_c | kap_a | dip | alt]
    return np.clip(out, 0, 255)


def kis(ad):
    yaz = Image.open(f"{HD}/{ad}_desen.png").convert("RGBA")
    a = np.asarray(yaz)
    k = karla(ad, yaz)
    q = np.asarray(A.kuantala(Image.fromarray(k.astype(np.uint8)), A.palet(ad, kis=True))).copy()
    fa = a[..., :3].astype(np.float32)
    kir = (fa[..., 0] > 100) & (fa[..., 0] > fa[..., 1] * 1.6) & (fa[..., 0] > fa[..., 2] * 1.6)
    lab, n = ndimage.label(kir)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        kir &= (boy < 1500)[lab]
    z, kapak = ZEMIN
    kir &= ~kapak                         # red cloth comes back, but not over snow caps
    q[kir] = a[kir, :3]
    q[z] = k[z].astype(np.uint8)          # snow tones bypass the palette (it would merge them)
    q[kapak] = k[kapak].astype(np.uint8)
    out = Image.fromarray(np.dstack([q, a[..., 3]]).astype(np.uint8), "RGBA") if ad == "on" else Image.fromarray(q.astype(np.uint8))
    p = f"{HD}/{ad}_karli.png"
    out.save(p)
    print(p)


if __name__ == "__main__":
    for ad in sys.argv[1:]:
        kis(ad)
