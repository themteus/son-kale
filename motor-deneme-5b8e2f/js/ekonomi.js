// =============================================================
//  EKONOMİ (ekonomi.js)
//  Kaynaklar, nüfus, binalar ve gün sonu hesabı.
//  Bütün sayılar ayarlar.js → EKONOMI, BINALAR, SUR, PAZAR.
//  "oyun" = savaş sahnesi (altın, sur canı orada durur).
// =============================================================

class Ekonomi {
  constructor() {
    this.kaynak = {};
    for (const k in KAYNAKLAR) this.kaynak[k] = EKONOMI.baslangic[k] || 0;
    this.nufus = EKONOMI.nufus;
    this.bina = {};
    for (const k in BINALAR) this.bina[k] = { seviye: BINALAR[k].bas.seviye, isci: BINALAR[k].bas.isci };
    this.asker = 0;         // Surdaki okçu asker (her biri bir yay ister)
    this.surSeviye = 1;
    this.atilan = 0;        // Bu dalgada atılan ok
    this.saplanan = 0;      // Bunların kaçı düşmana saplandı
    this.pazar = {};        // Bugünkü fiyat çarpanları
    this.acilOnarildi = false;
    this.rapor = null;
  }

  // ---------- Kişiler ----------
  get isci() { let n = 0; for (const k in this.bina) n += this.bina[k].isci; return n; }
  get bosta() { return this.nufus - this.isci - this.asker; }
  get barinak() { return BINALAR.ev.barinak[this.bina.ev.seviye - 1]; }
  yerSayisi(k) { const B = BINALAR[k]; return B.yer ? B.yer[this.bina[k].seviye - 1] : 0; }
  get askerYeri() { return SUR.askerYeri[this.surSeviye - 1]; }

  isciEkle(k, n) {
    const b = this.bina[k];
    if (n > 0 && (this.bosta <= 0 || b.isci >= this.yerSayisi(k))) return false;
    if (n < 0 && b.isci <= 0) return false;
    b.isci += n;
    return true;
  }
  askerEkle(n) {
    if (n > 0 && (this.bosta <= 0 || this.asker >= this.askerYeri || this.asker >= this.kaynak.yay)) return false;
    if (n < 0 && this.asker <= 0) return false;
    this.asker += n;
    return true;
  }

  // ---------- Kaynaklar ----------
  // Ok atılınca çağrılır; ambarda yoksa false
  okHarca(n) {
    if (this.kaynak.ok < n) return false;
    this.kaynak.ok -= n;
    this.atilan += n;
    return true;
  }
  okSaplandi() { this.saplanan++; }

  // bedel içinde altın da olabilir (oyun.altin)
  yeter(bedel, oyun) {
    for (const k in bedel) if ((k === 'altin' ? oyun.altin : this.kaynak[k]) < bedel[k]) return false;
    return true;
  }
  ode(bedel, oyun) {
    if (!this.yeter(bedel, oyun)) return false;
    for (const k in bedel) { if (k === 'altin') oyun.altin -= bedel[k]; else this.kaynak[k] -= bedel[k]; }
    return true;
  }
  yukseltBedeli(k) { return BINALAR[k].yukselt[this.bina[k].seviye - 1] || null; }
  yukselt(k, oyun) {
    const b = this.yukseltBedeli(k);
    if (!b || !this.ode(b, oyun)) return false;
    this.bina[k].seviye++;
    return true;
  }
  surBedeli() { return SUR.yukselt[this.surSeviye - 1] || null; }
  surYukselt(oyun) {
    const b = this.surBedeli();
    if (!b || !this.ode(b, oyun)) return false;
    this.surSeviye++;
    const fark = SUR.can[this.surSeviye - 1] - oyun.surEnFazla;
    oyun.surEnFazla += fark;
    oyun.surCan += fark;
    return true;
  }
  // Altınla acil onarım: günde bir kez, surun en çok yarısı
  acilOnarimBilgi(oyun) {
    const can = Math.min(oyun.surEnFazla - oyun.surCan, Math.round(oyun.surEnFazla * 0.5));
    return { can, altin: Math.ceil(can * EKONOMI.acilOnarim) };
  }
  acilOnar(oyun) {
    const b = this.acilOnarimBilgi(oyun);
    if (this.acilOnarildi || b.can <= 0 || oyun.altin < b.altin) return false;
    oyun.altin -= b.altin;
    oyun.surCan += b.can;
    this.acilOnarildi = true;
    return true;
  }

  // Seviyeye göre işçi verimi
  verim(k) { return 1 + (this.bina[k].seviye - 1) * EKONOMI.seviyeBonus; }
  get ucKalite() { return BINALAR.demirci.kalite[this.bina.demirci.seviye - 1]; }
  get yayKalite() { return BINALAR.yayci.kalite[this.bina.yayci.seviye - 1]; }

