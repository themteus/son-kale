// =============================================================
//  ARAYÜZ (arayuz.js)
//  Üst bilgi şeridi (sur canı, altın, dalga, dayanıklılık, rüzgâr),
//  düğmeler ve pencereler (başlangıç, dükkân, oyun sonu).
// =============================================================

const YAZI = {
  baslik: { fontFamily: '"Grenze Gotisch", serif', color: '#f0e2b8' },
  govde: { fontFamily: '"Alegreya Sans", sans-serif', color: '#efe6d2' },
};
const stil = (tur, boyut, ek = {}) => ({ ...YAZI[tur], fontSize: boyut + 'px', ...ek });

class Arayuz {
  constructor(sahne) {
    this.s = sahne;
    const d = 50;
    this.g = sahne.add.graphics().setDepth(d);
    this.surYazi = sahne.add.text(40, 26, '', stil('baslik', 30)).setDepth(d + 1);
    this.altinYazi = sahne.add.text(40, 100, '', stil('govde', 32, { fontStyle: 'bold', color: '#ffd76a' })).setDepth(d + 1);
    this.dalgaYazi = sahne.add.text(AYAR.en / 2, 24, '', stil('baslik', 44)).setOrigin(0.5, 0).setDepth(d + 1);
    this.kalanYazi = sahne.add.text(AYAR.en / 2, 78, '', stil('govde', 24, { color: '#c8bca4' })).setOrigin(0.5, 0).setDepth(d + 1);
    this.ruzgarYazi = sahne.add.text(AYAR.en - 250, 112, '', stil('govde', 22, { color: '#c8bca4' })).setOrigin(0.5, 0).setDepth(d + 1);
    this.duyuru = sahne.add.text(AYAR.en / 2, 300, '', stil('baslik', 84, { stroke: '#120e0c', strokeThickness: 10 }))
      .setOrigin(0.5).setDepth(d + 2).setAlpha(0);
    this.ipucu = sahne.add.text(AYAR.en / 2, 400, '', stil('govde', 30, { stroke: '#120e0c', strokeThickness: 6, align: 'center' }))
      .setOrigin(0.5).setDepth(d + 2).setAlpha(0);
    this.odak = sahne.add.graphics().setDepth(45);
    this.canlar = sahne.add.graphics().setDepth(44);
    // Sağ üst düğmeler
    this.sesDugme = this.dugme(AYAR.en - 150, 50, 90, 64, '♪', () => sahne.sesAcKapa(), 30);
    this.duraklatDugme = this.dugme(AYAR.en - 50, 50, 64, 64, 'II', () => sahne.duraklat(), 30);
    this.panel = null;
  }

  // Basit düğme: dikdörtgen + yazı, tıklanınca fn
  dugme(x, y, w, h, metin, fn, derinlik = 52, boyut = 30) {
    const kap = this.s.add.container(x, y).setDepth(derinlik);
    const arka = this.s.add.rectangle(0, 0, w, h, 0x2a211a, 0.92).setStrokeStyle(3, 0xc9a24a);
    const yazi = this.s.add.text(0, 0, metin, stil('govde', boyut, { fontStyle: 'bold' })).setOrigin(0.5);
    kap.add([arka, yazi]);
    arka.setInteractive({ useHandCursor: true })
      .on('pointerover', () => arka.setFillStyle(0x4a3a28, 0.95))
      .on('pointerout', () => arka.setFillStyle(0x2a211a, 0.92))
      .on('pointerdown', (p, lx, ly, e) => { e && e.stopPropagation(); this.s.uiTiklandi = true; this.s.sesCal('ui', 0.4); fn(); });
    kap.arka = arka;
    kap.yazi = yazi;
    return kap;
  }

