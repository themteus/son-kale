"""Re-draw a game sprite sheet frame by frame with SDXL + pixel-art LoRA + ControlNet canny.

Each frame is NEAREST-upscaled K times onto a 1024 canvas at a fixed offset, redrawn,
then BOX-downscaled from the same box. Frame registration (footY, centerX) is exact,
the silhouette comes from the old frame (no animation jitter), and every frame of a
unit shares one palette.

Usage:
  python birim.py deneme <birim> <frame indices...> --seeds 11 22 --denoise 0.5 --cn 0.7
  python birim.py tam <birim> --seed 22 --denoise 0.5 --cn 0.7
"""
import argparse
import json
import os
import sys
import time
import urllib.request

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = "D:/AI/son-kale/motor-deneme-5b8e2f"
GORSEL = "D:/AI/araclar/orijinal"  # frozen originals from PR 4 (repo copies get replaced)
COMFY = "D:/AI/ComfyUI"
OUT = f"{COMFY}/output/son-kale-v2"
URL = "http://127.0.0.1:8188"
BG = (200, 200, 200)
CHROMA_OLD = 1.0
CHROMA_GAIN = 1.0  # >1 boosts colour saturation (units that come out washed out)
Y_SHIFT = 0.0
KORU = []  # rig colours (thin lines like bowstrings) copied back pixel-exact after the redraw
LUMA_ESKI = 0.0  # 0..1: blend this much of the old/rig frame's brightness back in (steadier animation)

PROMPTS = json.load(open(os.path.join(os.path.dirname(__file__), "istemler.json"), encoding="utf-8"))
NEG_BASE = "blurry, photo, 3d render, realistic, text, watermark, multiple characters, background scenery, cropped, smooth gradient, jpeg artifacts"


YAYCILAR = ("okcu", "asker")  # bow sheets: one frame per aim angle x draw level
YAYCI_SUTUN = 11                # 2x sheets are re-flowed to 11 columns to stay under 4096 px


def layout(unit):
    J = json.load(open(f"{GORSEL}/kareler.json", encoding="utf-8"))
    if unit in YAYCILAR:
        K = dict(J[unit])
        n = len(K["acilar"])
        K["rows"] = {f"germe{g}": {"row": g, "frames": n, "fps": 12, "once": False} for g in range(len(K["germe"]))}
        K.setdefault("centerX", K["fw"] // 2)
        return K
    return J["birimler"][unit]


def frames_of(unit):
    """List of (index, row, col, name) in sheet order."""
    K = layout(unit)
    out = []
    for name, r in sorted(K["rows"].items(), key=lambda kv: kv[1]["row"]):
        for c in range(r["frames"]):
            out.append((len(out), r["row"], c, f"{name}{c}"))
    return out


KAYNAK = {}  # unit -> alternative source sheet (e.g. a code-drawn pose rig), same layout


def cut(unit, row, col):
    K = layout(unit)
    sheet = Image.open(KAYNAK.get(unit, f"{GORSEL}/{unit}.png")).convert("RGBA")
    fw, fh = K["fw"], K["fh"]
    return sheet.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))


