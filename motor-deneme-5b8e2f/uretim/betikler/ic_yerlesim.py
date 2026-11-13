"""Offline preview of the inner castle with the new props, drawn like kale.js does:
background, then buildings + decorations sorted by depth (y), front walls on top, outside items last.

  python ic_yerlesim.py [seviye] [cikti.png] [--izgara]
Placement list: D:/AI/araclar/ic_yerlesim.json  ->  copied to the game as assets/kale/kale_ic2.json
"""
import json
import sys

from PIL import Image, ImageDraw

KALE = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale"
IC = "D:/AI/son-kale/motor-deneme-5b8e2f/assets/kale/sus/ic2"
YER = "D:/AI/araclar/ic_yerlesim.json"


def disari_aktar():
    """Design file (base points) -> game file: y moves down by the baked shadow, plus the variant list."""
    import os
    L = json.load(open(YER, encoding="utf-8"))
    taban = json.load(open("D:/AI/araclar/ic_taban.json"))
    out = {"bolgeler": L.get("bolgeler", {}), "susler": [], "varyantlar": {}}
    for s in L["susler"]:
        e = {k: v for k, v in s.items() if k != "bolge"}
        e["y"] = s["y"] + round(taban.get(s["ad"], 0) * s.get("piksel", 1))
        out["susler"].append(e)
        v = [x for x in ("karli", "gece") if os.path.exists(f"{IC}/{s['ad']}_{x}.png")]
        if v:
            out["varyantlar"][s["ad"]] = v
    json.dump(out, open(f"{KALE}/kale_ic2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def main():
    seviye = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    out = sys.argv[2] if len(sys.argv) > 2 else "D:/AI/araclar/ic_onizleme.png"
    izgara = "--izgara" in sys.argv
    K = json.load(open(f"{KALE}/kale.json", encoding="utf-8"))
    L = disari_aktar()
    O = K["olcek"]
    canvas = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    arka = Image.open(f"{KALE}/arka.png").convert("RGBA")
    p = K.get("arkaPiksel", O)
    canvas.alpha_composite(arka.resize((int(arka.width * p), int(arka.height * p)), Image.Resampling.NEAREST))
    import os
    zp = f"{KALE}/sus/ic2/zemin.png"
    if os.path.exists(zp) and "--zeminsiz" not in sys.argv:
        z = Image.open(zp).convert("RGBA")
        canvas.alpha_composite(z.resize((int(z.width * p), int(z.height * p)), Image.Resampling.NEAREST))
    items = []  # (depth, image, x, y) with x,y = top-left
    for s in K["susler"]:
        im = Image.open(f"{KALE}/sus/{s['ad']}.png").convert("RGBA")
        sc = s.get("piksel", 1)
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.Resampling.NEAREST)
        if s.get("ayna"): im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        items.append(((30 if s.get("disari") else 10) + s["y"] / 2000, im, s["x"] - im.width // 2, s["y"] - im.height))
    for s in L["susler"]:
        im = Image.open(f"{IC}/{s['ad']}.png").convert("RGBA")
        sc = s.get("piksel", 1)
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.Resampling.NEAREST)
        if s.get("ayna"): im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        items.append(((30 if s.get("disari") else 10) + s["y"] / 2000, im, s["x"] - im.width // 2, s["y"] - im.height))
    for k in ["ciftlik", "demirci", "duvarci", "ev", "maden", "oduncu", "tasocagi", "yayci"]:
        m = K["binalar"][f"{k}{seviye}"]
        im = Image.open(f"{KALE}/{k}{seviye}.png").convert("RGBA")
        sc = m.get("piksel", O)
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.Resampling.NEAREST)
        items.append(((30 if m.get("disari") else 10) + m["dipY"] * O / 2000, im, int(m["x"] * O), int(m["y"] * O)))
    on = Image.open(f"{KALE}/on.png").convert("RGBA")
    po = K["on"].get("piksel", O)
    items.append((20, on.resize((int(on.width * po), int(on.height * po)), Image.Resampling.NEAREST), int(K["on"]["x"] * O), int(K["on"]["y"] * O)))
    for _, im, x, y in sorted(items, key=lambda t: t[0]):
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.paste(im, (x, y))
        canvas.alpha_composite(layer)
    if izgara:
        d = ImageDraw.Draw(canvas)
        for x in range(0, 1920, 100): d.line((x, 0, x, 1080), fill=(255, 255, 0, 120)); d.text((x + 2, 2), str(x), fill=(255, 255, 0))
        for y in range(0, 1080, 100): d.line((0, y, 1920, y), fill=(255, 255, 0, 120)); d.text((2, y + 2), str(y), fill=(255, 255, 0))
        for s in L["susler"]:
            d.ellipse((s["x"] - 3, s["y"] - 3, s["x"] + 3, s["y"] + 3), fill=(255, 0, 255))
            d.text((s["x"] + 4, s["y"] - 10), s["ad"], fill=(255, 0, 255))
    canvas.convert("RGB").save(out)
    print(out)


if __name__ == "__main__":
    main()