  // ---------- Pazar ----------
  fiyat(k, al) {
    const p = PAZAR[k].fiyat * (this.pazar[k] || 1);
    return Math.max(1, Math.round(al ? p : p * PAZAR.satis));
  }
  ticaret(k, al, oyun) {
    const P = PAZAR[k], m = this.pazar[k] || 1;
    if (al) {
      const f = this.fiyat(k, true);
      if (oyun.altin < f) return false;
      oyun.altin -= f;
      this.kaynak[k] += P.parti;
      this.pazar[k] = m * (1 + PAZAR.artis);
    } else {
      if (this.kaynak[k] < P.parti) return false;
      oyun.altin += this.fiyat(k, false);
      this.kaynak[k] -= P.parti;
      this.pazar[k] = Math.max(0.5, m / (1 + PAZAR.artis));
    }
    return true;
  }

  // ---------- Gün sonu ----------
  // uygula = false: hiçbir şeyi değiştirmeden tahmin döner (panellerde "yarın" için)
  gunuHesapla(oyun, uygula) {
    const r = { ...this.kaynak };
    const yapilan = {}, harcanan = {}, notlar = [];
    const kazan = (k, n) => { if (n > 0) { r[k] += n; yapilan[k] = (yapilan[k] || 0) + n; } };
    const harca = (k, n) => { if (n > 0) { r[k] -= n; harcanan[k] = (harcanan[k] || 0) + n; } };
    const B = BINALAR, b = this.bina;

    // 1) Ham madde
    for (const k of ['oduncu', 'tasocagi', 'maden', 'ciftlik']) {
      for (const m in B[k].uretim) kazan(m, Math.floor(b[k].isci * B[k].uretim[m] * this.verim(k)));
    }
    // 2) Demirci: demir → ok ucu
    {
      const ister = b.demirci.isci * B.demirci.tuketim.demir;
      const demir = Math.min(r.demir, ister);
      if (demir < ister) notlar.push('Demirciye demir yetmedi.');
      harca('demir', demir);
      kazan('uc', Math.floor(demir * B.demirci.uretim.uc * this.verim('demirci')));
    }
    // 3) Yaycı: önce eksik yaylar (askerler + 2 yedek), kalan emekle ok
    {
      let emek = b.yayci.isci;
      const istenen = Math.max(0, Math.min(this.askerYeri, this.asker + 2) - r.yay);
      let yay = 0;
      while (yay < istenen && emek >= 0.25 && r.odun >= B.yayci.yayBedeli.odun) {
        harca('odun', B.yayci.yayBedeli.odun);
        yay++;
        emek -= 0.25;
      }
      kazan('yay', yay);
      const okBasiOdun = B.yayci.tuketim.odun / B.yayci.uretim.ok;
      const sinir = Math.floor(emek * B.yayci.uretim.ok * this.verim('yayci'));
      const ok = Math.max(0, Math.min(sinir, r.uc, Math.floor(r.odun / okBasiOdun)));
      if (sinir > 0 && ok < sinir) notlar.push(r.uc < sinir ? 'Yaycıya ok ucu yetmedi.' : 'Yaycıya odun yetmedi.');
      harca('uc', ok);
      harca('odun', Math.ceil(ok * okBasiOdun));
      kazan('ok', ok);
    }
    // 4) Duvarcı: suru onarır (çok yıkıksa iki kat hızlı)
    let onarim = 0;
    {
      const D = B.duvarci;
      let emek = Math.floor(b.duvarci.isci * D.onarim * this.verim('duvarci'));
      const tasla = Math.floor(r.tas / D.tuketim.tas * D.onarim);
      const odunla = Math.floor(r.odun / D.tuketim.odun * D.onarim);
      const eksik = oyun.surEnFazla - oyun.surCan;
      if (eksik > 0 && Math.min(tasla, odunla) < emek) notlar.push('Duvarcılara taş ya da odun yetmedi.');
      emek = Math.min(emek, tasla, odunla);
      let harcananEmek = 0, can = oyun.surCan;
      while (emek > 0 && can < oyun.surEnFazla) {
        const parca = Math.min(emek, 10);
        const hizli = can / oyun.surEnFazla < D.azsaHizli ? 2 : 1;
        can = Math.min(oyun.surEnFazla, can + parca * hizli);
        emek -= parca;
        harcananEmek += parca;
      }
      onarim = Math.round(can - oyun.surCan);
      harca('tas', Math.ceil(harcananEmek / D.onarim * D.tuketim.tas));
      harca('odun', Math.ceil(harcananEmek / D.onarim * D.tuketim.odun));
    }
    // 5) Herkes yer
    const ihtiyac = this.nufus * EKONOMI.yemek;
    const yenen = Math.min(ihtiyac, r.yiyecek);
    harca('yiyecek', yenen);
    let olen = 0, gelen = 0;
    if (yenen < ihtiyac) {
      olen = Math.ceil((ihtiyac - yenen) / EKONOMI.aclikOlum);
      notlar.push(`Açlık! ${olen} kişi öldü.`);
    } else {
      const yer = this.barinak - this.nufus;
      gelen = Math.max(0, Math.min(EKONOMI.enFazlaGelen, yer, Math.floor(r.yiyecek / EKONOMI.gelenBasiYiyecek)));
      if (yer <= 0) notlar.push('Evlerde yer yok, sığınmacılar geri döndü.');
      else if (gelen === 0) notlar.push('Ambarda yiyecek az, sığınmacı gelmedi.');
    }
    // 6) Savaş alanından ok toplama
    const saplanan = Math.min(this.saplanan, this.atilan);
    const toplanan = Math.floor((this.atilan - saplanan) * EKONOMI.iskaToplama + saplanan * EKONOMI.isabetToplama);
    kazan('ok', toplanan);

    const rapor = { yapilan, harcanan, notlar, onarim, olen, gelen, toplanan, atilan: this.atilan, yenen, ihtiyac };
    if (!uygula) return rapor;

    this.kaynak = r;
    for (const k in r) r[k] = Math.max(0, Math.round(r[k]));
    oyun.surCan = Math.min(oyun.surEnFazla, oyun.surCan + onarim);
    this.kisiKaybet(olen);
    this.nufus += gelen;
    this.atilan = 0;
    this.saplanan = 0;
    this.acilOnarildi = false;
    for (const k in this.pazar) this.pazar[k] = 1 + (this.pazar[k] - 1) * 0.5;
    this.rapor = rapor;
    return rapor;
  }

