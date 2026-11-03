// =============================================================
//  SAVAŞ SAHNESİ (savas.js)
//  Oyunun kalbi: dalgalar, oklar, isabet, altın, dükkân.
//  Durumlar: 'menu' → 'savas' → 'dukkan' → 'savas' ... → 'bitti'
// =============================================================

// Kan, toz ve uçan yazılar
class Efekt {
  constructor(s) {
    this.s = s;
    this.kanParca = s.add.particles(0, 0, 'kare', {
      speed: { min: 80, max: 360 }, angle: { min: 190, max: 350 }, gravityY: 1600,
      lifespan: { min: 400, max: 800 }, scale: { start: 1, end: 0.4 }, tint: [0x7a1010, 0x9a1a14, 0x5a0a0a],
      emitting: false,
    }).setDepth(35);
    this.tozParca = s.add.particles(0, 0, 'daire', {
      speed: { min: 20, max: 120 }, angle: { min: 200, max: 340 }, gravityY: 200,
      lifespan: 600, scale: { start: 0.6, end: 1.4 }, alpha: { start: 0.5, end: 0 }, tint: 0x8a7a64,
      emitting: false,
    }).setDepth(34);
    this.tasParca = s.add.particles(0, 0, 'kare', {
      speed: { min: 120, max: 380 }, angle: { min: 200, max: 330 }, gravityY: 1800,
      lifespan: 900, scale: { start: 1.6, end: 1 }, tint: [0x6a6458, 0x8a8276, 0x4a443c],
      emitting: false,
    }).setDepth(35);
  }
  kan(x, y, n = 8, renk) {
    if (renk) this.kanParca.setParticleTint(renk); else this.kanParca.setParticleTint([0x7a1010, 0x9a1a14, 0x5a0a0a]);
    this.kanParca.explode(n, x, y);
  }
  toz(x, y, n = 4) { this.tozParca.explode(n, x, y); }
  tas(x, y, n = 6) { this.tasParca.explode(n, x, y); }
  yazi(x, y, metin, renk = '#ffd76a', boyut = 30) {
    const t = this.s.add.text(x, y, metin, stil('govde', boyut, { fontStyle: 'bold', color: renk, stroke: '#120e0c', strokeThickness: 5 }))
      .setOrigin(0.5).setDepth(46);
    this.s.tweens.add({ targets: t, y: y - 70, alpha: 0, duration: 1000, ease: 'Quad.easeOut', onComplete: () => t.destroy() });
  }
}

class SavasSahnesi extends Phaser.Scene {
  constructor() { super('savas'); }

  create() {
    this.durum = 'menu';
    this.dalga = 0;
    this.altin = 0;
    this.seviye = {};
    this.surEnFazla = AYAR.kale.can;
    this.surCan = this.surEnFazla;
    this.surIz = this.surCan;
    this.dayaniklilik = AYAR.dayaniklilik.enFazla;
    this.ruzgar = 0;
    this.dusmanlar = [];
    this.oklar = [];
    this.askerler = [];
    this.kuyruk = [];
    this.oldurulen = 0;
    this.kafaVurusu = 0;
    this.duraklatildi = false;

    this.manzara = new Manzara(this);
    this.kale = new Kale(this);
    this.oyuncu = new Okcu(this, AYAR.oyuncu.x, AYAR.oyuncu.ayakY, true);
    this.efekt = new Efekt(this);
    this.karanlik = this.add.rectangle(0, 0, AYAR.en, AYAR.boy, 0x0a0c1e, 0).setOrigin(0).setDepth(40);
    this.arayuz = new Arayuz(this);
    this.girdiKur();
    this.sesKur();
    this.arayuz.baslangic();
  }

