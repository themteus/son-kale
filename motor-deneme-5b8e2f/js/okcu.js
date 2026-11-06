// =============================================================
//  OKÇU (okcu.js)
//  Oyuncunun okçusu ve surdaki askerler bu sınıfı kullanır.
//  Görsel şeritte her 5 derecelik nişan açısı ve yay gerginliği
//  için ayrı bir kare var (3D modelden çizildi).
// =============================================================

class Okcu {
  constructor(sahne, x, ayakY, oyuncu) {
    this.s = sahne;
    this.oyuncu = oyuncu;
    this.anahtar = oyuncu ? 'okcu' : 'asker';
    this.M = sahne.cache.json.get('kareler')[this.anahtar];
    this.x = x;
    this.ayakY = ayakY;
    this.aci = -0.25;      // Nişan açısı (radyan, eksi = yukarı)
    this.germe = 0;        // 0 = gevşek, 1 = tam gerili
    this.geriyor = false;
    this.bekleme = 0;      // 0 olunca yeni ok hazır
    this.tutma = 0;        // Tam gerili kaç saniyedir tutuluyor
    this.otoBirak = false; // Kısa dokunuş: tam gerilince kendiliğinden at
    this.sprite = sahne.add.sprite(x, ayakY, this.anahtar, 0)
      .setOrigin(0.5, this.M.footY / this.M.fh).setScale(this.M.olcek || 1).setDepth(oyuncu ? 26 : 25);
    this.takiliOk = sahne.add.image(0, 0, 'ok').setOrigin(0, 0.5).setDepth(oyuncu ? 27 : 25.5);
    if (!oyuncu) this.bekleme = Math.random() * AYAR.asker.beklemeSn;
    this.kareyiAyarla();
  }

  // Şeritteki bir noktayı sahne koordinatına çevirir
  nokta(p) {
    const o = this.M.olcek || 1; // 2 kat detaylı şeritte olcek 0.5
    return { x: this.x + (p.x - this.M.fw / 2) * o, y: this.ayakY + (p.y - this.M.footY) * o };
  }
  get omuz() {
    const sifir = this.M.kareler[this.M.acilar.indexOf(0)];
    return this.nokta(sifir.shoulder);
  }

  // Açı ve germeye göre doğru kareyi seç
  kareyiAyarla() {
    const A = this.M.acilar;
    const derece = Phaser.Math.RadToDeg(this.aci);
    const i = kis(Math.round((derece - A[0]) / (A[1] - A[0])), 0, A.length - 1);
    const sira = this.M.germe.length === 3
      ? (this.germe < 0.25 ? 0 : this.germe < 0.75 ? 1 : 2)
      : (this.germe < 0.5 ? 0 : 1);
    this.sprite.setFrame(sira * A.length + i);
    const k = this.M.kareler[i];
    this.kiris = this.nokta(k['nock' + sira]);
    this.tutamak = this.nokta(k.grip);
    // Kirişe takılı ok: kuyruğu kirişte, ucu nişan yönünde
    const hazir = this.bekleme <= 0 && (this.oyuncu || this.germe > 0.5);
    this.takiliOk.setVisible(hazir);
    if (hazir) this.takiliOk.setPosition(this.kiris.x, this.kiris.y).setRotation(Phaser.Math.DegToRad(A[i]));
    if (hazir && this.oyuncu) {
      const t = this.s.okTuru;
      if (this.s.keskinHazir) this.takiliOk.setTint(0xffe08a);
      else if (t && t !== 'normal') this.takiliOk.setTint(OK_TURLERI[t].renk); else this.takiliOk.clearTint();
    }
  }

  guncelle(dt, oyun) {
    if (this.bekleme > 0) this.bekleme -= dt;
    if (this.oyuncu) this.oyuncuGuncelle(dt, oyun);
    else this.askerGuncelle(dt, oyun);
    this.kareyiAyarla();
  }

  // ---------------- Oyuncu ----------------
  oyuncuGuncelle(dt, oyun) {
    const B = AYAR.yay, D = AYAR.dayaniklilik, g = oyun.girdi;
    // İçgüdüsel atış: parmağın/farenin gösterdiği yere varacak kavis
    const istenen = kis(this.aciBul(g.x, g.y, oyun.okHizi()), -1.39, 1.39);
    const adim = kis(istenen - this.aci, -B.donmeHizi * dt, B.donmeHizi * dt);
    this.aci += adim;
    const hizlanma = oyun.germeCarpani();

    if (!this.geriyor) {
      this.germe = Math.max(0, this.germe - dt * 6);
      oyun.dayaniklilik = Math.min(D.enFazla, oyun.dayaniklilik + D.dolma * dt);
      if (this.bekleme <= 0 && (g.basili || g.dokundu)) {
        g.dokundu = false;
        this.geriyor = true;
        this.germe = 0;
        this.tutma = 0;
        this.otoBirak = false;
      }
      return;
    }
    // Yay gerilir; yorgun kol yavaş gerer, dayanıklılık bitince tam gerilmez
    this.yorgun = oyun.dayaniklilik < D.enFazla * D.yorgun;
    const enCok = oyun.dayaniklilik <= 0 ? 0.6 : 1;
    if (this.germe < enCok) {
      this.germe = Math.min(enCok, this.germe + dt / (B.germeSuresi * hizlanma * (this.yorgun ? 1.6 : 1)));
      oyun.dayaniklilik = Math.max(0, oyun.dayaniklilik - D.germe * dt);
    } else {
      this.tutma += dt;
      oyun.dayaniklilik = Math.max(0, oyun.dayaniklilik - D.tutma * dt);
    }
    if (this.otoBirak && this.germe >= enCok) return this.birak(oyun);
    if (!g.basili && !this.otoBirak) {
      if (this.germe < B.kisaDokunus) this.otoBirak = true; // kısa dokunuş
      else this.birak(oyun);
    }
  }

