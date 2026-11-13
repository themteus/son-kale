// =============================================================
//  SAVAŞ SAHNESİ (savas.js)
//  Oyunun kalbi: dalgalar, oklar, isabet, altın, dükkân.
//  Durumlar: 'menu' → (iç kale) → 'savas' → (iç kale / 'dukkan') ... → 'bitti'
//  Dalga bitince gün sonu hesaplanır ve iç kale sahnesi açılır.
// =============================================================

// Kan, toz, ateş, patlama ve uçan yazılar
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
    this.atesParca = s.add.particles(0, 0, 'daire', {
      speed: { min: 10, max: 60 }, angle: { min: 250, max: 290 }, gravityY: -220,
      lifespan: 500, scale: { start: 0.7, end: 0.1 }, alpha: { start: 0.9, end: 0 }, tint: [0xffd060, 0xff8a30, 0xe04a20],
      blendMode: 'ADD', emitting: false,
    }).setDepth(36);
    this.sifaParca = s.add.particles(0, 0, 'daire', {
      speed: { min: 20, max: 90 }, angle: { min: 230, max: 310 }, gravityY: -120,
      lifespan: 700, scale: { start: 0.6, end: 0.1 }, alpha: { start: 0.8, end: 0 }, tint: [0x8aff9a, 0x40d060],
      blendMode: 'ADD', emitting: false,
    }).setDepth(36);
    this.patlamaParca = s.add.particles(0, 0, 'daire', {
      speed: { min: 120, max: 520 }, lifespan: { min: 300, max: 800 }, scale: { start: 2.4, end: 0.2 },
      alpha: { start: 1, end: 0 }, tint: [0xffe080, 0xff9030, 0xd04020, 0x402a20], blendMode: 'ADD', emitting: false,
    }).setDepth(37);
  }
  // Piksel efekt şeridi oynatır (fx_<ad>); şerit yoksa ya da ekranda çok efekt varsa hiçbir şey yapmaz
  serit(ad, x, y, olcek = 3, ayar = {}) {
    const s = this.s, k = 'fx_' + ad;
    if (!s.anims.exists(k)) return null;
    this.seritSayisi = this.seritSayisi || 0;
    if (this.seritSayisi >= 60) return null;
    this.seritSayisi++;
    const sp = s.add.sprite(x, y, k, 0).setScale(olcek).setDepth(ayar.derinlik || 36);
    if (ayar.aci !== undefined) sp.setRotation(ayar.aci);
    if (ayar.orijin) sp.setOrigin(ayar.orijin[0], ayar.orijin[1]);
    if (ayar.renk) sp.setTint(ayar.renk);
    if (ayar.alfa) sp.setAlpha(ayar.alfa);
    if (ayar.ayna) sp.setFlipX(true);
    sp.once('animationcomplete', () => { sp.destroy(); this.seritSayisi--; });
    sp.play(k);
    return sp;
  }
  kivilcim(x, y, kalkanda) { this.serit('kivilcim', x, y, kalkanda ? 3 : 2.2, { derinlik: 37 }); }
  duman(x, y, agir) { this.serit('duman', x, y - 10, agir ? 4 : 2.6, { ayna: Math.random() < 0.5 }); }
  iz(x, y, aci) { this.serit('ok_izi', x, y, 2, { aci, orijin: [1, 0.5], derinlik: 29, alfa: 0.55 }); }
  kan(x, y, n = 8, renk) {
    if (renk) this.kanParca.setParticleTint(renk); else this.kanParca.setParticleTint([0x7a1010, 0x9a1a14, 0x5a0a0a]);
    this.kanParca.explode(n, x, y);
  }
  toz(x, y, n = 4) { this.tozParca.explode(n, x, y); }
  tas(x, y, n = 6) { this.tasParca.explode(n, x, y); }
  ates(x, y, n = 1) { this.atesParca.explode(n, x, y); }
  // Yanan düşmanın gövdesinde kısa alev (dusman.js çağırır)
  alev(x, y) { if (Math.random() < 0.35) this.serit('ates', x, y, 2, { orijin: [0.5, 0.9], ayna: Math.random() < 0.5 }); }
  sifa(x, y) { this.sifaParca.explode(6, x, y); }
  patlama(x, y) {
    if (this.serit('patlama', x, y, 3, { derinlik: 38 })) this.patlamaParca.explode(16, x, y);
    else this.patlamaParca.explode(40, x, y);
    this.tasParca.explode(10, x, y);
    this.kanParca.setParticleTint([0x6a7a20, 0x8a9a30]);
    this.kanParca.explode(16, x, y);
  }
  yazi(x, y, metin, renk = '#ffd76a', boyut = 30) {
    const t = this.s.add.text(x, y, metin, stil('govde', boyut, { fontStyle: 'bold', color: renk, stroke: '#120e0c', strokeThickness: 5 }))
      .setOrigin(0.5).setDepth(46);
    this.s.tweens.add({ targets: t, y: y - 70, alpha: 0, duration: 1000, ease: 'Quad.easeOut', onComplete: () => t.destroy() });
  }
}

