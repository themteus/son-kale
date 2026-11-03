// =============================================================
//  DÜŞMANLAR (dusman.js)
//  Zombi, koşucu, iskelet ve dev yürür, sura varınca vurur.
//  Yarasa havada uçar, kuledeki okçuya dalar.
//  Görseller sola bakar (kaleye doğru).
// =============================================================

class Dusman {
  constructor(sahne, turAdi, dalga) {
    const T = DUSMAN_TURLERI[turAdi];
    this.s = sahne;
    this.turAdi = turAdi;
    this.T = T;
    const m = sahne.cache.json.get('kareler').birimler[T.gorsel];
    this.canEnFazla = Math.round(T.can * (T.ucan ? Math.sqrt(dalgaCanCarpani(dalga)) : dalgaCanCarpani(dalga)));
    this.can = this.canEnFazla;
    this.hiz = T.hiz * (0.88 + Math.random() * 0.24);
    this.boy = T.boy;
    this.en = T.ucan ? T.boy * 1.3 : T.boy * 0.34;
    this.x = AYAR.en + 60 + Math.random() * 40;
    this.y = AYAR.zemin + Math.random() * 10; // ayak çizgisi (biraz derinlik)
    this.durum = 'yuru';   // yuru | vur | olu
    this.vurusSayaci = 0;
    this.itmeBekleme = 0;
    this.olu = false;      // true olunca listeden silinir
    this.saplananlar = []; // Üstünde saplı oklar
    // Sura vardığında duracağı yer (hepsi üst üste yığılmasın)
    this.durX = AYAR.kale.onX + this.en / 2 + 4 + Math.random() * 36;
    if (T.ucan) {
      this.ucusY = 260 + Math.random() * 260;
      this.y = this.ucusY;
      this.faz = Math.random() * 6;
      this.dalisX = 700 + Math.random() * 300;
    }
    this.sprite = sahne.add.sprite(this.x, this.y, T.gorsel, 0)
      .setOrigin(m.centerX / m.fw, m.footY / m.fh)
      .setDepth(20 + (this.y - AYAR.zemin) * 0.1 + Math.random() * 0.05);
    if (T.ucan) this.sprite.setOrigin(0.5, 0.5);
    this.sprite.play(T.gorsel + '_walk');
    this.sprite.anims.setProgress(Math.random());
  }

  // Vuruş kutusu (oklar için)
  get sol() { return this.x - this.en / 2; }
  get sag() { return this.x + this.en / 2; }
  get ust() { return this.T.ucan ? this.y - this.boy / 2 : this.y - this.boy; }
  get alt() { return this.T.ucan ? this.y + this.boy / 2 : this.y; }
  // Askerlerin nişan aldığı yer (göğüs)
  get nisanY() { return this.T.ucan ? this.y : this.y - this.boy * 0.62; }

  icindeMi(px, py) {
    return px >= this.sol && px <= this.sag && py >= this.ust && py <= this.alt;
  }
  kafaMi(py) {
    return this.T.ucan || py < this.ust + this.boy * this.T.kafa;
  }

  guncelle(dt, oyun) {
    if (this.durum === 'olu') return;
    if (this.itmeBekleme > 0) this.itmeBekleme -= dt;
    if (this.T.ucan) return this.uc(dt, oyun);

    if (this.durum === 'yuru') {
      this.x -= this.hiz * dt;
      if (this.x <= this.durX) {
        this.x = this.durX;
        this.durum = 'vur';
        this.vurusSayaci = this.T.vurus * 0.5;
        this.sprite.play(this.T.gorsel + '_attack');
      }
    } else if (this.durum === 'vur') {
      this.vurusSayaci -= dt;
      if (this.vurusSayaci <= 0) {
        this.vurusSayaci = this.T.vurus;
        oyun.kaleyeVur(this.T.hasar, this.x - this.en / 2, this.y - this.boy * 0.5, this.T.agir);
      }
    }
    this.sprite.setPosition(this.x, this.y);
    this.saplilariTasi();
  }

  // Yarasa: önce süzülür, sonra kuledeki okçuya dalar
  uc(dt, oyun) {
    this.faz += dt * 3;
    if (this.durum === 'yuru') {
      this.x -= this.hiz * dt;
      this.y = this.ucusY + Math.sin(this.faz) * 26;
      if (this.x < this.dalisX) {
        this.durum = 'vur';
        this.sprite.play(this.T.gorsel + '_attack');
      }
    } else {
      const tx = AYAR.oyuncu.x + 30, ty = AYAR.oyuncu.ayakY - 60;
      const dx = tx - this.x, dy = ty - this.y, d = Math.hypot(dx, dy);
      const v = this.hiz * 1.5;
      this.x += dx / d * v * dt;
      this.y += dy / d * v * dt + Math.sin(this.faz * 2) * 50 * dt;
      if (d < 30) {
        oyun.kaleyeVur(this.T.hasar, this.x, this.y, false);
        oyun.efekt.kan(this.x, this.y, 10, 0x2a2030);
        this.sprite.destroy();
        this.temizle();
        this.durum = 'olu';
        this.olu = true;
        return;
      }
    }
    this.sprite.setPosition(this.x, this.y);
    this.saplilariTasi();
  }

  // Oka geri itilme (ağır olanlar itilmez)
  it(miktar) {
    if (this.T.agir || this.T.ucan || this.durum !== 'yuru' || this.itmeBekleme > 0) return;
    this.x += miktar;
    this.itmeBekleme = 0.25;
  }

  // Ok isabet etti: hasar ver, gerekirse öl. Ölünce true döner.
  vur(hasar) {
    this.can -= hasar;
    this.sprite.setTint(0xff9a8a);
    this.s.time.delayedCall(80, () => { if (this.sprite.active) this.sprite.clearTint(); });
    if (this.can <= 0) {
      this.ol();
      return true;
    }
    return false;
  }

  ol() {
    this.durum = 'olu';
    this.sprite.play(this.T.gorsel + '_die');
    this.sprite.setDepth(15 + Math.random());
    const s = this.s;
    if (this.T.ucan) {
      // Yarasa yere düşer
      s.tweens.add({ targets: this.sprite, y: AYAR.zemin - 10, duration: 600, ease: 'Quad.easeIn' });
    }
    // Ceset bir süre kalır, sonra kaybolur
    s.tweens.add({
      targets: [this.sprite, ...this.saplananlar.map(o => o.sprite)],
      alpha: 0, delay: 2600, duration: 900,
      onComplete: () => { this.sprite.destroy(); this.temizle(); this.olu = true; },
    });
  }

  // Saplanan oklar zombiyle birlikte yürür
  saplilariTasi() {
    for (const o of this.saplananlar) o.sprite.setPosition(this.x + o.dx, this.y + o.dy);
  }
  temizle() {
    for (const o of this.saplananlar) o.sprite.destroy();
    this.saplananlar = [];
  }
}
