// =============================================================
//  YÜKLEME (yukle.js)
//  Önce kareler.json okunur (her şeridin kare boyu), sonra
//  görseller, dokular ve sesler yüklenir, animasyonlar kurulur.
// =============================================================

class YukleSahnesi extends Phaser.Scene {
  constructor() { super('yukle'); }

  preload() {
    this.load.json('kareler', 'assets/gorsel/kareler.json');
    this.load.json('kale', 'assets/kale/kale.json');
    this.load.json('efektler', 'assets/gorsel/efekt/efektler.json'); // efekt şeritlerinin kare boyları (yoksa efektler parçacıkla kalır)
    if (typeof Varyant !== 'undefined') Varyant.listeyiYukle(this.load); // iç kale bina varyantlarının listesi
    if (typeof IcSusler !== 'undefined') IcSusler.listeyiYukle(this.load); // iç kaleye eklenen yapı ve eşyaların yerleşimi
    this.yaziGoster();
  }

  // Yükleme çubuğu
  yaziGoster() {
    const { en, boy } = AYAR;
    this.add.text(en / 2, boy / 2 - 70, 'SON KALE', { fontFamily: 'Grenze Gotisch, serif', fontSize: '96px', color: '#e8d9b0' }).setOrigin(0.5);
    const cubuk = this.add.graphics();
    this.load.on('progress', p => {
      cubuk.clear();
      cubuk.fillStyle(0x2a2420).fillRect(en / 2 - 300, boy / 2 + 30, 600, 18);
      cubuk.fillStyle(0xc9a24a).fillRect(en / 2 - 300, boy / 2 + 30, 600 * p, 18);
    });
  }

  create() {
    const K = this.cache.json.get('kareler');
    const g = 'assets/gorsel/';
    for (const [ad, m] of Object.entries(K.birimler)) {
      this.load.spritesheet(ad, g + ad + '.png', { frameWidth: m.fw, frameHeight: m.fh });
    }
    this.load.spritesheet('okcu', g + 'okcu.png', { frameWidth: K.okcu.fw, frameHeight: K.okcu.fh });
    this.load.spritesheet('asker', g + 'asker.png', { frameWidth: K.asker.fw, frameHeight: K.asker.fh });
    for (const ad of Object.keys(K.susler)) this.load.image(ad, g + ad + '.png');
    // PixelLab ile çizilmiş savaş kalesi (varsa): tamamı ve mazgalsız gövde
    if (K.manzaraPl) this.load.image('manzara_pl', g + 'manzara_pl.png');
    if (K.kalePl) { this.load.image('kale_pl', g + 'kale_pl.png'); this.load.image('kale_pl_govde', g + 'kale_pl_govde.png'); }
    for (const ad of ['tas', 'cim', 'toprak', 'tahta']) this.load.image(ad, 'assets/doku/' + ad + '.png');
    // Piksel sanat efekt dokuları (yoksa kucukDokular() kodla çizer)
    for (const ad of ['ok', 'kare', 'daire']) this.load.image(ad, g + 'efekt/' + ad + '.png');
    // Efekt şeritleri: fx_kivilcim, fx_duman, fx_patlama, fx_ates, fx_ok_izi
    const E = this.cache.json.get('efektler') || {};
    for (const [ad, m] of Object.entries(E)) this.load.spritesheet('fx_' + ad, g + 'efekt/' + ad + '.png', { frameWidth: m.fw, frameHeight: m.fh });
    for (const ad of ['shoot', 'hit', 'kill', 'big_kill', 'hurt', 'coin', 'level_up', 'ui', 'impact', 'boss', 'confirm']) {
      this.load.audio(ad, 'assets/ses/' + ad + '.mp3');
    }
    this.load.audio('muzik', 'assets/ses/muzik.mp3');
    // İç kale: arka plan, her binanın 3 seviyesi, köylüler
    const KM = this.cache.json.get('kale');
    this.load.image('k_arka', 'assets/kale/arka.png');
    this.load.image('k_on', 'assets/kale/on.png'); // ön surlar (her şeyin önünde)
    this.load.image('k_arka_karli', 'assets/kale/arka_karli.png'); // kış (varyant.js zemin)
    this.load.image('k_on_karli', 'assets/kale/on_karli.png');
    for (const ad of Object.keys(KM.binalar)) this.load.image('k_' + ad, 'assets/kale/' + ad + '.png');
    if (typeof Varyant !== 'undefined') Varyant.gorselleriYukle(this); // karlı / gece / yıkık bina görselleri
    // Avludaki süs eşyaları (ağaç, fıçı, araba...); ic_susler.js yenilerini listeye ekler
    if (typeof IcSusler !== 'undefined') {
      IcSusler.birlestir(KM, this.cache.json.get('kale_ic2'));
      IcSusler.varyantlariYukle(this, this.cache.json.get('kale_ic2'));
    }
    for (const ad of new Set((KM.susler || []).map(s => s.ad))) {
      this.load.image('ks_' + ad, 'assets/kale/sus/' + ad + '.png');
      // eski süslerin kış / gece görselleri (ic2 olanlar IcSusler.varyantlariYukle ile gelir)
      if (!ad.startsWith('ic2/')) for (const v of ['karli', 'gece']) this.load.image('ks_' + ad + '_' + v, 'assets/kale/sus/' + ad + '_' + v + '.png');
    }
    for (const [ad, m] of Object.entries(KM.koylu)) this.load.spritesheet(ad, 'assets/kale/' + ad + '.png', { frameWidth: m.fw, frameHeight: m.fh });
    this.load.once('complete', () => this.bitti(K, KM));
    this.load.start();
  }