// Kayıt (en iyi dalga, zorluk, ses). Gizli pencerede çalışmazsa sessizce geçer.
const Kayit = {
  oku(ad, varsayilan) { try { const v = localStorage.getItem('sonKalePhaser.' + ad); return v === null ? varsayilan : v; } catch (e) { return varsayilan; } },
  yaz(ad, deger) { try { localStorage.setItem('sonKalePhaser.' + ad, String(deger)); } catch (e) { /* önemli değil */ } },
};

class SavasSahnesi extends Phaser.Scene {
  constructor() { super('savas'); }

  create() {
    this.scene.stop('kale'); // yeniden başlarken eski iç kale kapansın
    // Duraklatılmışken "Baştan Başla" denirse: animasyonlar bütün oyunda ortaktır, açılmalı
    if (this.anims.paused) this.anims.resumeAll();
    this.time.paused = false;
    this.durum = 'menu';
    this.dalga = 0;
    this.altin = 0;
    this.seviye = {};
    this.zorlukAdi = Kayit.oku('zorluk', 'normal');
    if (!ZORLUKLAR[this.zorlukAdi]) this.zorlukAdi = 'normal';
    this.zorluk = ZORLUKLAR[this.zorlukAdi];
    this.surEnFazla = AYAR.kale.can;
    this.surCan = this.surEnFazla;
    this.surIz = this.surCan;
    this.dayaniklilik = AYAR.dayaniklilik.enFazla;
    this.ruzgar = 0;
    this.dusmanlar = [];
    this.oklar = [];
    this.dusmanOklari = [];
    this.askerler = [];
    this.kuyruk = [];
    this.oldurulen = 0;
    this.kafaVurusu = 0;
    this.kafaSerisi = 0;     // Art arda kafa vuruşu
    this.keskinHazir = false;
    this.duraklatildi = false;
    this.okTuru = 'normal';
    this.stok = { ates: 0, delici: 0 };
    this.yagmurBekleme = 0;
    this.kurtuldu = false;
    this.gorulen = {};
    this.ekonomi = new Ekonomi();

    this.manzara = new Manzara(this);
    this.kale = new Kale(this);
    this.oyuncu = new Okcu(this, AYAR.oyuncu.x, AYAR.oyuncu.ayakY, true);
    this.efekt = new Efekt(this);
    this.karanlik = this.add.rectangle(0, 0, AYAR.en, AYAR.boy, 0x0a0c1e, 0).setOrigin(0).setDepth(40);
    this.arayuz = new Arayuz(this);
    this.girdiKur();
    this.sesKur();
    this.arayuz.baslangic();
    // Sekme / uygulama arka plana geçince savaş kendiliğinden duraklar
    const arkaPlan = () => { if (this.durum === 'savas' && !this.duraklatildi) this.duraklat(); };
    this.game.events.on('hidden', arkaPlan);
    this.events.once('shutdown', () => this.game.events.off('hidden', arkaPlan));
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
    // Klavye: Esc duraklat, M ses, 1-2-3 ok türü, Q yağmur; dükkânda 1-9 satın al, Boşluk devam
    this.input.keyboard.on('keydown', e => {
      if (e.repeat) return; // basılı tutulan tuş tekrar tekrar çalışmasın
      const k = e.key.toLowerCase();
      if (k === 'escape' || k === 'p') this.duraklat();
      else if (k === 'm') this.sesAcKapa();
      else if (this.durum === 'dukkan' && e.key >= '1' && e.key <= String(YUKSELTMELER.length)) {
        if (this.satinAl(YUKSELTMELER[+e.key - 1]) && this.arayuz.dukkanYenile) this.arayuz.dukkanYenile();
      } else if (this.durum === 'savas' && ['1', '2', '3'].includes(e.key)) this.okSec(['normal', 'ates', 'delici'][+e.key - 1]);
      else if (this.durum === 'savas' && k === 'q') this.yagmurYagdir();
      else if (k === ' ' && this.durum === 'dukkan') this.dalgaBaslat();
      else if (k === ' ' && this.durum === 'menu') this.devamEt();
    });
  }

