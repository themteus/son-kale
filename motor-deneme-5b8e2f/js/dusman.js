// =============================================================
//  DÜŞMANLAR (dusman.js)
//  Çoğu düşman yürür, sura varınca vurur. Özel olanlar:
//   menzil  : uzakta durur (Okçu İskelet ok atar, Şifacı iyileştirir)
//   tirman  : sura tırmanır, tepede sert vurur
//   patlar  : sura varınca ya da ölünce patlar
//   ucan    : yarasa, kuledeki okçuya dalar
//   kalkan  : gövdeye gelen okun bir kısmını tutar
//  Görseller sola bakar (kaleye doğru).
// =============================================================

class Dusman {
  constructor(sahne, turAdi, dalga, zorluk) {
    const T = DUSMAN_TURLERI[turAdi];
    this.s = sahne;
    this.turAdi = turAdi;
    this.T = T;
    const m = sahne.cache.json.get('kareler').birimler[T.gorsel];
    const canCarpani = T.ucan ? Math.sqrt(dalgaCanCarpani(dalga)) : T.patron ? 1 + dalga * 0.12 : dalgaCanCarpani(dalga);
    this.canEnFazla = Math.round(T.can * canCarpani * zorluk.can);
    this.can = this.canEnFazla;
    this.hiz = T.hiz * zorluk.hiz * (0.88 + Math.random() * 0.24);
    this.boy = T.boy;
    this.en = T.en || (T.ucan ? T.boy * 1.3 : T.boy * 0.34);
    this.x = AYAR.en + 60 + Math.random() * 40;
    this.y = AYAR.zemin + Math.random() * 10; // ayak çizgisi (biraz derinlik)
    this.durum = 'yuru';   // yuru | vur | tirman | olu
    this.vurusSayaci = 0;
    this.itmeBekleme = 0;
    this.yanma = 0;        // Ateşli ok: kalan yanma süresi
    this.olu = false;      // true olunca listeden silinir
    this.saplananlar = []; // Üstünde saplı oklar
    // Sura vardığında duracağı yer (hepsi üst üste yığılmasın)
    this.durX = AYAR.kale.onX + this.en / 2 + 4 + Math.random() * 36;
    if (T.menzil) this.durX = T.menzil[0] + Math.random() * (T.menzil[1] - T.menzil[0]);
    if (T.tirman) this.durX = AYAR.kale.onX + 18;
    if (T.ucan) {
      this.ucusY = 260 + Math.random() * 260;
      this.y = this.ucusY;
      this.faz = Math.random() * 6;
      this.dalisX = 700 + Math.random() * 300;
    }
    this.sprite = sahne.add.sprite(this.x, this.y, T.gorsel, 0)
      .setOrigin(m.centerX / m.fw, m.footY / m.fh)
      .setScale(m.olcek || 1)  // PixelLab kareleri küçük çizilir, ekranda büyütülür
      .setDepth((T.patron ? 22 : 20) + (this.y - AYAR.zemin) * 0.1 + Math.random() * 0.05);
    if (T.ucan) this.sprite.setOrigin(0.5, 0.5);
    this.sprite.play(T.gorsel + '_walk');
    this.sprite.anims.setProgress(Math.random());
    this.hizCarpani = 1; this.hizSure = 0; // Ak Dev kükremesiyle hızlanma
    if (T.patron) {
      this.A = akDev(dalga);
      if (this.A.renk) this.sprite.setTint(this.A.renk);
      this.kukremeSayaci = this.A.kukreme ? this.A.kukreme.aralik * 0.5 : 0;
      this.cagirSayaci = this.A.cagir ? 2 : 0;
      this.cagrilan = 0;
      this.zirh = 0; this.zirhSira = 0; this.ofkeli = false;
    }
  }

