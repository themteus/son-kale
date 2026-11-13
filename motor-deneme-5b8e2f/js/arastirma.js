// =============================================================
//  ARAŞTIRMA (arastirma.js)
//  Silah ustasının yanındaki "Araştırma" penceresi: altınla alınan
//  kalıcı (o oyun boyunca) geliştirmeler. Geç oyunda biriken altının
//  harcanacağı yer. Seviyeler ekonomi.arastirma içinde, kayda yazılır.
//  Sayılar aşağıda; etkiler Ar.* ile okunur.
// =============================================================

const ARASTIRMA = [
  { id: 'zanaat', ad: 'Usta Eller', aciklama: 'Bütün binaların üretimi +%8', fiyat: [250, 600, 1400] },
  { id: 'toplama', ad: 'Ok Toplayıcılar', aciklama: 'Savaş alanından daha çok ok toplanır (+%8 / +%10)', fiyat: [200, 500, 1100] },
  { id: 'harc', ad: 'Horasan Harcı', aciklama: 'Sur her vuruştan %8 az hasar alır', fiyat: [300, 700, 1600] },
  { id: 'goz', ad: 'Keskin Göz', aciklama: 'Kafa vuruşu çarpanı +0,25', fiyat: [300, 700, 1600] },
  { id: 'ganimet', ad: 'Ganimetçiler', aciklama: 'Düşmanlardan +%10 altın', fiyat: [250, 600, 1400] },
  { id: 'nefes', ad: 'Derin Nefes', aciklama: 'Dayanıklılık %25 hızlı dolar', fiyat: [200, 500, 1100] },
  { id: 'yag', ad: 'Kızgın Yağ', aciklama: 'E: surun dibine kızgın yağ dök (yakar ve tutuşturur). Her seviye daha geniş ve sert.', fiyat: [400, 900, 1800] },
];

// Kızgın Yağ: bekleme (sn), alan (surun önünden kaç birim), hasar (o dalganın zombi canının katı)
const YAG = { bekleme: 28, alan: [280, 360, 440], hasar: [1.4, 2.2, 3.2], yanmaSure: 3, yanma: 0.5 };

const Ar = {
  sv(o, id) { const a = o.ekonomi.arastirma; return (a && a[id]) || 0; },
  fiyat(o, u) { return u.fiyat[this.sv(o, u.id)]; },
  al(o, u) {
    const sv = this.sv(o, u.id), f = u.fiyat[sv];
    if (f === undefined || o.altin < f) return false;
    o.altin -= f;
    o.ekonomi.arastirma[u.id] = sv + 1;
    return true;
  },
  uretim(E) { return 1 + 0.08 * ((E.arastirma && E.arastirma.zanaat) || 0); },
  iskaToplama(E) { return Math.min(0.98, EKONOMI.iskaToplama + 0.08 * ((E.arastirma && E.arastirma.toplama) || 0)); },
  isabetToplama(E) { return EKONOMI.isabetToplama + 0.1 * ((E.arastirma && E.arastirma.toplama) || 0); },
  surHasari(o) { return 1 - 0.08 * this.sv(o, 'harc'); },
  kafa(o) { return 0.25 * this.sv(o, 'goz'); },
  altin(o) { return 1 + 0.1 * this.sv(o, 'ganimet'); },
  dolma(o) { return 1 + 0.25 * this.sv(o, 'nefes'); },
};