  // ---------------- Ses ----------------
  sesKur() {
    this.sesAcik = Kayit.oku('ses', 'acik') !== 'kapali';
    this.sound.mute = !this.sesAcik;
    // Ses yöneticisi bütün oyunda ortak: yeniden başlarken müzik ikinci kez eklenmesin
    this.muzik = this.sound.get('muzik') || this.sound.add('muzik', { loop: true, volume: 0.3 });
    this.arayuz.sesDugme.yazi.setText(this.sesAcik ? '♪' : '×');
  }
  sesCal(ad, ses = 0.5) {
    if (!this.sesAcik) return;
    this.sound.play(ad, { volume: ses, detune: (Math.random() - 0.5) * 200 });
  }
  sesAcKapa() {
    this.sesAcik = !this.sesAcik;
    this.sound.mute = !this.sesAcik;
    Kayit.yaz('ses', this.sesAcik ? 'acik' : 'kapali');
    this.arayuz.sesDugme.yazi.setText(this.sesAcik ? '♪' : '×');
  }

  duraklat() {
    if (this.durum !== 'savas') return;
    this.duraklatildi = !this.duraklatildi;
    this.girdi.basili = false;
    this.girdi.dokundu = false;
    // Gerili yay bırakılır (devam edince ok kendiliğinden uçmasın)
    this.oyuncu.geriyor = false;
    this.oyuncu.otoBirak = false;
    this.time.paused = this.duraklatildi; // Ok Yağmuru gibi zamanlı işler de dursun
    if (this.duraklatildi) { this.tweens.pauseAll(); this.anims.pauseAll(); this.arayuz.duraklatPaneli(); }
    else { this.tweens.resumeAll(); this.anims.resumeAll(); this.arayuz.paneliKapat(); }
  }

  // ---------------- Akış ----------------
  zorlukSec(ad) {
    this.zorlukAdi = ad;
    this.zorluk = ZORLUKLAR[ad];
    Kayit.yaz('zorluk', ad);
  }

  oyunuBaslat() {
    this.arayuz.paneliKapat();
    if (!this.muzik.isPlaying) this.muzik.play();
    this.durum = 'kale';
    this.iceGir();
  }

  // ---------------- Kayıt ----------------
  // Her gün iç kaleye girerken oyun kaydedilir; menüde "Devam et" çıkar.
  kaydet() {
    const E = this.ekonomi;
    const veri = {
      surum: 1, zorluk: this.zorlukAdi, dalga: this.dalga, altin: this.altin, seviye: this.seviye, stok: this.stok,
      surCan: Math.round(this.surCan), kurtuldu: this.kurtuldu, oldurulen: this.oldurulen, kafaVurusu: this.kafaVurusu,
      gorulen: this.gorulen, keskinHazir: this.keskinHazir, sonraki: this.kesif(),
      ekonomi: { kaynak: E.kaynak, nufus: E.nufus, bina: E.bina, asker: E.asker, surSeviye: E.surSeviye, pazar: E.pazar, rapor: E.rapor, acilOnarildi: E.acilOnarildi,
        yapi: E.yapi, moral: E.moral, sefer: E.sefer, solenYapildi: E.solenYapildi },
    };
    Kayit.yaz('kayit', JSON.stringify(veri));
  }
  kayitOku() {
    try { const v = JSON.parse(Kayit.oku('kayit', 'null')); return v && v.surum === 1 && ZORLUKLAR[v.zorluk] ? v : null; } catch (e) { return null; }
  }
  kayitSil() { Kayit.yaz('kayit', 'null'); }
  // Kayıtlı oyunu yükleyip iç kaleden devam et
  devamEt() {
    const v = this.kayitOku();
    if (!v) return this.oyunuBaslat();
    this.zorlukSec(v.zorluk);
    for (const k of ['dalga', 'altin', 'seviye', 'stok', 'kurtuldu', 'oldurulen', 'kafaVurusu', 'gorulen', 'keskinHazir', 'sonraki']) if (v[k] !== undefined) this[k] = v[k];
    Object.assign(this.ekonomi, v.ekonomi);
    this.surEnFazla = 0;
    this.surCanAyarla();
    this.surCan = Math.min(v.surCan, this.surEnFazla);
    this.surIz = this.surCan;
    this.kale.guncelle(this.surCan / this.surEnFazla);
    const gok = this.manzara.boya(this.dalga + 1);
    this.karanlik.setAlpha(gok.karanlik);
    this.kale.ortamTonu(gok.sis);
    this.arayuz.paneliKapat();
    if (!this.muzik.isPlaying) this.muzik.play();
    this.iceGir();
  }