  // ---------------- Girdi ----------------
  girdiKur() {
    this.girdi = { x: 1200, y: 700, basili: false, dokundu: false };
    this.input.addPointer(2);
    this.input.on('pointermove', p => { if (!this.uiTiklandi) { this.girdi.x = p.worldX; this.girdi.y = p.worldY; } });
    this.input.on('pointerdown', p => {
      if (this.uiTiklandi || this.durum !== 'savas' || this.duraklatildi) return;
      this.girdi.x = p.worldX; this.girdi.y = p.worldY;
      this.girdi.basili = true;
      this.girdi.dokundu = true;
    });
    this.input.on('pointerup', () => { this.girdi.basili = false; this.uiTiklandi = false; });
    // Klavye: Esc duraklat, M ses, 1-6 dükkân, Boşluk sonraki dalga
    this.input.keyboard.on('keydown', e => {
      if (e.key === 'Escape' || e.key === 'p') this.duraklat();
      else if (e.key === 'm' || e.key === 'M') this.sesAcKapa();
      else if (this.durum === 'dukkan' && e.key >= '1' && e.key <= String(YUKSELTMELER.length)) {
        if (this.satinAl(YUKSELTMELER[+e.key - 1]) && this.arayuz.dukkanYenile) this.arayuz.dukkanYenile();
      } else if (e.key === ' ' && this.durum === 'dukkan') this.dalgaBaslat();
      else if (e.key === ' ' && this.durum === 'menu') this.oyunuBaslat();
    });
  }

  // ---------------- Ses ----------------
  sesKur() {
    let kayitli = null;
    try { kayitli = localStorage.getItem('sonKalePhaser.ses'); } catch (e) { /* gizli pencere */ }
    this.sesAcik = kayitli !== 'kapali';
    this.sound.mute = !this.sesAcik;
    this.muzik = this.sound.add('muzik', { loop: true, volume: 0.3 });
  }
  sesCal(ad, ses = 0.5) {
    if (!this.sesAcik) return;
    this.sound.play(ad, { volume: ses, detune: (Math.random() - 0.5) * 200 });
  }
  sesAcKapa() {
    this.sesAcik = !this.sesAcik;
    this.sound.mute = !this.sesAcik;
    try { localStorage.setItem('sonKalePhaser.ses', this.sesAcik ? 'acik' : 'kapali'); } catch (e) { /* önemli değil */ }
    this.arayuz.sesDugme.yazi.setText(this.sesAcik ? '♪' : '×');
  }

  duraklat() {
    if (this.durum !== 'savas') return;
    this.duraklatildi = !this.duraklatildi;
    this.girdi.basili = false;
    if (this.duraklatildi) { this.tweens.pauseAll(); this.anims.pauseAll(); this.arayuz.duraklatPaneli(); }
    else { this.tweens.resumeAll(); this.anims.resumeAll(); this.arayuz.paneliKapat(); }
  }

  // ---------------- Akış ----------------
  oyunuBaslat() {
    this.arayuz.paneliKapat();
    if (!this.muzik.isPlaying) this.muzik.play();
    this.dalgaBaslat();
  }

  dalgaBaslat() {
    this.arayuz.paneliKapat();
    this.dalga++;
    this.durum = 'savas';
    // Dalga listesi
    const n = this.dalga, D = AYAR.dalga;
    const sayi = Math.round(D.temel + D.artis * n);
    this.kuyruk = [];
    for (let i = 0; i < sayi; i++) this.kuyruk.push(dusmanSec(n));
    if (n >= 4) {
      const yarasa = Math.floor((n - 2) * 0.8);
      for (let i = 0; i < yarasa; i++) this.kuyruk.splice(Math.floor(Math.random() * this.kuyruk.length), 0, 'yarasa');
    }
    this.cikisSayaci = D.ilkBekleme;
    this.cikisAraligi = Math.max(0.45, 1.8 - n * 0.1);
    // Günün rüzgârı
    const R = AYAR.ruzgar;
    this.ruzgar = Math.random() < R.sakinOlasilik ? 0 : (Math.random() * 2 - 1) * R.enFazla * Math.min(1, 0.4 + n * 0.1);
    // Gökyüzü dalgaya göre kararır
    const r = this.manzara.boya(n);
    this.karanlik.setAlpha(r.karanlik);
    this.askerleriDiz();
    this.arayuz.duyur(`${n}. Dalga`, this.ruzgar === 0 ? 'Rüzgâr yok' : '');
    this.gorulen = this.gorulen || {};
  }

  dalgaBitti() {
    this.durum = 'dukkan';
    const bonus = AYAR.dalga.bitirmeAltini + this.dalga * AYAR.dalga.bitirmeArtisi;
    this.altin += bonus;
    this.efekt.yazi(AYAR.en / 2, 420, `Dalga bitti! +${bonus} altın`, '#ffd76a', 44);
    this.sesCal('level_up', 0.5);
    this.girdi.basili = false;
    this.oyuncu.geriyor = false;
    this.time.delayedCall(1300, () => { if (this.durum === 'dukkan') this.arayuz.dukkan(this); });
  }

