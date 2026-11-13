"""Side-profile rig for the undead wolf (facing left), drawn in code.

Makes D:/AI/araclar/rig/kurt.png with the same layout as the game's kurt sheet
(116x116 frames, rows walk 9 / attack 9 / die 9, footY 97, centerX 58), so birim.py can
redraw it like any other sheet: motion and colour zones come from this rig, texture from SDXL.
"""
import math
import os

from PIL import Image, ImageDraw

FW = FH = 116
S = 4                      # draw at 4x, then BOX-downscale
FOOT = 97
OUT = "D:/AI/araclar/rig"

FUR = (66, 92, 98)
FUR_D = (44, 62, 68)
FUR_L = (96, 124, 128)
BONE = (226, 206, 192)
BONE_D = (176, 150, 140)
RIB_GAP = (60, 30, 36)
EYE = (220, 40, 30)
CLAW = (40, 30, 30)
MOUTH = (110, 30, 36)


def P(x, y):
    return (x * S, y * S)


def leg(d, hip, a1, a2, l1, l2, w, col, col_d, paw=True):
    """Two-segment leg from hip; angles in degrees from straight down (positive = forward/left)."""
    k = (hip[0] - math.sin(math.radians(a1)) * l1, hip[1] + math.cos(math.radians(a1)) * l1)
    f = (k[0] - math.sin(math.radians(a1 + a2)) * l2, k[1] + math.cos(math.radians(a1 + a2)) * l2)
    d.line([P(*hip), P(*k)], fill=col, width=int(w * S))
    d.line([P(*k), P(*f)], fill=col, width=int(w * 0.8 * S))
    d.ellipse([P(k[0] - w * 0.45, k[1] - w * 0.45), P(k[0] + w * 0.45, k[1] + w * 0.45)], fill=col_d)
    if paw:
        d.ellipse([P(f[0] - w * 0.9, f[1] - w * 0.5), P(f[0] + w * 0.5, f[1] + w * 0.4)], fill=col)
        for i in range(3):
            d.point(P(f[0] - w * 0.9 + i, f[1] + 0.2), fill=CLAW)
    return f


def wolf(d, ox, oy, body_tilt=0.0, head_drop=0.0, jaw=0.0, legs=None, tail=0.0, flat=0.0):
    """Wolf facing left. (ox, oy): hip-ish reference. legs: dict of 4 (a1, a2)."""
    legs = legs or {"fn": (0, 0), "ff": (0, 0), "bn": (0, 0), "bf": (0, 0)}
    t = math.radians(body_tilt)
    sh = (ox - 27 * math.cos(t), oy - 4 - 27 * math.sin(t) + flat)     # shoulders (front = left)
    hp = (ox + 4, oy - 2 + flat)                                       # hips
    # far legs first (darker)
    leg(d, (sh[0] + 3, sh[1] + 6), *legs["ff"], 15, 15, 6.0, BONE_D, RIB_GAP)
    leg(d, (hp[0] + 2, hp[1] + 4), *legs["bf"], 14, 16, 6.4, BONE_D, RIB_GAP)
    # tail (bushy, behind the hips)
    tx, ty = hp[0] + 9, hp[1] - 7
    pts = [(tx + i * 4.2, ty + i * (2.6 - tail * 0.08) - i * i * 0.15) for i in range(6)]
    for i, (x, y) in enumerate(pts):
        rr = 6 - i * 0.6
        d.ellipse([P(x - rr, y - rr), P(x + rr, y + rr)], fill=FUR if i < 5 else FUR_D)
    # body: fur back + exposed ribcage
    d.polygon([P(sh[0] - 4, sh[1] - 10), P((sh[0] + hp[0]) / 2, min(sh[1], hp[1]) - 15 + flat * 0.2),
               P(hp[0] + 10, hp[1] - 10), P(hp[0] + 12, hp[1] + 6), P(hp[0] - 4, hp[1] + 10),
               P(sh[0] + 4, sh[1] + 12), P(sh[0] - 8, sh[1] + 6)], fill=FUR)
    # spiky mane along the back
    for i in range(7):
        x = sh[0] - 2 + i * (hp[0] - sh[0]) / 7
        y = sh[1] - 12 + (hp[1] - sh[1]) * i / 7 - 2
        d.polygon([P(x - 2, y + 3), P(x + 1, y - 5 - (i % 2) * 2), P(x + 4, y + 3)], fill=FUR_D)
    # ribcage window
    cx0, cx1 = sh[0] + 6, hp[0] - 6
    cy = (sh[1] + hp[1]) / 2 + 2
    d.ellipse([P(cx0, cy - 7), P(cx1, cy + 9)], fill=RIB_GAP)
    n = 6
    for i in range(n):
        x = cx0 + 2 + i * (cx1 - cx0 - 4) / (n - 1)
        d.arc([P(x - 3, cy - 7), P(x + 3, cy + 9)], 270, 90, fill=BONE, width=int(1.6 * S))
    d.line([P(cx0, cy - 6), P(cx1, cy - 6)], fill=BONE, width=int(1.8 * S))  # spine
    # near legs (bone, lighter)
    leg(d, (sh[0] + 1, sh[1] + 8), *legs["fn"], 15, 15, 6.4, BONE, BONE_D)
    leg(d, (hp[0] - 1, hp[1] + 6), *legs["bn"], 14, 16, 7.0, BONE, BONE_D)
    # neck + head (left)
    hx, hy = sh[0] - 12, sh[1] - 8 + head_drop
    d.polygon([P(sh[0] + 2, sh[1] - 10), P(hx + 4, hy - 6), P(hx + 6, hy + 8), P(sh[0] + 4, sh[1] + 10)], fill=FUR)
    d.ellipse([P(hx - 7, hy - 7), P(hx + 7, hy + 7)], fill=FUR)                  # skull
    d.polygon([P(hx - 4, hy - 4), P(hx - 19, hy + 1), P(hx - 19, hy + 4), P(hx - 4, hy + 4)], fill=FUR_L)  # snout
    d.polygon([P(hx - 4, hy + 4 + jaw * 0.2), P(hx - 17, hy + 5 + jaw), P(hx - 4, hy + 8 + jaw * 0.5)], fill=FUR_D)  # jaw
    if jaw > 1:
        d.polygon([P(hx - 4, hy + 4), P(hx - 18, hy + 4), P(hx - 16, hy + 5 + jaw * 0.8), P(hx - 4, hy + 6)], fill=MOUTH)
        for i in range(3):
            d.polygon([P(hx - 16 + i * 4, hy + 4), P(hx - 15 + i * 4, hy + 6.5), P(hx - 14 + i * 4, hy + 4)], fill=BONE)
    d.polygon([P(hx + 1, hy - 5), P(hx + 4, hy - 15), P(hx + 6, hy - 4)], fill=FUR_D)   # ear
    d.ellipse([P(hx - 5, hy - 3), P(hx - 1, hy + 1)], fill=EYE)
    d.point(P(hx - 19, hy + 1), fill=CLAW)                                               # nose


