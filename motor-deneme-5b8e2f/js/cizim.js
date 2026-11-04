// =============================================================
//  MANZARA VE KALE (cizim.js)
//  Gökyüzü, dağlar, orman, zemin, süsler ve kale burada kurulur.
//  Kale taş dokusu (assets/doku/tas.png) ile döşenir; hasar
//  aldıkça çatlaklar, düşen mazgallar ve gedik eklenir.
// =============================================================

// Gökyüzü renkleri: gündüzden geceye (dalga ilerledikçe)
const GOK_RENKLERI = [
  { ust: 0x5b7fae, alt: 0xe8c89a, sis: 0x9aa6b0, karanlik: 0 },     // öğleden sonra
  { ust: 0x3d4f7a, alt: 0xe09a6a, sis: 0x8a7a80, karanlik: 0.08 },  // gün batımı
  { ust: 0x232a4a, alt: 0x8a5a6a, sis: 0x5a5068, karanlik: 0.2 },   // alacakaranlık
  { ust: 0x0d1226, alt: 0x2c2a48, sis: 0x2e3048, karanlik: 0.34 },  // gece
];

function renkKaris(a, b, t) {
  const ca = Phaser.Display.Color.IntegerToColor(a);
  const cb = Phaser.Display.Color.IntegerToColor(b);
  const c = Phaser.Display.Color.Interpolate.ColorWithColor(ca, cb, 100, Math.round(t * 100));
  return Phaser.Display.Color.GetColor(c.r, c.g, c.b);
}

// Dalga numarasına göre gökyüzü (1. dalga gündüz, ~9. dalga gece)
function gokRengi(dalga) {
  const t = kis((dalga - 1) / 8, 0, 1) * (GOK_RENKLERI.length - 1);
  const i = Math.min(GOK_RENKLERI.length - 2, Math.floor(t));
  const f = t - i;
  const a = GOK_RENKLERI[i], b = GOK_RENKLERI[i + 1];
  return {
    ust: renkKaris(a.ust, b.ust, f), alt: renkKaris(a.alt, b.alt, f),
    sis: renkKaris(a.sis, b.sis, f), karanlik: karis(a.karanlik, b.karanlik, f), gece: t / (GOK_RENKLERI.length - 1),
  };
}

class Manzara {
  constructor(sahne) {
    this.s = sahne;
    const { en, boy, zemin } = AYAR;
    this.gok = sahne.add.graphics().setDepth(0);
    this.ay = sahne.add.image(1500, 180, 'ay').setDepth(1).setTint(0xfff4d8);
    this.daglar = sahne.add.graphics().setDepth(2);
    this.uzakOrman = [];
    this.yakinOrman = [];
    // Uzak ve yakın orman (çam siluetleri)
    for (let x = 440; x < en + 60; x += 34 + Math.random() * 30) {
      const t = sahne.add.image(x, zemin - 40 + Math.random() * 10, 'cam' + (1 + Math.floor(Math.random() * 3)))
        .setOrigin(0.5, 1).setScale(0.55 + Math.random() * 0.35).setDepth(3);
      this.uzakOrman.push(t);
    }
    for (let x = 470; x < en + 80; x += 70 + Math.random() * 90) {
      if (x > 760 && x < 1000) continue; // orada açıklık: harabe görünsün
      const t = sahne.add.image(x, zemin - 6 + Math.random() * 6, 'cam' + (1 + Math.floor(Math.random() * 3)))
        .setOrigin(0.5, 1).setScale(0.9 + Math.random() * 0.5).setDepth(4);
      this.yakinOrman.push(t);
    }
    // Zemin: çimen şeridi + toprak
    this.toprak = sahne.add.tileSprite(0, zemin + 10, en, boy - zemin - 10, 'toprak').setOrigin(0, 0).setDepth(5).setTint(0x8a7a6a);
    this.toprak.tileScaleX = this.toprak.tileScaleY = 0.75;
    this.cim = sahne.add.tileSprite(0, zemin - 8, en, 22, 'cim').setOrigin(0, 0).setDepth(5).setTint(0xa0b090);
    this.cim.tileScaleX = this.cim.tileScaleY = 0.6;
    this.zeminGolge = sahne.add.graphics().setDepth(5);
    this.zeminGolge.fillGradientStyle(0x000000, 0x000000, 0x000000, 0x000000, 0, 0, 0.55, 0.55);
    this.zeminGolge.fillRect(0, zemin + 14, en, boy - zemin);
    this.zeminGolge.fillStyle(0x1a1410, 0.9).fillRect(0, zemin + 12, en, 3);
    // Süsler (Quaternius modellerinden çizildi)
    this.susler = [];
    const sus = (ad, x, olcek = 1, yukseklik = 6) => {
      const m = sahne.cache.json.get('kareler').susler[ad];
      const i = sahne.add.image(x, zemin + yukseklik, ad).setOrigin(m.centerX / m.fw, m.footY / m.fh).setScale(olcek).setDepth(6);
      this.susler.push(i);
      return i;
    };
    sus('sutun', 880, 1.1);
    sus('kaya2', 930, 0.8);
    sus('kaya2', 1560, 0.9);
    sus('cit', 640, 1);
    sus('cit', 760, 1);
    sus('kutuk', 1180, 1);
    sus('cali', 1320, 1);
    sus('cali', 520, 0.9);
    sus('cali', 1760, 1.1);
    sus('kaya2', 1840, 0.6);
    this.pixellabKur(sahne);
    this.boya(1);
  }