  oyunBitti() {
    this.durum = 'bitti';
    this.girdi.basili = false;
    this.cameras.main.shake(500, 0.012);
    this.sesCal('boss', 0.7);
    this.time.delayedCall(900, () => this.arayuz.oyunSonu(this));
  }

  askerleriDiz() {
    const istenen = Math.min(this.seviye.asker || 0, AYAR.askerYerleri.length);
    while (this.askerler.length < istenen) {
      const y = AYAR.askerYerleri[this.askerler.length];
      this.askerler.push(new Okcu(this, y.x, y.ayakY, false));
    }
  }

  // ---------------- Yükseltmeler ----------------
  satinAl(u) {
    const sv = this.seviye[u.id] || 0;
    if (sv >= u.enFazla) return false;
    if (u.id === 'onarim' && this.surCan >= this.surEnFazla) return false;
    const f = u.fiyat(sv, this);
    if (this.altin < f) return false;
    this.altin -= f;
    this.seviye[u.id] = sv + 1;
    if (u.id === 'sur') { this.surEnFazla += 120; this.surCan += 120; }
    if (u.id === 'onarim') this.surCan = Math.min(this.surEnFazla, this.surCan + this.surEnFazla * 0.35);
    if (u.id === 'asker') this.askerleriDiz();
    this.surIz = this.surCan;
    this.kale.guncelle(this.surCan / this.surEnFazla);
    this.sesCal('coin', 0.5);
    return true;
  }
  okHasari() { return AYAR.ok.hasar * (1 + 0.2 * (this.seviye.hasar || 0)); }
  okHizi() { return AYAR.ok.hiz; }
  okSayisi() { return 1 + (this.seviye.coklu || 0); }
  germeCarpani() { return Math.pow(0.88, this.seviye.germe || 0); }

  // ---------------- Oklar ----------------
  okEkle(x, y, aci, hiz, hasar, oyuncudan) {
    const sprite = this.add.image(x, y, 'ok').setOrigin(0.85, 0.5).setDepth(30);
    this.oklar.push({ x, y, vx: Math.cos(aci) * hiz, vy: Math.sin(aci) * hiz, hasar, oyuncudan, sprite, sapli: false, omur: 3 });
  }

  oklariGuncelle(dt) {
    const g = AYAR.yercekimi;
    for (const o of this.oklar) {
      if (o.sapli) {
        o.omur -= dt;
        if (o.omur < 1) o.sprite.setAlpha(Math.max(0, o.omur));
        if (o.omur <= 0) { o.sprite.destroy(); o.sil = true; }
        continue;
      }
      // Hızlı oklar zombinin içinden geçmesin diye adımı bölüyoruz
      const adim = Math.max(2, Math.ceil(Math.hypot(o.vx, o.vy) * dt / 16));
      for (let k = 0; k < adim && !o.sil && !o.sapli; k++) {
        const d = dt / adim;
        o.vy += g * d;
        o.vx += this.ruzgar * d;
        o.x += o.vx * d;
        o.y += o.vy * d;
        // Ucunun konumu (sprite'ın ucu ileride)
        const a = Math.atan2(o.vy, o.vx);
        const ux = o.x + Math.cos(a) * 8, uy = o.y + Math.sin(a) * 8;
        for (const z of this.dusmanlar) {
          if (z.durum === 'olu' || !z.icindeMi(ux, uy)) continue;
          this.isabet(o, z, ux, uy);
          break;
        }
        if (!o.sil && !o.sapli && o.y >= AYAR.zemin + 6) {
          o.y = AYAR.zemin + 6;
          o.sapli = true;
          o.omur = 3;
          this.efekt.toz(o.x, AYAR.zemin + 4, 3);
        }
      }
      if (o.x > AYAR.en + 80 || o.x < -80) { o.sprite.destroy(); o.sil = true; continue; }
      o.sprite.setPosition(o.x, o.y);
      if (!o.sapli) o.sprite.setRotation(Math.atan2(o.vy, o.vx));
    }
    this.oklar = this.oklar.filter(o => !o.sil);
  }

