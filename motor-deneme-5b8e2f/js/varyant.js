// =============================================================
//  VARYANT (varyant.js)
//  İç kale binalarının görünümü oyunun durumuna göre değişir:
//   - Sur ağır hasarlıysa binalar yıkık görünür (histerezisli).
//   - Mevsimler gün sayısına göre döner; kışın binalar karlı.
//   - Savaşa çıkarken akşam olur: binalar kısa bir an gece görünür.
//  Öncelik: yıkık > gece > karlı > normal. Varyant dosyası yoksa
//  binanın normal görseli kalır. Görseller assets/kale/varyant/.
//  Hızlı deneme: ?sezon=kis&hasar=0.3&gece=1
// =============================================================

const VARYANT_AYAR = {
  sezonUzunlugu: 5,          // her mevsim kaç gün sürer
  sezonlar: [
    { ad: 'İlkbahar', kod: 'ilkbahar' },
    { ad: 'Yaz', kod: 'yaz' },
    { ad: 'Sonbahar', kod: 'sonbahar' },
    { ad: 'Kış', kod: 'kis', varyant: 'karli' },
  ],
  yikikAlt: 0.4,             // sur canı bu oranın altına inince binalar yıkık
  yikikUst: 0.6,             // onarılıp bu oranı geçince yeniden sağlam
  gecisMs: 650,              // görünüm değişince çapraz geçiş süresi
  geceBekleMs: 1100,         // savaşa çıkarken gece görünümü ne kadar kalır
  // zemin, ön surlar ve süslere verilen ton (binalarla uyumlu dursun)
  ton: { karli: 0xcfdbec, gece: 0x56648c },
  // Gece görselleri (binalar, şapel...) zeminden açık ve mavi kalıyordu: zeminin tonuna çekilir
  geceDokuTon: 0xdece8f,
  koyluGeceTon: 0x9aa6c8,   // köylüler gece hafif kararır (fenersiz parlak kalmasın)
  klasor: 'assets/kale/varyant/',
};

