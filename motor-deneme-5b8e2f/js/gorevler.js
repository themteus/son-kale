// =============================================================
//  GÖREVLER (gorevler.js)
//  İlk günlerde oyunu adım adım öğreten küçük, ödüllü görevler.
//  Sırayla açılır; biri bitince ödülü verilir, sıradaki gelir.
//  Hepsi bitince her gün bir "günün görevi" çıkar (ödülü Şan, şan.js).
//  hedef: iç kalede etiketi yanıp sönen yer (kale.js → etiket)
//  tamam(o, E): görev bitti mi? (o = savaş sahnesi, E = ekonomi)
// =============================================================

const GOREVLER = [
  { ad: 'Yaycıya 2 işçi ver', aciklama: 'Yaycı odun ve uçtan ok yapar. Ok biterse kule susar.', hedef: 'yayci', odul: { altin: 20 },
    tamam: (o, E) => E.bina.yayci.isci >= 2 },
  { ad: 'Sura bir okçu asker çıkar', aciklama: 'Kapı kulesine tıkla: her asker bir yay ister.', hedef: 'sur', odul: { altin: 25 },
    tamam: (o, E) => E.asker >= 1 },
  { ad: 'Bir gece 3 kafa vuruşu yap', aciklama: 'Kafaya isabet iki kat vurur ve altın verir.', odul: { altin: 30 },
    tamam: (o) => o.sonAtis && o.sonAtis.kafa >= 3 },
  { ad: 'Silah ustasından bir yükseltme al', aciklama: 'Alttaki "Silah ustası" düğmesi: yay, ok ve askerler.', odul: { altin: 30 },
    tamam: (o) => ['hasar', 'germe', 'coklu', 'yagmur', 'egitim', 'payanda'].some(k => (o.seviye[k] || 0) > 0) },
  { ad: 'Bir binayı 2. seviyeye çıkar', aciklama: 'Binaya tıkla, "Yükselt": daha çok işçi, daha çok üretim.', hedef: 'ciftlik', odul: { odun: 30, tas: 20 },
    tamam: (o, E) => Object.values(E.bina).some(b => b.seviye >= 2) },
  { ad: 'Pazarda alışveriş yap', aciklama: 'Kuyu meydanındaki pazarda fazlanı sat, eksiğini al.', hedef: 'pazar', odul: { altin: 30 },
    tamam: (o, E) => (E.ticaretSayisi || 0) > 0 },
  { ad: '5\'li kombo yap', aciklama: 'Düşmanları art arda hızlı öldür: kombo ek altın verir.', odul: { altin: 50 },
    tamam: (o) => o.enIyiKombo >= 5 },
  { ad: 'Suru 2. seviyeye çıkar', aciklama: 'Kapı kulesi: sur daha sağlam olur, okçu yeri artar.', hedef: 'sur', odul: { altin: 60 },
    tamam: (o, E) => E.surSeviye >= 2 },
  { ad: 'Kışlayı kur', aciklama: 'Kışla askerleri hızlandırır ve 4 yatak verir.', hedef: 'kisla', odul: { altin: 80 },
    tamam: (o, E) => E.yapi.kisla.seviye >= 1 },
  { ad: 'Ahırdan sefere adam gönder', aciklama: 'Boştaki halk ertesi gün ganimetle döner. Biraz risklidir.', hedef: 'ahir', odul: { altin: 60 },
    tamam: (o, E) => E.sefer > 0 || (E.rapor && E.rapor.sefer) },
  { ad: 'İlk Ak Devi yık', aciklama: '10. gece birinci höyük açılır. Kafasına vur!', odul: { altin: 150 },
    tamam: (o) => o.dalga >= PATRON_ARASI },
];

// Günün görevi: öğretici görevler bitince her gün biri seçilir. Ödülü Şan (oyunlar arası).
//  hedef(n) : n. dalgaya göre sayı · tamam(o, h): dünkü gecede başarıldı mı
const GUNLUK_GOREVLER = [
  { ad: h => `Bu gece %${h} isabet tuttur`, hedef: () => 65, san: 2,
    tamam: (o, h) => o.sonAtis && o.sonAtis.isabet + o.sonAtis.iska >= 10 && 100 * o.sonAtis.isabet / (o.sonAtis.isabet + o.sonAtis.iska) >= h },
  { ad: h => `Bu gece ${h} kafa vuruşu yap`, hedef: n => Math.min(30, 6 + Math.round(n * 0.6)), san: 2,
    tamam: (o, h) => o.sonAtis && o.sonAtis.kafa >= h },
  { ad: h => `Bu gece ${h}'li kombo yap`, hedef: n => Math.min(14, 5 + Math.floor(n / 4)), san: 2,
    tamam: (o, h) => o.sonAtis && o.sonAtis.kombo >= h },
  { ad: h => `Geceyi surun %${h} canıyla bitir`, hedef: () => 80, san: 2,
    tamam: (o, h) => o.sonAtis && o.sonAtis.surOran * 100 >= h },
];

const Gorevler = {
  // Oyun durumu (savas.js kaydeder): sira = sıradaki öğretici görev, gunluk = bugünün görevi
  yeni() { return { sira: 0, gunluk: null }; },

  simdiki(o) {
    const G = o.gorev;
    if (G.sira < GOREVLER.length) {
      const g = GOREVLER[G.sira];
      return { ad: g.ad, aciklama: g.aciklama, hedef: g.hedef, odul: this.odulYazi(g.odul) };
    }
    if (G.gunluk) {
      const g = GUNLUK_GOREVLER[G.gunluk.i];
      return { ad: 'Günün görevi: ' + g.ad(G.gunluk.h), aciklama: 'Başarırsan bir sonraki oyuna kalan Şan kazanırsın.', odul: `${g.san} Şan`, gunluk: true };
    }
    return null;
  },

  odulYazi(od) {
    return Object.entries(od).map(([k, v]) => `${v} ${k === 'altin' ? 'altın' : KAYNAKLAR[k].ad.toLowerCase()}`).join(', ');
  },

  // Öğretici görev bitti mi? Bittiyse ödül verilir; yazı(metin) bildirimi gösterir.
  kontrol(o, yazi) {
    const G = o.gorev, E = o.ekonomi;
    let biten = null;
    while (G.sira < GOREVLER.length && GOREVLER[G.sira].tamam(o, E)) {
      const g = GOREVLER[G.sira];
      for (const [k, v] of Object.entries(g.odul)) { if (k === 'altin') o.altin += v; else E.kaynak[k] += v; }
      G.sira++;
      biten = g;
    }
    if (biten) {
      if (yazi) yazi(`Görev tamam: ${biten.ad}\nÖdül: ${this.odulYazi(biten.odul)}`);
      o.sesCal('level_up', 0.4);
    }
    return biten;
  },

  // Gece bitince: günün görevini değerlendir, yarına yenisini seç
  geceBitti(o) {
    const G = o.gorev;
    let sonuc = null;
    if (G.gunluk) {
      const g = GUNLUK_GOREVLER[G.gunluk.i];
      if (g.tamam(o, G.gunluk.h)) { sonuc = `Günün görevi başarıldı: +${g.san} Şan`; San.ekle(g.san); o.sanKazanilan = (o.sanKazanilan || 0) + g.san; }
      G.gunluk = null;
    }
    if (G.sira >= GOREVLER.length) {
      const i = Math.floor(Math.random() * GUNLUK_GOREVLER.length);
      G.gunluk = { i, h: GUNLUK_GOREVLER[i].hedef(o.dalga + 1) };
    }
    return sonuc;
  },
};
