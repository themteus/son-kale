import sys, glob, os
sys.path.insert(0, "D:/AI/araclar")
import numpy as np
from PIL import Image
import birim as B
unit, tag, seed = "zombi", sys.argv[1], 22
frames = [f for f in B.frames_of(unit) if f[0] in (0, 3, 12, 18)]
raw = {}
for (idx, row, col, name) in frames:
    p = glob.glob(f"{B.COMFY}/output/son-kale-v2/{unit}/ham/{tag}_s{seed}_{idx:02d}_*.png")[0]
    old = B.cut(unit, row, col)
    _, place = B.make_input(unit, idx, row, col)
    raw[idx] = (old, B.back_to_frame(p, old, place))
def strip(rows):
    K = B.layout(unit); n = len(frames)
    s = Image.new("RGBA", (K["fw"] * n, K["fh"] * len(rows)), (214, 204, 184, 255))
    for r, d in enumerate(rows):
        for j, (idx, *_ ) in enumerate(frames):
            s.alpha_composite(d[idx], (j * K["fw"], r * K["fh"]))
    return s
olds = {i: v[0] for i, v in raw.items()}
news = {i: v[1] for i, v in raw.items()}
variants = [olds]
for n in (24, 32):
    pal = B.build_palette(list(news.values()), n)
    variants.append({i: B.apply_palette(f, pal) for i, f in news.items()})
# palette from old + new pixels: keeps the old accent colours (belt, bruises)
pal = B.build_palette(list(news.values()) + list(olds.values()), 32)
variants.append({i: B.apply_palette(f, pal) for i, f in news.items()})
s = strip(variants)
s.convert("RGB").resize((s.width * 3, s.height * 3), Image.Resampling.NEAREST).save(f"{B.OUT}/{unit}/_palet_{tag}.png")
print("ok")
