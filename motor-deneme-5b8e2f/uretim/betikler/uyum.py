"""Make the new inner-castle props sit in the PixelLab art: shared palette, softer saturation,
a soft ground shadow (light from the top left), and the same 1px dark outline.

Reads D:/AI/ComfyUI/output/son-kale-v2/ic/secilen/<ad>.png, writes the repo's
assets/kale/sus/ic2/<ad>.png (+ _karli/_gece) and D:/AI/araclar/ic_taban.json
(how many pixels the shadow added below the base: placement y must move down by that).
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, "D:/AI/araclar")
import bina  # noqa: E402  (karla_ust, gecele)

KALE = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"
SEC = "D:/AI/ComfyUI/output/son-kale-v2/ic/secilen"
HEDEF = f"{KALE}/sus/ic2"
HAYVAN = {"tavuk", "domuz", "kopek", "at_kahve", "at_beyaz"}
BUYUK = {"kisla", "sapel", "ahir", "ambar"}


def pixellab_paleti(n=72):
    """Palette of the existing PixelLab art (buildings + decorations + ground)."""
    px = []
    files = glob.glob(f"{KALE}/*[123].png") + glob.glob(f"{KALE}/sus/*.png") + [f"{KALE}/arka.png"]
    for f in files:
        a = np.asarray(Image.open(f).convert("RGBA"))
        p = a[a[..., 3] > 200][:, :3]
        if len(p) > 20000:
            p = p[np.random.RandomState(0).choice(len(p), 20000, replace=False)]
        px.append(p)
    px = np.concatenate(px)
    side = int(np.ceil(np.sqrt(len(px))))
    pad = np.zeros((side * side, 3), np.uint8); pad[:len(px)] = px; pad[len(px):] = px[0]
    return Image.fromarray(pad.reshape(side, side, 3)).quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def uyumla(im, pal, doygunluk=0.82):
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    rgb = a[..., :3]
    lum = rgb @ np.array([0.3, 0.59, 0.11])
    rgb = lum[..., None] + (rgb - lum[..., None]) * doygunluk           # calmer colours
    rgb = rgb * 0.96 + np.array([6, 3, 0]) * 1.0                         # slightly warm, like the PixelLab light
    q = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
    out = np.dstack([np.asarray(q), a[..., 3].astype(np.uint8)])
    # 1px dark outline on the silhouette edge (like PixelLab)
    solid = out[..., 3] > 0
    edge = solid & ~ndimage.binary_erosion(solid, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    out[edge, :3] = (out[edge, :3] * 0.35).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def golge(im, guc=78):
    """Soft elliptical ground shadow under the base, pushed to the bottom right (sun top left).
    Returns the new image and how many pixels were added below the old base."""
    w, h = im.size
    a = np.asarray(im.getchannel("A")) > 0
    cols = np.nonzero(a.any(0))[0]
    base_w = (cols.max() - cols.min() + 1) if len(cols) else w
    ew, eh = base_w * 0.62, max(3, base_w * 0.2)
    cx, cy = (cols.min() + cols.max()) / 2 + base_w * 0.08, h - eh * 0.35
    pad_r = int(max(0, cx + ew - w) + 2)
    pad_b = int(max(0, cy + eh - h) + 1)
    W, H = w + 2 * pad_r, h + pad_b
    yy, xx = np.mgrid[0:H, 0:W]
    d = ((xx - (cx + pad_r)) / ew) ** 2 + ((yy - cy) / eh) ** 2
    alpha = np.clip(1.0 - d, 0, 1) ** 0.8 * guc
    alpha = (np.round(alpha / 26) * 26).clip(0, guc)                    # banded, pixel-art style
    sh = np.zeros((H, W, 4), np.uint8)
    sh[..., :3] = (36, 28, 22)
    sh[..., 3] = alpha.astype(np.uint8)
    canvas = Image.fromarray(sh, "RGBA")
    canvas.alpha_composite(im, (pad_r, 0))
    return canvas, pad_b


def main():
    os.makedirs(HEDEF, exist_ok=True)
    pal = pixellab_paleti()
    taban = {}
    for f in sorted(glob.glob(f"{SEC}/*.png")):
        ad = os.path.splitext(os.path.basename(f))[0]
        im = uyumla(Image.open(f), pal, 0.75 if ad.startswith("tezgah") else 0.85)
        sonuc, dy = golge(im, 60 if ad in HAYVAN else 78)
        sonuc.save(f"{HEDEF}/{ad}.png")
        taban[ad] = dy
        # winter / evening versions from the harmonised art (shadow added after, so it stays a shadow)
        if ad not in HAYVAN:
            k = bina.karla_ust(im, 0.5 if ad in BUYUK and ad != "sapel" else 0.28 if ad == "sapel" else 0.35)
            golge(k, 78)[0].save(f"{HEDEF}/{ad}_karli.png")
        isik = dict(isik_v=1.1) if ad in ("ahir", "saman", "ambar") else dict(isik_v=0.9, isik_s=0.65)
        golge(bina.gecele(im, **isik), 70)[0].save(f"{HEDEF}/{ad}_gece.png")
    json.dump(taban, open("D:/AI/araclar/ic_taban.json", "w"), indent=1)
    print(taban)


if __name__ == "__main__":
    main()
