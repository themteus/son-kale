"""Side-profile humanoid archer rig (code-drawn pose guide for SDXL redraws).

okcuiskelet: facing left, 132x132 frames, rows walk 8 / attack 9 / die 7, footY 113.
Colour zones (hood, cloak, bones, trousers, boots, bow) stay identical in every frame,
so birim.py's chroma transfer keeps the costume consistent across all rows.
"""
import math
import os

from PIL import Image, ImageDraw

S = 4
OUT = "D:/AI/araclar/rig"

RENK = {
    "okcuiskelet": dict(hood=(78, 82, 74), hood_d=(52, 56, 50), cloak=(92, 98, 86), cloak_d=(62, 68, 58),
                        skin=(222, 214, 196), skin_d=(170, 160, 142), pants=(64, 74, 96), pants_d=(44, 52, 70),
                        boot=(110, 70, 42), bow=(130, 86, 48), string=(220, 220, 210), quiver=(120, 76, 44),
                        face=(30, 26, 28), belt=(110, 74, 40)),
}


def P(x, y):
    return (x * S, y * S)


def seg(d, a, b, w, col):
    d.line([P(*a), P(*b)], fill=col, width=max(1, int(w * S)))
    r = w / 2
    d.ellipse([P(b[0] - r, b[1] - r), P(b[0] + r, b[1] + r)], fill=col)


def limb(start, a1, a2, l1, l2, yon):
    """Angles in degrees from straight down; positive swings toward the facing direction."""
    k = (start[0] + yon * math.sin(math.radians(a1)) * l1, start[1] + math.cos(math.radians(a1)) * l1)
    e = (k[0] + yon * math.sin(math.radians(a1 + a2)) * l2, k[1] + math.cos(math.radians(a1 + a2)) * l2)
    return k, e


def arm_to(start, target, l1, l2, bend=1):
    """Two-bone IK: elbow position for a hand at target."""
    dx, dy = target[0] - start[0], target[1] - start[1]
    dist = max(1e-3, min(l1 + l2 - 0.01, math.hypot(dx, dy)))
    a = math.atan2(dy, dx)
    c = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    b = math.acos(max(-1, min(1, c)))
    el = (start[0] + math.cos(a + bend * b) * l1, start[1] + math.sin(a + bend * b) * l1)
    hand = (start[0] + math.cos(a) * dist, start[1] + math.sin(a) * dist)
    return el, hand


