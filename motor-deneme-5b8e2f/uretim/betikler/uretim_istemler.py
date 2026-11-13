"""Build uretim/istemler.json: per production type, the settings read from the ComfyUI PNG metadata
(ayarlar_png.json, made by uretim_topla.py) plus the post-processing values from the scripts.
Values that are not recorded anywhere are written as "bilinmiyor".

  python uretim_istemler.py <repo>/motor-deneme-5b8e2f/uretim
"""
import json
import sys

B = "bilinmiyor"


def grupla(A, on_ek):
    """{tag: settings} for the workflows whose name starts with on_ek (prompt text kept once per tag)."""
    return {k.split("__", 2)[-1]: v for k, v in A.items() if k.startswith(on_ek)}


def main(h):
    A = json.load(open(f"{h}/ayarlar_png.json", encoding="utf-8"))
    birimler = sorted({k.split("__")[1] for k in A if k.startswith("son-kale-v2__")} -
                      {"bina", "ic", "arka_hd", "efekt"})
    I = {
        "_aciklama": ("Her üretim türü için ComfyUI ayarları. 'comfyui' alanları çıktı PNG'lerinin içindeki gerçek iş "
                      "akışından okundu (seed, adım, CFG, denoise, ControlNet gücü, istemler). 'son_islem' alanları "
                      "betiklerdeki koddan. Kaydı olmayan değerler 'bilinmiyor'. Tam iş akışları: is-akislari/ui (sürükle-bırak) "
                      "ve is-akislari/api."),
        "ortak": {
            "checkpoint": "sd_xl_base_1.0.safetensors", "lora": "pixel-art-xl.safetensors",
            "vae": "sdxl_vae_fp16_fix.safetensors", "controlnet": "xinsir_canny_sdxl.safetensors",
            "ornekleyici": "dpmpp_2m", "zamanlayici": "karras", "adim": 25, "cozunurluk": [1024, 1024],
            "gpu_notu": "RX 6700 XT: ComfyUI'yi run_amd.py ile başlat (cudnn kapalı). Büyük işlerde VAEDecodeTiled kullan, düz VAEDecode ~9.6 GB isteyip her işi ~10 kat yavaşlatıyor.",
        },
        "savas_birimleri_2x": {
            "betik": "betikler/birim.py (+ rig_insan.py, rig_kurt.py, rig_okcu.py poz rig'leri, kontur.py, aktar.py)",
            "giris": "assets/gorsel/<birim>.png sayfasının her karesi, karakter ~860 px olacak şekilde K kat NEAREST büyütülüp 1024x1024 gri (200,200,200) tuvale konur; rig'li birimlerde --kaynak rig/<ad>.png",
            "istemler_dosyasi": "betikler/istemler.json (birim başına pos/neg; negatif başına NEG_BASE eklenir)",
            "son_islem": {
                "kucultme": "aynı kutudan BOX küçültme, --kat 2 (sayfa 2x)", "alfa": "eski karenin siluet maskesi (NEAREST), kenar bandında arka plan rengine yakın pikseller atılır",
                "palet": "build_palette: yeni + eski karelerin opak pikselleri, varsayılan --renk 32 (birim başına kullanılan değer: bilinmiyor)",
                "kontur": "kontur.py: 2x'te 2 px koyu dış kontur (22,17,20), kontrast 1.12 (her birimde çalıştırıldı mı: bilinmiyor)",
                "kayit": "footY / centerX aynı kalır, kareler.json'daki fw/fh 2 katına çıkar",
            },
            "birimler": {u: grupla(A, f"son-kale-v2__{u}__") for u in birimler},
            "not": "Bir birimde birden çok tarif etiketi varsa (v1, rig1, rig2v...), oyundaki sayfanın hangisinden geldiği kayıtlı değil: bilinmiyor.",
        },
        "efektler_ve_seritler": {
            "betik": "betikler/efekt.py",
            "comfyui": "kullanılmadı: dokular (daire, kare, ok) ve şeritler (kivilcim, duman, patlama, ates, ok_izi) tamamen kodla çizildi, random.seed(7)",
        },
        "bina_varyantlari": {
            "betik": "betikler/bina.py (+ bina_sheet.py karşılaştırma)",
            "giris": "assets/kale/<bina><1-3>.png, siluet ~860 px olacak şekilde NEAREST büyütülüp 1024 gri tuvale; karlı sürümde önce kodla kar eklenir (karla / karla_ust)",
            "karli": {"comfyui": grupla(A, "son-kale-v2__bina__karli4"), "son_islem": "BOX küçültme orijinal boyuta, siluet eskiden, palet --renk 24, kar maskesi kroma aktarımı"},
            "yikik": {"comfyui": grupla(A, "son-kale-v2__bina__yikik3"), "son_islem": "siluet yeni görselden; çiftlik/maden/taşocağı/oduncu için YIKIK_OZEL istemi, denoise 0.78, CN 0.6, end_percent 0.7 (diğerleri 0.45); palet --renk 24"},
            "gece": {"comfyui": "kullanılmadı: bina.gecele() kodla koyu mavi ton + sarı pencere ışığı"},
            "eski_denemeler": {k: v for k, v in grupla(A, "son-kale-v2__bina__").items() if not k.startswith(("karli4", "yikik3"))},
        },
        "ic2_esyalari": {
            "betik": "betikler/ic.py (üretim) -> betikler/uyum.py (palet, gölge, karlı/gece) -> betikler/ic_yerlesim.py (yerleşim önizleme), zemin_ic2.py (zemin izleri, kodla)",
            "giris": "binalar (sapel, ahir, kisla, ambar) ve silahrafi/manken/bayrak: kodla çizilmiş izometrik taslak + ControlNet; diğerleri boş latent txt2img",
            "comfyui": grupla(A, "son-kale-v2__ic__"),
            "son_islem": {"kesme": "köşe renginden arka plan ayıklanır, gölge halkası atılır", "kucultme": "BOX, ekrandaki hedef boya (ic.py VARLIK tablosu, ör. kuyu 54 px, sapel 190 px)",
                          "palet": "eşya başına 24 renk, sonra uyum.py: PixelLab binalarından 72 renklik ortak palet, doygunluk 0.82", "golge": "sol üstten ışık, güç 78 (hayvanlar 60, gece 70)",
                          "secilen_seed": "ComfyUI/output/son-kale-v2/ic/secilen/ altındaki seçim; hangi seed'in seçildiği her eşya için kayıtlı değil: bilinmiyor"},
        },
        "ic_kale_arka_plan_hd": {
            "betik": "betikler/arka_hd.py",
            "giris": "D:/AI/araclar/orijinal/kale/arka.png ve on.png (orijinal 1280x720 / 1240x482; repoda assets/kale/eski/), 1.5x NEAREST büyütme -> 1920x1080 / 1860x723",
            "parca": {"boy": 512, "ortusme": 128, "sd_boyu": "her parça 1024'e NEAREST büyütülür (2x)"},
            "comfyui": {**A.get("son-kale-v2__arka_hd__arka", {}), "lora_guc": [0.8, 0.8], "canny_esik": [0.4, 0.8],
                        "canny_girisi": "parçanın GaussianBlur(1.2) yumuşatılmış kopyası (yalnız büyük hatlar kilitlenir)",
                        "vae": "VAEEncodeTiled / VAEDecodeTiled 512, örtüşme 64"},
            "kis": "--kis: girdi bitmiş yaz HD görseli, kış istemi (POS_KIS / NEG_KIS arka_hd.py içinde); denoise/CN raporlanan komutta",
            "son_islem": {"birlestirme": "parçalar BOX küçültülüp kenarları yumuşak ağırlıkla birleştirilir", "palet": "orijinalden 64 renk (kış: + karlı bina varyantlarından, 96 renk), titreşimsiz",
                          "alfa": "on.png: orijinal alfa maskesinin 1.5x NEAREST kopyası, birebir"},
            "denemeler": grupla(A, "son-kale-v2__arka_hd__deneme"),
        },
        "kaide_temizligi": {"durum": "henüz yapılmadı (adım 2, onay bekliyor)", "ayarlar": B},
        "dusman_olcek_esitleme": {"durum": "henüz yapılmadı (adım 3, onay bekliyor)", "hedef_olcek": 0.5, "ayarlar": B},
        "ilk_denemeler": {k: v for k, v in A.items() if k.startswith(("son-kale-deneme__", "son-kale-deneme2__"))},
    }
    json.dump(I, open(f"{h}/istemler.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("yazildi", len(json.dumps(I)))


if __name__ == "__main__":
    main(sys.argv[1])
