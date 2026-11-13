"""Sheet: original + variants for given building names, x2 NEAREST on a ground colour."""
import os, sys
from PIL import Image, ImageDraw
O = "D:/AI/ComfyUI/output/son-kale-v2/bina"
out, names, suffixes = sys.argv[1], sys.argv[2].split(","), sys.argv[3].split(",") if len(sys.argv) > 3 else [""]
cols = [("eski", lambda n, s: f"D:/AI/araclar/orijinal/kale/{n}.png")] + [
    (f"{v}{s}", (lambda v, s: lambda n, _: f"{O}/{v}/{n}{s}.png")(v, s)) for v in ("karli", "gece", "yikik") for s in suffixes]
S = 2; tiles = []
for n in names:
    row = []
    for label, f in cols:
        p = f(n, None)
        if not os.path.exists(p): continue
        im = Image.open(p).convert("RGBA"); im = im.resize((im.width * S, im.height * S), Image.Resampling.NEAREST)
        t = Image.new("RGBA", (im.width + 20, im.height + 30), (120, 140, 90, 255)); t.alpha_composite(im, (10, 26))
        ImageDraw.Draw(t).text((6, 6), f"{n} {label}", fill=(255, 255, 255)); row.append(t)
    tiles.append(row)
W = max(sum(t.width + 6 for t in r) for r in tiles); H = sum(max(t.height for t in r) + 6 for r in tiles)
sheet = Image.new("RGB", (W, H), (40, 40, 40)); y = 0
for r in tiles:
    x = 0
    for t in r: sheet.paste(t.convert("RGB"), (x, y)); x += t.width + 6
    y += max(t.height for t in r) + 6
sheet.save(out); print(out, sheet.size)
