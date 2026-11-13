"""New inner-castle props/buildings for Son Kale (isometric 2:1 pixel art).

Each asset: prompt + either a code-drawn isometric sketch (ControlNet canny keeps the 2:1 angle)
or plain txt2img for small round props. Output is cut from the gray background, cropped,
BOX-downscaled to the on-screen height, palette-reduced and outlined.

  python ic.py kuyu sapel --seeds 11 22 33
  python ic.py hepsi --seeds 11 22 33
Output: D:/AI/ComfyUI/output/son-kale-v2/ic/<ad>_s<seed>.png
"""
import argparse
import glob
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import birim as B  # noqa: E402

OUT = f"{B.OUT}/ic"
BG = (200, 200, 200)
STIL = ("pixel art, isometric 2:1 view from the south-east, {p}, medieval castle courtyard game asset, "
        "single object, centered, plain flat light gray background, crisp pixels, clean dark outline, "
        "warm sunlight from top left, cozy medieval city builder style, PixelLab style")
NEG = ("blurry, photo, 3d render, realistic, text, watermark, multiple objects, ground tiles, grass field, "
       "cropped, top-down, side view, front view, people, frame, border")

# small props / animals: a plainer template, otherwise SDXL turns them into little buildings
STIL_KUCUK = ("pixel art game sprite, {p}, isometric 3/4 view from above, single object only, centered, "
              "plain flat light gray background, crisp pixels, clean dark outline, warm sunlight from top left, PixelLab style")
NEG_KUCUK = ("building, house, tower, dome, hut, roof, tent, blurry, photo, 3d render, realistic, text, watermark, "
             "ground tiles, grass, cropped, people, frame, border")
YENI = {  # second round for the assets that came out as buildings
    "araba": "a simple wooden two-wheeled hand cart with a long handle, carrying two burlap sacks",
    "sandik": "a small pile of three square wooden crates stacked on top of each other, with two tied burlap sacks",
    "silahrafi": "a flat wooden weapon rack, two posts and a crossbar, with three spears and two swords leaning on it, a round shield on the side",
    "tavuk": "three small farm chickens pecking on the ground, white and brown feathers, red combs",
    "domuz": "a single pink farm pig standing on four legs, side profile, curly tail",
    "kopek": "a single brown medieval hunting dog standing on four legs, full side profile, tail up",
    "atlar": "two horses standing side by side in profile on four legs, a brown horse and a white horse, saddles and bridles",
    "odun2": "a long low rectangular stack of chopped firewood logs, round log ends visible, an axe stuck in a chopping block",
}