  ciz(oyun) {
    const g = this.g;
    g.clear();
    // Sur canı
    const oran = kis(oyun.surCan / oyun.surEnFazla, 0, 1);
    this.surYazi.setText('Sur');
    g.fillStyle(0x120e0c, 0.85).fillRoundedRect(96, 28, 420, 34, 8);
    g.fillStyle(0x5a1a14, 1).fillRect(102, 34, 408 * kis(oyun.surIz / oyun.surEnFazla, 0, 1), 22);
    g.fillStyle(oran > 0.4 ? 0xc9503a : 0xe0302a, 1).fillRect(102, 34, 408 * oran, 22);
    g.fillStyle(0xffffff, 0.15).fillRect(102, 34, 408 * oran, 6);
    // Dayanıklılık
    g.fillStyle(0x120e0c, 0.85).fillRoundedRect(96, 70, 260, 18, 6);
    const st = oyun.dayaniklilik / AYAR.dayaniklilik.enFazla;
    g.fillStyle(st < AYAR.dayaniklilik.yorgun ? 0xe0803a : 0xe8c34a, 1).fillRect(100, 74, 252 * st, 10);
    // Altın
    g.fillStyle(0xd8a830, 1).fillCircle(56, 120, 14);
    g.fillStyle(0xffe08a, 1).fillCircle(52, 116, 6);
    this.altinYazi.setPosition(80, 100).setText(String(oyun.altin));
    this.dalgaYazi.setText(oyun.dalga > 0 ? 'Dalga ' + oyun.dalga : '');
    const kalan = oyun.kalanDusman();
    this.kalanYazi.setText(oyun.durum === 'savas' ? (kalan > 0 ? kalan + ' düşman kaldı' : '') : '');
    // Rüzgâr oku
    const r = oyun.ruzgar / AYAR.ruzgar.enFazla;
    const rx = AYAR.en - 250, ry = 100;
    g.fillStyle(0x120e0c, 0.7).fillRoundedRect(rx - 110, ry - 22, 220, 40, 10);
    if (Math.abs(r) < 0.05) this.ruzgarYazi.setText('Rüzgâr yok');
    else {
      const uz = 90 * Math.abs(r), yon = Math.sign(r);
      g.lineStyle(5, 0xd8e4f0, 0.9).lineBetween(rx - uz * yon, ry - 2, rx + uz * yon, ry - 2);
      g.fillStyle(0xd8e4f0, 0.9).fillTriangle(rx + uz * yon + 14 * yon, ry - 2, rx + uz * yon, ry - 12, rx + uz * yon, ry + 8);
      this.ruzgarYazi.setText(r > 0 ? 'Arkadan rüzgâr' : 'Karşıdan rüzgâr');
    }
    this.ruzgarYazi.setPosition(rx, ry + 22);
    // Düşman can çubukları
    const c = this.canlar;
    c.clear();
    for (const d of oyun.dusmanlar) {
      if (d.durum === 'olu' || d.can >= d.canEnFazla) continue;
      const w = Math.max(40, d.en * (d.T.ucan ? 0.8 : 1.6)), x = d.x - w / 2, y = d.ust - 16;
      c.fillStyle(0x120e0c, 0.8).fillRect(x - 2, y - 2, w + 4, 10);
      c.fillStyle(0xc9503a, 1).fillRect(x, y, w * kis(d.can / d.canEnFazla, 0, 1), 6);
    }
    // Odak halkası: yay gerilirken nişan noktasında
    const o = this.odak, ok = oyun.oyuncu;
    o.clear();
    if (oyun.durum === 'savas' && ok.geriyor) {
      const mesafe = Math.hypot(oyun.girdi.x - ok.omuz.x, oyun.girdi.y - ok.omuz.y);
      const sp = ok.sapma();
      const yar = kis(mesafe * sp * 1.3, 10, 140);
      const sakin = sp <= AYAR.yay.sapma * 1.2;
      o.lineStyle(3, sakin ? 0xffeca8 : 0xf3e7c4, sakin ? 0.85 : 0.4).strokeCircle(oyun.girdi.x, oyun.girdi.y, yar);
      o.fillStyle(0xf3e7c4, 0.6).fillCircle(oyun.girdi.x, oyun.girdi.y, 3);
    }
  }

  // Ortada büyük yazı (dalga başlığı vb.)
  duyur(metin, alt = '') {
    this.s.tweens.killTweensOf([this.duyuru, this.ipucu]);
    this.duyuru.setText(metin).setAlpha(0).setScale(0.9);
    this.ipucu.setText(alt).setAlpha(0);
    this.s.tweens.add({ targets: this.duyuru, alpha: 1, scale: 1, duration: 300, hold: 1400, yoyo: true });
    if (alt) this.s.tweens.add({ targets: this.ipucu, alpha: 1, duration: 300, hold: 2400, yoyo: true });
  }

  // ---------------- Pencereler ----------------
  paneliKapat() {
    if (this.panel) this.panel.destroy();
    this.panel = null;
  }

  // Ortada koyu pencere; icerik(kap, w, h) içini doldurur
  panelAc(w, h, icerik) {
    this.paneliKapat();
    const s = this.s;
    const kap = s.add.container(AYAR.en / 2, AYAR.boy / 2).setDepth(60);
    const perde = s.add.rectangle(0, 0, AYAR.en, AYAR.boy, 0x07060a, 0.55).setInteractive();
    const arka = s.add.rectangle(0, 0, w, h, 0x1c1612, 0.96).setStrokeStyle(4, 0xc9a24a);
    const ic = s.add.rectangle(0, 0, w - 24, h - 24).setStrokeStyle(1, 0x6a5430);
    kap.add([perde, arka, ic]);
    icerik(kap, w, h);
    this.panel = kap;
    return kap;
  }