  bitti(K, KM) {
    // Her düşman (ve köylü) için animasyonlar: <ad>_walk, <ad>_attack ...
    for (const [ad, m] of [...Object.entries(K.birimler), ...Object.entries(KM.koylu)]) {
      const sutun = Math.max(...Object.values(m.rows).map(r => r.frames));
      for (const [anim, r] of Object.entries(m.rows)) {
        const kareler = [];
        for (let i = 0; i < r.frames; i++) kareler.push({ key: ad, frame: r.row * sutun + i });
        this.anims.create({ key: ad + '_' + anim, frames: kareler, frameRate: r.fps, repeat: r.once ? 0 : -1 });
      }
    }
    // Efekt şeritlerinin animasyonları: fx_<ad> (bir kez oynar)
    const FPS = { kivilcim: 26, duman: 14, patlama: 16, ates: 16, ok_izi: 30 };
    for (const [ad, m] of Object.entries(this.cache.json.get('efektler') || {})) {
      if (!this.textures.exists('fx_' + ad)) continue;
      this.anims.create({ key: 'fx_' + ad, frames: this.anims.generateFrameNumbers('fx_' + ad, { start: 0, end: m.kare - 1 }), frameRate: FPS[ad] || 14, repeat: 0 });
    }
    this.kucukDokular();
    // Yazı tipleri hazır olunca oyuna geç
    const yazilar = document.fonts ? Promise.all([
      document.fonts.load('48px "Grenze Gotisch"'), document.fonts.load('24px "Alegreya Sans"'),
      document.fonts.load('bold 24px "Alegreya Sans"'),
    ]).catch(() => {}) : Promise.resolve();
    const zamanAsimi = new Promise(r => setTimeout(r, 2500));
    Promise.race([yazilar, zamanAsimi]).then(() => this.scene.start('savas'));
  }

  // Kodla üretilen küçük dokular: ok, kan, toz, kıvılcım, çam
  kucukDokular() {
    const g = this.make.graphics({ x: 0, y: 0 }, false);
    // Dosyadan yüklenen doku varsa onu kullan, kodla çizileni üretme
    const ure = (ad, w, h) => { if (!this.textures.exists(ad)) g.generateTexture(ad, w, h); };
    // Ok (sağa bakar, ucu sağda): 60x12
    g.fillStyle(0x1a1410).fillRect(2, 4, 50, 4);
    g.fillStyle(0x7a5530).fillRect(3, 5, 48, 2);
    g.fillStyle(0xd8d0bc).fillTriangle(0, 0, 14, 6, 0, 12);
    g.fillStyle(0xb8ae98).fillTriangle(2, 3, 12, 6, 2, 9);
    g.fillStyle(0x1a1410).fillTriangle(48, 1, 60, 6, 48, 11);
    g.fillStyle(0xbfc4c8).fillTriangle(49, 3, 58, 6, 49, 9);
    ure('ok', 60, 12);
    g.clear();
    g.fillStyle(0xffffff).fillRect(0, 0, 6, 6);
    ure('kare', 6, 6);
    g.clear();
    g.fillStyle(0xffffff).fillCircle(8, 8, 8);
    ure('daire', 16, 16);
    g.clear();
    g.fillStyle(0xffffff).fillCircle(48, 48, 48);
    g.generateTexture('ay', 96, 96);
    g.clear();
    // Çam silueti (tek renk, sonra boyanır): 120x260
    const cam = (w, h, ad) => {
      g.clear();
      g.fillStyle(0xffffff);
      g.fillRect(w / 2 - 5, h - 40, 10, 40);
      const kat = 6;
      for (let i = 0; i < kat; i++) {
        const y = h - 34 - i * (h - 50) / kat;
        const gen = (w / 2) * (1 - i / (kat + 1.5));
        g.fillTriangle(w / 2 - gen, y, w / 2 + gen, y, w / 2, y - (h - 40) / kat * 1.8);
      }
      g.generateTexture(ad, w, h);
    };
    cam(120, 260, 'cam1');
    cam(90, 300, 'cam2');
    cam(150, 220, 'cam3');
    g.destroy();
  }
}