# name: (prompt, target height on screen in px, mode, denoise, controlnet)
VARLIK = {
    # --- buildings (sketch + controlnet) ---
    "sapel": ("a small stone chapel with a pointed slate roof, a bell tower with a bronze bell, arched stained glass windows, wooden door, a stone cross on the roof", 190, "taslak", 0.9, 0.55),
    "ahir": ("a long wooden horse stable with a thatched straw roof, open stalls, hay inside, wooden fence posts", 120, "taslak", 0.9, 0.55),
    "kisla": ("a long stone and timber soldiers barracks with a red tiled roof, small windows, a wooden door, a banner by the door", 140, "taslak", 0.9, 0.55),
    "ambar": ("a tall wooden granary barn on stone stilts with a steep thatched roof and a loading hatch", 130, "taslak", 0.9, 0.55),
    # --- props (txt2img) ---
    "kuyu": ("a round stone water well with a small wooden roof, a rope and a wooden bucket", 54, "metin", 1.0, 0),
    "cesme": ("a round stone town fountain with clear blue water and a small statue spout in the middle", 50, "metin", 1.0, 0),
    "tezgah2": ("a medieval market stall with a blue and white striped awning, baskets of apples and bread on the counter", 62, "metin", 1.0, 0),
    "tezgah3": ("a medieval market stall with a green awning, bolts of colorful cloth and pottery on the counter", 62, "metin", 1.0, 0),
    "araba": ("a wooden two-wheeled hand cart loaded with sacks and a barrel", 40, "metin", 1.0, 0),
    "sandik": ("a pile of wooden crates and burlap grain sacks", 36, "metin", 1.0, 0),
    "fici2": ("a stack of three wooden barrels with iron hoops", 34, "metin", 1.0, 0),
    "silahrafi": ("a wooden A-frame weapon rack with four spears leaning on it and a round wooden shield", 52, "taslak", 0.8, 0.7),
    "manken": ("a straw training dummy: a burlap sack body stuffed with straw on a wooden cross post, a round straw head, a wooden shield tied to it", 50, "taslak", 0.8, 0.7),
    "mesale": ("a tall iron brazier on a stand with a burning fire", 40, "metin", 1.0, 0),
    "bayrak": ("a tall wooden pole with a long hanging red heraldic banner with a gold lion, small stone base", 100, "taslak", 0.8, 0.7),
    "tavuk": ("a small group of three chickens, white and brown", 22, "metin", 1.0, 0),
    "domuz": ("a pink pig standing", 26, "metin", 1.0, 0),
    "kopek": ("a brown medieval hunting dog sitting", 24, "metin", 1.0, 0),
    "atlar": ("two horses, one brown and one white, standing side by side with saddles", 58, "metin", 1.0, 0),
    "odun2": ("a neat stack of split firewood logs with an axe", 36, "metin", 1.0, 0),
    "saman": ("a big round haystack with a wooden pitchfork", 48, "metin", 1.0, 0),
}


# ---------------- isometric sketches (shape + angle for ControlNet) ----------------
X, Y = (2, 1), (-2, 1)


def add(p, q, k=1.0):
    return (p[0] + q[0] * k, p[1] + q[1] * k)


def up(p, k):
    return (p[0], p[1] - k)


def kutu(d, P0, a, b, h, duvar_sol, duvar_sag, cati=None, rh=0, cati_renk=(150, 60, 40), kapi=True, pencere=2):
    """Box with optional gable roof (ridge along X). P0 = back corner of footprint."""
    P1, P3 = add(P0, X, a), add(P0, Y, b)
    P2 = add(P1, Y, b)
    Q0, Q1, Q2, Q3 = up(P0, h), up(P1, h), up(P2, h), up(P3, h)
    d.polygon([P3, P2, Q2, Q3], fill=duvar_sol)
    d.polygon([P2, P1, Q1, Q2], fill=duvar_sag)
    d.line([P3, P2, P1], fill=(40, 30, 25), width=4); d.line([Q3, Q2, Q1], fill=(40, 30, 25), width=4); d.line([P2, Q2], fill=(40, 30, 25), width=4)
    for i in range(pencere):
        c = add(add(P3, X, a * (i + 1) / (pencere + 1)), (0, -h * 0.6))
        d.polygon([c, add(c, X, 8), up(add(c, X, 8), 26), up(c, 26)], fill=(40, 34, 40))
    if kapi:
        c = add(P3, X, a * 0.15)
        d.polygon([c, add(c, X, 14), up(add(c, X, 14), h * 0.55), up(c, h * 0.55)], fill=(70, 45, 28))
    if cati:
        R0 = up(((Q0[0] + Q3[0]) / 2, (Q0[1] + Q3[1]) / 2), rh)
        R1 = up(((Q1[0] + Q2[0]) / 2, (Q1[1] + Q2[1]) / 2), rh)
        d.polygon([Q2, Q1, R1], fill=duvar_sag)
        d.polygon([add(Q3, Y, 6), add(add(Q2, Y, 6), X, 6), add(R1, X, 6), add(R0, X, -6)], fill=cati_renk)
        d.line([R0, R1], fill=(40, 30, 25), width=4); d.line([add(Q3, Y, 6), add(add(Q2, Y, 6), X, 6)], fill=(40, 30, 25), width=4)
    return P0, P1, P2, P3


