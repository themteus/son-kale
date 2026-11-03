// =============================================================
//  İÇ KALE (kale.js)
//  Dalgalar arasında açılan sahne: binalar, köylüler, ambar.
//  Binaya tıkla → sağda paneli açılır (işçi, yükseltme).
//  Kapı kulesi = sur ve askerler, kuyu meydanı = pazar,
//  arkadaki büyük kule = günün raporu.
//  Görseller 3D sahneden çizildi (assets/kale, kale.json).
// =============================================================

// Tıklanabilir yerler (1920x1080 sahnede dikdörtgen: x, y, en, boy)
const KALE_ALANLARI = {
  // ey: adın yazıldığı yükseklik (alanın üstünden)
  sur:   { ad: 'Sur ve Kapı', x: 1770, y: 430, w: 150, h: 330, ey: 30 },
  pazar: { ad: 'Pazar',       x: 850, y: 600, w: 220, h: 130, ey: 0 },
  rapor: { ad: 'Günün raporu', x: 840, y: 40,  w: 240, h: 320, ey: 160 },
};

class KaleSahnesi extends Phaser.Scene {
  constructor() { super('kale'); }

  init(veri) {
    this.oyun = veri.oyun;
    this.ilkRapor = veri.rapor || null;
  }

  create() {
    this.E = this.oyun.ekonomi;
    this.M = this.cache.json.get('kale');
    this.add.image(0, 0, 'k_arka').setOrigin(0);
    this.secili = null;
    this.panel = null;
    this.binaSprite = {};
    this.etiket = {};
    this.koyluler = { };   // grup adı → köylü listesi
    this.binalariKur();
    this.alanlariKur();
    this.arayuzKur();
    this.yenile();
    this.events.on('wake', (s, veri) => { this.ilkRapor = veri && veri.rapor; this.yenile(); this.raporGoster(); });
    this.raporGoster();
  }

  // ---------------- Binalar ----------------
  binalariKur() {
    for (const k of Object.keys(BINALAR)) {
      const sp = this.add.image(0, 0, 'k_' + k + '1').setOrigin(0);
      sp.setInteractive({ pixelPerfect: true, useHandCursor: true })
        .on('pointerover', () => this.etiketVurgu(k, true))
        .on('pointerout', () => this.etiketVurgu(k, false))
        .on('pointerdown', () => this.sec(k));
      this.binaSprite[k] = sp;
      const t = this.add.text(0, 0, '', stil('govde', 22, { fontStyle: 'bold', backgroundColor: '#1a1410cc', padding: { x: 8, y: 3 } }))
        .setOrigin(0.5, 1).setDepth(90);
      this.etiket[k] = t;
    }
  }
  binaMeta(k) { return this.M.binalar[k + this.E.bina[k].seviye]; }
  binaGorsel(k) {
    const m = this.binaMeta(k), sp = this.binaSprite[k];
    sp.setTexture('k_' + k + this.E.bina[k].seviye).setPosition(m.x, m.y).setDepth(10 + m.dipY / 1000);
    const B = BINALAR[k], b = this.E.bina[k];
    const yazi = k === 'ev' ? `${B.ad}  ${this.E.nufus}/${this.E.barinak}` : `${B.ad}  ${b.isci}/${this.E.yerSayisi(k)}`;
    this.etiket[k].setText(yazi).setPosition(m.merkez[0], m.y + 18);
  }
  etiketVurgu(k, acik) {
    this.etiket[k].setColor(acik || this.secili === k ? '#ffe08a' : '#efe6d2');
  }

  alanlariKur() {
    for (const [ad, A] of Object.entries(KALE_ALANLARI)) {
      const z = this.add.zone(A.x, A.y, A.w, A.h).setOrigin(0).setInteractive({ useHandCursor: true });
      const t = this.add.text(A.x + A.w / 2, A.y + A.ey, A.ad,
        stil('govde', 22, { fontStyle: 'bold', backgroundColor: '#1a1410cc', padding: { x: 8, y: 3 } })).setOrigin(0.5, 1).setDepth(90);
      z.on('pointerover', () => t.setColor('#ffe08a')).on('pointerout', () => t.setColor(this.secili === ad ? '#ffe08a' : '#efe6d2'))
        .on('pointerdown', () => this.sec(ad));
      this.etiket[ad] = t;
    }
  }

