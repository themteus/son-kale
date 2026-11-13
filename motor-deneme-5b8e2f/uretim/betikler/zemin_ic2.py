"""Ground decal layer for the inner castle (drawn over arka.png, under everything else).

Pixel-art strokes in the background's own colours: trampled dirt paths from building doors to the
main street, worn patches under the market / training yard / farm, straw around the stable,
stone chips by the mason, grass tufts at wall feet. Drawn at the background's resolution
(1280x720, shown x1.5), so its pixels match the ground art.

  python zemin_ic2.py  ->  assets/kale/sus/ic2/zemin.png (+ _karli, _gece)
Coordinates in the spec are SCREEN pixels (1920x1080).
"""
import json
import math
import random

import numpy as np
from PIL import Image, ImageDraw

KALE = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"
OUT = f"{KALE}/sus/ic2"
SPEC = "D:/AI/araclar/zemin_ic2.json"
W, H, K = 1280, 720, 1.5
random.seed(4)


def renkler():
    """Sample the ground colours from the background around the courtyard."""
    a = np.asarray(Image.open(f"{KALE}/arka.png").convert("RGB")).astype(int)
    patch = a[int(470 / K):int(560 / K), int(1250 / K):int(1330 / K)].reshape(-1, 3)   # plain courtyard dirt
    toprak = np.median(patch, 0)
    return {
        "patika": tuple(int(min(255, c * 1.13 + 8)) for c in toprak),
        "patika_k": tuple(int(c * 1.0 + 2) for c in toprak),
        "ezik": tuple(int(c * 0.86) for c in toprak),
        "ezik_k": tuple(int(c * 0.76) for c in toprak),
        "saman": (196, 164, 86), "saman_k": (156, 124, 60),
        "tas": (138, 130, 120), "tas_k": (96, 90, 84),
        "ot": (86, 118, 52), "ot_k": (60, 88, 40),
        "camur": tuple(int(c * 0.62) for c in toprak),
    }


def S(p):
    return (p[0] / K, p[1] / K)


def benek(d, x, y, r, c, ck, yogun=0.55):
    """Ragged pixel blob: a disc with noisy edge and darker speckles."""
    for yy in range(int(y - r), int(y + r) + 1):
        for xx in range(int(x - r * 1.6), int(x + r * 1.6) + 1):
            dx, dy = (xx - x) / (r * 1.6), (yy - y) / r
            q = dx * dx + dy * dy
            if q < 1 and random.random() < (1.0 if q < 0.55 else yogun):
                d.point((xx, yy), fill=ck if random.random() < 0.18 else c)


def patika(d, pts, gen, R):
    pts = [S(p) for p in pts]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(1, math.hypot(x1 - x0, y1 - y0)))
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if i % 2 == 0:
                benek(d, x + random.uniform(-0.6, 0.6), y + random.uniform(-0.4, 0.4), gen / K / 2.4, R["patika"], R["patika_k"], 0.5)


def alan(d, merkez, rx, ry, R, tur="ezik"):
    cx, cy = S(merkez)
    for _ in range(int(rx * ry / 120) + 6):
        a, r = random.uniform(0, 2 * math.pi), random.random() ** 0.6
        benek(d, cx + math.cos(a) * rx / K * r, cy + math.sin(a) * ry / K * r, random.uniform(2.5, 5), R[tur], R[tur + "_k"] if tur + "_k" in R else R[tur], 0.45)


def serpinti(d, merkez, rx, ry, n, tur, R):
    cx, cy = S(merkez)
    for _ in range(n):
        x, y = cx + random.uniform(-rx, rx) / K, cy + random.uniform(-ry, ry) / K
        if tur == "saman":
            L = random.randint(2, 4); ang = random.uniform(-0.5, 0.5)
            d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=random.choice([R["saman"], R["saman_k"]]))
        elif tur == "tas":
            d.rectangle([x, y, x + random.randint(1, 2), y + 1], fill=random.choice([R["tas"], R["tas_k"]]))
        elif tur == "ot":
            for k in range(random.randint(2, 4)):
                d.line([(x + k, y), (x + k + random.choice([-1, 0, 1]), y - random.randint(2, 4))], fill=random.choice([R["ot"], R["ot_k"]]))


def ciz(spec, R):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for a in spec.get("alanlar", []):
        alan(d, a["m"], a["rx"], a["ry"], R, a.get("tur", "ezik"))
    for p in spec.get("patikalar", []):
        patika(d, p["n"], p.get("gen", 22), R)
    for s in spec.get("serpinti", []):
        serpinti(d, s["m"], s["rx"], s["ry"], s["n"], s["tur"], R)
    return im


def main():
    spec = json.load(open(SPEC, encoding="utf-8"))
    R = renkler()
    im = ciz(spec, R)
    im.save(f"{OUT}/zemin.png")
    # winter: paths become slushy, patches snowy; evening: darker blue
    a = np.asarray(im).astype(np.float32)
    k = a.copy(); k[..., :3] = k[..., :3] * 0.72 + np.array([200, 206, 218]) * 0.28
    Image.fromarray(k.astype(np.uint8), "RGBA").save(f"{OUT}/zemin_karli.png")
    g = a.copy(); lum = g[..., :3] @ np.array([0.3, 0.59, 0.11]); g[..., 0] = lum * 0.3; g[..., 1] = lum * 0.36; g[..., 2] = lum * 0.55
    Image.fromarray(g.astype(np.uint8), "RGBA").save(f"{OUT}/zemin_gece.png")
    print("zemin:", im.size, int((a[..., 3] > 0).sum()), "piksel")


if __name__ == "__main__":
    main()
