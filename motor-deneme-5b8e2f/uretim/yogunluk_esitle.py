# Savaş birimlerinin piksel yoğunluğunu kale/manzarayla eşitler (olcek 0.5 ile ekranda 2 px).
# Her kare kendi köşesinden BxB (varsayılan 4) bloklara bölünür.
#  - Alfa: blok en az 1/3 doluysa opak (ince asa/yay kaybolmasın).
#  - Renk: düz bloklarda en sık opak renk. Bloğun içinde güçlü parlaklık farkı varsa
#    (silah ucu, göz, kenar ışığı) en sık 3 renkten komşu blokların ortalamasına göre
#    en çok ayrışanı seçilir: vurgu ve ince ayrıntı korunur.
#  - Kontur: siluet kenarındaki açık bloklar karenin en koyu rengine çekilir.
# Şerit boyutu, kare yerleri, footY/centerX değişmez.
import sys
import numpy as np
from PIL import Image
from collections import Counter

def lum(c): return 0.3 * int(c[0]) + 0.59 * int(c[1]) + 0.11 * int(c[2])

def kare_isle(fr, B):
    fh, fw = fr.shape[:2]
    gh, gw = (fh + B - 1) // B, (fw + B - 1) // B
    op = np.zeros((gh, gw), bool); ort = np.zeros((gh, gw)); bloklar = {}
    for gy in range(gh):
        for gx in range(gw):
            blk = fr[gy*B:(gy+1)*B, gx*B:(gx+1)*B].reshape(-1, 4)
            o = blk[blk[:, 3] > 127]
            if len(o) == 0 or len(o) * 3 < len(blk): continue
            op[gy, gx] = True; bloklar[(gy, gx)] = o
            ort[gy, gx] = np.mean([lum(c) for c in o[:, :3]])
    out = np.zeros_like(fr)
    for (gy, gx), o in bloklar.items():
        sayim = Counter(map(tuple, o[:, :3])).most_common()
        ls = [lum(c) for c in o[:, :3]]
        if max(ls) - min(ls) > 60 and len(sayim) > 1:
            y0, y1, x0, x1 = max(0, gy-1), min(gh, gy+2), max(0, gx-1), min(gw, gx+2)
            m = op[y0:y1, x0:x1].copy(); m[gy-y0, gx-x0] = False
            komsu = ort[y0:y1, x0:x1][m].mean() if m.any() else ort[gy, gx]
            aday = [k for k, n in sayim[:3] if n >= 2] or [sayim[0][0]]
            renk = max(aday, key=lambda k: abs(lum(k) - komsu))
        else:
            en = sayim[0][1]
            renk = min([k for k, n in sayim if n == en], key=lambda k: lum(k))
        out[gy*B:(gy+1)*B, gx*B:(gx+1)*B] = (*renk, 255)
    # kontur
    if op.any():
        g = out[::B, ::B]
        L = g[..., :3].astype(int).sum(2)
        koyu = g[op][np.argmin(L[op])][:3]
        pad = np.pad(op, 1)
        kenar = op & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
        for gy, gx in zip(*np.where(kenar & (L > 210))):
            out[gy*B:(gy+1)*B, gx*B:(gx+1)*B, :3] = koyu
    out[:fh, :fw, 3] = np.where(out[:fh, :fw, 3] > 0, 255, 0)
    return out[:fh, :fw]

def isle(giris, cikis, fw, fh, B=4):
    a = np.array(Image.open(giris).convert('RGBA'))
    H, W = a.shape[:2]; out = np.zeros_like(a)
    for fy in range(0, H - fh + 1, fh):
        for fx in range(0, W - fw + 1, fw):
            out[fy:fy+fh, fx:fx+fw] = kare_isle(a[fy:fy+fh, fx:fx+fw], B)
    Image.fromarray(out).save(cikis)

if __name__ == '__main__':
    isle(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]) if len(sys.argv) > 5 else 4)