  // ---------------- Arayüz ----------------
  arayuzKur() {
    const D = 100;
    this.ust = this.add.graphics().setDepth(D);
    this.ust.fillStyle(0x120e0c, 0.88).fillRect(0, 0, AYAR.en, 64);
    this.ust.lineStyle(2, 0x6a5430).lineBetween(0, 64, AYAR.en, 64);
    this.kaynakYazi = {};
    // Kaynak adı küçük, sayı büyük; yanında yarınki değişim
    let x = 20;
    for (const k of ['odun', 'tas', 'demir', 'yiyecek', 'uc', 'ok', 'yay']) {
      this.ust.fillStyle(KAYNAKLAR[k].renk, 1).fillRect(x, 10, 14, 14);
      this.add.text(x + 20, 17, KAYNAKLAR[k].ad, stil('govde', 18, { color: '#b8ac94' })).setOrigin(0, 0.5).setDepth(D + 1);
      this.kaynakYazi[k] = this.add.text(x, 44, '', stil('govde', 24, { fontStyle: 'bold' })).setOrigin(0, 0.5).setDepth(D + 1);
      x += 196;
    }
    this.altinYazi = this.add.text(AYAR.en - 230, 32, '', stil('govde', 28, { fontStyle: 'bold', color: '#ffd76a' })).setOrigin(1, 0.5).setDepth(D + 1);
    this.gunYazi = this.add.text(AYAR.en - 24, 32, '', stil('baslik', 34)).setOrigin(1, 0.5).setDepth(D + 1);
    // Alt şerit
    this.alt = this.add.graphics().setDepth(D);
    this.alt.fillStyle(0x120e0c, 0.88).fillRect(0, AYAR.boy - 96, AYAR.en, 96);
    this.alt.lineStyle(2, 0x6a5430).lineBetween(0, AYAR.boy - 96, AYAR.en, AYAR.boy - 96);
    this.halkYazi = this.add.text(30, AYAR.boy - 48, '', stil('govde', 26, { fontStyle: 'bold' })).setOrigin(0, 0.5).setDepth(D + 1);
    this.uyari = this.add.text(AYAR.en / 2, AYAR.boy - 130, '', stil('govde', 26, { color: '#ffb080', stroke: '#120e0c', strokeThickness: 6 }))
      .setOrigin(0.5).setDepth(D + 1);
    this.dugme(890, AYAR.boy - 48, 270, 70, 'Otomatik dağıt', () => { this.E.otomatikDagit(this.oyun); this.yenile(); }, D + 1, 26);
    this.dugme(1180, AYAR.boy - 48, 270, 70, 'Silah ustası', () => this.dukkanaGit(), D + 1, 26);
    this.savasDugme = this.dugme(1620, AYAR.boy - 48, 520, 76, '', () => this.savasaCik(), D + 1, 32);
  }

  dugme(x, y, w, h, metin, fn, derinlik = 101, boyut = 28) {
    const kap = this.add.container(x, y).setDepth(derinlik);
    const arka = this.add.rectangle(0, 0, w, h, 0x2a211a, 0.95).setStrokeStyle(3, 0xc9a24a);
    const yazi = this.add.text(0, 0, metin, stil('govde', boyut, { fontStyle: 'bold' })).setOrigin(0.5);
    kap.add([arka, yazi]);
    arka.setInteractive({ useHandCursor: true })
      .on('pointerover', () => arka.setFillStyle(0x4a3a28, 0.95))
      .on('pointerout', () => arka.setFillStyle(0x2a211a, 0.95))
      .on('pointerdown', (p, lx, ly, e) => { e && e.stopPropagation(); this.oyun.sesCal('ui', 0.4); fn(); });
    kap.arka = arka;
    kap.yazi = yazi;
    return kap;
  }