def frame(draw_fn):
    im = Image.new("RGBA", (FW * S, FH * S), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im))
    return im.resize((FW, FH), Image.Resampling.BOX)


def walk(i, n=9):
    p = 2 * math.pi * i / n
    sw = lambda ph: (28 * math.sin(p + ph), max(0, -30 * math.sin(p + ph + 0.6)))
    legs = {"fn": sw(0), "bf": sw(0.3), "ff": sw(math.pi), "bn": sw(math.pi + 0.3)}
    bob = 1.2 * abs(math.sin(p))
    return lambda d: wolf(d, 66, 61 - bob, legs=legs, tail=8 * math.sin(p), head_drop=1.0 * math.sin(p * 2))


def attack(i, n=9):
    # crouch (0-2), lunge with open jaws (3-5), recover (6-8)
    ph = [0, 0.3, 0.6, 1.0, 1.0, 0.8, 0.5, 0.25, 0.05][i]
    crouch = [0, 2, 4, 1, 0, 0, 1, 1, 0][i]
    reach = 10 * ph
    legs = {"fn": (35 * ph, -10 * ph), "ff": (28 * ph, -5 * ph), "bn": (-25 * ph, 15 * ph), "bf": (-18 * ph, 10 * ph)}
    return lambda d: wolf(d, 66 - reach * 0.6, 61 + crouch, body_tilt=-6 * ph, head_drop=4 * ph - 2, jaw=7 * ph, legs=legs, tail=-10 * ph)


def die(i, n=9):
    # stagger back, front legs buckle, collapse onto its side, lie flat with legs stretched
    k = i / (n - 1)
    fall = min(1, k * 1.4)
    legs = {"fn": (70 * fall, -20 * fall), "ff": (60 * fall, -15 * fall), "bn": (-70 * fall, 10 * fall), "bf": (-60 * fall, 8 * fall)}
    return lambda d: wolf(d, 66 + 3 * k, 61, body_tilt=8 * math.sin(k * 3.1), head_drop=14 * fall,
                          jaw=4 * k, legs=legs, tail=-20 * fall, flat=24 * fall)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = [walk, attack, die]
    sheet = Image.new("RGBA", (FW * 9, FH * 3), (0, 0, 0, 0))
    for r, fn in enumerate(rows):
        for c in range(9):
            sheet.alpha_composite(frame(fn(c)), (c * FW, r * FH))
    # ground-align: lowest opaque pixel of the walk row should sit on FOOT
    sheet.save(f"{OUT}/kurt.png")
    prev = Image.new("RGBA", sheet.size, (214, 204, 184, 255)); prev.alpha_composite(sheet)
    prev.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST).convert("RGB").save(f"{OUT}/kurt_onizleme.png")
    a = sheet.getchannel("A")
    print("walk row lowest y:", max(y for y in range(FH) for x in range(FW) if a.getpixel((x, y)) > 0))


if __name__ == "__main__":
    main()