  // PixelLab çizimi varsa: dağ, orman, zemin ve süsler tek görsel olur (gökyüzü ve ay koddan kalır).
  pixellabKur(sahne) {
    const P = sahne.cache.json.get('kareler').manzaraPl;
    if (!P || !sahne.textures.exists('manzara_pl')) return;
    const { en, boy } = AYAR;
    for (const o of [this.daglar, this.toprak, this.cim, this.zeminGolge, ...this.uzakOrman, ...this.yakinOrman, ...this.susler]) o.setVisible(false);
    this.uzakOrman = []; this.yakinOrman = [];
    sahne.add.rectangle(0, boy - 40, en, 40, 0x1e120c).setOrigin(0).setDepth(2);  // görselin altındaki ince boşluk
    this.pl = sahne.add.image(P.x, P.y, 'manzara_pl').setOrigin(0).setScale(P.piksel).setDepth(3);
  }

  // Dalgaya göre gökyüzü ve sis renklerini uygula
  boya(dalga) {
    const r = gokRengi(dalga);
    const { en, zemin } = AYAR;
    this.gok.clear();
    this.gok.fillGradientStyle(r.ust, r.ust, r.alt, r.alt, 1);
    this.gok.fillRect(0, 0, en, zemin + 20);
    // Ay ancak gece görünür, gündüz güneş gibi alçakta durur
    this.ay.setPosition(1500, karis(520, 170, r.gece)).setAlpha(0.35 + 0.6 * r.gece)
      .setTint(r.gece > 0.5 ? 0xe8ecff : 0xfff0c0).setScale(karis(1.3, 0.8, r.gece));
    // Dağlar: iki sıra, sise karışmış
    this.daglar.clear();
    const dag = (taban, tepe, renk, tohum) => {
      this.daglar.fillStyle(renk, 1);
      this.daglar.beginPath();
      this.daglar.moveTo(0, zemin);
      let x = 0, rnd = tohum;
      const r1 = () => { rnd = (rnd * 9301 + 49297) % 233280; return rnd / 233280; };
      while (x <= en) {
        this.daglar.lineTo(x, taban - tepe * (0.3 + 0.7 * r1()));
        x += 60 + r1() * 120;
      }
      this.daglar.lineTo(en, zemin);
      this.daglar.closePath();
      this.daglar.fillPath();
    };
    dag(zemin - 160, 260, renkKaris(r.sis, r.ust, 0.25), 7);
    dag(zemin - 80, 170, renkKaris(r.sis, 0x1a1c24, 0.35), 3);
    const uzak = renkKaris(r.sis, 0x10141a, 0.55);
    const yakin = renkKaris(r.sis, 0x0a0c10, 0.8);
    for (const t of this.uzakOrman) t.setTint(uzak);
    for (const t of this.yakinOrman) t.setTint(yakin);
    // PixelLab manzarası: geceye doğru sise boğulup kararır
    if (this.pl) this.pl.setTint(renkKaris(0xffffff, renkKaris(r.sis, 0x202838, 0.5), Math.min(1, r.gece * 0.85)));
    return r;
  }
}