  // Her değişiklikten sonra: binalar, köylüler, şeritler, panel
  yenile() {
    const E = this.E, o = this.oyun;
    for (const k of Object.keys(BINALAR)) { this.binaGorsel(k); this.etiketVurgu(k, false); }
    const t = E.gunuHesapla(o, false);
    for (const k in this.kaynakYazi) {
      const net = (t.yapilan[k] || 0) - (t.harcanan[k] || 0);
      this.kaynakYazi[k].setText(`${E.kaynak[k]}` + (net ? ` (${net > 0 ? '+' : ''}${net})` : ''));
      this.kaynakYazi[k].setColor(net < 0 && E.kaynak[k] + net < 0 ? '#ff9a7a' : '#efe6d2');
    }
    this.altinYazi.setText(`Altın ${o.altin}`);
    this.gunYazi.setText(`${o.dalga + 1}. Gün`);
    this.halkYazi.setText(`Halk ${E.nufus}/${E.barinak}  ·  İşçi ${E.isci}  ·  Asker ${E.asker}  ·  Boşta ${E.bosta}`);
    this.halkYazi.setColor(E.bosta > 0 ? '#ffe08a' : '#efe6d2');
    const sonraki = o.dalga + 1;
    this.savasDugme.yazi.setText(sonraki % PATRON_ARASI === 0 ? `Savaşa çık ▶ (Ak Dev!)` : `Savaşa çık ▶ ${sonraki}. dalga`);
    // Uyarılar
    const u = [];
    if (t.yenen < t.ihtiyac) u.push('Yiyecek yetmeyecek: çiftliğe işçi ver!');
    // Dünkü kadar ok atılırsa yeter mi? (her dalga biraz daha çok ister)
    const dun = E.rapor ? E.rapor.atilan : 0;
    if (E.kaynak.ok < Math.max(80, dun * 1.2)) u.push(`Ambarda ok az: dün ${dun} ok atıldı!`);
    if (o.surCan < o.surEnFazla * 0.4) u.push('Sur ağır hasarlı: duvarcıya işçi ver ya da altınla onar.');
    if (E.bosta > 0) u.push(`${E.bosta} kişi boşta.`);
    this.uyari.setText(u.join('   '));
    this.koyluleriDiz();
    if (this.panelYenile) this.panelYenile();
  }

  // ---------------- Seçim paneli (sağda) ----------------
  sec(ad) {
    this.oyun.sesCal('ui', 0.3);
    this.secili = ad;
    for (const k in this.etiket) this.etiket[k].setColor(k === ad ? '#ffe08a' : '#efe6d2');
    if (ad === 'sur') this.panelKur('Sur ve Askerler', p => this.surPaneli(p));
    else if (ad === 'pazar') this.panelKur('Pazar', p => this.pazarPaneli(p));
    else if (ad === 'rapor') this.raporGoster(true);
    else this.panelKur(BINALAR[ad].ad, p => this.binaPaneli(p, ad));
  }

  panelKapat() {
    if (this.panel) this.panel.destroy();
    this.panel = null;
    this.panelYenile = null;
    this.secili = null;
    for (const k in this.etiket) this.etiket[k].setColor('#efe6d2');
  }

  // Sağda pencere. icerik(p) satırları ekler; p.satir(y, metin) vb.
  panelKur(baslik, icerik) {
    if (this.panel) this.panel.destroy();
    const W = 560, H = 880, x = AYAR.en - W / 2 - 16, y = 84 + H / 2;
    const kap = this.add.container(x, y).setDepth(110);
    kap.add(this.add.rectangle(0, 0, W, H, 0x1c1612, 0.96).setStrokeStyle(3, 0xc9a24a).setInteractive());
    kap.add(this.add.text(0, -H / 2 + 46, baslik, stil('baslik', 48)).setOrigin(0.5));
    const kapat = this.dugme(W / 2 - 34, -H / 2 + 34, 48, 48, '×', () => this.panelKapat(), 111, 30);
    kap.add(kapat);
    const p = {
      kap, sol: -W / 2 + 30, en: W - 60, ust: -H / 2 + 110,
      yazi: (yy, metin, boyut = 26, renk = '#efe6d2', ek = {}) => {
        const t = this.add.text(-W / 2 + 30, yy, metin, stil('govde', boyut, { color: renk, wordWrap: { width: W - 60 }, ...ek }));
        kap.add(t); return t;
      },
      dugme: (xx, yy, w, h, metin, fn, boyut = 26) => {
        const b = this.dugme(xx, yy, w, h, metin, () => { fn(); this.yenile(); }, 111, boyut);
        kap.add(b); return b;
      },
    };
    this.panelYenile = null;
    icerik(p);
    this.panel = kap;
    if (this.panelYenile) this.panelYenile();
  }