  // Azgın (seçkin) düşman: iri, dayanıklı, mor (ayarlar.js → AZGIN)
  azginYap() {
    this.azgin = true;
    this.canEnFazla = Math.round(this.canEnFazla * AZGIN.can);
    this.can = this.canEnFazla;
    this.hiz *= AZGIN.hiz;
    this.boy *= AZGIN.boy; this.en *= AZGIN.boy;
    this.sprite.setScale(this.sprite.scaleX * AZGIN.boy);
    this.asilRenk();
  }

  // Ak Devin rengi (yanma/parlama bitince buna döner)
  asilRenk() {
    if (this.yanma > 0) return this.sprite.setTint(0xffb080).setTintMode(Phaser.TintModes.MULTIPLY);
    if (this.zirh > 0) return this.sprite.setTint(0x9ab0e8).setTintMode(Phaser.TintModes.MULTIPLY);
    if (this.ofkeli) return this.sprite.setTint(0xffa090).setTintMode(Phaser.TintModes.MULTIPLY);
    if (this.A && this.A.renk) return this.sprite.setTint(this.A.renk).setTintMode(Phaser.TintModes.MULTIPLY);
    if (this.azgin) return this.sprite.setTint(AZGIN.renk).setTintMode(Phaser.TintModes.MULTIPLY);
    return this.sprite.clearTint();
  }

  // Ok hasarı çarpanı (savas.isabet çağırır): Ak Dev gövdesi ve sis zırhı
  hasarCarpani(kafa, oyun) {
    if (!this.A) return 1;
    if (this.zirh > 0) {
      if (kafa) {
        this.zirh = 0;
        this.sprite.setAlpha(1);
        this.asilRenk();
        oyun.efekt.yazi(this.x, this.ust - 90, 'Sis dağıldı!', '#b4d0ff', 34);
        oyun.sesCal('confirm', 0.4);
        return 1;
      }
      return this.A.zirh.oran;
    }
    return kafa ? 1 : this.A.govde;
  }

  // Ak Devin özel saldırıları (her kare)
  patronGuncelle(dt, oyun) {
    const A = this.A;
    if (A.kukreme && (this.kukremeSayaci -= dt) <= 0) {
      const K = A.kukreme;
      this.kukremeSayaci = K.aralik;
      for (const d of oyun.dusmanlar) {
        if (d === this || !d.canli || d.T.ucan || Math.abs(d.x - this.x) > K.alan) continue;
        d.hizCarpani = K.hiz; d.hizSure = K.sure;
        oyun.efekt.toz(d.x, d.y, 2);
      }
      oyun.efekt.yazi(this.x, this.ust - 60, 'KÜKREME!', '#ff9a7a', 40);
      oyun.sesCal('boss', 0.35);
      oyun.sars(300, 0.004);
    }
    if (A.cagir && this.cagrilan < A.cagir.enCok && this.x < AYAR.en - 80 && (this.cagirSayaci -= dt) <= 0) {
      this.cagirSayaci = A.cagir.aralik;
      for (let i = 0; i < A.cagir.sayi && this.cagrilan < A.cagir.enCok; i++) {
        const z = new Dusman(oyun, A.cagir.tur, oyun.dalga, oyun.zorluk);
        z.x = kis(this.x - 60 - Math.random() * 140, AYAR.kale.onX + 120, AYAR.en - 40);
        z.sprite.setPosition(z.x, z.y);
        z.cagrildi = true;
        oyun.dusmanlar.push(z);
        oyun.efekt.toz(z.x, z.y, 8);
        oyun.efekt.duman(z.x, z.y, false);
        this.cagrilan++;
      }
      oyun.efekt.yazi(this.x, this.ust - 60, 'Ölüler kalkıyor!', '#c4dcae', 34);
      oyun.sesCal('hurt', 0.4);
    }
    const oran = this.can / this.canEnFazla;
    if (A.zirh) {
      if (this.zirh > 0) {
        this.zirh -= dt;
        if (Math.random() < dt * 10) oyun.efekt.toz(this.x + (Math.random() - 0.5) * this.en * 2, this.y - this.boy * Math.random(), 1);
        if (this.zirh <= 0) { this.sprite.setAlpha(1); this.asilRenk(); }
      } else if (this.zirhSira < A.zirh.esik.length && oran < A.zirh.esik[this.zirhSira]) {
        this.zirhSira++;
        this.zirh = A.zirh.sure;
        this.sprite.setAlpha(0.75);
        this.asilRenk();
        oyun.efekt.yazi(this.x, this.ust - 60, 'Sise büründü!', '#b4d0ff', 36);
        oyun.sesCal('impact', 0.3);
      }
    }
    if (A.ofke && !this.ofkeli && oran < A.ofke.esik) {
      this.ofkeli = true;
      this.hiz *= A.ofke.hiz;
      this.asilRenk();
      oyun.arayuz.duyur('Ak Dev öfkelendi!', 'Hızlandı: sura varmadan bitir!');
      oyun.sars(400, 0.008);
    }
  }

