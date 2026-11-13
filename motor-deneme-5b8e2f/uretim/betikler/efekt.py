"""Pixel-art effect textures for Son Kale.

Particle textures used by savas.js (white/grey so Phaser tint still colours them):
  daire.png 16x16, kare.png 6x6, and a coloured arrow ok.png 60x12 (points right).
Extra animation strips (not wired into the game yet):
  kivilcim (spark), duman (smoke), patlama (explosion), ates (fire), ok_izi (arrow trail).
"""
import math
import os
import random

import numpy as np
from PIL import Image

OUT = "D:/AI/ComfyUI/output/son-kale-v2/efekt"
os.makedirs(OUT, exist_ok=True)
random.seed(7)


def img(w, h):
    return np.zeros((h, w, 4), np.uint8)


def put(a, x, y, c):
    h, w = a.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        a[y, x] = c if len(c) == 4 else (*c, 255)


def outline(a, col=(20, 14, 12, 255)):
    """1px outline around opaque pixels (outside)."""
    solid = a[..., 3] > 0
    grow = solid.copy()
    grow[1:] |= solid[:-1]; grow[:-1] |= solid[1:]; grow[:, 1:] |= solid[:, :-1]; grow[:, :-1] |= solid[:, 1:]
    a[grow & ~solid] = col
    return a


def save(a, name):
    Image.fromarray(a, "RGBA").save(f"{OUT}/{name}.png")


# ---------- particle textures (tintable) ----------
def daire():
    """Chunky pixel puff: white core, light-grey shade at bottom-right, stepped edge."""
    a = img(16, 16)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            if r <= 7.6:
                shade = 255
                if dx + dy > 5.5:
                    shade = 214
                elif dx + dy > 2.5:
                    shade = 236
                if dx + dy < -7 and r < 6.5:
                    shade = 255
                put(a, x, y, (shade, shade, shade, 255))
    # knock out a few edge pixels so it reads as a puff, not a perfect disc
    for x, y in [(3, 1), (12, 1), (1, 4), (14, 11), (4, 14), (11, 14)]:
        a[y, x, 3] = 0
    save(a, "daire")


def kare():
    a = img(6, 6)
    a[:, :] = (255, 255, 255, 255)
    a[5, :] = (205, 205, 205, 255)
    a[:, 5] = (205, 205, 205, 255)
    a[0, 0, 3] = 0
    save(a, "kare")