// -------------------------------------------------------------
//  KALE
// -------------------------------------------------------------
class Kale {
  constructor(sahne) {
    this.s = sahne;
    const K = AYAR.kale;
    const z = AYAR.zemin;
    this.parcalar = [];
    // Sur gövdesi (kulenin arkasından ön yüze kadar)
    const sur = sahne.add.tileSprite(0, K.surUst, K.onX, z - K.surUst + 14, 'tas').setOrigin(0, 0).setDepth(10);
    sur.tileScaleX = sur.tileScaleY = 0.7;
    sur.setTint(0xb8b0a4);
    // Kule
    const kule = sahne.add.tileSprite(K.kuleSol, K.kuleUst, K.kuleSag - K.kuleSol, z - K.kuleUst + 14, 'tas').setOrigin(0, 0).setDepth(11);
    kule.tileScaleX = kule.tileScaleY = 0.7;
    kule.tilePositionX = 40;
    kule.setTint(0xc8c0b4);
    this.parcalar.push(sur, kule);
    // Mazgallar (dişler): her biri ayrı, hasarla düşebilir
    this.mazgallar = [];
    const dis = (x, y, w, h, derinlik) => {
      const d = sahne.add.tileSprite(x, y, w, h, 'tas').setOrigin(0, 0).setDepth(derinlik);
      d.tileScaleX = d.tileScaleY = 0.7;
      d.tilePositionX = x * 1.3;
      d.setTint(0xc0b8ac);
      this.mazgallar.push(d);
      this.parcalar.push(d);
    };
    for (let x = 0; x < K.onX - 10; x += 44) {
      if (x + 30 > K.kuleSol && x < K.kuleSag) continue;
      dis(x, K.surUst - 30, 30, 30, 10);
    }
    for (let x = K.kuleSol - 8; x < K.kuleSag; x += 42) dis(x, K.kuleUst - 34, 30, 34, 11);
    // Gölgeler, kenarlar, mazgal delikleri, kapı (bir kez çizilir)
    this.golge = sahne.add.graphics().setDepth(12);
    this.golgeCiz();
    // Hasar katmanı (aşama değişince yeniden çizilir)
    this.hasarCizim = sahne.add.graphics().setDepth(12);
    this.asama = 0;
    this.tohum = 1;
    this.pixellabKur();
  }

  // PixelLab çizimi varsa: taş dokulu parçaların yerine tek görsel. Mazgallar aynı görselden
  // kırpılır, böylece hasarla tek tek düşmeye devam eder. Çatlak ve gedik katmanı aynı kalır.
  pixellabKur() {
    const s = this.s, P = s.cache.json.get('kareler').kalePl;
    if (!P || !s.textures.exists('kale_pl')) return;
    for (const p of this.parcalar) p.setVisible(false);
    this.golge.setVisible(false);
    const govde = s.add.image(P.x, P.y, 'kale_pl_govde').setOrigin(0).setScale(P.piksel).setDepth(11);
    this.mazgallar = this.mazgallar.map(d => s.add.image(P.x, P.y, 'kale_pl').setOrigin(0).setScale(P.piksel).setDepth(d.depth)
      .setCrop((d.x - P.x) / P.piksel - 1, (d.y - P.y) / P.piksel - 1, d.width / P.piksel + 2, d.height / P.piksel + 1));
    this.parcalar = [govde, ...this.mazgallar];
  }

  golgeCiz() {
    const g = this.golge, K = AYAR.kale, z = AYAR.zemin;
    // Kulenin sura düşen gölgesi
    g.fillStyle(0x000000, 0.28).fillRect(K.kuleSag, K.surUst, 26, z - K.surUst);
    // Kule kenarları: sol koyu, sağ aydınlık
    g.fillStyle(0x000000, 0.35).fillRect(K.kuleSol, K.kuleUst, 12, z - K.kuleUst);
    g.fillStyle(0xffffff, 0.1).fillRect(K.kuleSag - 10, K.kuleUst, 10, z - K.kuleUst);
    // Sur ön yüzü (kalınlık) ve payanda
    g.fillStyle(0x000000, 0.3).fillRect(K.onX - 22, K.surUst, 22, z - K.surUst);
    g.fillStyle(0x000000, 0.18).fillRect(K.onX - 40, K.surUst + 120, 18, z - K.surUst - 120);
    // Taç kuşağı: mazgalların altında çıkıntı
    g.fillStyle(0x2a2420, 1).fillRect(0, K.surUst - 2, K.onX + 6, 10);
    g.fillStyle(0x8a8276, 1).fillRect(0, K.surUst - 2, K.onX + 6, 4);
    g.fillStyle(0x2a2420, 1).fillRect(K.kuleSol - 10, K.kuleUst - 2, K.kuleSag - K.kuleSol + 20, 12);
    g.fillStyle(0x8a8276, 1).fillRect(K.kuleSol - 10, K.kuleUst - 2, K.kuleSag - K.kuleSol + 20, 4);
    // Ok yarıkları
    for (const y of [470, 640, 790]) {
      g.fillStyle(0x0c0a0c, 1).fillRect(208, y, 10, 46);
      g.fillStyle(0x0c0a0c, 1).fillRect(200, y + 16, 26, 8);
    }
    // Ahşap kapı (surun dibinde, kemerli)
    g.fillStyle(0x1a1410, 1).fillRect(26, z - 150, 70, 164);
    g.fillCircle(61, z - 150, 35);
    g.fillStyle(0x5a3c22, 1).fillRect(32, z - 146, 58, 160);
    g.fillCircle(61, z - 146, 29);
    g.fillStyle(0x3a2616, 1);
    for (let x = 44; x < 90; x += 14) g.fillRect(x, z - 170, 3, 184);
    g.fillStyle(0x2a2a2e, 1).fillRect(32, z - 110, 58, 6).fillRect(32, z - 40, 58, 6);
    // Dipte kir ve yosun
    g.fillGradientStyle(0x1e2416, 0x1e2416, 0x1e2416, 0x1e2416, 0, 0, 0.6, 0.6);
    g.fillRect(0, z - 120, K.onX, 134);
    // Dış çizgi
    g.lineStyle(3, 0x14100e, 1);
    g.strokeRect(K.kuleSol, K.kuleUst, K.kuleSag - K.kuleSol, z - K.kuleUst + 14);
    g.lineBetween(K.onX, K.surUst, K.onX, z + 14);
    // Bayrak direği ve sancak
    g.fillStyle(0x2a2018, 1).fillRect(K.kuleSol + 14, K.kuleUst - 150, 6, 120);
  }