  // Şu anki sapma (odak halkası da bunu gösterir)
  sapma() {
    const B = AYAR.yay;
    const yorgunluk = kis((this.tutma - B.sabitSure) / 2.5, 0, 1);
    return B.sapma + B.zayifSapma * (1 - this.germe) * (1 - this.germe)
      + B.yorgunSapma * (yorgunluk + (this.yorgun ? 1 : 0));
  }

  birak(oyun) {
    const B = AYAR.yay;
    const p = this.germe;
    const guc = B.enAzGuc + (1 - B.enAzGuc) * p;
    const hasarCarpani = 0.4 + (B.tamHasar - 0.4) * p * p;
    const aci = this.aci + gaussRastgele() * this.sapma();
    oyun.dayaniklilik = Math.max(0, oyun.dayaniklilik - AYAR.dayaniklilik.atis);
    this.geriyor = false;
    this.tutma = 0;
    this.otoBirak = false;
    this.bekleme = B.takmaSuresi * oyun.germeCarpani();
    const sayi = oyun.okSayisi();
    // Kafa serisiyle kazanılan keskin ok: tam gerili atışta harcanır
    const keskin = oyun.keskinHazir && p >= 0.9;
    const carp = keskin ? AYAR.keskin.hasar : 1;
    if (this.at(oyun, aci, oyun.okHizi() * guc * (1 + gaussRastgele() * 0.03), oyun.okHasari() * hasarCarpani * carp, sayi, oyun.okTuruHarca(sayi), keskin) !== false) {
      if (keskin) oyun.keskinHazir = false;
      oyun.sesCal('shoot', 0.35);
    }
  }

  // ---------------- Asker ----------------
  askerGuncelle(dt, oyun) {
    const A = AYAR.asker;
    const hedef = this.hedefBul(oyun);
    if (!hedef) { this.germe = Math.max(0, this.germe - dt * 3); return; }
    if (this.onu === undefined) this.onu = 1 + gaussRastgele() * A.onuHatasi;
    this.aci = kis(this.nisanAl(hedef, oyun.okHizi(), this.onu, oyun), -1.39, 1.39);
    // Atıştan az önce yayı gerer
    this.germe = this.bekleme < 0.45 ? 1 : 0;
    if (this.bekleme <= 0) {
      // Okçu Eğitimi: hasar +%15, sapma -%12 (her seviye)
      const egitim = oyun.seviye.egitim || 0;
      this.at(oyun, this.aci + gaussRastgele() * A.sapma * Math.pow(0.88, egitim), oyun.okHizi(),
        oyun.okHasari() * A.hasarOrani * oyun.ekonomi.yayKalite.hasar * (1 + 0.15 * egitim), 1);
      this.bekleme = A.beklemeSn * (0.9 + Math.random() * 0.2);
      this.onu = undefined;
    }
  }

  hedefBul(oyun) {
    let en = null;
    for (const d of oyun.dusmanlar) {
      if (!d.canli || d.x > AYAR.en - 20) continue;
      if (!en || d.x < en.x) en = d;
    }
    return en;
  }

  nisanAl(d, hiz, onu, oyun) {
    let tx = d.x;
    const ty = d.nisanY;
    const sure = Math.max(0, (tx - this.omuz.x) / (hiz * 0.9));
    if (d.durum === 'yuru') tx -= d.hiz * sure * onu;
    tx -= 0.5 * oyun.ruzgar * sure * sure;
    return this.aciBul(tx, ty, hiz);
  }

  // ---------------- Ortak ----------------
  // Belli hızla atılan okun (tx, ty) noktasına varması için gereken açı
  aciBul(tx, ty, hiz) {
    const g = AYAR.yercekimi, o = this.omuz;
    const dx = tx - o.x;
    const dy = o.y - ty; // yukarı artı
    if (dx < 10) return Math.atan2(-dy, Math.max(dx, 1));
    const v2 = hiz * hiz;
    const disc = v2 * v2 - g * (g * dx * dx + 2 * dy * v2);
    if (disc < 0) return -Math.PI / 4; // menzil dışı: en uzağa
    return -Math.atan((v2 - Math.sqrt(disc)) / (g * dx));
  }

  // Normal oklar ambardan düşer; ateşli/delici oklar dükkândan alınan ayrı stoktur
  at(oyun, aci, hiz, hasar, sayi, tur = 'normal', keskin = false) {
    const ambar = tur === 'normal';
    if (ambar && !oyun.ekonomi.okHarca(sayi)) {
      if (this.oyuncu) oyun.okBitti();
      return false;
    }
    const ara = AYAR.ok.cokluAci;
    for (let i = 0; i < sayi; i++) {
      const a = aci + (i - (sayi - 1) / 2) * ara;
      const orta = i === Math.floor((sayi - 1) / 2);
      const ok = oyun.okEkle(this.tutamak.x, this.tutamak.y, a, hiz, orta ? hasar : hasar * AYAR.ok.yanOkOrani, this.oyuncu, tur, ambar, keskin && orta);
      ok.yan = !orta; // yan oklar kafa serisini bozmaz
    }
  }

  yokEt() {
    this.sprite.destroy();
    this.takiliOk.destroy();
  }
}