  bedelYazi(b) {
    return Object.entries(b).map(([k, v]) => `${v} ${k === 'altin' ? 'altın' : KAYNAKLAR[k].ad.toLowerCase()}`).join(', ');
  }

  // Yükseltme satırı (bina ya da sur)
  yukseltSatiri(p, yy, bedelFn, fn) {
    const t = p.yazi(yy, '', 24, '#c8bca4');
    const b = p.dugme(-110, yy + 92, 300, 64, 'Yükselt', fn, 28);
    return () => {
      const bedel = bedelFn();
      if (!bedel) { t.setText('En yüksek seviyede.'); b.setVisible(false); return; }
      const yeter = this.E.yeter(bedel, this.oyun);
      t.setText('Yükseltme: ' + this.bedelYazi(bedel));
      t.setColor(yeter ? '#c8bca4' : '#d08070');
      b.setVisible(true);
      b.yazi.setColor(yeter ? '#ffd76a' : '#7a7060');
    };
  }

  binaPaneli(p, k) {
    const E = this.E, B = BINALAR[k];
    const sv = p.yazi(p.ust, '', 30, '#c9a24a', { fontStyle: 'bold' });
    p.yazi(p.ust + 44, B.aciklama, 24, '#c8bca4');
    const satirlar = [];
    if (k !== 'ev') {
      const isci = p.yazi(p.ust + 150, '', 30, '#efe6d2', { fontStyle: 'bold' });
      p.dugme(-190, p.ust + 240, 110, 64, '−', () => E.isciEkle(k, -1), 40);
      p.dugme(-60, p.ust + 240, 110, 64, '+', () => E.isciEkle(k, 1), 40);
      const uretim = p.yazi(p.ust + 300, '', 26);
      satirlar.push(() => {
        isci.setText(`${B.is[0].toUpperCase() + B.is.slice(1)}: ${E.bina[k].isci} / ${E.yerSayisi(k)}   (boşta ${E.bosta})`);
        uretim.setText(this.uretimMetni(k));
      });
    } else {
      const n = p.yazi(p.ust + 150, '', 30, '#efe6d2', { fontStyle: 'bold' });
      const g = p.yazi(p.ust + 200, '', 24, '#c8bca4');
      satirlar.push(() => {
        n.setText(`Halk ${E.nufus} / ${E.barinak}`);
        g.setText('Ambarda yiyecek ve evde yer varsa her gün en çok 3 sığınmacı gelir.');
      });
    }
    satirlar.push(this.yukseltSatiri(p, p.ust + 470, () => E.yukseltBedeli(k), () => E.yukselt(k, this.oyun) && this.oyun.sesCal('level_up', 0.4)));
    this.panelYenile = () => {
      sv.setText(`Seviye ${E.bina[k].seviye}` + (B.kalite ? ` · ${B.kalite[E.bina[k].seviye - 1].ad}` : ''));
      for (const f of satirlar) f();
    };
  }

  uretimMetni(k) {
    const E = this.E, B = BINALAR[k], w = E.bina[k].isci, v = E.verim(k);
    if (k === 'duvarci') return `Günde en çok ${Math.floor(w * B.onarim * v)} sur canı onarır\n(her 40 can için 3 taş, 1 odun).\nSur: ${Math.round(this.oyun.surCan)}/${this.oyun.surEnFazla}`;
    if (k === 'demirci') return `Günde ${w * B.tuketim.demir} demirden ${Math.floor(w * B.tuketim.demir * B.uretim.uc * v)} ok ucu.\nOk hasarı ×${E.ucKalite.hasar}`;
    if (k === 'yayci') return `Günde en çok ${Math.floor(w * B.uretim.ok * v)} ok (her ok 1 uç ister).\nÖnce eksik yayları yapar (yay: ${E.kaynak.yay}).\nAsker oku hasarı ×${E.yayKalite.hasar}`;
    const [m, n] = Object.entries(B.uretim)[0];
    return `Günde +${Math.floor(w * n * v)} ${KAYNAKLAR[m].ad.toLowerCase()}` + (k === 'ciftlik' ? `\nHalk günde ${E.nufus} yiyecek yer.` : '');
  }