  // Hasar aşaması: >0.8 sağlam, >0.6 çatlak, >0.4 düşen taş, >0.2 kırık mazgal, altı gedik
  guncelle(oran) {
    const asama = oran > 0.8 ? 0 : oran > 0.6 ? 1 : oran > 0.4 ? 2 : oran > 0.2 ? 3 : 4;
    if (asama === this.asama) return;
    this.asama = asama;
    const g = this.hasarCizim, K = AYAR.kale, z = AYAR.zemin;
    g.clear();
    let r = 11;
    const rnd = () => { r = (r * 9301 + 49297) % 233280; return r / 233280; };
    const catlak = (x, y, uzunluk, kalin) => {
      g.lineStyle(kalin, 0x0e0c0c, 0.9);
      g.beginPath();
      g.moveTo(x, y);
      let cx = x, cy = y;
      for (let i = 0; i < 6; i++) {
        cx += (rnd() - 0.6) * uzunluk / 3;
        cy += uzunluk / 6;
        g.lineTo(cx, cy);
      }
      g.strokePath();
    };
    if (asama >= 1) {
      catlak(K.onX - 30, K.surUst + 20, 160, 3);
      catlak(K.kuleSag - 40, K.kuleUst + 60, 140, 2);
    }
    if (asama >= 2) {
      catlak(K.onX - 70, K.surUst + 140, 200, 3);
      catlak(K.kuleSol + 50, K.kuleUst + 20, 180, 3);
      // Düşmüş taş izleri ve is
      g.fillStyle(0x1a1612, 0.8).fillRect(K.onX - 60, K.surUst + 60, 34, 22).fillRect(K.kuleSag - 70, K.kuleUst + 160, 28, 18);
      g.fillStyle(0x000000, 0.25).fillEllipse(K.onX - 40, K.surUst + 30, 90, 60);
      // Moloz
      g.fillStyle(0x6a6458, 1);
      for (let i = 0; i < 8; i++) g.fillRect(K.onX + 4 + rnd() * 50, z - 4 - rnd() * 10, 8 + rnd() * 10, 6 + rnd() * 6);
    }
    for (let i = 0; i < this.mazgallar.length; i++) {
      // Aşama 3'ten itibaren mazgalların bir kısmı düşer
      const dus = asama >= 3 && (i % 3 === 1 || (asama >= 4 && i % 2 === 0));
      this.mazgallar[i].setVisible(!dus);
    }
    if (asama >= 4) {
      // Ön yüzde gedik
      g.fillStyle(0x0a0808, 1);
      g.fillTriangle(K.onX, K.surUst + 40, K.onX - 70, K.surUst + 110, K.onX, K.surUst + 220);
      g.fillStyle(0x3a342c, 1);
      g.fillTriangle(K.onX, K.surUst + 70, K.onX - 44, K.surUst + 112, K.onX, K.surUst + 180);
      catlak(K.onX - 80, K.surUst + 200, 220, 4);
    }
  }

  // Vurulunca kısa kızarma
  parla() {
    for (const p of this.parcalar) {
      if (p.asilRenk === undefined) p.asilRenk = p.tintTopLeft;
      p.setTint(0xff8a70);
    }
    this.s.time.delayedCall(70, () => { for (const p of this.parcalar) p.setTint(p.asilRenk); });
  }
}