  isabet(o, z, x, y) {
    const kafa = z.kafaMi(y);
    let hasar = o.hasar * (kafa ? AYAR.ok.kafaCarpani : 1);
    if (!kafa && z.T.kemik) hasar *= z.T.kemik; // İskelet: oklar kemikten kayar
    const oldu = z.vur(hasar);
    this.efekt.kan(x, y, kafa ? 12 : 6, z.turAdi === 'iskelet' ? 0xd8d0bc : null);
    z.it(8);
    this.sesCal('hit', 0.35);
    if (kafa && o.oyuncudan) {
      this.kafaVurusu++;
      this.altin += AYAR.ok.kafaAltin;
      this.efekt.yazi(x, z.ust - 20, `KAFA! +${AYAR.ok.kafaAltin}`);
    }
    if (oldu) {
      const altin = Math.round(z.T.altin * (1 + AYAR.dalga.altinArtisi * (this.dalga - 1)));
      this.altin += altin;
      this.oldurulen++;
      this.efekt.yazi(z.x, z.ust - 50, `+${altin}`, '#ffd76a', 26);
      this.sesCal(z.T.agir ? 'big_kill' : 'kill', 0.45);
    }
    // Ok düşmanın üstünde saplı kalır (ölüyse yere düşer gibi kaybolur)
    if (!oldu || !z.T.ucan) {
      o.sapli = true;
      o.omur = 99;
      o.sil = true;
      const sp = o.sprite;
      sp.setDepth(z.sprite.depth + 0.01);
      z.saplananlar.push({ sprite: sp, dx: x - z.x + Math.cos(Math.atan2(o.vy, o.vx)) * 6, dy: y - z.y });
      sp.setPosition(x, y);
    } else {
      o.sprite.destroy();
      o.sil = true;
    }
  }

  // Düşman sura (ya da yarasa kuleye) vurdu
  kaleyeVur(hasar, x, y, agir) {
    if (this.durum !== 'savas') return;
    this.surCan = Math.max(0, this.surCan - hasar);
    this.kale.parla();
    this.kale.guncelle(this.surCan / this.surEnFazla);
    this.efekt.tas(x, y, agir ? 10 : 4);
    this.efekt.yazi(x + 10, y - 30, `-${hasar}`, '#ff6a50', 26);
    this.cameras.main.shake(agir ? 220 : 90, agir ? 0.006 : 0.002);
    this.sesCal('impact', agir ? 0.6 : 0.3);
    if (this.surCan <= 0) this.oyunBitti();
  }

  kalanDusman() {
    return this.kuyruk.length + this.dusmanlar.filter(d => d.durum !== 'olu').length;
  }

  // ---------------- Her kare ----------------
  update(zaman, ms) {
    const dt = Math.min(ms / 1000, 0.05) * (this.hiz || 1); // hiz: test botu oyunu hızlandırabilir
    if (!this.duraklatildi) {
      if (this.durum === 'savas') this.savasGuncelle(dt);
      else if (this.durum !== 'menu') {
        // Dükkânda / oyun sonunda oklar düşmeye, cesetler kaybolmaya devam etsin
        this.oklariGuncelle(dt);
      }
      // Sur canının iz çubuğu yavaşça iner
      this.surIz = this.surIz > this.surCan ? Math.max(this.surCan, this.surIz - this.surEnFazla * 0.25 * dt) : this.surCan;
    }
    this.oyuncu.kareyiAyarla();
    this.arayuz.ciz(this);
  }

  savasGuncelle(dt) {
    // Yeni düşman çıkar
    if (this.kuyruk.length) {
      this.cikisSayaci -= dt;
      if (this.cikisSayaci <= 0) {
        const tur = this.kuyruk.shift();
        this.dusmanlar.push(new Dusman(this, tur, this.dalga));
        const T = DUSMAN_TURLERI[tur];
        if (T.ipucu && !this.gorulen[tur]) {
          this.gorulen[tur] = true;
          this.arayuz.duyur('Yeni düşman: ' + T.ad, T.ipucu);
        }
        this.cikisSayaci = tur === 'yarasa' ? 0.3 : this.cikisAraligi * (0.6 + Math.random() * 0.8);
      }
    }
    this.oyuncu.guncelle(dt, this);
    for (const a of this.askerler) a.guncelle(dt, this);
    for (const d of this.dusmanlar) d.guncelle(dt, this);
    this.dusmanlar = this.dusmanlar.filter(d => !d.olu);
    this.oklariGuncelle(dt);
    if (this.durum === 'savas' && this.kalanDusman() === 0) this.dalgaBitti();
  }
}