  surPaneli(p) {
    const E = this.E, o = this.oyun;
    const can = p.yazi(p.ust, '', 30, '#efe6d2', { fontStyle: 'bold' });
    const onarB = p.dugme(-40, p.ust + 90, 440, 64, '', () => E.acilOnar(o) && o.sesCal('coin', 0.5), 24);
    const yuk = this.yukseltSatiri(p, p.ust + 150, () => E.surBedeli(), () => E.surYukselt(o) && o.sesCal('level_up', 0.4));
    p.yazi(p.ust + 340, 'Okçu askerler', 30, '#c9a24a', { fontStyle: 'bold' });
    const ask = p.yazi(p.ust + 384, '', 28, '#efe6d2', { fontStyle: 'bold' });
    p.dugme(-190, p.ust + 470, 110, 64, '−', () => { E.askerEkle(-1); }, 40);
    p.dugme(-60, p.ust + 470, 110, 64, '+', () => { E.askerEkle(1); }, 40);
    p.yazi(p.ust + 520, 'Sur her yükseldiğinde bir okçu yeri daha açılır. Her asker bir kişi ve bir yay ister. Yaycı boş kalan vaktinde yay yapar. Askerler de ambardan ok harcar.', 22, '#c8bca4');
    this.panelYenile = () => {
      can.setText(`Sur canı ${Math.round(o.surCan)} / ${o.surEnFazla}  ·  Seviye ${E.surSeviye}`);
      const b = E.acilOnarimBilgi(o);
      if (E.acilOnarildi) onarB.yazi.setText('Bugün onarıldı').setColor('#7a7060');
      else if (b.can <= 0) onarB.yazi.setText('Sur sağlam').setColor('#7a7060');
      else onarB.yazi.setText(`Altınla onar: +${b.can} can · ${b.altin} altın`).setColor(o.altin >= b.altin ? '#ffd76a' : '#7a7060');
      yuk();
      ask.setText(`Asker: ${E.asker} / ${E.askerYeri}   ·   Yay: ${E.kaynak.yay}`);
    };
  }

  pazarPaneli(p) {
    const E = this.E, o = this.oyun;
    p.yazi(p.ust, 'Bir parti al ya da sat. Aldıkça fiyat o gün artar.', 24, '#c8bca4');
    const satirlar = [];
    Object.keys(PAZAR).filter(k => KAYNAKLAR[k]).forEach((k, i) => {
      const yy = p.ust + 70 + i * 120;
      const t = p.yazi(yy, '', 28, '#efe6d2', { fontStyle: 'bold' });
      const al = p.dugme(-110, yy + 70, 220, 58, '', () => E.ticaret(k, true, o) && o.sesCal('coin', 0.4), 24);
      const sat = p.dugme(120, yy + 70, 200, 58, '', () => E.ticaret(k, false, o) && o.sesCal('coin', 0.3), 24);
      satirlar.push(() => {
        t.setText(`${KAYNAKLAR[k].ad} ×${PAZAR[k].parti}   (ambarda ${E.kaynak[k]})`);
        const fa = E.fiyat(k, true), fs = E.fiyat(k, false);
        al.yazi.setText(`Al · ${fa} altın`).setColor(o.altin >= fa ? '#ffd76a' : '#7a7060');
        sat.yazi.setText(`Sat · ${fs}`).setColor(E.kaynak[k] >= PAZAR[k].parti ? '#efe6d2' : '#7a7060');
      });
    });
    this.panelYenile = () => satirlar.forEach(f => f());
  }

  // Gün sonu raporu (ortada). zorla = kuleye tıklandı
  raporGoster(zorla) {
    const r = this.E.rapor;
    if (!r || (!this.ilkRapor && !zorla)) return;
    this.ilkRapor = null;
    const ad = k => KAYNAKLAR[k].ad.toLowerCase();
    const yapilan = Object.entries(r.yapilan).filter(([k]) => k !== 'ok').map(([k, v]) => `+${v} ${ad(k)}`);
    const okYapilan = (r.yapilan.ok || 0) - r.toplanan;
    const satir = [
      `Üretim: ${yapilan.join(', ') || 'yok'}`,
      `Oklar: ${r.atilan} atıldı, ${r.toplanan} toplandı` + (okYapilan > 0 ? `, yaycı ${okYapilan} yaptı` : ''),
      r.onarim > 0 ? `Duvarcılar suru ${r.onarim} can onardı.` : '',
      `Halk ${r.yenen} yiyecek yedi.` + (r.gelen ? ` ${r.gelen} sığınmacı geldi.` : ''),
      ...r.notlar,
    ].filter(Boolean);
    this.panelKur(`${this.oyun.dalga}. günün raporu`, p => {
      p.yazi(p.ust, satir.join('\n\n'), 26, '#efe6d2', { lineSpacing: 4 });
      p.dugme(0, 360, 260, 66, 'Tamam', () => this.panelKapat(), 28);
    });
    this.secili = 'rapor';
  }

