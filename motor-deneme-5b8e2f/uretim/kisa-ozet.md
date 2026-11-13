# Son Kale görsel üretimi: kısa özet

Bu klasör, Son Kale görsellerini bu PC'deki ComfyUI ile (Claude olmadan) yeniden üretebilmen için.

## İçerik

| Yol | Ne |
|---|---|
| `betikler/` | Kullanılan bütün Python betikleri, olduğu gibi (`birim.py`, `bina.py`, `ic.py`, `uyum.py`, `arka_hd.py` ...) ve onların okuduğu JSON'lar (`istemler.json` = birim istemleri, `ic_yerlesim.json`, `rig/*_noktalar.json`) |
| `is-akislari/ui/` | ComfyUI'ye **sürükle-bırak** ile açılan iş akışları (her tarif için bir tane) |
| `is-akislari/api/` | Aynı iş akışlarının API biçimi (betiklerin ComfyUI'ye gönderdiği hâli) |
| `istemler.json` | Her üretim türünün ayarları: istemler, model, LoRA, ControlNet, seed, adım, CFG, denoise, parça boyu, son işlem. Kaydı olmayan değerler `bilinmiyor`. |
| `ayarlar_png.json` | Çıktı PNG'lerinin içinden okunan ham ayarlar (istemler.json bunlardan kuruldu) |

Dosya adları: `son-kale-v2__<tür>__<tarif>_s<seed>.json`. Örnek: `son-kale-v2__zombi__v1_s22.json` = zombi, tarif v1, seed 22.

## Gerekenler

- `D:\AI\ComfyUI` ve modeller: `models/checkpoints/sd_xl_base_1.0.safetensors`, `models/loras/pixel-art-xl.safetensors`,
  `models/vae/sdxl_vae_fp16_fix.safetensors`, `models/controlnet/xinsir_canny_sdxl.safetensors`.
- ComfyUI'yi **AMD başlatıcısıyla** aç (RX 6700 XT'de MIOpen çöküyor):
  ```
  cd D:\AI\ComfyUI
  .venv\Scripts\python.exe run_amd.py --listen 127.0.0.1 --port 8188
  ```
- Betikleri ComfyUI'nin Python'uyla çalıştır (scipy, numpy, PIL orada var):
  `D:\AI\ComfyUI\.venv\Scripts\python.exe <betik> ...`
- Betikler `D:/AI/araclar` ve `D:/AI/son-kale` yollarını sabit kullanıyor. Başka yerden çalıştıracaksan dosya başındaki
  `REPO`, `COMFY`, `GORSEL` gibi sabitleri düzelt. Orijinal görseller `D:/AI/araclar/orijinal/` altında dondurulmuş durumda.

## Elle (ComfyUI arayüzünde) tek görsel üretmek

1. `is-akislari/ui/` içinden istediğin tarifi ComfyUI sayfasına sürükle.
2. **LoadImage** düğümüne giriş görselini koy. Giriş her zaman 1024x1024 gri (200,200,200) zemin üzerine, eski
   görselin **NEAREST (en yakın komşu)** ile büyütülmüş hâli:
   - savaş birimi: tek kare, karakter ~860 px olacak kadar tamsayı katla büyütülüp ortalanır
   - bina: binanın kendisi, ~860 px olacak şekilde
   - arka plan: 512x512 parça, 2 katına (1024) büyütülür; ikinci LoadImage (canny girişi) aynı parçanın hafif bulanık kopyası
3. **Queue** ile çalıştır. Çıktı `ComfyUI/output/` altına düşer.
4. Çıktıyı oyuna sokmadan önce son işlem şart (BOX ile eski boya küçült, eski siluet maskesi, palet). Bunu elle yapmak
   zor; aşağıdaki betikler bunu otomatik yapıyor. Arayüz daha çok "bir ayarı tek kare üzerinde denemek" için.

## Betiklerle (önerilen yol)

Hepsi `D:\AI\araclar` içinden, ComfyUI açıkken çalışır; işler kuyruğa alınır, bitince son işlem yapılır.

