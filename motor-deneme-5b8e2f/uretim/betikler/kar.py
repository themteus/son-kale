"""Code-painted snow for the 1x inner-castle background (input for the winter redraw).

Ground (grass, dirt) becomes snow with the original shading kept as cool white tones;
every surface facing up (wall walk, crenellation tops, tower caps, roof ridges) gets a
snow cap where the pixel above it belongs to another region. Trees get snow on their
upper edges. Same layout to the pixel.

  python kar.py <yaz.png> <cikti.png> [--alfa]
"""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    return mx, mn, s, r, g, b


def kar_rengi(lum, soguk=1.0):
    """luminance 0..255 -> snow colour (shadows blue-grey, lit parts near white)."""
    t = np.clip((lum - 40) / 150, 0, 1)[..., None]
    golge = np.array([118, 132, 160], np.float32)
    isik = np.array([236, 240, 248], np.float32)
    return golge + (isik - golge) * t ** 0.8


def karla(im, alfa=None, kalinlik=3):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    mx, mn, s, r, g, b = hsv(a)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    # classes
    cimen = (g > r * 1.02) & (g > b * 1.15) & (lum > 55)                 # lit grass
    agac = (g >= r) & (g > b) & (lum <= 55)                                # dark pine needles / grass shadow
    toprak = (r > g * 1.08) & (g > b * 1.08) & (s > 0.28) & (s < 0.7) & (lum > 30) & (lum < 175)
    tas = (s < 0.28) & (lum > 50)
    cati = (r > g * 1.3) & (s >= 0.45)                                     # red tiles
    out = a.copy()
    # ground is smooth (low local contrast), walls and towers have mortar lines (high contrast)
    m = ndimage.uniform_filter(lum, 9)
    sd = np.sqrt(np.maximum(ndimage.uniform_filter(lum ** 2, 9) - m ** 2, 0))
    toprak &= r > g * 1.3
    zemin = (cimen & (sd < 34)) | (toprak & (sd < 18))
    zemin = ndimage.binary_closing(ndimage.binary_opening(zemin, np.ones((3, 3))), np.ones((5, 5)))
    lab, n = ndimage.label(zemin)
    if n:
        boy = np.bincount(lab.ravel()); boy[0] = 0
        zemin = (boy >= 300)[lab]
    zemin &= (cimen | toprak | (sd < 10))
    if alfa is not None:
        zemin &= alfa
    # ground: snow keeping the texture (local luminance) but compressed into bright tones
    out[zemin] = kar_rengi(lum[zemin] * 0.6 + 110)
    # snow caps: solid objects (walls, towers, roofs, trees) as smoothed regions, so mortar lines
    # do not split them; a cap is the top `kal` px of an object where the ground lies above it
    nesne = ~zemin
    nesne = ndimage.binary_opening(ndimage.binary_closing(nesne, np.ones((5, 5))), np.ones((3, 3)))
    zem = ndimage.binary_opening(zemin, np.ones((3, 3)))
    for maske, kal in ((tas | cati, kalinlik), (agac, 2)):
        m = nesne & ndimage.binary_closing(maske, np.ones((5, 5)))
        # ground within (kal + 3) px above: skips the dark outline row between wall top and ground
        ust = np.zeros_like(m)
        for d in range(1, kal + 4):
            yukari = np.zeros_like(m)
            yukari[d:] = zem[:-d]
            ust |= m & yukari
        # only lit pixels, ragged lower edge so it reads as snow, not a painted line
        ust &= lum > 45
        out[ust] = kar_rengi(lum[ust] * 0.4 + 150)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    src = Image.open(sys.argv[1])
    al = np.asarray(src.getchannel("A")) > 0 if src.mode == "RGBA" else None
    k = karla(src, al)
    if src.mode == "RGBA":
        k = k.convert("RGBA"); k.putalpha(src.getchannel("A"))
    k.save(sys.argv[2])