const Varyant = {
  // URL ile deneme: ?sezon=kis|yaz|...  ?hasar=0.3 (sur oranı)  ?gece=1
  test: (() => {
    try {
      const p = new URLSearchParams(location.search);
      return { sezon: p.get('sezon'), hasar: p.has('hasar') ? +p.get('hasar') : null, gece: p.get('gece') === '1' };
    } catch (e) { return {}; }
  })(),

  // yukle.js preload: hangi varyant dosyaları var?
  listeyiYukle(loader) { loader.json('kale_varyant', VARYANT_AYAR.klasor + 'varyantlar.json'); },
  // yukle.js create: listedeki dosyaları kv_<bina><seviye>_<varyant> olarak yükle
  gorselleriYukle(sahne) {
    const L = sahne.cache.json.get('kale_varyant');
    if (!L || !L.dosyalar) return;
    for (const [bina, v] of Object.entries(L.dosyalar)) {
      for (const [ad, d] of Object.entries(v)) sahne.load.image(`kv_${bina}_${ad}`, VARYANT_AYAR.klasor + d.dosya);
    }
  },

  gun(oyun) { return (oyun.dalga || 0) + 1; },
  sezon(oyun) {
    const S = VARYANT_AYAR.sezonlar;
    if (this.test.sezon) {
      const t = S.find(s => s.kod === this.test.sezon);
      if (t) return t;
    }
    return S[Math.floor((this.gun(oyun) - 1) / VARYANT_AYAR.sezonUzunlugu) % S.length];
  },

  // Sur hasarı (histerezis: %40 altında yıkılır, %60 üstüne çıkınca düzelir)
  yikikMi(oyun) {
    const oran = this.test.hasar !== null && this.test.hasar !== undefined
      ? this.test.hasar
      : (oyun.surEnFazla ? oyun.surCan / oyun.surEnFazla : 1);
    if (oyun.varyantYikik === undefined) oyun.varyantYikik = oran < (VARYANT_AYAR.yikikAlt + VARYANT_AYAR.yikikUst) / 2;
    if (oran < VARYANT_AYAR.yikikAlt) oyun.varyantYikik = true;
    else if (oran > VARYANT_AYAR.yikikUst) oyun.varyantYikik = false;
    return oyun.varyantYikik;
  },

  hal(sahne) {
    const o = sahne.oyun;
    if (this.yikikMi(o)) return 'yikik';
    if (sahne.geceMi || this.test.gece) return 'gece';
    return this.sezon(o).varyant || null;
  },

  // Akşam (savaşa çıkış) ya da ?gece=1: yıkık hâlde de gece tonu verilir
  geceAktif(sahne) { return !!(sahne.geceMi || this.test.gece); },

  kisMi(sahne) { return this.sezon(sahne.oyun).varyant === 'karli'; },

  // Binanın gösterilecek dokusu (varyant yoksa normal doku).
  // Kış gecesi: karsız _gece yerine karlı doku (üstüne gece tonu, bkz. tonla)
  anahtar(sahne, temel, hal) {
    if (!hal) return temel;
    const kv = h => 'kv_' + temel.slice(2) + '_' + h;   // k_demirci3 → kv_demirci3_karli
    if (hal === 'gece' && this.kisMi(sahne) && sahne.textures.exists(kv('karli'))) return kv('karli');
    // kış + sur hasarı: yıkık binanın karlı sürümü
    if (hal === 'yikik' && this.kisMi(sahne) && sahne.textures.exists(kv('yikik_karli'))) return kv('yikik_karli');
    return sahne.textures.exists(kv(hal)) ? kv(hal) : temel;
  },
  // Doku gece görseliyse hafif ton; gündüz/kar görseli gece gösteriliyorsa koyu gece tonu
  tonla(sahne, sp, doku) {
    if (doku.endsWith('_gece')) sp.setTint(VARYANT_AYAR.geceDokuTon);
    else if (this.geceAktif(sahne) && (doku.endsWith('_karli') || doku.endsWith('_yikik') || this.hal(sahne) === 'yikik')) sp.setTint(VARYANT_AYAR.ton.gece);
    else sp.clearTint();
  },

  // Köylü ve nöbetçiler gece hafif kararır (kale.js koyluYap da çağırır)
  koyluTonu(sahne, sp) {
    if (this.geceAktif(sahne)) sp.setTint(VARYANT_AYAR.koyluGeceTon); else sp.clearTint();
  },
  geceTonu(sp, doku) {
    if (doku.endsWith('_gece')) sp.setTint(VARYANT_AYAR.geceDokuTon); else sp.clearTint();
  },

  // Bina sprite'ına dokuyu uygular; değişiyorsa eskisi yavaşça kaybolur
  uygula(sahne, sp, temel) {
    const yeni = this.anahtar(sahne, temel, this.hal(sahne));
    const eski = sp.texture && sp.texture.key;
    if (eski === yeni) { this.tonla(sahne, sp, yeni); return; } // doku aynı kalsa da ton (kış gündüz → kış gecesi) güncellenmeli
    if (!eski || eski === '__MISSING' || !sp.visible || !sahne.sys.isActive()) { sp.setTexture(yeni); this.tonla(sahne, sp, yeni); return; }
    const hayalet = sahne.add.image(sp.x, sp.y, eski).setOrigin(sp.originX, sp.originY)
      .setScale(sp.scaleX, sp.scaleY).setDepth(sp.depth + 0.001);
    sp.setTexture(yeni);
    this.tonla(sahne, sp, yeni);
    sahne.tweens.add({ targets: hayalet, alpha: 0, duration: VARYANT_AYAR.gecisMs, onComplete: () => hayalet.destroy() });
  },

  // Zemin, ön surlar ve süsler: kışın soğuk, akşam koyu ton.
  // Süsün o hâle ait görseli varsa (ks_<ad>_karli / _gece) onu gösterir, yoksa tonlar.
  zemin(sahne) {
    const h = this.hal(sahne);
    const ton = h === 'gece' ? VARYANT_AYAR.ton.gece : h === 'karli' ? VARYANT_AYAR.ton.karli : null;
    for (const c of sahne.children.list) {
      const k = c.texture && c.texture.key;
      if (k && /^(koylu|nobetci)/.test(k)) { this.koyluTonu(sahne, c); continue; }
      if (!k || !(/^k_(arka|on)(_|$)/.test(k) || k.startsWith('ks_'))) continue;
      // k_arka_karli / k_on_karli / ks_<ad>_karli|_gece varsa onu göster.
      // Kış her hâlde karlı kalır: gece = karlı doku + gece tonu, yıkık (sur hasarı) = karlı doku.
      c.temelDoku = c.temelDoku || k;
      const var_ = h2 => sahne.textures.exists(c.temelDoku + '_' + h2) ? c.temelDoku + '_' + h2 : null;
      const kis = this.kisMi(sahne) ? var_('karli') : null;
      let doku = c.temelDoku, tint = null;
      if (h === 'gece') {
        if (kis) { doku = kis; tint = VARYANT_AYAR.ton.gece; }
        else if (var_('gece')) { doku = var_('gece'); tint = VARYANT_AYAR.geceDokuTon; }
        else tint = VARYANT_AYAR.ton.gece;
      } else if (h === 'karli' || h === 'yikik') {
        if (kis) doku = kis;
        else if (h === 'karli') tint = VARYANT_AYAR.ton.karli;
        if (h === 'yikik' && this.geceAktif(sahne)) tint = VARYANT_AYAR.ton.gece; // yıkık + akşam
      }
      if (k !== doku) c.setTexture(doku);
      if (tint === null) c.clearTint(); else c.setTint(tint);
    }
  },

  // Savaşa çıkarken: akşam olur, sonra savaş başlar
  aksam(sahne, devam) {
    if (!sahne.textures.exists('kv_ev1_gece')) return devam();
    sahne.geceMi = true;
    sahne.yenile();
    sahne.time.delayedCall(VARYANT_AYAR.geceBekleMs, () => { sahne.geceMi = false; devam(); });
  },
};