  // Pencere içine düğme (konteynere eklenir)
  panelDugme(kap, x, y, w, h, metin, fn, boyut = 30) {
    const b = this.dugme(0, 0, w, h, metin, fn, 61, boyut);
    b.setPosition(x, y);
    kap.add(b);
    return b;
  }

  baslangic() {
    this.panelAc(980, 640, (kap) => {
      const s = this.s;
      kap.add(s.add.text(0, -230, 'SON KALE', stil('baslik', 120)).setOrigin(0.5));
      kap.add(s.add.text(0, -140, 'Phaser 4 deneme sürümü · savaş ekranı', stil('govde', 30, { color: '#c9a24a' })).setOrigin(0.5));
      const dokun = s.sys.game.device.input.touch;
      const anlatim = dokun
        ? 'Vurmak istediğin yere bas: yay gerilir. Bırak: ok uçar.\nKısa dokunuş yayı tam gerip kendiliğinden atar.\nKafaya isabet iki kat vurur ve altın verir.'
        : 'Fareyle vurmak istediğin yere bak, basılı tutup yayı ger, bırak.\nHalka küçülünce nişan oturmuştur. Uzun germek kolu yorar.\nKafaya isabet iki kat vurur ve altın verir.';
      kap.add(s.add.text(0, -10, anlatim, stil('govde', 30, { align: 'center', lineSpacing: 10 })).setOrigin(0.5));
      this.panelDugme(kap, 0, 200, 360, 90, 'Savaşa Başla', () => s.oyunuBaslat(), 40);
    });
  }

  dukkan(oyun) {
    this.panelAc(1240, 840, (kap) => {
      const s = this.s;
      kap.add(s.add.text(0, -370, `${oyun.dalga}. dalga atlatıldı`, stil('baslik', 64)).setOrigin(0.5));
      const altin = s.add.text(0, -300, '', stil('govde', 34, { fontStyle: 'bold', color: '#ffd76a' })).setOrigin(0.5);
      kap.add(altin);
      const satirlar = [];
      const yenile = () => {
        altin.setText(`Altın: ${oyun.altin}`);
        for (const r of satirlar) r();
      };
      YUKSELTMELER.forEach((u, i) => {
        const y = -210 + i * 92;
        const ad = s.add.text(-560, y - 18, '', stil('govde', 34, { fontStyle: 'bold' })).setOrigin(0, 0.5);
        const ac = s.add.text(-560, y + 18, u.aciklama, stil('govde', 24, { color: '#b8ac94' })).setOrigin(0, 0.5);
        kap.add([ad, ac]);
        const b = this.panelDugme(kap, 400, y, 300, 70, '', () => { if (oyun.satinAl(u)) yenile(); }, 30);
        satirlar.push(() => {
          const sv = oyun.seviye[u.id] || 0;
          const bitti = sv >= u.enFazla || (u.id === 'onarim' && oyun.surCan >= oyun.surEnFazla);
          ad.setText(`${i + 1}. ${u.ad}` + (u.enFazla < 99 ? `  ${'●'.repeat(sv)}${'○'.repeat(u.enFazla - sv)}` : ''));
          const f = u.fiyat(sv, oyun);
          b.yazi.setText(bitti ? (u.id === 'onarim' ? 'Sur sağlam' : 'Tamam') : `${f} altın`);
          const alir = !bitti && oyun.altin >= f;
          b.yazi.setColor(alir ? '#ffd76a' : '#7a7060');
          b.arka.setStrokeStyle(3, alir ? 0xc9a24a : 0x4a4030);
        });
      });
      this.panelDugme(kap, 0, 350, 420, 84, 'Sonraki Dalga ▶', () => s.dalgaBaslat(), 36);
      yenile();
      this.dukkanYenile = yenile;
    });
  }

  oyunSonu(oyun) {
    this.panelAc(900, 520, (kap) => {
      const s = this.s;
      kap.add(s.add.text(0, -170, 'Kale düştü', stil('baslik', 96, { color: '#e07060' })).setOrigin(0.5));
      kap.add(s.add.text(0, -50, `${oyun.dalga}. dalgaya kadar dayandın\n${oyun.oldurulen} düşman öldü · ${oyun.kafaVurusu} kafa vuruşu`,
        stil('govde', 34, { align: 'center', lineSpacing: 10 })).setOrigin(0.5));
      this.panelDugme(kap, 0, 140, 360, 90, 'Yeniden Dene', () => s.scene.restart(), 40);
    });
  }

  duraklatPaneli() {
    this.panelAc(700, 420, (kap) => {
      const s = this.s;
      kap.add(s.add.text(0, -120, 'Duraklatıldı', stil('baslik', 80)).setOrigin(0.5));
      this.panelDugme(kap, 0, 20, 340, 80, 'Devam', () => s.duraklat(), 36);
      this.panelDugme(kap, 0, 120, 340, 70, 'Baştan Başla', () => s.scene.restart(), 30);
    });
  }
}