  // İç kale sahnesine geç (savaş sahnesi uyur)
  iceGir(rapor) {
    if (this.durum !== 'bitti') this.kaydet();
    this.arayuz.paneliKapat();
    this.durum = 'kale';
    if (this.scene.isSleeping('kale')) this.scene.wake('kale', { rapor });
    else this.scene.launch('kale', { oyun: this, rapor });
    this.scene.sleep();
  }
  // İç kaleden savaşa
  iceridenCik() {
    this.scene.wake();
    this.dalgaBaslat();
  }
  // İç kaleden silah ustasına (dükkân)
  dukkanAc() {
    this.scene.wake();
    this.durum = 'dukkan';
    this.arayuz.dukkan(this);
  }

  dalgaBaslat() {
    // İç kalede ve dükkânda yapılanlar da kaydedilsin (dalga artmadan önce)
    this.kaydet();
    // Gözcülerin bildirdiği liste: dalga artmadan önce alınmalı (sonra alınırsa bir sonraki dalganın listesi gelir)
    const liste = this.kesif().kuyruk.slice();
    this.arayuz.paneliKapat();
    this.dalga++;
    this.atis = { iska: 0, isabet: 0, kafa: 0 }; // Dalga sonu özeti için (oyuncunun okları)
    this.durum = 'savas';
    // Dalga listesi (keşif raporunda önceden gösterilen liste)
    const n = this.dalga, D = AYAR.dalga;
    this.kuyruk = liste;
    this.sonraki = null;
    const patron = this.kuyruk.includes('patron');
    this.cikisSayaci = D.ilkBekleme;
    this.cikisAraligi = Math.max(0.45, 1.8 - n * 0.1);
    // Günün rüzgârı
    const R = AYAR.ruzgar;
    this.ruzgar = Math.random() < R.sakinOlasilik ? 0 : (Math.random() * 2 - 1) * R.enFazla * Math.min(1, 0.4 + n * 0.1);
    // Gökyüzü dalgaya göre kararır
    const r = this.manzara.boya(n);
    this.karanlik.setAlpha(r.karanlik);
    this.kale.ortamTonu(r.sis);
    this.askerleriDiz();
    this.barikatKuruldu = false;
    if (patron) this.arayuz.duyur(`${n}. Dalga`, 'Yerin sarsılıyor... Ak Dev geliyor!');
    else this.arayuz.duyur(`${n}. Dalga`, this.ruzgar === 0 ? 'Rüzgâr yok' : '');
  }

  // Bir dalganın düşman listesi
  dalgaListesi(n) {
    const D = AYAR.dalga;
    const sayi = Math.round(D.temel + D.artis * n);
    const kuyruk = [];
    for (let i = 0; i < sayi; i++) kuyruk.push(dusmanSec(n));
    if (n >= 4) {
      const yarasa = Math.floor((n - 2) * 0.8);
      for (let i = 0; i < yarasa; i++) kuyruk.splice(Math.floor(Math.random() * kuyruk.length), 0, 'yarasa');
    }
    // Patron dalgası: sürünün ortasında gelir
    if (n % PATRON_ARASI === 0) kuyruk.splice(Math.floor(kuyruk.length / 2), 0, 'patron');
    return kuyruk;
  }

  // Keşif: sıradaki dalga önceden belli olur, iç kalede gösterilir.
  // ozet: "34 düşman · 3 Dev · 2 Kalkanlı" gibi kısa yazı
  kesif() {
    const n = this.dalga + 1;
    if (!this.sonraki || this.sonraki.n !== n) {
      const kuyruk = this.dalgaListesi(n);
      const say = {};
      for (const t of kuyruk) say[t] = (say[t] || 0) + 1;
      // Tehlikeli olanlar önce yazılır
      const onemli = ['patron', 'kalkanlidev', 'dev', 'sifaci', 'patlayan', 'tirmanici', 'kalkanli', 'okcuiskelet', 'kurt'];
      const parcalar = onemli.filter(t => say[t]).map(t => `${say[t]} ${DUSMAN_TURLERI[t].ad}`);
      const tehlike = say.patron ? 3 : (say.dev || 0) + (say.kalkanlidev || 0) * 2 + (say.patlayan || 0) >= 4 ? 2 : 1;
      this.sonraki = { n, kuyruk, say, tehlike,
        ozet: `${kuyruk.length} düşman` + (parcalar.length ? ' · ' + parcalar.slice(0, 4).join(' · ') : '') };
    }
    return this.sonraki;
  }

