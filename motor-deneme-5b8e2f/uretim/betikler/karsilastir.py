"""Game-scale old/new pairs for several units: python karsilastir.py out.png unit1 unit2 ..."""
import sys
from PIL import Image, ImageDraw
sys.path.insert(0, "D:/AI/araclar")
import birim as B
out, units = sys.argv[1], sys.argv[2:]
rows = []
for u in units:
    K = B.layout(u); new = Image.open(f"{B.OUT}/{u}/{u}.png"); old = Image.open(f"{B.GORSEL}/{u}.png")
    R = K["rows"]; fw, fh = K["fw"], K["fh"]
    s = max(1, round(288 / max(fw, fh)))
    picks = [("walk", 2), ("walk", R["walk"]["frames"] - 3), ("attack", R["attack"]["frames"] - 2), ("die", 4)]
    tiles = []
    for rn, c in picks:
        r = R[rn]["row"]
        o = old.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)).resize((fw * s, fh * s), Image.Resampling.NEAREST)
        n = new.crop((c * fw * 2, r * fh * 2, (c + 1) * fw * 2, (r + 1) * fh * 2)).resize((fw * s, fh * s), Image.Resampling.NEAREST)
        t = Image.new("RGBA", (fw * s * 2 + 10, fh * s), (214, 204, 184, 255)); t.alpha_composite(o, (0, 0)); t.alpha_composite(n, (fw * s + 10, 0)); tiles.append(t)
    row = Image.new("RGBA", (sum(t.width + 10 for t in tiles), tiles[0].height + 26), (214, 204, 184, 255))
    ImageDraw.Draw(row).text((6, 6), u + ":  her ciftte sol = eski PixelLab, sag = yeni ComfyUI (2 kat detay)", fill=(30, 20, 20))
    x = 0
    for t in tiles: row.alpha_composite(t, (x, 26)); x += t.width + 10
    rows.append(row)
W = max(r.width for r in rows); H = sum(r.height + 8 for r in rows)
o = Image.new("RGB", (W, H), (60, 60, 60)); y = 0
for r in rows: o.paste(r.convert("RGB"), (0, y)); y += r.height + 8
o.save(out); print(out, o.size)
