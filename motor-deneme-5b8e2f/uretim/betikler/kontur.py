"""PixelLab-style finishing for a 2x sprite sheet: a bold near-black outer outline
(2px at 2x = 1px of the old art) and a little extra contrast.

  python kontur.py <in.png> <out.png> [--kare 300] [--kontrast 1.12]
Works per frame so the outline never bleeds into a neighbouring frame.
"""
import argparse

import numpy as np
from PIL import Image
from scipy import ndimage

KONTUR = (22, 17, 20)


def isle(im, kalinlik=2, kontrast=1.12):
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    solid = a[..., 3] > 0
    rgb = a[..., :3]
    m = rgb[solid].mean(axis=0) if solid.any() else np.zeros(3)
    rgb = (rgb - m) * kontrast + m
    out = np.dstack([np.clip(rgb, 0, 255), a[..., 3]]).astype(np.uint8)
    ring = ndimage.binary_dilation(solid, structure=np.ones((3, 3)), iterations=kalinlik) & ~solid
    out[ring] = (*KONTUR, 255)
    return Image.fromarray(out, "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("girdi")
    ap.add_argument("cikti")
    ap.add_argument("--kare", type=int, default=300)
    ap.add_argument("--kalinlik", type=int, default=2)
    ap.add_argument("--kontrast", type=float, default=1.12)
    a = ap.parse_args()
    sheet = Image.open(a.girdi).convert("RGBA")
    out = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    for y in range(0, sheet.height, a.kare):
        for x in range(0, sheet.width, a.kare):
            f = sheet.crop((x, y, x + a.kare, y + a.kare))
            out.paste(isle(f, a.kalinlik, a.kontrast), (x, y))
    out.save(a.cikti)
    print(a.cikti)


if __name__ == "__main__":
    main()