  dalgaBitti() {
    this.durum = 'dukkan';
    const bonus = Math.round((AYAR.dalga.bitirmeAltini + this.dalga * AYAR.dalga.bitirmeArtisi) * this.zorluk.altin);
    this.altin += bonus;
    this.efekt.yazi(AYAR.en / 2, 420, `Dalga bitti! +${bonus} altın`, '#ffd76a', 44);
    // Oyuncunun isabet özeti
    const A = this.atis, toplam = A ? A.isabet + A.iska : 0;
    if (toplam > 0) {
      const yuzde = Math.round(100 * A.isabet / toplam);
      this.time.delayedCall(250, () => this.efekt.yazi(AYAR.en / 2, 480,
        `İsabet %${yuzde} (${A.isabet}/${toplam})` + (A.kafa ? ` · ${A.kafa} kafa` : ''), yuzde >= 60 ? '#a0e0a0' : '#efe6d2', 32));
    }
    this.sesCal('level_up', 0.5);
    this.girdi.basili = false;
    this.oyuncu.geriyor = false;
    this.enIyiKaydet();
    // Kurtuluş günü: yardım ordusu gelir
    if (!this.kurtuldu && this.dalga >= this.zorluk.kurtulus) {
      this.kurtuldu = true;
      this.durum = 'zafer';
      this.time.delayedCall(1300, () => this.arayuz.zafer(this));
      return;
    }
    this.time.delayedCall(1300, () => this.gunuBitir());
  }

  // Gün sonu: üretim, yemek, onarım, ok toplama → iç kale
  gunuBitir() {
    if (this.durum === 'bitti') return;
    const r = this.ekonomi.gunuHesapla(this, true);
    this.surIz = this.surCan;
    this.kale.guncelle(this.surCan / this.surEnFazla);
    if (this.ekonomi.nufus < EKONOMI.enAzNufus) return this.oyunBitti('Halk tükendi');
    this.iceGir(r);
  }

  enIyiKaydet() {
    const ad = 'enIyi.' + this.zorlukAdi;
    if (this.dalga > +Kayit.oku(ad, 0)) Kayit.yaz(ad, this.dalga);
  }

  oyunBitti(neden = 'Kale düştü') {
    if (this.durum === 'bitti') return;
    this.kayitSil();
    this.neden = neden;
    this.durum = 'bitti';
    this.girdi.basili = false;
    this.cameras.main.shake(500, 0.012);
    this.sesCal('boss', 0.7);
    this.time.delayedCall(900, () => this.arayuz.oyunSonu(this));
  }

  // Surdaki askerler iç kalede atananlar kadar olur
  askerleriDiz() {
    const istenen = Math.min(this.ekonomi.asker, AYAR.askerYerleri.length);
    while (this.askerler.length < istenen) {
      const y = AYAR.askerYerleri[this.askerler.length];
      this.askerler.push(new Okcu(this, y.x, y.ayakY, false));
    }
    while (this.askerler.length > istenen) this.askerler.pop().yokEt();
  }

  // ---------------- Yükseltmeler ----------------
  satinAl(u) {
    const sv = this.seviye[u.id] || 0;
    if (sv >= u.enFazla) return false;
    const f = u.fiyat(sv, this);
    if (this.altin < f) return false;
    this.altin -= f;
    if (u.stok) this.stok[u.id] += 10;
    else this.seviye[u.id] = sv + 1;
    if (u.id === 'payanda') this.surCanAyarla();
    this.sesCal('coin', 0.5);
    return true;
  }
  // Surun en yüksek canı: sur seviyesi × payanda. Artan kadar can da eklenir.
  surCanAyarla() {
    const yeni = Math.round(SUR.can[this.ekonomi.surSeviye - 1] * (1 + 0.1 * (this.seviye.payanda || 0)));
    this.surCan += Math.max(0, yeni - this.surEnFazla);
    this.surEnFazla = yeni;
    this.surCan = Math.min(this.surCan, this.surEnFazla);
  }

  // Ok hasarı: dükkân (Keskin Uçlar) × demircinin uç kalitesi
  okHasari() { return AYAR.ok.hasar * (1 + 0.2 * (this.seviye.hasar || 0)) * this.ekonomi.ucKalite.hasar; }
  okHizi() { return AYAR.ok.hiz; }
  okSayisi() { return 1 + (this.seviye.coklu || 0); }
  germeCarpani() { return Math.pow(0.88, this.seviye.germe || 0); }

  // Ok türü seç (stok yoksa normal kalır)
  okSec(tur) {
    if (tur !== 'normal' && this.stok[tur] <= 0) {
      this.efekt.yazi(AYAR.oyuncu.x + 80, AYAR.oyuncu.ayakY - 140, `${OK_TURLERI[tur].ad} ok kalmadı`, '#e0a080', 26);
      return;
    }
    this.okTuru = tur;
    this.sesCal('ui', 0.3);
  }
  // Oyuncunun bir sonraki okunun türü: stoktan düşer
  okTuruHarca(sayi) {
    const t = this.okTuru;
    if (t === 'normal') return 'normal';
    this.stok[t] = Math.max(0, this.stok[t] - sayi);
    if (this.stok[t] <= 0) this.okTuru = 'normal';
    return t;
  }