def insan(d, R, hip, yon=-1, legs=((0, 0), (0, 0)), lean=0.0, aim=None, draw=0.0, fall=0.0, arms_idle=(10, -10)):
    """yon=-1 faces left. aim: bow angle in degrees (0 = straight ahead, negative = up) or None (bow held low).
    draw: 0..1 string pull. fall: 0..1 body rotation backwards (death)."""
    rot = math.radians(-yon * 80 * fall + lean * yon)
    def R2(p):  # rotate around the hip for falling
        x, y = p[0] - hip[0], p[1] - hip[1]
        return (hip[0] + x * math.cos(rot) - y * math.sin(rot), hip[1] + x * math.sin(rot) + y * math.cos(rot))

    shoulder = R2((hip[0], hip[1] - 31))
    neck = R2((hip[0] + yon * 1, hip[1] - 34))
    head = R2((hip[0] + yon * 2, hip[1] - 42))
    # far leg, far arm first
    k, f = limb(hip, legs[1][0], legs[1][1], 15, 15, yon)
    seg(d, hip, k, 6, R["pants_d"]); seg(d, k, f, 5.2, R["pants_d"]); seg(d, f, (f[0] + yon * 4, f[1]), 4.6, R["boot"])
    # quiver on the back
    qb = R2((hip[0] - yon * 5, hip[1] - 20))
    d.polygon([P(qb[0] - 2, qb[1] + 10), P(qb[0] + 3, qb[1] + 10), P(qb[0] + 5 - yon * 2, qb[1] - 8), P(qb[0] - 0 - yon * 2, qb[1] - 8)], fill=R["quiver"])
    for i in range(3):
        d.line([P(qb[0] + 1 - yon * 2 + i, qb[1] - 8), P(qb[0] + 1 - yon * 3 + i * 1.5, qb[1] - 13)], fill=R["string"], width=S)
    # cloak (behind the body, flowing back)
    c = [R2((hip[0] - yon * 9, hip[1] - 32)), R2((hip[0] + yon * 4, hip[1] - 32)), R2((hip[0] + yon * 6, hip[1] + 6)),
         R2((hip[0] - yon * 13, hip[1] + 12)), R2((hip[0] - yon * 14, hip[1] - 6))]
    d.polygon([P(*q) for q in c], fill=R["cloak"])
    d.line([P(*c[3]), P(*c[4])], fill=R["cloak_d"], width=2 * S)
    # torso (ribs)
    t = [R2((hip[0] - yon * 6, hip[1] - 30)), R2((hip[0] + yon * 5, hip[1] - 30)), R2((hip[0] + yon * 5, hip[1] - 2)), R2((hip[0] - yon * 5, hip[1] - 2))]
    d.polygon([P(*q) for q in t], fill=R["skin_d"])
    for i in range(4):
        a, b = R2((hip[0] - yon * 4, hip[1] - 26 + i * 5.5)), R2((hip[0] + yon * 4, hip[1] - 26 + i * 5.5))
        d.line([P(*a), P(*b)], fill=R["skin"], width=int(1.6 * S))
    belt_a, belt_b = R2((hip[0] - yon * 4, hip[1] - 2)), R2((hip[0] + yon * 4, hip[1] - 2))
    d.line([P(*belt_a), P(*belt_b)], fill=R["belt"], width=3 * S)
    # near leg
    k, f = limb(hip, legs[0][0], legs[0][1], 15, 15, yon)
    seg(d, hip, k, 6.4, R["pants"]); seg(d, k, f, 5.6, R["pants"]); seg(d, f, (f[0] + yon * 4.5, f[1]), 5, R["boot"])
    # head: skull face in a hood
    d.ellipse([P(head[0] - 8, head[1] - 9), P(head[0] + 8, head[1] + 8)], fill=R["hood"])
    fx = head[0] + yon * 3
    d.ellipse([P(fx - 4, head[1] - 4), P(fx + 4, head[1] + 5)], fill=R["skin"])
    d.point(P(fx + yon * 1, head[1] - 1), fill=R["face"]); d.point(P(fx + yon * 1, head[1] + 2), fill=R["face"])
    d.polygon([P(head[0] - yon * 6, head[1] - 5), P(head[0] - yon * 10, head[1] + 2), P(head[0] - yon * 4, head[1] + 4)], fill=R["hood_d"])
    # arms + bow
    if aim is None:
        k1, h1 = limb(shoulder, arms_idle[0], -5, 12, 12, yon)
        k2, h2 = limb(shoulder, arms_idle[1], 15, 12, 12, yon)
        seg(d, shoulder, k2, 4, R["skin_d"]); seg(d, k2, h2, 3.4, R["skin_d"])
        # bow held low and diagonal in the front hand
        bt, bb = (h1[0] + yon * 4, h1[1] - 14), (h1[0] - yon * 6, h1[1] + 10)
        d.line([P(*bt), P(h1[0] + yon * 2, h1[1]), P(*bb)], fill=R["bow"], width=int(2.2 * S))
        d.line([P(*bt), P(*bb)], fill=R["string"], width=S)
        seg(d, shoulder, k1, 4.2, R["skin"]); seg(d, k1, h1, 3.6, R["skin"])
    else:
        a = math.radians(aim)
        dirx, diry = yon * math.cos(a), math.sin(a)
        grip = (shoulder[0] + dirx * 22, shoulder[1] + diry * 22)
        nock = (grip[0] - dirx * (6 + 14 * draw), grip[1] - diry * (6 + 14 * draw))
        # far (drawing) arm to the nock
        el2, h2 = arm_to(shoulder, nock, 12, 12, bend=-yon)
        seg(d, shoulder, el2, 4, R["skin_d"]); seg(d, el2, h2, 3.4, R["skin_d"])
        # bow: perpendicular to aim, bends back with draw
        px, py = -diry, dirx
        L = 19
        top, bot = (grip[0] + px * L, grip[1] + py * L), (grip[0] - px * L, grip[1] - py * L)
        mid = (grip[0] + dirx * 3, grip[1] + diry * 3)
        d.line([P(*top), P(*mid), P(*bot)], fill=R["bow"], width=int(2.2 * S))
        d.line([P(*top), P(*nock), P(*bot)], fill=R["string"], width=S)
        if draw > 0.2:  # arrow
            tip = (grip[0] + dirx * 8, grip[1] + diry * 8)
            d.line([P(*nock), P(*tip)], fill=R["bow"], width=S)
            d.polygon([P(tip[0] + dirx * 3, tip[1] + diry * 3), P(tip[0] + px * 1.5, tip[1] + py * 1.5), P(tip[0] - px * 1.5, tip[1] - py * 1.5)], fill=R["string"])
        el1, h1 = arm_to(shoulder, grip, 12, 12, bend=yon)
        seg(d, shoulder, el1, 4.2, R["skin"]); seg(d, el1, h1, 3.6, R["skin"])


