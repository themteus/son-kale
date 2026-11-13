# Kış yıkık görsellerinde bina dibindeki sıcak turuncu toprak/kor lekelerini soğutur
# (alt %40'taki doygun turuncu pikseller: doygunluk düşer, hafif mavi-gri).
import sys, colorsys
import numpy as np
from PIL import Image
for yol in sys.argv[1:]:
    a = np.array(Image.open(yol).convert('RGBA')).astype(float)
    H = a.shape[0]; n = 0
    for y in range(int(H * 0.6), H):
        for x in range(a.shape[1]):
            r, g, b, al = a[y, x]
            if al == 0: continue
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            if 0.03 < h < 0.15 and s > 0.45 and v > 0.3:
                l = (r + g + b) / 3
                a[y, x, :3] = np.clip([l + (r-l)*0.3 - 4, l + (g-l)*0.3, l + (b-l)*0.3 + 8], 0, 255); n += 1
    Image.fromarray(a.astype(np.uint8)).save(yol); print(yol, n)