  // ---------------- Köylüler ----------------
  // Her binada en çok 4 işçi, boştakiler meydanda, askerler kapıda
  koyluleriDiz() {
    const E = this.E;
    const istek = {};
    for (const k of Object.keys(BINALAR)) if (k !== 'ev') istek[k] = Math.min(4, E.bina[k].isci);
    istek.bosta = Math.min(6, Math.max(0, E.bosta));
    istek.asker = E.asker;
    for (const [g, n] of Object.entries(istek)) {
      const l = this.koyluler[g] || (this.koyluler[g] = []);
      while (l.length < n) l.push(this.koyluYap(g, l.length));
      while (l.length > n) l.pop().sprite.destroy();
    }
  }

  koyluYap(grup, i) {
    const tur = ['koylu1', 'koylu2', 'koylu3'][(grup.length + i) % 3];
    const ev = this.M.binalar['ev' + this.E.bina.ev.seviye].merkez;
    const sp = this.add.sprite(ev[0], ev[1] + 60, tur, 0).setOrigin(0.5, 0.96);
    const k = { sprite: sp, tur, grup, x: ev[0] + (Math.random() - 0.5) * 60, y: ev[1] + 60, bekle: Math.random() * 2, hedef: null, is: false };
    sp.setPosition(k.x, k.y);
    if (grup === 'asker') sp.setTint(0xa8b8d0);
    return k;
  }

  // Grubun çalışma yeri (binanın önü, meydan ya da kapı)
  yerBul(k) {
    if (k.grup === 'bosta') return [880 + Math.random() * 160, 720 + Math.random() * 60];
    if (k.grup === 'asker') return [1700 + Math.random() * 60, 640 + Math.random() * 70];
    const m = this.binaMeta(k.grup);
    return [m.merkez[0] + (Math.random() - 0.5) * 120, Math.min(960, m.dipY + 6 + Math.random() * 24)];
  }

  update(t, ms) {
    const dt = Math.min(ms / 1000, 0.05);
    for (const l of Object.values(this.koyluler)) for (const k of l) this.koyluGuncelle(k, dt);
  }

  koyluGuncelle(k, dt) {
    const sp = k.sprite;
    if (k.hedef) {
      const dx = k.hedef[0] - k.x, dy = k.hedef[1] - k.y, d = Math.hypot(dx, dy);
      if (d < 4) {
        k.hedef = null;
        k.bekle = 2 + Math.random() * 5;
        // İşçi binasında çalışır, ötekiler bekler
        const calis = !['bosta', 'asker'].includes(k.grup) && k.isBasi;
        sp.play(k.tur + (calis ? '_work' : '_idle'), true);
      } else {
        const v = 70 * dt;
        k.x += dx / d * v;
        k.y += dy / d * v * 0.8;
        sp.setFlipX(dx > 0);
      }
    } else {
      k.bekle -= dt;
      if (k.bekle <= 0) {
        // İşçi: çoğunlukla işinin başına, arada bir meydana gidip gelir
        k.isBasi = !['bosta', 'asker'].includes(k.grup) && (Math.random() < 0.75 || !k.isBasi);
        k.hedef = k.isBasi || k.grup === 'bosta' || k.grup === 'asker' ? this.yerBul(k) : [900 + Math.random() * 120, 700 + Math.random() * 50];
        sp.play(k.tur + '_walk', true);
      }
    }
    sp.setPosition(k.x, k.y).setDepth(10 + k.y / 1000);
  }

  // ---------------- Çıkış ----------------
  dukkanaGit() {
    this.panelKapat();
    this.scene.sleep();
    this.oyun.dukkanAc();
  }

  savasaCik() {
    this.panelKapat();
    this.scene.sleep();
    this.oyun.iceridenCik();
  }
}