def ok():
    """60x12 arrow pointing right: fletching left, shaft, iron head right."""
    a = img(60, 12)
    shaft_d, shaft_l, shaft_m = (92, 60, 32), (150, 104, 58), (122, 84, 46)
    for x in range(10, 49):
        put(a, x, 5, shaft_l); put(a, x, 6, shaft_m)
    for x in range(14, 46, 7):  # wood grain
        put(a, x, 6, shaft_d)
    # fletching: off-white feathers with a red band
    feather, feather_s, band = (232, 222, 196), (190, 178, 150), (170, 40, 32)
    for i in range(12):
        x = 1 + i
        top = 5 - max(0, 4 - i // 3)
        for y in range(top, 5):
            put(a, x, y, feather if y < 4 else feather_s)
        for y in range(7, 12 - (5 - max(0, 4 - i // 3))):
            put(a, x, y, feather_s if y > 7 else feather)
    for y in range(1, 11):
        if a[y, 6, 3]:
            put(a, 6, y, band)
    for x in range(1, 13):
        put(a, x, 5, shaft_l); put(a, x, 6, shaft_m)
    put(a, 0, 5, (230, 210, 170)); put(a, 0, 6, (230, 210, 170))  # nock
    # iron head
    steel, steel_l, steel_d = (150, 158, 166), (214, 220, 226), (92, 98, 108)
    for i, x in enumerate(range(48, 59)):
        half = max(0, 4 - i // 2)
        for y in range(6 - half, 6 + half):
            put(a, x, y, steel)
        put(a, x, 6 - half, steel_l) if half else None
        put(a, x, 5 + half, steel_d) if half else None
    put(a, 58, 5, steel_l); put(a, 58, 6, steel)
    outline(a)
    save(a, "ok")


# ---------- animation strips ----------
def strip(frames, name):
    h = max(f.shape[0] for f in frames); w = max(f.shape[1] for f in frames)
    s = np.zeros((h, w * len(frames), 4), np.uint8)
    for i, f in enumerate(frames):
        s[:f.shape[0], i * w:i * w + f.shape[1]] = f
    save(s, name)
    return w, h, len(frames)


FIRE = [(255, 248, 200), (255, 214, 96), (255, 150, 40), (220, 80, 24), (140, 40, 20), (60, 26, 20)]
SMOKE = [(200, 196, 188), (164, 158, 150), (122, 116, 110), (86, 82, 78)]


def blob(a, cx, cy, r, colors, light=(-0.6, -0.6)):
    """Stepped pixel ball shaded with a colour ramp (first colour = lit side)."""
    h, w = a.shape[:2]
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x - cx, y - cy)
            if d <= r and 0 <= x < w and 0 <= y < h:
                lit = ((x - cx) * light[0] + (y - cy) * light[1]) / max(r, 1)
                t = (d / max(r, 1)) * 0.6 + (0.5 - lit * 0.5) * 0.4
                c = colors[min(len(colors) - 1, int(t * len(colors)))]
                a[y, x] = (*c, 255)


def kivilcim():
    """Hit spark: 6 frames, 24x24, star burst that shrinks."""
    frames = []
    rays = [(math.cos(k * math.pi / 4 + 0.2), math.sin(k * math.pi / 4 + 0.2)) for k in range(8)]
    for f in range(6):
        a = img(24, 24)
        L = [3, 8, 10, 9, 6, 3][f]
        for k, (dx, dy) in enumerate(rays):
            ln = L if k % 2 == 0 else L * 0.6
            for t in range(int(ln)):
                c = FIRE[0] if t < ln * 0.4 else FIRE[1] if t < ln * 0.75 else FIRE[2]
                if f >= 3 and t < ln * 0.5:
                    continue  # centre burns out first
                put(a, int(round(12 + dx * t)), int(round(12 + dy * t)), c)
        if f < 3:
            blob(a, 12, 12, [2, 3, 2][f], FIRE[:2])
        frames.append(a)
    return strip(frames, "kivilcim")


def duman():
    """Smoke puff: 8 frames, 32x32, grows, rises and thins out (grey, tintable)."""
    frames = []
    puffs = [(random.uniform(-5, 5), random.uniform(-3, 3), random.uniform(3, 5)) for _ in range(5)]
    for f in range(8):
        a = img(32, 32)
        g = 1 + f * 0.22
        for (px, py, r) in puffs:
            blob(a, 16 + px * g, 22 + py * g - f * 1.6, r * g, SMOKE)
        if f >= 5:  # thin out with a checker pattern
            mask = (np.indices((32, 32)).sum(0) % (2 if f == 5 else 1 + (f - 5))) == 0
            a[mask & (a[..., 3] > 0) & (np.random.RandomState(f).rand(32, 32) < 0.25 * (f - 4))] = 0
        frames.append(a)
    return strip(frames, "duman")


def patlama():
    """Explosion: 8 frames, 64x64: flash, fireball, smoke ring, debris."""
    frames = []
    debris = [(random.uniform(0, 2 * math.pi), random.uniform(10, 28)) for _ in range(14)]
    for f in range(8):
        a = img(64, 64)
        if f == 0:
            blob(a, 32, 32, 7, FIRE[:2])
        elif f <= 3:
            r = [0, 14, 19, 21][f]
            for k in range(7):
                ang = k * 2 * math.pi / 7 + f
                blob(a, 32 + math.cos(ang) * r * 0.45, 32 + math.sin(ang) * r * 0.45, r * 0.55, FIRE[1:5] if f > 1 else FIRE[:4])
            blob(a, 32, 32, r * 0.45, FIRE[:3])
        else:
            r = 20 + (f - 3) * 3
            for k in range(8):
                ang = k * 2 * math.pi / 8 + 0.3
                blob(a, 32 + math.cos(ang) * r * 0.6, 32 + math.sin(ang) * r * 0.6 - (f - 3) * 2, 7 - (f - 4), SMOKE)
            if f == 4:
                blob(a, 32, 32, 9, FIRE[2:5])
        for (ang, dist) in debris:  # flying stones
            if 1 <= f <= 6:
                d = dist * (f / 6)
                x, y = 32 + math.cos(ang) * d * 1.2, 32 + math.sin(ang) * d * 1.2 + f * f * 0.35
                put(a, int(x), int(y), (70, 62, 54)); put(a, int(x) + 1, int(y), (110, 100, 88))
        frames.append(outline(a, (30, 18, 14, 255)) if f <= 3 else a)
    return strip(frames, "patlama")


def ates():
    """Looping flame: 6 frames, 24x32."""
    frames = []
    for f in range(6):
        a = img(24, 32)
        for y in range(32):
            t = y / 31
            width = 9 * math.sin(math.pi * min(1, (t * 1.15))) * (0.55 + 0.45 * t)
            sway = math.sin(f * math.pi / 3 + y * 0.35) * (1 - t) * 3
            for x in range(24):
                d = abs(x - 12 - sway)
                if d <= width and width > 0.8:
                    k = d / max(width, 1) * 0.6 + (1 - t) * 0.5
                    c = FIRE[min(4, int(k * 5))]
                    a[y, x] = (*c, 255)
        # flicker tongues
        for (tx, ty) in [(9, 6 + f % 3), (15, 4 + (f + 2) % 3)]:
            put(a, tx, ty, FIRE[2]); put(a, tx, ty + 1, FIRE[2])
        frames.append(a)
    return strip(frames, "ates")


def ok_izi():
    """Arrow trail: 6 frames, 48x6, a streak that fades from the tail (tintable white)."""
    frames = []
    for f in range(6):
        a = img(48, 6)
        length = 48 - f * 7
        for x in range(48 - length, 48):
            t = (x - (48 - length)) / max(length, 1)
            if (x + f) % (1 if t > 0.5 else 2) == 0:
                v = int(150 + 105 * t)
                put(a, x, 2, (v, v, v)); put(a, x, 3, (v, v, v))
                if t > 0.75:
                    put(a, x, 1, (v, v, v)); put(a, x, 4, (v, v, v))
        frames.append(a)
    return strip(frames, "ok_izi")


def preview(info):
    """GIF with every strip playing side by side on the battle ground colour, x4."""
    sheets = {n: Image.open(f"{OUT}/{n}.png") for n in info}
    n_max = max(v[2] for v in info.values())
    S = 4
    W = sum(v[0] * S + 16 for v in info.values()); H = max(v[1] for v in info.values()) * S + 16
    imgs = []
    for i in range(n_max * 2):
        c = Image.new("RGBA", (W, H), (58, 52, 48, 255)); x = 8
        for n, (w, h, k) in info.items():
            fr = sheets[n].crop(((i % k) * w, 0, (i % k + 1) * w, h)).resize((w * S, h * S), Image.Resampling.NEAREST)
            c.alpha_composite(fr, (x, 8 + (H - 16 - h * S) // 2)); x += w * S + 16
        imgs.append(c.convert("RGB"))
    imgs[0].save(f"{OUT}/efektler_onizleme.gif", save_all=True, append_images=imgs[1:], duration=90, loop=0)
    # static sheet of the particle textures, tinted like the game does
    tex = Image.new("RGBA", (420, 120), (58, 52, 48, 255))
    for j, (n, tint) in enumerate([("daire", (255, 144, 48)), ("daire", (138, 122, 100)), ("kare", (154, 26, 20)), ("ok", None)]):
        t = Image.open(f"{OUT}/{n}.png").convert("RGBA")
        if tint:
            arr = np.asarray(t).astype(np.float32); arr[..., :3] *= np.array(tint) / 255; t = Image.fromarray(arr.astype(np.uint8))
        t = t.resize((t.width * 4, t.height * 4), Image.Resampling.NEAREST)
        tex.alpha_composite(t, (10 + j * 100 if n != "ok" else 170, 20 if n != "ok" else 70))
    tex.save(f"{OUT}/dokular_onizleme.png")


if __name__ == "__main__":
    daire(); kare(); ok()
    info = {"kivilcim": kivilcim(), "duman": duman(), "patlama": patlama(), "ates": ates(), "ok_izi": ok_izi()}
    import json
    json.dump({n: {"fw": w, "fh": h, "kare": k} for n, (w, h, k) in info.items()}, open(f"{OUT}/efektler.json", "w"), indent=1)
    preview(info)
    print(info)
