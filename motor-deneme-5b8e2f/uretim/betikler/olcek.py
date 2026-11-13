"""Same on-screen pixel size for every enemy (target olcek 0.5).

Each enemy sheet is drawn at some density and scaled on screen by kareler.json olcek (0.42-0.93),
so one art pixel shows as 0.42-0.93 screen px. Here every sheet is rebuilt at
F = 2 * olcek / 0.5 times the original 1x frame, so with olcek 0.5 the on-screen size stays the same.
Detail comes from the raw 1024 px SDXL redraws birim.py already made (ComfyUI/output/son-kale-v2/
<unit>/ham), BOX-downscaled from the same box -> real new pixels, no blocky upscale. Colours are
quantized to the current sheet's palette, the silhouette is the current sheet's (smoothly resized),
baked die fades are kept. Wide sheets are re-flowed into fewer columns (Phaser numbers frames in
reading order, so row * columns + i still works).

  python olcek.py deneme zombi        -> D:/AI/son-kale-cikti/olcek/<unit>.png comparisons
  python olcek.py tam [units...]      -> repo sheets + kareler.json (old ones kept in assets/gorsel/eski_olcek/)
"""
import glob
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import birim as B  # noqa: E402

G = f"{B.REPO}/assets/gorsel"
CIKTI = "D:/AI/son-kale-cikti/olcek"
HEDEF = 0.5
MAKS = 4096
DUSMAN = ["zombi", "kosucu", "dev", "iskelet", "yarasa", "kalkanli", "tirmanici", "patlayan", "sifaci",
          "okcuiskelet", "kurt", "kalkanlidev", "patron"]
ETIKET = {"kurt": ["rig3_s22", "v1_s22"], "okcuiskelet": []}   # okcuiskelet: its rig sheet is gone
RIG = {"kurt": "D:/AI/araclar/rig/kurt.png", "okcuiskelet": "D:/AI/araclar/rig/okcuiskelet.png"}


def mevcut(unit):
    """The sheet as it was before this script (kept in eski_olcek/ after the first run)."""
    if os.path.exists(f"{G}/eski_olcek/{unit}.png"):
        J = json.load(open(f"{G}/eski_olcek/kareler.json", encoding="utf-8"))
        return J["birimler"][unit], Image.open(f"{G}/eski_olcek/{unit}.png").convert("RGBA")
    J = json.load(open(f"{G}/kareler.json", encoding="utf-8"))
    return J["birimler"][unit], Image.open(f"{G}/{unit}.png").convert("RGBA")


def kare(sheet, K, idx, sutun):
    fw, fh = K["fw"], K["fh"]
    r, c = divmod(idx, sutun)
    return sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))


def ham(unit, etiket, idx):
    d = sorted(glob.glob(f"{B.OUT}/{unit}/ham/{etiket}_{idx:02d}_*.png"))
    return d[-1] if d else None


YER = {}


def hizala(unit, idx, row, col, g, cur, L):
    """Placement of the frame inside the raw 1024 image: the bbox placement or the old fixed one
    (zombi was drawn with it), plus a small search; chosen once per unit on its first frame."""
    if unit in YER:
        mod, dx, dy = YER[unit]
    else:
        ca = np.asarray(cur)
        m = ca[..., 3] > 200
        en = None
        for mod in ("bbox", "eski"):
            if mod == "eski":
                B.ESKI_YERLESIM.add(unit)
            else:
                B.ESKI_YERLESIM.discard(unit)
            _, (ox, oy, k) = B.make_input(unit, idx, row, col)
            for dy in range(-12, 13, 2):
                for dx in range(-12, 13, 2):
                    b = np.asarray(g.crop((ox + dx, oy + dy, ox + dx + L["fw"] * k, oy + dy + L["fh"] * k))
                                   .resize(cur.size, Image.Resampling.BOX)).astype(int)
                    h = np.abs(b[m] - ca[m][:, :3]).mean()
                    if en is None or h < en[0]:
                        en = (h, mod, dx, dy)
        _, mod, dx, dy = en
        YER[unit] = (mod, dx, dy)
        print(unit, "yerlesim", mod, dx, dy, round(en[0], 1), flush=True)
    if mod == "eski":
        B.ESKI_YERLESIM.add(unit)
    else:
        B.ESKI_YERLESIM.discard(unit)
    _, (ox, oy, k) = B.make_input(unit, idx, row, col)
    return ox + dx, oy + dy, k