  // Vuruş kutusu (oklar için). Tırmanırken kutu dik durur.
  get sol() { return this.x - this.en / 2; }
  get sag() { return this.x + this.en / 2; }
  get ust() { return this.T.ucan ? this.y - this.boy / 2 : this.y - this.boy; }
  get alt() { return this.T.ucan ? this.y + this.boy / 2 : this.y; }
  // Askerlerin nişan aldığı yer (göğüs)
  get nisanY() { return this.T.ucan ? this.y : this.y - this.boy * 0.62; }
  get canli() { return this.durum !== 'olu'; }

  icindeMi(px, py) {
    return px >= this.sol && px <= this.sag && py >= this.ust && py <= this.alt;
  }
  kafaMi(py) {
    if (this.durum === 'tirman') return py < this.ust + this.boy * 0.3;
    return this.T.ucan || py < this.ust + this.boy * this.T.kafa;
  }

  guncelle(dt, oyun) {
    if (this.durum === 'olu') return;
    if (this.itmeBekleme > 0) this.itmeBekleme -= dt;
    // Ateşli ok: yanarken her saniye hasar alır
    if (this.yanma > 0) {
      this.yanma -= dt;
      this.can -= this.yanmaHasari * dt;
      if (Math.random() < dt * 12) oyun.efekt.ates(this.x + (Math.random() - 0.5) * this.en, this.y - this.boy * Math.random());
      if (oyun.efekt.alev && Math.random() < dt * 12) oyun.efekt.alev(this.x + (Math.random() - 0.5) * this.en * 0.7, this.y - this.boy * (0.15 + 0.55 * Math.random()));
      if (this.yanma <= 0) this.asilRenk();
      if (this.can <= 0) { oyun.dusmanOldu(this, false); return; }
    }
    if (this.T.ucan) return this.uc(dt, oyun);
    if (this.A) this.patronGuncelle(dt, oyun);
    if (this.hizSure > 0 && (this.hizSure -= dt) <= 0) this.hizCarpani = 1;

    if (this.durum === 'yuru') {
      this.x -= this.hiz * this.hizCarpani * dt;
      if (this.x <= this.durX) {
        this.x = this.durX;
        this.vurusSayaci = this.T.vurus * 0.5;
        if (this.T.patlar) { this.patla(oyun, true); return; }
        if (this.T.tirman) {
          this.durum = 'tirman';
          this.sprite.play(this.T.gorsel + '_attack').setRotation(Math.PI / 2);
          this.boy = 70;
        } else {
          this.durum = 'vur';
          this.sprite.play(this.T.gorsel + '_attack');
        }
      }
    } else if (this.durum === 'tirman') {
      // Sur yüzünde yukarı sürünür
      this.y -= this.T.tirman * dt;
      if (this.y - 40 <= AYAR.kale.surUst) {
        this.durum = 'vur';
        this.y = AYAR.kale.surUst + 4;
        this.x = AYAR.kale.onX - 20;
        this.boy = this.T.boy * 0.5;
        this.sprite.setRotation(0);
      }
    } else if (this.durum === 'vur') {
      this.vurusSayaci -= dt;
      if (this.vurusSayaci <= 0) {
        this.vurusSayaci = this.T.vurus;
        if (this.T.menzil && this.T.sifa) this.iyilestir(oyun);
        else if (this.T.menzil) oyun.dusmanOkuAt(this);
        else oyun.kaleyeVur(this.T.hasar, this.x - this.en / 2, this.y - this.boy * 0.5, this.T.agir);
      }
    }
    this.sprite.setPosition(this.x, this.y);
    this.saplilariTasi();
  }