def taslak(ad):
    im = Image.new("RGB", (1024, 1024), BG)
    d = ImageDraw.Draw(im)
    tas_s, tas_d, ahsap_s, ahsap_d = (130, 126, 120), (165, 160, 150), (120, 84, 50), (160, 118, 72)
    if ad == "sapel":
        kutu(d, (430, 430), 150, 80, 190, tas_s, tas_d, cati=True, rh=130, cati_renk=(80, 84, 96), pencere=3)
        # bell tower at the front end
        kutu(d, (680, 520), 45, 45, 340, tas_s, tas_d, cati=True, rh=120, cati_renk=(80, 84, 96), kapi=False, pencere=1)
    elif ad == "ahir":
        kutu(d, (330, 470), 200, 90, 120, ahsap_s, ahsap_d, cati=True, rh=90, cati_renk=(200, 170, 90), kapi=False, pencere=0)
        P3 = add((330, 470), Y, 90)
        for i in range(4):  # open stalls
            c = add(add(P3, X, 200 * (0.1 + 0.22 * i)), (0, -4))
            d.polygon([c, add(c, X, 30), up(add(c, X, 30), 80), up(c, 80)], fill=(50, 36, 24))
    elif ad == "kisla":
        kutu(d, (320, 470), 210, 85, 150, tas_s, ahsap_d, cati=True, rh=100, cati_renk=(160, 60, 40), pencere=4)
    elif ad == "ambar":
        P0 = (470, 470)
        for c in [P0, add(P0, X, 110), add(P0, Y, 80), add(add(P0, X, 110), Y, 80)]:  # stilts
            d.rectangle([c[0] - 8, c[1] - 60, c[0] + 8, c[1] + 20], fill=tas_s)
        kutu(d, up(P0, 60), 110, 80, 170, ahsap_s, ahsap_d, cati=True, rh=170, cati_renk=(200, 170, 90), kapi=False, pencere=1)
    if ad == "manken":
        d.rectangle([505, 380, 520, 900], fill=ahsap_s)                      # post
        d.rectangle([380, 470, 650, 488], fill=ahsap_d)                      # arms
        d.ellipse([440, 470, 590, 760], fill=(196, 168, 100))                # straw body
        d.ellipse([465, 330, 565, 430], fill=(206, 178, 110))                # head
        d.ellipse([560, 560, 680, 700], fill=(130, 88, 50))                  # shield
        d.ellipse([400, 880, 620, 920], fill=(110, 80, 50))                  # base
    elif ad == "silahrafi":
        d.polygon([(380, 900), (520, 420), (540, 420), (410, 900)], fill=ahsap_s)   # A-frame legs
        d.polygon([(660, 900), (540, 420), (520, 420), (630, 900)], fill=ahsap_d)
        d.rectangle([400, 640, 650, 660], fill=ahsap_d)                       # crossbar
        for i, x in enumerate([430, 490, 560, 620]):                          # spears
            d.line([(x, 900), (x + 20, 300)], fill=(110, 80, 50), width=10)
            d.polygon([(x + 12, 300), (x + 20, 250), (x + 28, 300)], fill=(190, 196, 204))
        d.ellipse([600, 640, 740, 780], fill=(140, 96, 52))                   # shield
    elif ad == "bayrak":
        d.rectangle([502, 120, 520, 900], fill=ahsap_s)                       # pole
        d.rectangle([470, 110, 552, 130], fill=ahsap_d)                       # top bar
        d.polygon([(520, 140), (680, 150), (690, 560), (600, 520), (520, 560)], fill=(150, 34, 36))   # banner
        d.ellipse([570, 260, 640, 340], fill=(210, 170, 60))                  # emblem
        d.polygon([(440, 900), (580, 900), (600, 930), (420, 930)], fill=tas_s)                       # base
    name = f"v2_ic_{ad}.png"
    im.save(f"{B.COMFY}/input/{name}")
    return name


