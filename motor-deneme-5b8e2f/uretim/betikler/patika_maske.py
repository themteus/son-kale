"""Cut the path layer (assets/kale/sus/ic2/zemin.png) where it runs over props baked into the
background (hay bales and barrels, market stalls, well, cart, torch): inside the protected boxes of
arka_hd.py, path pixels lying on a non-ground background pixel become transparent.

  python patika_maske.py
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arka_hd as A  # noqa: E402

KALE = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"
ORJ = "D:/AI/araclar/orijinal/kale"


def main():
    p = f"{KALE}/sus/ic2/zemin.png"
    yedek = f"{ORJ}/ic2_zemin.png"
    if not os.path.exists(yedek):
        Image.open(p).save(yedek)
    z = np.asarray(Image.open(yedek).convert("RGBA")).copy()
    arka = np.asarray(Image.open(f"{KALE}/arka.png").convert("RGB")).astype(np.float32)
    H, W = arka.shape[:2]
    r, g, b = arka[..., 0], arka[..., 1], arka[..., 2]
    lum = arka @ [0.299, 0.587, 0.114]
    mo = ndimage.uniform_filter(lum, 5)
    sd = np.sqrt(np.maximum(ndimage.uniform_filter(lum ** 2, 5) - mo ** 2, 0))
    zemin = ((g > r * 0.98) & (g > b * 1.1)) | ((r > g * 1.2) & (g > b) & (sd < 16) & (lum < 150))
    nesne = ndimage.binary_closing(~zemin, np.ones((3, 3)))
    nesne = ndimage.binary_opening(nesne, np.ones((2, 2)))
    kutu = np.zeros((H, W), bool)
    for kutu_ in A.KORU["arka"].values():
        (x0, y0, x1, y1) = kutu_[0] if len(kutu_) == 3 else kutu_
        kutu[int(y0 * 1.5):int(y1 * 1.5), int(x0 * 1.5):int(x1 * 1.5)] = True
    kes = kutu & nesne & (z[..., 3] > 0)
    z[kes, 3] = 0
    Image.fromarray(z, "RGBA").save(p)
    print(p, int(kes.sum()), "px")


if __name__ == "__main__":
    main()