  // Şifacı: yakındaki düşmanları iyileştirir
  iyilestir(oyun) {
    for (const d of oyun.dusmanlar) {
      if (!d.canli || d === this || Math.abs(d.x - this.x) > this.T.sifaAlan) continue;
      if (d.can >= d.canEnFazla) continue;
      d.can = Math.min(d.canEnFazla, d.can + d.canEnFazla * this.T.sifa);
      oyun.efekt.sifa(d.x, d.y - d.boy * 0.6);
    }
    oyun.efekt.sifa(this.x, this.y - this.boy);
  }

  // Patlayan: sura varınca (kaleye) ya da ölünce (yanındakilere) patlar
  patla(oyun, suraVardi) {
    if (this.patladi) return;
    this.patladi = true;
    this.durum = 'olu'; // önce ölü say: zincirleme patlamada tekrar patlamasın
    const alan = this.T.patlar;
    oyun.efekt.patlama(this.x, this.y - this.boy * 0.5);
    oyun.sesCal('big_kill', 0.6);
    oyun.sars(260, 0.008);
    if (suraVardi) oyun.kaleyeVur(this.T.hasar, AYAR.kale.onX, this.y - this.boy * 0.5, true);
    else {
      // Ölünce yakındaki düşmanlara hasar: o dalgadaki zombi canının 0.8 katı
      const hasar = DUSMAN_TURLERI.zombi.can * dalgaCanCarpani(oyun.dalga) * 0.8;
      for (const d of oyun.dusmanlar) {
        if (d === this || !d.canli || Math.abs(d.x - this.x) > alan || d.T.ucan) continue;
        if (d.vur(hasar)) oyun.dusmanOldu(d, false);
      }
    }
    this.durum = 'olu';
    this.sprite.destroy();
    this.temizle();
    this.olu = true;
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

  tutustur(hasar, sure) {
    this.yanma = sure;
    this.yanmaHasari = hasar;
    this.sprite.setTint(0xffb080).setTintMode(Phaser.TintModes.MULTIPLY);
  }

  // Ok isabet etti: hasar ver. Ölünce true döner (ölümü oyun işler).
  vur(hasar) {
    if (!this.canli) return false;
    this.can -= hasar;
    // Kısa beyaz parlama (isabet hissi), sonra eski rengine döner
    this.sprite.setTint(0xffffff).setTintMode(Phaser.TintModes.FILL);
    this.s.time.delayedCall(60, () => { if (this.sprite.active) this.asilRenk(); });
    return this.can <= 0;
  }

  ol(oyun) {
    if (this.T.patlar) return this.patla(oyun, false);
    this.durum = 'olu';
    this.sprite.setRotation(0);
    if (this.T.tirman && this.y < AYAR.zemin - 5) {
      // Surdan düşer
      this.s.tweens.add({ targets: this.sprite, y: AYAR.zemin, x: AYAR.kale.onX + 40, duration: 500, ease: 'Quad.easeIn' });
    }
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

  // Saplanan oklar düşmanla birlikte yürür
  saplilariTasi() {
    for (const o of this.saplananlar) o.sprite.setPosition(this.x + o.dx, this.y + o.dy);
  }
  temizle() {
    for (const o of this.saplananlar) o.sprite.destroy();
    this.saplananlar = [];
  }
}