  // Ok Yağmuru: nişan noktasının çevresine gökten ok düşer
  yagmurYagdir() {
    const sv = this.seviye.yagmur || 0;
    if (!sv || this.yagmurBekleme > 0 || this.durum !== 'savas') return;
    const sayi = Math.min(this.ekonomi.kaynak.ok, YAGMUR.temelOk + YAGMUR.seviyeBasi * (sv - 1));
    if (sayi <= 0 || !this.ekonomi.okHarca(sayi)) return this.okBitti();
    this.yagmurBekleme = YAGMUR.bekleme;
    const hedef = kis(this.girdi.x, AYAR.kale.onX + 120, AYAR.en - 60);
    for (let i = 0; i < sayi; i++) {
      this.time.delayedCall(i * 45, () => {
        const x = hedef + (Math.random() - 0.5) * 2 * YAGMUR.yayilma - 260;
        this.okEkle(x, -40 - Math.random() * 80, 1.12 + Math.random() * 0.08, 1150, this.okHasari() * YAGMUR.hasarOrani, false, 'normal', true);
      });
    }
    this.sesCal('confirm', 0.5);
  }

  // ---------------- Oklar ----------------
  // Ambarda ok kalmadı uyarısı (sık tekrar etmesin)
  okBitti() {
    if (this.okBittiUyari > 0) return;
    this.okBittiUyari = 3;
    this.efekt.yazi(AYAR.oyuncu.x + 120, AYAR.oyuncu.ayakY - 150, 'Ambarda ok kalmadı!', '#ff8a70', 32);
  }

  // ambar: ok iç kalenin ambarından çıktı (savaştan sonra bir kısmı toplanır)
  okEkle(x, y, aci, hiz, hasar, oyuncudan, tur = 'normal', ambar = false, keskin = false) {
    const sprite = this.add.image(x, y, 'ok').setOrigin(0.85, 0.5).setDepth(30);
    if (tur !== 'normal') sprite.setTint(OK_TURLERI[tur].renk);
    if (keskin) sprite.setTint(0xffe08a).setScale(1.3);
    const delip = Math.max(tur === 'delici' ? OK_TURLERI.delici.delip : 1, keskin ? AYAR.keskin.delip : 1);
    this.oklar.push({ x, y, vx: Math.cos(aci) * hiz, vy: Math.sin(aci) * hiz, hasar, oyuncudan, tur, sprite, sapli: false, omur: 3,
      delip, keskin, vurulan: [], ambar });
    return this.oklar[this.oklar.length - 1];
  }

  // Okçu İskelet sura ok atar (oyuncu bu okları havada vurabilir)
  dusmanOkuAt(d) {
    const x = d.x - 20, y = d.y - d.boy * 0.7;
    const tx = AYAR.kale.onX - 30 - Math.random() * 60, ty = AYAR.kale.surUst + 20 + Math.random() * 160;
    // Yaklaşık 1.3 sn uçacak bir kavis
    const t = 1.3, g = AYAR.yercekimi;
    const vx = (tx - x) / t, vy = (ty - y - 0.5 * g * t * t) / t;
    const sprite = this.add.image(x, y, 'ok').setOrigin(0.85, 0.5).setDepth(30).setTint(0x9a8a70);
    this.dusmanOklari.push({ x, y, vx, vy, hasar: d.T.hasar, sprite });
    this.sesCal('shoot', 0.15);
  }