  // Kişi kaybı: önce boştakiler, sonra işçiler, en son askerler
  kisiKaybet(n) {
    n = Math.min(n, this.nufus);
    this.nufus -= n;
    let fazla = -this.bosta;
    for (const k of ['maden', 'tasocagi', 'oduncu', 'duvarci', 'demirci', 'yayci', 'ciftlik']) {
      while (fazla > 0 && this.bina[k].isci > 0) { this.bina[k].isci--; fazla--; }
    }
    while (fazla > 0 && this.asker > 0) { this.asker--; fazla--; }
  }

  // ---------- "Otomatik dağıt" ----------
  // Önce yiyecek yetecek kadar çiftçi, sonra yay kadar asker,
  // hasarlı sura duvarcı, kalanlar ok zincirine (maden → demirci → yaycı).
  otomatikDagit(oyun) {
    for (const k in this.bina) this.bina[k].isci = 0;
    this.asker = 0;
    const doldur = (k, n) => { while (n-- > 0 && this.isciEkle(k, 1)) { /* doldur */ } };
    const ciftci = BINALAR.ciftlik.uretim.yiyecek * this.verim('ciftlik');
    doldur('ciftlik', Math.ceil(this.nufus / ciftci) + 1);
    while (this.askerEkle(1)) { /* yay kadar asker */ }
    doldur('duvarci', Math.ceil((oyun.surEnFazla - oyun.surCan) / BINALAR.duvarci.onarim));
    const B = BINALAR, r = this.kaynak;
    const w = k => this.bina[k].isci;
    const bos = k => w(k) < this.yerSayisi(k);
    const denge = () => ({
      demir: w('maden') * B.maden.uretim.demir * this.verim('maden') + r.demir / 3 - w('demirci') * B.demirci.tuketim.demir,
      uc: w('demirci') * B.demirci.tuketim.demir * B.demirci.uretim.uc * this.verim('demirci') + r.uc / 3 - w('yayci') * B.yayci.uretim.ok * this.verim('yayci'),
      odun: w('oduncu') * B.oduncu.uretim.odun * this.verim('oduncu') + r.odun / 4 - w('yayci') * B.yayci.tuketim.odun - w('duvarci') * B.duvarci.tuketim.odun - 15,
      tas: w('tasocagi') * B.tasocagi.uretim.tas * this.verim('tasocagi') + r.tas / 4 - w('duvarci') * B.duvarci.tuketim.tas - 12,
    });
    let sira = 0, guvenlik = 200;
    while (this.bosta > 0 && guvenlik-- > 0) {
      const d = denge();
      let k = null;
      if (d.demir < 0 && bos('maden')) k = 'maden';
      else if (d.uc < 0 && bos('demirci')) k = 'demirci';
      else if (d.odun < 0 && bos('oduncu')) k = 'oduncu';
      else if (d.tas < 0 && bos('tasocagi')) k = 'tasocagi';
      else if (bos('yayci')) k = 'yayci';
      else {
        const kalan = ['oduncu', 'tasocagi', 'maden', 'demirci', 'ciftlik', 'duvarci'].filter(bos);
        if (!kalan.length) break;
        k = kalan[sira++ % kalan.length];
      }
      this.isciEkle(k, 1);
    }
  }
}
