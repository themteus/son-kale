# Yıkık varyantların siluetinde dış koyu çizginin hemen içinde kalan açık gri hâleyi
# (üretimden kalan arka plan artığı) koyu kontur rengine çevirir. Kar (çok açık) korunur.
import sys
import numpy as np
from PIL import Image
for yol in sys.argv[1:]:
    a = np.array(Image.open(yol).convert('RGBA')).astype(int)
    op = a[..., 3] > 0
    def halka(m): return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    h1 = halka(op); ic = op & ~h1
    toplam = 0
    koyu = np.median(a[h1][:, :3], axis=0)
    for _ in range(2):                       # 2. ve 3. halka
        h = halka(ic)
        px = a[..., :3]; lum = px.mean(2); sat = px.max(2) - px.min(2)
        gri = h & (lum > 110) & (lum < 212) & (sat < 45)
        a[gri, :3] = koyu
        toplam += int(gri.sum()); ic = ic & ~h
    Image.fromarray(a.astype(np.uint8)).save(yol)
    print(yol, toplam)