# ---------------- comfy workflows ----------------
def wf_metin(prefix, seed, pos, neg):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
        "2": {"class_type": "LoraLoader", "inputs": {"model": ["1", 0], "clip": ["1", 1], "lora_name": "pixel-art-xl.safetensors", "strength_model": 1.0, "strength_clip": 1.0}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "sdxl_vae_fp16_fix.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 1], "text": pos}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 1], "text": neg}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0], "seed": seed, "steps": 25, "cfg": 6.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }


# ---------------- cut out + pixelize ----------------
def kes(path, hedef_boy, renk=24):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    h, w, _ = rgb.shape
    corners = np.array([rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]])
    bg = np.median(corners, axis=0)
    near = np.abs(rgb - bg).max(axis=2) <= 26
    lab, n = ndimage.label(near)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = np.bincount(lab.ravel())
    is_bg = np.zeros(n + 1, bool)
    for i in range(1, n + 1):
        if i in border or sizes[i] > 0.002 * w * h:
            is_bg[i] = True
    alpha = ~is_bg[lab]
    # drop the soft drop-shadow ring: very dark-gray low-saturation pixels touching the background
    flab, fn = ndimage.label(alpha)
    if fn > 1:
        fs = np.bincount(flab.ravel()); fs[0] = 0
        alpha = (fs >= 0.08 * fs.max())[flab]
    if not alpha.any():
        return None
    ys, xs = np.nonzero(alpha)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    im = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")
    im.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
    im = im.crop((x0, y0, x1, y1))
    s = hedef_boy / im.height
    small = im.resize((max(1, round(im.width * s)), hedef_boy), Image.Resampling.BOX)
    a = np.asarray(small.getchannel("A"))
    small.putalpha(Image.fromarray(np.where(a >= 128, 255, 0).astype(np.uint8)))
    pal = B.build_palette([small], renk)
    return B.apply_palette(small, pal)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("adlar", nargs="+")
    ap.add_argument("--seeds", nargs="+", type=int, default=[11, 22, 33])
    ap.add_argument("--tur2", action="store_true", help="küçük eşyalar için ikinci istem şablonu")
    ap.add_argument("--onde", action="store_true", help="ComfyUI kuyruğunun önüne al")
    a = ap.parse_args()
    adlar = list(VARLIK) if a.adlar == ["hepsi"] else a.adlar
    B.ONDE = a.onde
    os.makedirs(OUT, exist_ok=True)
    jobs, meta = [], {}
    for ad in adlar:
        p, boy, mod, dn, cn = VARLIK[ad]
        tur2 = a.tur2 and ad in YENI
        pos = STIL_KUCUK.format(p=YENI[ad]) if tur2 else STIL.format(p=p)
        neg = NEG_KUCUK if tur2 else NEG
        inp = taslak(ad) if mod == "taslak" else None
        for s in a.seeds:
            prefix = f"son-kale-v2/ic/ham/{ad}{'_t2' if tur2 else ''}_s{s}"
            done = sorted(glob.glob(f"{B.COMFY}/output/{prefix}_*.png"))
            meta[prefix] = (ad + ("_t2" if tur2 else ""), s, boy, done[-1] if done else None)
            if done:
                continue
            if mod == "taslak":
                wf = B.workflow(inp, prefix, s, dn, cn, pos, neg)
                wf["14"]["inputs"]["end_percent"] = 0.6
            else:
                wf = wf_metin(prefix, s, pos, neg)
            jobs.append((prefix, wf))
    print(f"{len(jobs)} cizim kuyruga alindi ({len(meta) - len(jobs)} hazir)", flush=True)
    paths = B.run_jobs(jobs) if jobs else {}
    for prefix, (ad, s, boy, done) in meta.items():
        im = kes(paths.get(prefix, done), boy)
        if im is not None:
            im.save(f"{OUT}/{ad}_s{s}.png")
    print("kaydedildi:", OUT)


if __name__ == "__main__":
    main()
