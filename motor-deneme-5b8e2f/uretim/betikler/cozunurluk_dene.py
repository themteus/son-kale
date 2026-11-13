import sys, glob
sys.path.insert(0, "D:/AI/araclar")
import numpy as np
from PIL import Image
import birim as B
unit, tag, seed, F = "zombi", sys.argv[1], 22, 2
frames = [f for f in B.frames_of(unit) if f[0] in (0, 3, 12, 18)]
K = B.layout(unit); fw, fh = K["fw"], K["fh"]
olds, news = {}, {}
for (idx, row, col, name) in frames:
    p = glob.glob(f"{B.COMFY}/output/son-kale-v2/{unit}/ham/{tag}_s{seed}_{idx:02d}_*.png")[0]
    old = B.cut(unit, row, col); _, (ox, oy, k) = B.make_input(unit, idx, row, col)
    g = Image.open(p).convert("RGB").crop((ox, oy, ox + fw * k, oy + fh * k)).resize((fw * F, fh * F), Image.Resampling.BOX).convert("RGBA")
    a = old.getchannel("A").resize((fw * F, fh * F), Image.Resampling.NEAREST).point(lambda v: 255 if v >= 128 else 0)
    g.putalpha(a); news[idx] = g; olds[idx] = old
pal = B.build_palette(list(news.values()) + list(olds.values()), 32)
news = {i: B.apply_palette(f, pal) for i, f in news.items()}
n = len(frames)
s = Image.new("RGBA", (fw * F * n, fh * F * 2), (214, 204, 184, 255))
for j, (idx, *_ ) in enumerate(frames):
    s.alpha_composite(olds[idx].resize((fw * F, fh * F), Image.Resampling.NEAREST), (j * fw * F, 0))
    s.alpha_composite(news[idx], (j * fw * F, fh * F))
s.convert("RGB").resize((s.width * 3 // 2, s.height * 3 // 2), Image.Resampling.NEAREST).save(f"{B.OUT}/{unit}/_cozunurluk_x2_{tag}.png")
print("ok")
