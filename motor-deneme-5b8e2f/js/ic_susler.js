// =============================================================
//  İÇ KALE SÜSLERİ (ic_susler.js)
//  assets/kale/kale_ic2.json'daki yapı ve eşyaları (şapel, ahır,
//  kuyu, tezgâhlar, hayvanlar...) iç kalenin süs listesine ekler.
//  Bunlar kale.js'in mevcut süs çizimiyle gelir: tıklanmaz, y'ye
//  göre sıralanır, varyant.js'in kış/gece tonunu alır.
//  Görseller: assets/kale/sus/ic2/<ad>.png
//  Yerleşim: araçla ölçülüp düzenlendi (binalar sura binmez, şapel/ahır/kışla
//  avlunun içinde). Patikalar kapıdan meydana ve her binanın kapısına gider.
//  Yoğunluk: IC_AYAR.yogunluk (1 = hepsi, 0.66 = önemliler,
//  0.33 = yalnız temel olanlar). Deneme: ?yogunluk=0.5
// =============================================================

const IC_AYAR = {
  yogunluk: 1,
};

const IcSusler = {
  // yukle.js preload
  listeyiYukle(loader) { loader.json('kale_ic2', 'assets/kale/kale_ic2.json'); },

  // yukle.js create: süs listesine ekle (görseller kale.js'in süs yüklemesiyle gelir)
  birlestir(KM, L) {
    if (!KM || !L || !Array.isArray(L.susler)) return;
    let y = IC_AYAR.yogunluk;
    try { const p = new URLSearchParams(location.search); if (p.has('yogunluk')) y = +p.get('yogunluk'); } catch (e) { /* önemli değil */ }
    const sinir = y >= 0.99 ? 3 : y >= 0.5 ? 2 : y > 0 ? 1 : 0;
    KM.susler = KM.susler || [];
    for (const s of L.susler) {
      if ((s.oncelik || 1) > sinir) continue;
      KM.susler.push({ ad: 'ic2/' + s.ad, x: s.x, y: s.y, piksel: s.piksel || 1, ayna: !!s.ayna, disari: !!s.disari });
    }
  },

  // kale.js create: zemin katmanı (patikalar, ezilmiş toprak, ot, saman), arka planın hemen üstünde
  zeminKatmani(sahne) {
    if (!sahne.textures.exists('ks_ic2/zemin')) return;
    // Patika katmanı ekran boyunda (1920 genişlik → 1x); eski 1280'lik katman 1.5x büyütülür
    const p = AYAR.en / sahne.textures.get('ks_ic2/zemin').getSourceImage().width;
    sahne.add.image(0, 0, 'ks_ic2/zemin').setOrigin(0).setScale(p).setDepth(1);
  },

  // yukle.js create: zemin katmanı ve kış/gece görselleri (ks_ic2/<ad>_karli, _gece); varyant.js bunları kullanır
  varyantlariYukle(sahne, L) {
    // Patikaların ayrı kış/gece görseli yok: arka planla aynı tonu alır (yoksa gece mavi kalıyordu)
    sahne.load.image('ks_ic2/zemin', 'assets/kale/sus/ic2/zemin.png');
    if (!L || !L.varyantlar) return;
    for (const [ad, liste] of Object.entries(L.varyantlar)) {
      for (const v of liste) sahne.load.image(`ks_ic2/${ad}_${v}`, `assets/kale/sus/ic2/${ad}_${v}.png`);
    }
  },
};
