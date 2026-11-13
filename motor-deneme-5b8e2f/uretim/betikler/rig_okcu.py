"""Side-profile rig for the player archer (okcu) and the wall soldiers (asker), facing right.

Same frame layout as the game: 150x150, one frame per aim angle (-80..80 step 5) per draw level
(okcu: 3 levels, asker: 2), footY 146. The bow geometry copies the old sheet (shoulder position,
grip distance, nock distances), so arrows leave from the same points; grip/shoulder/nock points
for kareler.json are computed here from the rig.
v2: fuller body, cloak folds, shaded hood / great helm, breastplate + gold-trimmed tabard,
bracers and pauldrons, colours close to the old PixelLab art.
Output: D:/AI/araclar/rig/<okcu|asker>.png (33 columns, like the original) + <ad>_noktalar.json
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig_insan import seg, limb, arm_to  # noqa: E402
import rig_insan  # noqa: E402

OUT = "D:/AI/araclar/rig"
FW = FH = 150
CANVAS = 4                     # canvas pixels per frame pixel
ACILAR = list(range(-80, 81, 5))

STIL = {
    "okcu": dict(germe=[0, 0.5, 1], omuz=(80.0, 70.9), tutamak=26.4, nock=[7.7, 19.9, 32.1],
                 hood=(44, 90, 50), hood_d=(26, 58, 32), cloak=(40, 84, 46), cloak_d=(24, 54, 30),
                 tunic=(86, 58, 40), tunic_d=(58, 38, 26), skin=(214, 168, 136), arm=(96, 66, 44), arm_d=(64, 44, 30),
                 pauldron=(150, 156, 166), pants=(52, 44, 42), pants_d=(36, 30, 30), boot=(92, 58, 34),
                 bow=(132, 86, 46), string=(226, 222, 206), quiver=(118, 74, 40), belt=(70, 46, 28), helm=False),
    "asker": dict(kalca=2.5, germe=[0, 1], omuz=(79.7, 68.8), tutamak=25.3, nock=[7.2, 30.1],
                  hood=(156, 162, 174), hood_d=(104, 108, 120), cloak=(110, 24, 30), cloak_d=(80, 16, 22),
                  tunic=(132, 30, 36), tunic_d=(92, 20, 26), skin=(214, 168, 136), arm=(138, 144, 156), arm_d=(96, 100, 112),
                  pauldron=(170, 176, 188), pants=(42, 38, 48), pants_d=(30, 28, 36), boot=(92, 58, 34),
                  bow=(132, 86, 46), string=(226, 222, 206), quiver=(118, 74, 40), belt=(200, 160, 60), helm=True),
}


def koyu(c, f=0.72):
    return tuple(int(v * f) for v in c)


def acik(c, f=1.25):
    return tuple(min(255, int(v * f)) for v in c)


def ciz(d, R, aci, nock_d, k):
    """One frame. k = frame-to-canvas scale. Returns grip, shoulder, nock in frame coords."""
    rig_insan.S = k
    P = rig_insan.P
    sx, sy = R["omuz"]
    hip = (sx - 2, sy + 34 + R.get("kalca", 0))
    shoulder = (sx, sy)
    helm = R["helm"]
    tun, tun_d = R["tunic"], R["tunic_d"]
    # back leg (far)
    kf, ff = limb(hip, -18, 10, 19, 19, 1)
    seg(d, hip, kf, 8.5, R["pants_d"]); seg(d, kf, ff, 7.5, R["pants_d"])
    d.polygon([P(ff[0] - 4, ff[1] - 6), P(ff[0] + 4, ff[1] - 6), P(ff[0] + 8, ff[1] + 2), P(ff[0] - 4, ff[1] + 2)], fill=koyu(R["boot"], 0.8))
    # quiver on the back
    q = (sx - 11, sy + 3)
    d.polygon([P(q[0] - 4, q[1] + 16), P(q[0] + 3, q[1] + 16), P(q[0] + 1, q[1] - 11), P(q[0] - 6, q[1] - 11)], fill=R["quiver"])
    d.line([P(q[0] - 4, q[1] + 4), P(q[0] + 2, q[1] + 4)], fill=koyu(R["quiver"]), width=k)
    for i in range(4):
        d.line([P(q[0] - 5 + i * 1.6, q[1] - 11), P(q[0] - 7 + i * 2, q[1] - 18)], fill=R["string"], width=k)
    # cloak / back panel with folds
    if not helm:
        cl = [P(sx - 13, sy - 6), P(sx + 4, sy - 6), P(sx + 7, hip[1] + 16), P(sx - 6, hip[1] + 20), P(sx - 20, hip[1] + 18), P(sx - 21, sy + 6)]
        d.polygon(cl, fill=R["cloak"])
        for x in (-17, -12, -6):
            d.line([P(sx + x + 1, sy + 2), P(sx + x - 1, hip[1] + 18)], fill=R["cloak_d"], width=k)
        d.line([P(sx - 21, sy + 6), P(sx - 20, hip[1] + 18)], fill=acik(R["cloak"], 1.2), width=k)
    else:
        d.polygon([P(sx - 12, sy - 2), P(sx - 4, sy - 2), P(sx - 6, hip[1] + 14), P(sx - 14, hip[1] + 12)], fill=R["cloak_d"])
    # torso
    if helm:
        d.polygon([P(sx - 11, sy - 4), P(sx + 10, sy - 4), P(sx + 10, sy + 6), P(sx - 11, sy + 6)], fill=R["arm"])        # breastplate
        d.line([P(sx - 9, sy - 2), P(sx + 8, sy - 2)], fill=acik(R["arm"], 1.25), width=k)
        d.polygon([P(sx - 10, sy + 2), P(sx + 9, sy + 2), P(hip[0] + 12, hip[1] + 14), P(hip[0] - 11, hip[1] + 14)], fill=tun)  # tabard
        d.polygon([P(sx + 3, sy + 2), P(sx + 9, sy + 2), P(hip[0] + 12, hip[1] + 14), P(hip[0] + 5, hip[1] + 14)], fill=tun_d)
        for x in (-5, 0):
            d.line([P(sx + x, sy + 6), P(hip[0] + x - 1, hip[1] + 13)], fill=tun_d, width=k)
        for a_, b_ in [((sx - 10, sy + 2), (hip[0] - 11, hip[1] + 14)), ((sx + 9, sy + 2), (hip[0] + 12, hip[1] + 14)),
                       ((hip[0] - 11, hip[1] + 14), (hip[0] + 12, hip[1] + 14))]:
            d.line([P(*a_), P(*b_)], fill=R["belt"], width=k)                                   # gold trim
        d.line([P(sx - 1, sy + 8), P(sx - 1, sy + 20)], fill=R["belt"], width=2 * k)             # cross
        d.line([P(sx - 6, sy + 12), P(sx + 4, sy + 12)], fill=R["belt"], width=2 * k)
    else:
        d.polygon([P(sx - 12, sy - 3), P(sx + 10, sy - 3), P(hip[0] + 12, hip[1] + 4), P(hip[0] - 11, hip[1] + 4)], fill=tun)
        d.polygon([P(sx + 3, sy - 3), P(sx + 10, sy - 3), P(hip[0] + 12, hip[1] + 4), P(hip[0] + 5, hip[1] + 4)], fill=tun_d)
        for x in (-6, -1):
            d.line([P(sx + x, sy + 4), P(hip[0] + x, hip[1] + 2)], fill=tun_d, width=k)
        d.line([P(sx + 2, sy - 2), P(sx - 2, sy + 10)], fill=koyu(tun, 0.6), width=k)
    # belt, buckle, pouch
    by = hip[1] - 2
    d.line([P(hip[0] - 11, by), P(hip[0] + 12, by)], fill=(70, 46, 28), width=3 * k)
    d.rectangle([P(hip[0] + 3, by - 2), P(hip[0] + 6, by + 1)], fill=(200, 170, 70))
    d.rounded_rectangle([P(hip[0] - 8, by), P(hip[0] - 3, by + 6)], radius=k, fill=koyu(R["quiver"], 0.85))
    # near leg
    kn, fn = limb(hip, 16, -8, 19, 19, 1)
    seg(d, hip, kn, 9, R["pants"]); seg(d, kn, fn, 8, R["pants"])
    d.ellipse([P(kn[0] - 3.5, kn[1] - 3), P(kn[0] + 3.5, kn[1] + 3)], fill=koyu(R["pants"], 0.85))
    d.polygon([P(fn[0] - 5, fn[1] - 8), P(fn[0] + 5, fn[1] - 8), P(fn[0] + 9, fn[1] + 2), P(fn[0] - 5, fn[1] + 2)], fill=R["boot"])
    d.line([P(fn[0] - 5, fn[1] - 7), P(fn[0] + 5, fn[1] - 7)], fill=acik(R["boot"], 1.3), width=2 * k)
    # head
    hx, hy = sx + 2, sy - 14
    if helm:
        d.rounded_rectangle([P(hx - 9, hy - 11), P(hx + 9, hy + 9)], radius=4 * k, fill=R["hood"])
        d.chord([P(hx - 9, hy - 15), P(hx + 9, hy - 3)], 180, 360, fill=R["hood"])
        d.polygon([P(hx + 3, hy - 11), P(hx + 9, hy - 9), P(hx + 9, hy + 9), P(hx + 3, hy + 9)], fill=R["hood_d"])
        d.line([P(hx - 7, hy - 9), P(hx - 7, hy + 6)], fill=acik(R["hood"], 1.2), width=k)
        d.line([P(hx + 1, hy - 2), P(hx + 9, hy - 2)], fill=(24, 24, 30), width=2 * k)          # visor slit
        for i in range(3):
            d.point(P(hx + 5, hy + 2 + i * 2), fill=(30, 30, 36))                                 # breathing holes
        d.line([P(hx, hy - 14), P(hx, hy + 9)], fill=R["hood_d"], width=k)
        d.rectangle([P(hx - 7, hy + 9), P(hx + 7, hy + 12)], fill=koyu(R["hood"], 0.85))          # gorget
    else:
        d.ellipse([P(hx - 11, hy - 12), P(hx + 9, hy + 10)], fill=R["hood"])
        d.polygon([P(hx - 2, hy - 13), P(hx + 6, hy - 11), P(hx - 2, hy - 7)], fill=R["hood"])
        d.ellipse([P(hx + 1, hy - 5), P(hx + 9, hy + 6)], fill=R["skin"])                      # face in profile
        d.polygon([P(hx + 8, hy - 1), P(hx + 11, hy + 2), P(hx + 8, hy + 3)], fill=R["skin"])  # nose
        d.ellipse([P(hx + 1, hy - 5), P(hx + 4, hy + 6)], fill=koyu(R["skin"], 0.7))
        d.point(P(hx + 6, hy - 1), fill=(30, 24, 20))
        d.arc([P(hx - 11, hy - 12), P(hx + 9, hy + 10)], 120, 300, fill=R["hood_d"], width=2 * k)
        d.polygon([P(hx - 11, hy - 2), P(hx - 16, hy + 10), P(hx - 3, hy + 9)], fill=R["hood_d"])
    # bow + arms (same geometry as v1, so arrow points stay)
    a = math.radians(aci)
    dx, dy = math.cos(a), math.sin(a)
    grip = (sx + dx * R["tutamak"], sy + dy * R["tutamak"])
    nock = (grip[0] - dx * nock_d, grip[1] - dy * nock_d)
    el2, h2 = arm_to(shoulder, nock, 14, 14, bend=1)
    seg(d, shoulder, el2, 6, koyu(R["arm"], 0.8)); seg(d, el2, h2, 5.2, koyu(R["arm"], 0.8))
    d.ellipse([P(h2[0] - 2.8, h2[1] - 2.8), P(h2[0] + 2.8, h2[1] + 2.8)], fill=koyu(R["arm_d"], 0.9))
    px, py = -dy, dx
    L = 24
    top, bot = (grip[0] + px * L, grip[1] + py * L), (grip[0] - px * L, grip[1] - py * L)
    bend = 4 + nock_d * 0.12
    mid = (grip[0] + dx * bend, grip[1] + dy * bend)
    d.line([P(*top), P((top[0] + mid[0]) / 2 + dx * 2, (top[1] + mid[1]) / 2 + dy * 2), P(*mid),
            P((bot[0] + mid[0]) / 2 + dx * 2, (bot[1] + mid[1]) / 2 + dy * 2), P(*bot)], fill=R["bow"], width=int(3.4 * k))
    d.line([P(*top), P(*nock), P(*bot)], fill=R["string"], width=k)
    el1, h1 = arm_to(shoulder, grip, 14, 14, bend=-1)
    seg(d, shoulder, el1, 6.4, R["arm"]); seg(d, el1, h1, 5.6, R["arm"])
    vm = ((el1[0] + h1[0]) / 2, (el1[1] + h1[1]) / 2)
    d.ellipse([P(vm[0] - 3.2, vm[1] - 3.2), P(vm[0] + 3.2, vm[1] + 3.2)], fill=R["arm_d"])      # bracer
    d.ellipse([P(h1[0] - 3, h1[1] - 3), P(h1[0] + 3, h1[1] + 3)], fill=koyu(R["arm_d"], 0.9))  # glove
    d.ellipse([P(sx - 8, sy - 6), P(sx + 7, sy + 6)], fill=R["pauldron"])                       # pauldron
    d.ellipse([P(sx - 6, sy + 1), P(sx + 6, sy + 9)], fill=koyu(R["pauldron"], 0.8))
    d.arc([P(sx - 8, sy - 6), P(sx + 7, sy + 6)], 190, 280, fill=acik(R["pauldron"], 1.2), width=k)
    return grip, shoulder, nock


def sayfa(ad):
    R = STIL[ad]
    rows = len(R["germe"])
    sheet = Image.new("RGBA", (FW * len(ACILAR), FH * rows), (0, 0, 0, 0))
    noktalar = []
    for i, aci in enumerate(ACILAR):
        e = {"a": aci}
        for g in range(rows):
            im = Image.new("RGBA", (FW * CANVAS, FH * CANVAS), (0, 0, 0, 0))
            grip, sh, nk = ciz(ImageDraw.Draw(im), R, aci, R["nock"][g], CANVAS)
            sheet.alpha_composite(im.resize((FW, FH), Image.Resampling.BOX), (i * FW, g * FH))
            e["grip"] = {"x": round(grip[0], 1), "y": round(grip[1], 1)}
            e["shoulder"] = {"x": round(sh[0], 1), "y": round(sh[1], 1)}
            e[f"nock{g}"] = {"x": round(nk[0], 1), "y": round(nk[1], 1)}
        noktalar.append(e)
    return sheet, noktalar


def main():
    os.makedirs(OUT, exist_ok=True)
    for ad in ("okcu", "asker"):
        sheet, noktalar = sayfa(ad)
        sheet.save(f"{OUT}/{ad}.png")
        json.dump(noktalar, open(f"{OUT}/{ad}_noktalar.json", "w"), indent=0)
        prev = Image.new("RGBA", (FW * 6, FH * len(STIL[ad]["germe"])), (214, 204, 184, 255))
        for j, i in enumerate([0, 8, 12, 16, 24, 32]):
            for g in range(len(STIL[ad]["germe"])):
                prev.alpha_composite(sheet.crop((i * FW, g * FH, (i + 1) * FW, (g + 1) * FH)), (j * FW, g * FH))
        prev.resize((prev.width * 2, prev.height * 2), Image.Resampling.NEAREST).convert("RGB").save(f"{OUT}/{ad}_onizleme.png")
        a = sheet.getchannel("A")
        print(ad, sheet.size, "ayak", a.crop((0, 0, a.width, FH)).getbbox()[3] - 1, noktalar[16]["grip"])


if __name__ == "__main__":
    main()