def scale_for(unit):
    K = layout(unit)
    x0, y0, x1, y1 = union_bbox(unit)
    return max(1, 860 // max(x1 - x0, y1 - y0))


_BBOX = {}


def union_bbox(unit):
    """Box covering the character in every frame (frame coordinates)."""
    if unit not in _BBOX:
        boxes = [cut(unit, r, c).getchannel("A").getbbox() for (_, r, c, _) in frames_of(unit)]
        boxes = [b for b in boxes if b]
        _BBOX[unit] = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    return _BBOX[unit]


ESKI_YERLESIM = set()  # units generated before the bbox-based placement (zombi)


def make_input(unit, idx, row, col):
    """Upscale the frame k times so the character (not the frame) fills ~860 px, centred."""
    fr = cut(unit, row, col)
    if unit in ESKI_YERLESIM:
        K = layout(unit); k = max(1, 800 // max(K["fw"], K["fh"]))
        return f"v2_{unit}_{idx:02d}.png", ((1024 - fr.width * k) // 2, (1024 - fr.height * k) // 2, k)
    k = scale_for(unit)
    x0, y0, x1, y1 = union_bbox(unit)
    big = fr.resize((fr.width * k, fr.height * k), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (1024, 1024), BG + (255,))
    ox = int(512 - (x0 + x1) / 2 * k)
    oy = int(512 - (y0 + y1) / 2 * k)
    layer = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    layer.paste(big, (ox, oy))
    canvas.alpha_composite(layer)
    name = f"v2_{unit}_{idx:02d}.png"
    canvas.convert("RGB").save(f"{COMFY}/input/{name}")
    return name, (ox, oy, k)


def workflow(inp, prefix, seed, denoise, cn, pos, neg, steps=25):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
        "2": {"class_type": "LoraLoader", "inputs": {"model": ["1", 0], "clip": ["1", 1], "lora_name": "pixel-art-xl.safetensors", "strength_model": 1.0, "strength_clip": 1.0}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "sdxl_vae_fp16_fix.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 1], "text": pos}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 1], "text": neg}},
        "10": {"class_type": "LoadImage", "inputs": {"image": inp}},
        "11": {"class_type": "VAEEncode", "inputs": {"pixels": ["10", 0], "vae": ["3", 0]}},
        "12": {"class_type": "Canny", "inputs": {"image": ["10", 0], "low_threshold": 0.3, "high_threshold": 0.6}},
        "13": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "xinsir_canny_sdxl.safetensors"}},
        "14": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["4", 0], "negative": ["5", 0], "control_net": ["13", 0], "image": ["12", 0], "strength": cn, "start_percent": 0.0, "end_percent": 0.85, "vae": ["3", 0]}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": ["14", 0], "negative": ["14", 1], "latent_image": ["11", 0], "seed": seed, "steps": steps, "cfg": 6.0, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": denoise}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }


def api(path, data=None):
    last = None
    for _ in range(40):
        try:
            req = urllib.request.Request(URL + path, data=data, headers={"Content-Type": "application/json"} if data else {})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(5)
    raise SystemExit(f"ComfyUI'ye ulasilamadi: {path}: {last}")


ONDE = False  # True: put these jobs at the front of the ComfyUI queue


def run_jobs(jobs):
    """jobs: list of (prefix, workflow). Queue all, wait, return {prefix: output path}."""
    ids = {}
    for prefix, wf in (reversed(jobs) if ONDE else jobs):
        r = api("/prompt", json.dumps({"prompt": wf, "front": ONDE}).encode())
        if "prompt_id" not in r:
            raise SystemExit(f"hata: {r}")
        ids[r["prompt_id"]] = prefix
    out, t0 = {}, time.time()
    while len(out) < len(ids):
        time.sleep(10)
        q = api("/queue")
        busy = {x[1] for x in q["queue_running"] + q["queue_pending"]}
        for pid, prefix in ids.items():
            if prefix in out or pid in busy:
                continue
            h = api(f"/history/{pid}")
            if pid not in h:
                continue
            st = h[pid]["status"]["status_str"]
            if st != "success":
                raise SystemExit(f"{prefix} basarisiz: {json.dumps(h[pid]['status'])[-800:]}")
            im = [i for o in h[pid]["outputs"].values() for i in o.get("images", [])][0]
            out[prefix] = os.path.join(COMFY, "output", im["subfolder"], im["filename"])
            print(f"  {len(out)}/{len(ids)} {prefix.split('/')[-1]}  ({time.time() - t0:.0f} s)", flush=True)
    return out