def kare(fw, fh, fn):
    im = Image.new("RGBA", (fw * S, fh * S), (0, 0, 0, 0))
    fn(ImageDraw.Draw(im))
    return im.resize((fw, fh), Image.Resampling.BOX)


def okcuiskelet():
    R = RENK["okcuiskelet"]
    FW = FH = 132
    HIP = (63, 113 - 32)
    def walk(i, n=8):
        p = 2 * math.pi * i / n
        L = lambda ph: (28 * math.sin(p + ph), max(0, 34 * math.sin(p + ph + 1.4)))
        bob = 1.5 * abs(math.sin(p))
        return lambda d: insan(d, R, (HIP[0], HIP[1] - bob), legs=(L(0), L(math.pi)), lean=3, arms_idle=(15 * math.sin(p + math.pi), 10 * math.sin(p)))
    def attack(i, n=9):
        # raise bow (0-2), draw (3-5), hold (6), release (7-8)
        aim = [20, 5, -8, -10, -10, -10, -10, -10, -6][i]
        draw = [0, 0, 0.1, 0.4, 0.75, 1.0, 1.0, 0.0, 0.0][i]
        stance = ((12, 6), (-14, 10))
        return lambda d: insan(d, R, HIP, legs=stance, lean=-2, aim=aim, draw=draw)
    def die(i, n=7):
        k = i / (n - 1)
        legs = ((10 + 50 * k, 20 * k), (-10 + 40 * k, 30 * k))
        drop = 22 * min(1, k * 1.2)
        return lambda d: insan(d, R, (HIP[0] + 8 * k, HIP[1] + drop), legs=legs, fall=min(1, k * 1.15), arms_idle=(40 * k, 80 * k))
    rows = [(walk, 8), (attack, 9), (die, 7)]
    sheet = Image.new("RGBA", (FW * 9, FH * 3), (0, 0, 0, 0))
    for r, (fn, n) in enumerate(rows):
        for c in range(n):
            sheet.alpha_composite(kare(FW, FH, fn(c)), (c * FW, r * FH))
    return sheet


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet = okcuiskelet()
    sheet.save(f"{OUT}/okcuiskelet.png")
    prev = Image.new("RGBA", sheet.size, (214, 204, 184, 255)); prev.alpha_composite(sheet)
    prev.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST).convert("RGB").save(f"{OUT}/okcuiskelet_onizleme.png")
    print("ok", sheet.size)


if __name__ == "__main__":
    main()