**Savaş birimi (2x sayfa)**
```
python birim.py deneme zombi 0 3 12 --seeds 11 22 --denoise 0.55 --cn 0.7    # birkaç kare, karşılaştırma şeridi
python birim.py tam zombi --seed 22 --denoise 0.55 --cn 0.7 --etiket v1       # bütün sayfa
python kontur.py <cikti.png> <cikti.png>                                       # koyu dış kontur
python aktar.py zombi                                                          # oyuna kopyala, kareler.json güncelle
```
Okçu/asker/kurt/okçu-iskelet önce rig ile poz çizilir: `python rig_okcu.py`, `python rig_kurt.py`, `python rig_insan.py`,
sonra `birim.py tam <ad> --kaynak D:/AI/araclar/rig/<ad>.png ...`. Her birimin denoise/CN/seed değeri `istemler.json →
savas_birimleri_2x.birimler`.

**Bina varyantları (karlı / yıkık / gece)**
```
python bina.py hepsi --varyant karli yikik gece --seed 22
python bina_sheet.py D:/AI/son-kale-cikti/binalar.png ev1,ev2,ev3       # karşılaştırma
```
Çıktı `ComfyUI/output/son-kale-v2/bina/<varyant>/`. Gece sürümü yapay zekâsız (kodla ton).

**İç kale eşyaları (ic2)**
```
python ic.py kuyu sapel --seeds 11 22 33     # her eşya için 3 aday
# beğendiğini ComfyUI/output/son-kale-v2/ic/secilen/<ad>.png olarak kopyala
python uyum.py                               # palet + gölge + _karli/_gece, repoya yazar
python ic_yerlesim.py 3 D:/AI/son-kale-cikti/yerlesim.png   # yerleşim önizleme
python zemin_ic2.py                          # zemin izleri (kodla)
```

**İç kale arka planı / ön sur (1x piksel yoğunluğu)**
```
python arka_hd.py deneme arka --x 495 --y 570 --t 512 768 --denoise 0.4 0.55   # ayar denemesi
python arka_hd.py tam arka --t 512 --ov 128 --denoise 0.4 --cn 0.5 --seed 7
python arka_hd.py tam on   --t 512 --ov 128 --denoise 0.4 --cn 0.5 --seed 7
python arka_hd.py tam arka --kis ...   # karlı sürüm: bitmiş yaz görselinden başlar
```
Çıktı `ComfyUI/output/son-kale-v2/arka_hd/`. Tam arka plan bu GPU'da parça başı ~2.5 dk (15 parça).

**Efektler / şeritler**: `python efekt.py` (yapay zekâ yok, tamamen kod).

**Ayar dosyalarını yeniden toplamak**: `python uretim_topla.py <bu klasör>` sonra `python uretim_istemler.py <bu klasör>`.

## Bilinen tuzaklar

- Düz `VAEDecode` bu kartta ~9.6 GB isteyip taşıyor, sonraki bütün işler ~10 kat yavaşlıyor. Yavaşlarsa ComfyUI'yi
  yeniden başlat; büyük işlerde `VAEDecodeTiled` kullan (arka_hd.py öyle yapıyor).
- Denoise yükseldikçe kompozisyon kayar (arka planda 0.55'te sur hattı oynuyor, 0.4 güvenli).
- Seed sabit kalırsa sonuç tekrarlanır; aynı ayarla farklı sonuç için seed'i değiştir.

## İç kale arka planı: son akış (yaz + kış)

```
python arka_hd.py tam arka --t 512 --ov 128 --denoise 0.4 --cn 0.5 --seed 7   # 64 px aynalı dolgu, koruma kutuları
python arka_hd.py tam on   --t 512 --ov 128 --denoise 0.4 --cn 0.5 --seed 7
python tas_desen.py on        # surlara kodla düzenli taş deseni -> on_desen.png
python tas_desen.py arka      # aynı + ana kale sarmaşık/kırmızı, meşale, ön sur halesi -> arka_desen.png
python kar2.py arka on       # kış: nesneler bütün, kar yalnız üst kenarlarda + 4-5 tonlu zemin karı -> *_karli.png
```
Oyuna: `arka_desen.png -> assets/kale/arka.png`, `on_desen.png -> on.png`, `*_karli.png` aynı adla.
Yüz poligonları `tas_desen.py` içinde (orijinal 1280x720 / 1240x482 koordinatları), koruma kutuları `arka_hd.py KORU`.