  dusmanOklariniGuncelle(dt) {
    const g = AYAR.yercekimi;
    for (const o of this.dusmanOklari) {
      o.vy += g * dt;
      o.x += o.vx * dt;
      o.y += o.vy * dt;
      o.sprite.setPosition(o.x, o.y).setRotation(Math.atan2(o.vy, o.vx));
      // Oyuncunun oku çarparsa ikisi de düşer
      for (const p of this.oklar) {
        if (p.sapli || p.sil || !p.oyuncudan) continue;
        if (Math.abs(p.x - o.x) < 26 && Math.abs(p.y - o.y) < 18) {
          o.sil = true;
          this.altin += 1;
          this.efekt.yazi(o.x, o.y - 30, 'Havada! +1', '#a0e0ff', 26);
          this.efekt.tas(o.x, o.y, 4);
          this.sesCal('hit', 0.3);
          break;
        }
      }
      if (!o.sil && o.x <= AYAR.kale.onX) {
        o.sil = true;
        this.kaleyeVur(o.hasar, o.x, o.y, false);
      }
      if (!o.sil && o.y > AYAR.zemin) o.sil = true;
      if (o.sil) o.sprite.destroy();
    }
    this.dusmanOklari = this.dusmanOklari.filter(o => !o.sil);
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
      if (o.tur === 'ates' && Math.random() < dt * 30) this.efekt.ates(o.x, o.y);
      if (o.oyuncudan && Math.random() < dt * 20) this.efekt.iz(o.x, o.y, Math.atan2(o.vy, o.vx));
      // Hızlı oklar düşmanın içinden geçmesin diye adımı bölüyoruz
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
          if (!z.canli || o.vurulan.includes(z) || !z.icindeMi(ux, uy)) continue;
          this.isabet(o, z, ux, uy);
          break;
        }
        if (!o.sil && !o.sapli && o.y >= AYAR.zemin + 6) {
          if (o.oyuncudan && !o.yan && !o.vurulan.length) { this.seriBoz(); this.iskaSay(); }
          o.y = AYAR.zemin + 6;
          o.sapli = true;
          o.omur = 3;
          this.efekt.toz(o.x, AYAR.zemin + 4, 3);
        }
      }
      if (o.sil) continue;
      if (o.x > AYAR.en + 80 || o.x < -80) {
        if (o.oyuncudan && !o.yan && !o.vurulan.length) { this.seriBoz(); this.iskaSay(); }
        o.sprite.destroy(); o.sil = true; continue;
      }
      o.sprite.setPosition(o.x, o.y);
      if (!o.sapli) o.sprite.setRotation(Math.atan2(o.vy, o.vx));
    }
    this.oklar = this.oklar.filter(o => !o.sil);
  }

  // Dalga sonu özeti için oyuncunun ıskası
  iskaSay() { if (this.atis && this.durum === 'savas') this.atis.iska++; }

  isabet(o, z, x, y) {
    if (o.ambar && !o.vurulan.length) this.ekonomi.okSaplandi();
    if (o.oyuncudan && !o.yan && !o.vurulan.length && this.atis) this.atis.isabet++;
    o.vurulan.push(z);
    const kafa = z.kafaMi(y);
    let hasar = o.hasar * (kafa ? AYAR.ok.kafaCarpani : 1);
    if (!kafa && z.T.kemik) hasar *= z.T.kemik;                 // İskelet: oklar kemikten kayar
    const kalkanda = !kafa && z.T.kalkan && o.tur !== 'delici' && !o.keskin;  // Delici ve keskin ok kalkanı deler
    if (kalkanda) hasar *= 1 - z.T.kalkan;
    if (o.tur === 'ates') z.tutustur(o.hasar * OK_TURLERI.ates.yanma, OK_TURLERI.ates.yanmaSure);
    const oldu = z.vur(hasar);
    this.efekt.kivilcim(x, y, kalkanda);
    if (kalkanda) { this.efekt.tas(x, y, 3); this.sesCal('impact', 0.2); }
    else this.efekt.kan(x, y, kafa ? 12 : 6, z.T.kemik ? 0xd8d0bc : null);
    z.it(8);
    this.sesCal('hit', 0.35);
    if (o.oyuncudan && !o.yan && o.vurulan.length === 1 && !o.keskin) { if (kafa) this.seriKafa(); else this.seriBoz(); }
    if (kafa && o.oyuncudan) {
      this.kafaVurusu++;
      if (this.atis) this.atis.kafa++;
      this.altin += AYAR.ok.kafaAltin;
      this.efekt.yazi(x, z.ust - 20, `KAFA! +${AYAR.ok.kafaAltin}`);
    }
    if (oldu) this.dusmanOldu(z, true);
    // Delici ok birkaç düşmandan geçer
    o.delip--;
    if (o.delip > 0 && !kalkanda) return;
    // Ok düşmanın üstünde saplı kalır (ölen uçan düşmanda kaybolur)
    if (z.canli || !z.T.ucan) {
      o.sapli = true;
      o.omur = 99;
      o.sil = true;
      const sp = o.sprite;
      if (z.canli || z.sprite.active) {
        sp.setDepth(z.sprite.depth + 0.01);
        z.saplananlar.push({ sprite: sp, dx: x - z.x + Math.cos(Math.atan2(o.vy, o.vx)) * 6, dy: y - z.y });
        sp.setPosition(x, y);
        // Öldüren ok: ceset solarken o da solsun (yoksa birden kaybolur)
        if (!z.canli) this.tweens.add({ targets: sp, alpha: 0, delay: 2600, duration: 900 });
      } else sp.destroy();
    } else {
      o.sprite.destroy();
      o.sil = true;
    }
  }

  // Düşman öldü: altın, sayaç, ses
  dusmanOldu(z, oktan) {
    if (!z.canli) return;
    const altin = Math.round(z.T.altin * (1 + AYAR.dalga.altinArtisi * (this.dalga - 1)) * this.zorluk.altin);
    this.altin += altin;
    this.oldurulen++;
    this.efekt.yazi(z.x, z.ust - 50, `+${altin}`, '#ffd76a', z.T.patron ? 44 : 26);
    this.sesCal(z.T.agir ? 'big_kill' : 'kill', 0.45);
    if (z.T.patron) {
      this.arayuz.duyur('Ak Dev yıkıldı!', `+${altin} altın`);
      this.cameras.main.shake(400, 0.01);
    }
    z.ol(this);
  }

  // Düşman sura (ya da yarasa kuleye) vurdu
  kaleyeVur(hasar, x, y, agir) {
    if (this.durum !== 'savas') return;
    this.surCan = Math.max(0, this.surCan - hasar);
    this.kale.parla();
    this.kale.guncelle(this.surCan / this.surEnFazla);
    this.efekt.tas(x, y, agir ? 10 : 4);
    this.efekt.duman(x, y, agir);
    this.efekt.yazi(x + 10, y - 30, `-${hasar}`, '#ff6a50', 26);
    this.cameras.main.shake(agir ? 220 : 90, agir ? 0.006 : 0.002);
    this.sesCal('impact', agir ? 0.6 : 0.3);
    if (this.surCan <= 0 && !this.barikatKur()) this.oyunBitti();
  }

  // Sur yıkıldı: ambarda odun varsa halk bir kez barikat kurar
  barikatKur() {
    const B = AYAR.barikat, E = this.ekonomi;
    if (this.barikatKuruldu || E.kaynak.odun < B.odun) return false;
    this.barikatKuruldu = true;
    E.kaynak.odun -= B.odun;
    this.surCan = Math.round(this.surEnFazla * B.canOrani);
    this.kale.guncelle(this.surCan / this.surEnFazla);
    this.arayuz.duyur('Barikat!', `Halk ${B.odun} odunla gediği kapattı. Bir daha yıkılırsa kale düşer.`);
    this.sesCal('impact', 0.7);
    return true;
  }

  // Kafa serisi: oyuncunun okları için
  seriKafa() {
    this.kafaSerisi++;
    if (this.kafaSerisi >= AYAR.keskin.seri && !this.keskinHazir) {
      this.keskinHazir = true;
      this.kafaSerisi = 0;
      this.efekt.yazi(AYAR.oyuncu.x + 120, AYAR.oyuncu.ayakY - 160, 'Keskin ok hazır!', '#ffe08a', 34);
      this.sesCal('confirm', 0.4);
    }
  }
  seriBoz() { this.kafaSerisi = 0; }

  kalanDusman() {
    return this.kuyruk.length + this.dusmanlar.filter(d => d.canli).length;
  }
  patron() {
    return this.dusmanlar.find(d => d.T.patron && d.canli);
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
    if (this.yagmurBekleme > 0) this.yagmurBekleme -= dt;
    if (this.okBittiUyari > 0) this.okBittiUyari -= dt;
    // Yeni düşman çıkar
    if (this.kuyruk.length) {
      this.cikisSayaci -= dt;
      if (this.cikisSayaci <= 0) {
        const tur = this.kuyruk.shift();
        this.dusmanlar.push(new Dusman(this, tur, this.dalga, this.zorluk));
        const T = DUSMAN_TURLERI[tur];
        if (T.ipucu && !this.gorulen[tur]) {
          this.gorulen[tur] = true;
          this.arayuz.duyur('Yeni düşman: ' + T.ad, T.ipucu);
        }
        if (T.patron) this.sesCal('boss', 0.7);
        this.cikisSayaci = (tur === 'yarasa' ? 0.3 : this.cikisAraligi * (0.6 + Math.random() * 0.8)) * this.zorluk.cikis;
      }
    }
    this.oyuncu.guncelle(dt, this);
    for (const a of this.askerler) a.guncelle(dt, this);
    for (const d of this.dusmanlar) d.guncelle(dt, this);
    this.dusmanlar = this.dusmanlar.filter(d => !d.olu);
    this.oklariGuncelle(dt);
    this.dusmanOklariniGuncelle(dt);
    if (this.durum === 'savas' && this.kalanDusman() === 0) this.dalgaBitti();
  }
}
