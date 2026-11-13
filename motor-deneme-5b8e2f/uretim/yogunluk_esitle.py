# Savaş birimlerinin piksel yoğunluğunu kale/manzarayla eşitler (ekranda 1 sanat pikseli = 2 px).
# Her kare kendi köşesinden BxB (varsayılan 4: olcek 0.5 ile ekranda 2 px) bloklara bölünür; blok rengi en sık görülen opak renk
# (eşitlikte en koyu: kontur korunur), alfa çoğunlukla. blok aynı renkle doldurulur:
# şerit boyutu, kare yerleri, footY/centerX değişmez.
import sys
import numpy as np
from PIL import Image
from collections import Counter
def isle(giris, cikis, fw, fh, B=4):
    a = np.array(Image.open(giris).convert('RGBA'))
    H, W = a.shape[:2]; out = np.zeros_like(a)
    for fy in range(0, H - fh + 1, fh):
        for fx in range(0, W - fw + 1, fw):
            for y in range(fy, fy + fh, B):
                for x in range(fx, fx + fw, B):
                    blk = a[y:min(y+B, fy+fh), x:min(x+B, fx+fw)].reshape(-1, 4)
                    op = blk[blk[:, 3] > 127]
                    if len(op) * 3 < len(blk) or len(op) == 0:   # ince çizgiler (asa, yay) kaybolmasın: 1/3 dolu yeter
                        continue
                    c = Counter(map(tuple, op[:, :3])).most_common()
                    en = c[0][1]
                    adaylar = [k for k, n in c if n == en]
                    renk = min(adaylar, key=lambda k: sum(int(v) for v in k))
                    out[y:min(y+B, fy+fh), x:min(x+B, fx+fw)] = (*renk, 255)
    # Kontur: siluet kenarındaki açık sanat pikselleri karenin en koyu konturuyla
    for fy in range(0, H - fh + 1, fh):
        for fx in range(0, W - fw + 1, fw):
            fr = out[fy:fy+fh, fx:fx+fw]
            g = fr[::B, ::B]
            op = g[..., 3] > 0
            if not op.any(): continue
            lum = g[..., :3].astype(int).sum(2)
            koyu = g[op][np.argmin(lum[op])][:3]
            pad = np.pad(op, 1)
            kenar = op & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
            acik = kenar & (lum > 3 * 70)
            for gy, gx in zip(*np.where(acik)):
                fr[gy*B:(gy+1)*B, gx*B:(gx+1)*B, :3] = koyu
    # Göz gibi küçük doygun vurgular: orijinal blokta doygun piksel varsa onu koru
    Image.fromarray(out).save(cikis)
if __name__ == '__main__':
    isle(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]) if len(sys.argv) > 5 else 4)