def back_to_frame(gen_path, old_frame, place, F=1):
    """Downscale the generated image back into the frame box at F x the old size.

    Alpha starts as the old silhouette (NEAREST-upscaled) so the motion stays identical;
    at F > 1 the blocky edge is smoothed by dropping edge pixels that are background-coloured.
    """
    ox, oy, k = place
    g = Image.open(gen_path).convert("RGB")
    box = g.crop((ox, oy, ox + old_frame.width * k, oy + old_frame.height * k))
    size = (old_frame.width * F, old_frame.height * F)
    small = box.resize(size, Image.Resampling.BOX)
    a = old_frame.getchannel("A").point(lambda v: 255 if v >= 128 else 0).resize(size, Image.Resampling.NEAREST)
    mask = np.asarray(a) == 255
    if F > 1:
        rgb = np.asarray(small).astype(np.int16)
        near_bg = np.abs(rgb - np.array(BG)).max(axis=2) <= 35
        # thin glowing lines (magic auras) live entirely in the edge band: keep vivid old pixels
        o = np.asarray(old_frame.convert("RGB").resize(size, Image.Resampling.NEAREST)).astype(np.float32)
        omx, omn = o.max(axis=2), o.min(axis=2)
        vivid_old = (omx > 140) & ((omx - omn) / np.maximum(omx, 1) > 0.5)
        near_bg &= ~vivid_old
        band = mask & ~ndimage.binary_erosion(mask, iterations=F)
        mask = mask & ~(band & near_bg)
        mask = ndimage.binary_opening(mask, structure=np.ones((2, 2))) | (mask & ~band)
    # Colour identity from the old frame, shading detail from the redraw: frames are pixel
    # aligned, so take luma (Y) from the new image and chroma (Cb, Cr) mostly from the old one.
    old_big = old_frame.convert("RGB").resize(size, Image.Resampling.NEAREST)
    yo = np.asarray(old_big.convert("YCbCr")).astype(np.float32)
    yn = np.asarray(small.convert("YCbCr")).astype(np.float32)
    m = mask
    if m.sum() > 20:
        Yn = yn[..., 0]
        mu_n, sd_n = Yn[m].mean(), Yn[m].std() + 1e-3
        mu_o, sd_o = yo[..., 0][m].mean(), yo[..., 0][m].std() + 1e-3
        Y = (Yn - mu_n) / sd_n * sd_o + mu_o + Y_SHIFT
        Y = Y * (1 - LUMA_ESKI) + yo[..., 0] * LUMA_ESKI
        C = yo[..., 1:] * CHROMA_OLD + yn[..., 1:] * (1 - CHROMA_OLD)
        C = (C - 128) * CHROMA_GAIN + 128
        ycc = np.dstack([np.clip(Y, 0, 255), np.clip(C, 0, 255)]).astype(np.uint8)
        small = Image.fromarray(ycc, "YCbCr").convert("RGB")
    # Keep vivid accent colours (belts, eyes, blood, fire) from the old frame when the
    # redraw washed them out.
    oldc = np.asarray(old_big).astype(np.float32) / 255
    newc = np.asarray(small).astype(np.float32) / 255
    def sat(c):
        mx, mn = c.max(axis=2), c.min(axis=2)
        return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0), mx
    so, vo = sat(oldc)
    sn, _ = sat(newc)
    accent = mask & (so > 0.5) & (vo > 0.55) & (sn < so - 0.2)
    arr = np.asarray(small).copy()
    arr[accent] = (oldc[accent] * 255).astype(np.uint8)
    if KORU:
        ob = np.asarray(old_frame.resize(size, Image.Resampling.NEAREST)).astype(np.int16)
        hit = np.zeros(mask.shape, bool)
        for c in KORU:
            hit |= (np.abs(ob[..., :3] - np.array(c)).max(axis=2) <= 12) & (ob[..., 3] > 0)
        arr[hit] = ob[hit][:, :3].astype(np.uint8)
        mask = mask | hit
    small = Image.fromarray(arr).convert("RGBA")
    small.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
    return small


