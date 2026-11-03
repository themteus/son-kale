# Son Kale · Phaser 4 deneme sürümü (savaş ekranı)

Eski oyunun (kule-savunma/) savaş ekranının Phaser 4 motoruyla yeniden yapılmış hali.
Henüz iç kale, ekonomi ve cephe haritası yok; yalnızca savaş + dalga arası dükkân.

## Çalıştırma
Bir yerel sunucu gerekir (dosyayı çift tıklamak yetmez, tarayıcı görselleri yüklemez):
`python3 -m http.server` → http://localhost:8000

## Dosyalar
- `js/ayarlar.js`  : bütün sayılar (hasar, hız, can, dalgalar, dükkân)
- `js/yukle.js`    : görsel/ses yükleme, animasyonlar
- `js/cizim.js`    : gökyüzü, dağlar, orman, zemin, kale ve hasar aşamaları
- `js/dusman.js`   : zombi, koşucu, iskelet, dev, yarasa
- `js/okcu.js`     : oyuncunun yayı (bas = ger, bırak = at) ve okçu askerler
- `js/arayuz.js`   : üst bilgi, düğmeler, pencereler
- `js/savas.js`    : oyunun akışı, oklar, isabet
- `assets/gorsel/kareler.json`: her şeridin kare boyu ve ayak noktası

## Görseller nereden?
Karakterler Quaternius'un CC0 (serbest, ticari kullanım dahil) 3D modellerinden yandan
çizilip piksel şeride çevrildi. Dokular Screaming Brain Studios (CC0), sesler Kenney (CC0),
müzik "Battle Theme A" cynicmusic (CC0). Ayrıntı: `assets/LISANS-NOTICE.txt`.
Phaser 4.2.1 MIT lisanslıdır.

Başka bir çizim (ör. itch.io paketi ya da Gemini çizimleri) koymak için: aynı adla
`assets/gorsel/` içine şerit koy ve `kareler.json` içindeki kare boylarını güncelle.
