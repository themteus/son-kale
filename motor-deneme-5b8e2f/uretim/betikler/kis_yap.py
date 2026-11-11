"""Winter versions of the 1x background / front walls from the finished summer images.

summer (arka_desen.png / on_desen.png) -> code-painted snow (kar.py: ground, wall tops, merlons,
tower caps, 1 px cold outline under the snow) -> winter palette (old art + buildings + snowy
building variants, no dithering) -> small bright reds put back exactly.
No SDXL pass: at denoise 0.25 it changed almost nothing and softened the 1 px stone pattern.

  python kis_yap.py on arka
Output: D:/AI/ComfyUI/output/son-kale-v2/arka_hd/<ad>_karli.png
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arka_hd as A  # noqa: E402
import kar  # noqa: E402

HD = "D:/AI/ComfyUI/output/son-kale-v2/arka_hd"


def kis(ad):
    yaz = Image.open(f"{HD}/{ad}_desen.png").convert("RGBA")
    a = np.asarray(yaz)
    alfa = a[..., 3] > 0
    if ad == "on":
        k = np.asarray(kar.karla(yaz.convert("RGB"), alfa))
    else:  # mirror-pad so the mask cleanup does not leave the outer pixels unsnowed
        P = 12
        rgb = np.pad(a[..., :3], ((P, P), (P, P), (0, 0)), mode="reflect")
        k = np.asarray(kar.karla(Image.fromarray(rgb), None))[P:-P, P:-P]
    q = np.asarray(A.kuantala(Image.fromarray(k), A.palet(ad, kis=True))).copy()
    f = a[..., :3].astype(np.float32)
    kir = (f[..., 0] > 100) & (f[..., 0] > f[..., 1] * 1.6) & (f[..., 0] > f[..., 2] * 1.6)
    lab, n = ndimage.label(kir)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        kir &= (boy < 1500)[lab]
    q[kir] = a[kir, :3]
    if ad == "on":
        out = Image.fromarray(np.dstack([q, a[..., 3]]).astype(np.uint8), "RGBA")
    else:
        out = Image.fromarray(q.astype(np.uint8))
    p = f"{HD}/{ad}_karli.png"
    out.save(p)
    print(p)


if __name__ == "__main__":
    for ad in sys.argv[1:]:
        kis(ad)