def build_palette(frames, n):
    """One palette for the whole unit from the opaque pixels of all frames."""
    px = []
    for f in frames:
        arr = np.asarray(f)
        px.append(arr[arr[..., 3] == 255][:, :3])
    px = np.concatenate(px)
    side = int(np.ceil(np.sqrt(len(px))))
    pad = np.zeros((side * side, 3), np.uint8)
    pad[: len(px)] = px
    pad[len(px):] = px[0]
    strip = Image.fromarray(pad.reshape(side, side, 3))
    # Reserve slots for vivid accent colours, which median cut would merge away.
    f = px.astype(np.float32) / 255
    mx, mn = f.max(1), f.min(1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    vivid = px[(s > 0.5) & (mx > 0.55)]
    n_acc = 6 if len(vivid) >= 30 else 0
    base = strip.quantize(colors=n - n_acc, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    cols = np.array(base.getpalette()[: 3 * (n - n_acc)]).reshape(-1, 3)
    if n_acc:
        vs = int(np.ceil(np.sqrt(len(vivid))))
        vp = np.zeros((vs * vs, 3), np.uint8); vp[: len(vivid)] = vivid; vp[len(vivid):] = vivid[0]
        acc = Image.fromarray(vp.reshape(vs, vs, 3)).quantize(colors=n_acc, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        cols = np.concatenate([cols, np.array(acc.getpalette()[: 3 * n_acc]).reshape(-1, 3)])
    pal = Image.new("P", (1, 1))
    flat = cols.astype(int).ravel().tolist()
    pal.putpalette(flat + flat[:3] * (256 - len(cols)))
    return pal


def apply_palette(frame, pal_img):
    a = np.asarray(frame.getchannel("A"))
    q = frame.convert("RGB").quantize(palette=pal_img, dither=Image.Dither.NONE).convert("RGB")
    arr = np.asarray(q).copy()
    # 1px dark outline on the silhouette edge (inside, so the size never changes)
    solid = a == 255
    edge = solid & ~ndimage.binary_erosion(solid, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    colors = np.asarray(q).reshape(-1, 3)
    darkest = colors[np.argmin(colors.sum(1))] if solid.any() else np.array([20, 16, 20])
    out_col = (darkest * 0.6).astype(np.uint8)
    arr[edge] = out_col
    rgba = np.dstack([arr, np.where(solid, 255, 0).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def assemble(unit, frames_dict, F):
    K = layout(unit)
    old = Image.open(f"{GORSEL}/{unit}.png")
    fw, fh = K["fw"] * F, K["fh"] * F
    sheet = Image.new("RGBA", (old.width * F, old.height * F), (0, 0, 0, 0))
    for (idx, row, col, name) in frames_of(unit):
        if idx in frames_dict:
            sheet.paste(frames_dict[idx], (col * fw, row * fh))
    return sheet


def _frames_seq(unit):
    K = layout(unit)
    for name, r in sorted(K["rows"].items(), key=lambda kv: kv[1]["row"]):
        reps = 1 if r["once"] else 2
        for rep in range(reps):
            for c in range(r["frames"]):
                last = rep == reps - 1 and c == r["frames"] - 1
                yield r["row"], c, int(1000 / r["fps"]) + (400 if last else 0)


def side_by_side_gif(unit, old, new, F, path, s=2, bg=(214, 204, 184)):
    """Old (left) and new (right) at the same on-screen size."""
    K = layout(unit); fw, fh = K["fw"], K["fh"]
    imgs, durs = [], []
    for row, c, d in _frames_seq(unit):
        o = old.crop((c * fw, row * fh, (c + 1) * fw, (row + 1) * fh)).resize((fw * F * s, fh * F * s), Image.Resampling.NEAREST)
        n = new.crop((c * fw * F, row * fh * F, (c + 1) * fw * F, (row + 1) * fh * F)).resize((fw * F * s, fh * F * s), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (o.width * 2 + 16, o.height), bg + (255,))
        canvas.alpha_composite(o, (0, 0)); canvas.alpha_composite(n, (o.width + 16, 0))
        imgs.append(canvas.convert("RGB")); durs.append(d)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durs, loop=0)


def new_gif(unit, new, F, path, s=2, bg=(214, 204, 184)):
    K = layout(unit); fw, fh = K["fw"] * F, K["fh"] * F
    imgs, durs = [], []
    for row, c, d in _frames_seq(unit):
        f = new.crop((c * fw, row * fh, (c + 1) * fw, (row + 1) * fh))
        b = Image.new("RGBA", f.size, bg + (255,)); b.alpha_composite(f)
        imgs.append(b.convert("RGB").resize((fw * s, fh * s), Image.Resampling.NEAREST)); durs.append(d)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durs, loop=0)


def compare_png(old, new, F, path, bg=(214, 204, 184)):
    o = old.resize((old.width * F, old.height * F), Image.Resampling.NEAREST)
    out = Image.new("RGBA", (o.width, o.height * 2 + 30), bg + (255,))
    out.alpha_composite(o, (0, 0)); out.alpha_composite(new, (0, o.height + 30))
    ImageDraw.Draw(out).text((6, o.height + 8), "ust: eski PixelLab (buyutulmus)   alt: yeni ComfyUI (2 kat detay)", fill=(40, 30, 30))
    out.convert("RGB").save(path)


def new_layout(unit, F):
    if unit in YAYCILAR:
        J = json.load(open(f"{GORSEL}/kareler.json", encoding="utf-8"))
        K = json.loads(json.dumps(J[unit]))
        for key in ("fw", "fh", "footY"):
            K[key] = K[key] * F
        rig_nokta = os.path.join(os.path.dirname(KAYNAK.get(unit, "")), f"{unit}_noktalar.json")
        if unit in KAYNAK and os.path.exists(rig_nokta):
            K["kareler"] = json.load(open(rig_nokta))   # points come from the pose rig, not the old art
        for k in K["kareler"]:
            for name, p in k.items():
                if isinstance(p, dict):
                    k[name] = {"x": round(p["x"] * F, 1), "y": round(p["y"] * F, 1)}
        K["olcek"] = round(1 / F, 4)  # okcu.js reads this (new, defaults to 1)
        return K
    K = json.loads(json.dumps(layout(unit)))
    for key in ("fw", "fh", "footY", "centerX"):
        K[key] = K[key] * F
    K["olcek"] = round(K.get("olcek", 1) / F, 4)
    return K


def reflow(sheet, fw, fh, cols):
    """Re-flow a sheet's frames (row-major order) into `cols` columns; Phaser numbers frames
    left-to-right, top-to-bottom, so frame indices stay the same."""
    n_cols, n_rows = sheet.width // fw, sheet.height // fh
    n = n_cols * n_rows
    rows = (n + cols - 1) // cols
    out = Image.new("RGBA", (cols * fw, rows * fh), (0, 0, 0, 0))
    for i in range(n):
        f = sheet.crop(((i % n_cols) * fw, (i // n_cols) * fh, (i % n_cols + 1) * fw, (i // n_cols + 1) * fh))
        out.paste(f, ((i % cols) * fw, (i // cols) * fh))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mod", choices=["deneme", "tam"])
    ap.add_argument("birim")
    ap.add_argument("kareler", nargs="*", type=int)
    ap.add_argument("--seeds", nargs="+", type=int, default=[22])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--denoise", type=float, default=0.5)
    ap.add_argument("--cn", type=float, default=0.7)
    ap.add_argument("--renk", type=int, default=32)
    ap.add_argument("--kat", type=int, default=2)
    ap.add_argument("--etiket", default="")
    ap.add_argument("--yeniden", action="store_true", help="uretme, ham gorsellerden yeniden isle")
    ap.add_argument("--eski-yerlesim", action="store_true")
    ap.add_argument("--kaynak", default=None, help="eski kareler yerine bu sayfayı kullan (poz rig'i)")
    ap.add_argument("--doygunluk", type=float, default=1.0)
    ap.add_argument("--luma-eski", type=float, default=0.0)
    ap.add_argument("--palet-kaynak", default=None, help="paleti bu görselden al (ör. eski PixelLab sayfası)")
    ap.add_argument("--renk-eski", type=float, default=1.0, help="renk tonunun ne kadarı eski/rig karesinden (1 = tamamı)")
    ap.add_argument("--koru", nargs="*", default=[], help="korunacak rig renkleri, ör. 226,222,206")
    ap.add_argument("--parlaklik", type=float, default=0.0, help="Y kaydirma (eski ortalamaya ek)")
    a = ap.parse_args()

    unit, F = a.birim, a.kat
    global CHROMA_GAIN, Y_SHIFT, LUMA_ESKI, CHROMA_OLD
    CHROMA_GAIN, Y_SHIFT, LUMA_ESKI = a.doygunluk, a.parlaklik, a.luma_eski
    CHROMA_OLD = a.renk_eski
    KORU[:] = [tuple(int(v) for v in c.split(",")) for c in a.koru]
    if a.kaynak:
        KAYNAK[unit] = a.kaynak
    if a.eski_yerlesim:
        ESKI_YERLESIM.add(unit)
    P = PROMPTS[unit]
    pos, neg = P["pos"], NEG_BASE + ", " + P.get("neg", "")
    allf = frames_of(unit)
    pick = [f for f in allf if (a.mod == "tam" or f[0] in a.kareler)]
    seeds = [a.seed] if a.seed is not None else a.seeds
    tag = a.etiket or f"d{int(a.denoise * 100)}_c{int(a.cn * 100)}"
    udir = f"{OUT}/{unit}"
    os.makedirs(udir, exist_ok=True)

    jobs, meta = [], {}
    for (idx, row, col, name) in pick:
        inp, place = make_input(unit, idx, row, col)
        for s in seeds:
            prefix = f"son-kale-v2/{unit}/ham/{tag}_s{s}_{idx:02d}"
            jobs.append((prefix, workflow(inp, prefix, s, a.denoise, a.cn, pos, neg)))
            meta[prefix] = (idx, row, col, place, s)
    t0 = time.time()
    if a.yeniden:
        import glob
        paths = {p: sorted(glob.glob(f"{COMFY}/output/{p}_*.png"))[-1] for p, _ in jobs}
    else:
        import glob
        # resume: frames already drawn (e.g. before a restart) are reused
        paths = {}
        for p, _ in jobs:
            done = sorted(glob.glob(f"{COMFY}/output/{p}_*.png"))
            if done:
                paths[p] = done[-1]
        todo = [(p, w) for p, w in jobs if p not in paths]
        print(f"{unit}: {len(todo)} cizim kuyruga alindi ({len(paths)} hazir)", flush=True)
        paths.update(run_jobs(todo) if todo else {})
        print(f"uretim bitti: {time.time() - t0:.0f} s", flush=True)

    old_sheet = Image.open(KAYNAK.get(unit, f"{GORSEL}/{unit}.png")).convert("RGBA")
    for s in seeds:
        frames, olds = {}, []
        for prefix, (idx, row, col, place, ss) in meta.items():
            if ss != s:
                continue
            old = cut(unit, row, col)
            olds.append(old)
            frames[idx] = back_to_frame(paths[prefix], old, place, F)
        # palette from new + old pixels keeps the old accent colours (belts, eyes, metal)
        if a.palet_kaynak:
            pal = build_palette([Image.open(a.palet_kaynak).convert("RGBA")], a.renk)   # palette of the reference art
        else:
            pal = build_palette(list(frames.values()) + olds, a.renk)
        frames = {i: apply_palette(f, pal) for i, f in frames.items()}
        # keep baked-in fades (e.g. die rows that get more transparent each frame)
        for prefix, (idx, row, col, place, ss) in meta.items():
            if ss != s:
                continue
            oa = np.asarray(cut(unit, row, col).getchannel("A"))
            level = int(np.median(oa[oa > 0])) if (oa > 0).any() else 255
            if level < 250:
                arr = np.asarray(frames[idx]).copy()
                arr[..., 3] = (arr[..., 3].astype(np.uint16) * level // 255).astype(np.uint8)
                frames[idx] = Image.fromarray(arr, "RGBA")
        if a.mod == "tam":
            sheet = assemble(unit, frames, F)
            if unit in YAYCILAR:
                K2 = new_layout(unit, F)
                reflow(sheet, K2["fw"], K2["fh"], YAYCI_SUTUN).save(f"{udir}/{unit}.png")
            else:
                sheet.save(f"{udir}/{unit}.png")
            json.dump(new_layout(unit, F), open(f"{udir}/kareler_{unit}.json", "w", encoding="utf-8"), ensure_ascii=False)
            new_gif(unit, sheet, F, f"{udir}/{unit}_onizleme.gif")
            side_by_side_gif(unit, old_sheet, sheet, F, f"{udir}/eski_yeni.gif")
            compare_png(old_sheet, sheet, F, f"{udir}/karsilastirma.png")
            print(f"kaydedildi: {udir}")
        else:
            K = layout(unit); fw, fh = K["fw"] * F, K["fh"] * F
            chosen = [f for f in allf if f[0] in frames]
            strip = Image.new("RGBA", (fw * len(chosen), fh * 2), (214, 204, 184, 255))
            for j, (idx, row, col, name) in enumerate(chosen):
                strip.alpha_composite(cut(unit, row, col).resize((fw, fh), Image.Resampling.NEAREST), (j * fw, 0))
                strip.alpha_composite(frames[idx], (j * fw, fh))
            p = f"{udir}/deneme_{tag}_s{s}.png"
            strip.convert("RGB").resize((strip.width * 3 // 2, strip.height * 3 // 2), Image.Resampling.NEAREST).save(p)
            print("deneme:", p)


if __name__ == "__main__":
    main()