def palet_of(sheet):
    a = np.asarray(sheet)
    px = a[a[..., 3] > 200][:, :3]
    renk = np.unique(px, axis=0)
    pal = Image.new("P", (1, 1))
    flat = renk[:256].reshape(-1).tolist()
    pal.putpalette(flat + flat[:3] * (256 - len(renk[:256])))
    return pal, len(renk)


def kur(unit, etiket=None, kaydet=False):
    K, sheet = mevcut(unit)
    if unit in RIG and os.path.exists(RIG[unit]):
        B.KAYNAK[unit] = RIG[unit]
    L = B.layout(unit)                       # 1x original layout (frames, fw, fh)
    s = K["olcek"] / HEDEF                   # resample factor of the current 2x sheet
    F = (K["fw"] / L["fw"]) * s              # new size relative to the 1x frame
    nfw, nfh = round(L["fw"] * F), round(L["fh"] * F)
    sutun0 = max(r["frames"] for r in K["rows"].values())
    sutun = min(sutun0, MAKS // nfw)
    satir_say = max(r["row"] for r in K["rows"].values()) + 1
    toplam = satir_say * sutun0
    pal, nrenk = palet_of(sheet)
    etiketler = [etiket] if etiket else ETIKET.get(unit, ["v1_s22"])
    hata = []
    yedek_say = [0]
    KARE = {}
    for (idx, row, col, name) in B.frames_of(unit):
        L_idx = row * sutun0 + col
        cur = kare(sheet, K, L_idx, sutun0)            # current 2x frame (layout of the game sheet)
        p = None
        for e in (etiketler if s > 1.0 else []):      # shrinking: the current sheet has all the detail
            p = ham(unit, e, idx)
            if p:
                break
        if p:
            g = Image.open(p).convert("RGB")
            ox, oy, k = hizala(unit, idx, row, col, g, cur, L)
            box = g.crop((ox, oy, ox + L["fw"] * k, oy + L["fh"] * k)).resize((nfw, nfh), Image.Resampling.BOX)
            cur_a0 = np.asarray(cur)
            m0 = cur_a0[..., 3] > 0
            chk0 = np.asarray(box.resize(cur.size, Image.Resampling.BOX)).astype(int)
            h0 = np.abs(chk0[m0] - cur_a0[m0][:, :3]).mean() if m0.any() else 0
            if h0 > 32:                          # this frame was not made from that raw drawing
                p = None
                yedek_say[0] += 1
        if not p:                                      # no raw redraw: smooth resample of the sheet
            box = Image.fromarray(np.asarray(cur)[..., :3]).resize((nfw, nfh), Image.Resampling.BOX if s < 1 else Image.Resampling.LANCZOS)
        # silhouette and fades from the current frame
        ca = np.asarray(cur.getchannel("A").resize((nfw, nfh), Image.Resampling.BOX))
        tam = ca >= 128
        rgb = np.asarray(box.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")).copy()
        # outline: where the current frame has a dark silhouette edge, keep it dark
        cur_a = np.asarray(cur)
        kenar_eski = (cur_a[..., 3] > 200) & ~ndimage.binary_erosion(cur_a[..., 3] > 200)
        koyu_kenar = kenar_eski.any() and (cur_a[kenar_eski][:, :3].astype(int).sum(1) < 150).mean() > 0.6
        if koyu_kenar:
            e = tam & ~ndimage.binary_erosion(tam)
            koyu = cur_a[kenar_eski][:, :3].astype(int)
            rgb[e] = np.median(koyu[koyu.sum(1) < 150], 0).astype(np.uint8)
        oa = cur_a[..., 3]
        seviye = int(np.median(oa[oa > 0])) if (oa > 0).any() else 255
        alfa = np.where(tam, min(seviye, 255) if seviye < 250 else 255, 0).astype(np.uint8)
        fr = Image.fromarray(np.dstack([rgb, alfa]), "RGBA")
        KARE[L_idx] = fr
        if p:
            # how close the raw source is to the current art (picks the right tag for rig units)
            chk = np.asarray(box.resize(cur.size, Image.Resampling.BOX)).astype(int)
            m = cur_a[..., 3] > 200
            hata.append(np.abs(chk[m] - cur_a[m][:, :3]).mean() if m.any() else 0)
    if yedek_say[0] > 0.3 * max(1, len(B.frames_of(unit))) and not etiket:
        # many frames were made from another recipe: one source for the whole unit (no style flicker)
        ETIKET[unit] = []
        YER.pop(unit, None)
        return kur(unit, etiket=None, kaydet=kaydet)
    # trim the empty margin shared by all frames (+2 px), so big sheets stay within 4096 px
    kutular = [f.getchannel("A").getbbox() for f in KARE.values()]
    kutular = [k for k in kutular if k]
    x0 = max(0, min(k[0] for k in kutular) - 2); y0 = max(0, min(k[1] for k in kutular) - 2)
    x1 = min(nfw, max(k[2] for k in kutular) + 2); y1 = min(nfh, max(k[3] for k in kutular) + 2)
    footY, centerX = round(K["footY"] * s) - y0, round(K["centerX"] * s) - x0
    nfw, nfh = x1 - x0, y1 - y0
    sutun = sutun0
    while sutun > 1 and (sutun * nfw > MAKS or -(-toplam // sutun) * nfh > MAKS):
        if sutun * nfw <= MAKS and -(-toplam // (sutun + 1)) * nfh <= MAKS and (sutun + 1) * nfw <= MAKS:
            sutun += 1; break
        sutun -= 1
    if -(-toplam // sutun) * nfh > MAKS:          # too tall: use the widest layout that fits
        sutun = MAKS // nfw
    out = Image.new("RGBA", (sutun * nfw, -(-toplam // sutun) * nfh), (0, 0, 0, 0))
    for L_idx, fr in KARE.items():
        r, c = divmod(L_idx, sutun)
        out.paste(fr.crop((x0, y0, x1, y1)), (c * nfw, r * nfh))
    yeni = dict(K)
    yeni.update(fw=nfw, fh=nfh, footY=footY, centerX=centerX, olcek=HEDEF)
    bilgi = dict(unit=unit, s=round(s, 3), fw=nfw, fh=nfh, boyut=out.size, sutun=sutun, renk=nrenk, hata=round(float(np.mean(hata)) if hata else -1, 1),
                 ham=len(hata), yedek=yedek_say[0], etiket=etiketler)
    return out, yeni, bilgi, sheet, K


def karsilastir(unit, out, yeni, sheet, K, yol):
    """Old vs new at game size (both scaled by their olcek), 3 frames, x2 for viewing."""
    sutun0 = max(r["frames"] for r in K["rows"].values())
    sutun = out.width // yeni["fw"]
    secim = [0, K["rows"]["attack"]["row"] * sutun0 + 2, K["rows"]["die"]["row"] * sutun0 + 3]
    parcalar = []
    for L_idx in secim:
        a = kare(sheet, K, L_idx, sutun0)
        a = a.resize((round(a.width * K["olcek"]), round(a.height * K["olcek"])), Image.Resampling.NEAREST)
        r, c = divmod(L_idx, sutun)
        b = out.crop((c * yeni["fw"], r * yeni["fh"], (c + 1) * yeni["fw"], (r + 1) * yeni["fh"]))
        b = b.resize((round(b.width * HEDEF), round(b.height * HEDEF)), Image.Resampling.NEAREST)
        parcalar += [a, b]
    W = sum(p.width + 6 for p in parcalar); H = max(p.height for p in parcalar)
    S = Image.new("RGBA", (W, H), (150, 140, 120, 255)); x = 0
    for p in parcalar:
        S.alpha_composite(p, (x, H - p.height)); x += p.width + 6
    S.resize((S.width * 3, S.height * 3), Image.Resampling.NEAREST).save(yol)


if __name__ == "__main__":
    mod, units = sys.argv[1], sys.argv[2:] or DUSMAN
    os.makedirs(CIKTI, exist_ok=True)
    J = json.load(open(f"{G}/kareler.json", encoding="utf-8"))
    for u in units:
        out, yeni, bilgi, sheet, K = kur(u)
        print(bilgi, flush=True)
        karsilastir(u, out, yeni, sheet, K, f"{CIKTI}/{u}.png")
        if mod == "tam":
            os.makedirs(f"{G}/eski_olcek", exist_ok=True)
            if not os.path.exists(f"{G}/eski_olcek/{u}.png"):
                shutil.copy(f"{G}/{u}.png", f"{G}/eski_olcek/{u}.png")
            out.save(f"{G}/{u}.png")
            J["birimler"][u] = yeni
    if mod == "tam":
        if not os.path.exists(f"{G}/eski_olcek/kareler.json"):
            shutil.copy(f"{G}/kareler.json", f"{G}/eski_olcek/kareler.json")
        json.dump(J, open(f"{G}/kareler.json", "w", encoding="utf-8"), ensure_ascii=False)
