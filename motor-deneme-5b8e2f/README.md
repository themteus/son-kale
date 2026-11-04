# Son Kale · Phaser 4 sürümü

Eski oyunun (kule-savunma/) Phaser 4 motoruyla yeniden yapılmış hali.
Gündüz iç kaleyi yönetirsin, gece surda savaşırsın. Her dalga bir gündür.
Henüz cephe haritası (dört sur) yok; tek cephede savaşılır.

## Çalıştırma
Bir yerel sunucu gerekir (dosyayı çift tıklamak yetmez, tarayıcı görselleri yüklemez):
`python3 -m http.server` → http://localhost:8000

## Oyunun akışı
1. İç kale: halkı binalara dağıt (ya da "Otomatik dağıt"), bina ve sur yükselt,
   pazardan al-sat, silah ustasından (dükkân) yay yükseltmesi al.
2. Savaş: her ok ambardan gider. Askerler de ok harcar.
3. Gün sonu: binalar üretir, halk yer, duvarcılar suru onarır, ıskalanan okların
   çoğu, saplananların azı toplanır. Rapor iç kalede açılır.
4. Sur ilk yıkıldığında ambarda 40 odun varsa halk bir kez barikat kurar (surun %25'i).
   İkinci kez yıkılırsa ya da halk 5 kişinin altına inerse oyun biter.

## Yardımcı kurallar
- **Gözcüler:** iç kalede ve dükkânda yarınki dalga yazar (kaç düşman, kaç dev, patron var mı).
- **Kafa serisi:** art arda 3 kafa vuruşu → sıradaki tam gerili ok "keskin" olur (×2 hasar,
  kalkanı ve 3 düşmanı deler). Iskalamak seriyi bozar. Sol üstteki 3 elmas seriyi gösterir.
- **Eksiği altınla al:** bina ve sur yükseltmesinde malzeme eksikse, eksik kısım pazar
  fiyatının biraz üstüne altınla alınabilir.
- **Kayıt:** her gün iç kaleye girerken oyun kaydedilir; menüde "Devam et" çıkar.
  Kale düşünce kayıt silinir.

## Dosyalar
- `js/ayarlar.js`  : bütün sayılar (hasar, hız, can, dalgalar, dükkân, binalar, sur, pazar)
- `js/yukle.js`    : görsel/ses yükleme, animasyonlar
- `js/cizim.js`    : savaş ekranının gökyüzü, dağlar, orman, zemin, kale ve hasar aşamaları
- `js/dusman.js`   : düşman türleri ve davranışları
- `js/okcu.js`     : oyuncunun yayı (bas = ger, bırak = at) ve okçu askerler
- `js/arayuz.js`   : savaş ekranının üst bilgisi, düğmeler, pencereler
- `js/ekonomi.js`  : kaynaklar, nüfus, binalar, gün sonu hesabı, pazar, otomatik dağıt
- `js/kale.js`     : iç kale sahnesi (binalar, köylüler, paneller)
- `js/savas.js`    : oyunun akışı, oklar, isabet
- `assets/gorsel/kareler.json`: savaş şeritlerinin kare boyu ve ayak noktası
- `assets/kale/kale.json`: iç kale binalarının yeri (her binanın 3 seviyesi), tıklama alanları, köylü şeritleri

## Görseller nereden?
Karakterler Quaternius'un CC0 (serbest, ticari kullanım dahil) 3D modellerinden yandan
çizilip piksel şeride çevrildi. İç kale izometrik açıdan (2:1) çizildi: surlar, kuleler,
binalar (3 seviye) ve süs eşyaları 3D parçalardan kurulup küçük boyda çizildi, renkleri
azaltılıp siyah kontur verildi, oyunda 3 kat büyütülür. Maden ve taş ocağı surun dışındadır. Sesler Kenney (CC0),
müzik "Battle Theme A" cynicmusic (CC0). Ayrıntı: `assets/LISANS-NOTICE.txt`.
Phaser 4.2.1 MIT lisanslıdır.

Başka bir çizim koymak için: aynı adla `assets/gorsel/` ya da `assets/kale/` içine
görsel koy ve json dosyasındaki boyları/yerleri güncelle.
