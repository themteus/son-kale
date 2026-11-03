// =============================================================
//  AYARLAR (ayarlar.js)
//  Oyunun bütün sayıları burada. Dengeyi değiştirmek için önce
//  bu dosyaya bak. Sahne 1920x1080 birim; ekrana göre ölçeklenir.
// =============================================================

const AYAR = {
  en: 1920,
  boy: 1080,
  zemin: 920,          // Zombilerin ayağının bastığı çizgi
  yercekimi: 1800,     // Oklar bu yüzden kavis çizer

  kale: {
    can: 500,          // Surun başlangıç canı
    onX: 420,          // Surun ön yüzü (zombiler burada durur)
    surUst: 580,       // Surun üst kenarı (askerler burada durur)
    kuleSol: 110,
    kuleSag: 310,
    kuleUst: 380,      // Kulenin tepesi (oyuncu burada durur)
  },

  oyuncu: { x: 205, ayakY: 380 },

  // Okçu askerlerin duracağı yerler (sırayla dolar)
  askerYerleri: [
    { x: 372, ayakY: 580 },
    { x: 290, ayakY: 380 },
    { x: 62, ayakY: 580 },
    { x: 130, ayakY: 380 },
    { x: 18, ayakY: 580 },
  ],

  ok: {
    hasar: 25,         // Bir okun hasarı
    hiz: 1800,         // Tam gerili yayın ok hızı
    kafaCarpani: 2,    // Kafaya isabette hasar çarpanı
    kafaAltin: 1,      // Her kafa vuruşunda altın
    yanOkOrani: 0.6,   // Çoklu okta yandaki okların hasar oranı
    cokluAci: 0.07,    // Çoklu okta oklar arası açı (radyan)
  },

  // Oyuncunun yayı: bas = ger, bırak = at
  yay: {
    germeSuresi: 0.85, // Tam germe süresi (sn)
    takmaSuresi: 0.35, // Atıştan sonra yeni ok takma süresi
    kisaDokunus: 0.35, // Bundan az gerip bırakınca yay tam gerilip kendiliğinden atar
    enAzGuc: 0.55,     // Hiç gerilmemiş yayın hız oranı
    tamHasar: 1.5,     // Tam gerili yayın hasar çarpanı
    sapma: 0.03,       // Tam gerili yayda bile sapma (radyan)
    zayifSapma: 0.09,  // Az gerilince eklenen sapma
    yorgunSapma: 0.06, // Uzun tutunca / dayanıklılık azken eklenen sapma
    sabitSure: 1.2,    // Tam gerili bu kadar sn sabit tutulur, sonra kol yorulur
    donmeHizi: 4,      // Kolun nişana dönme hızı (radyan/sn)
  },

  dayaniklilik: {
    enFazla: 100,
    germe: 12,         // Gererken saniyede harcanan
    tutma: 9,          // Tam gerili tutarken saniyede harcanan
    atis: 5,           // Her atış
    dolma: 26,         // Germezken saniyede dolan
    yorgun: 0.3,       // Bu oranın altında yorgun: yavaş gerer, çok sapar
  },

  asker: {
    hasarOrani: 0.6,   // Oyuncu hasarının yüzde kaçı
    beklemeSn: 1.1,    // İki atış arası
    sapma: 0.035,      // Nişan sapması (radyan)
    onuHatasi: 0.15,   // Yürüyen zombinin önüne nişan alırken yanılma payı
  },

  ruzgar: { enFazla: 280, sakinOlasilik: 0.25 },

  dalga: {
    temel: 4,          // 1. dalgadaki zombi ~ temel + artis
    artis: 2.6,        // Her dalgada eklenen zombi
    canArtisi: 0.14,   // Her dalgada zombi canı %14 artar...
    bilesik: 0.045,    // ...üstüne bileşik %4.5
    ilkBekleme: 1.2,
    bitirmeAltini: 10, // Dalga bitince: bitirmeAltini + dalga * bitirmeArtisi
    bitirmeArtisi: 5,
    altinArtisi: 0.03, // Zombi altını her dalgada %3 artar
  },
};

// Bir dalgadaki zombi canı çarpanı (1. dalga = 1)
function dalgaCanCarpani(dalga) {
  const d = AYAR.dalga;
  return (1 + (dalga - 1) * d.canArtisi) * Math.pow(1 + d.bilesik, dalga - 1);
}

// -------------------------------------------------------------
//  DÜŞMAN TÜRLERİ
//  gorsel: assets/gorsel içindeki şerit (yürüme/saldırı/ölüm)
//  boy   : ekrandaki boyu (vuruş kutusu buna göre)
//  kafa  : boyun üstten yüzde kaçı kafa sayılır
// -------------------------------------------------------------
const DUSMAN_TURLERI = {
  zombi:   { ad: 'Zombi',   gorsel: 'zombi',   can: 50,  hiz: 52,  hasar: 8,  vurus: 1.0, altin: 5,  boy: 118, kafa: 0.26 },
  kosucu:  { ad: 'Koşucu',  gorsel: 'kosucu',  can: 30,  hiz: 116, hasar: 5,  vurus: 0.6, altin: 7,  boy: 104, kafa: 0.28 },
  iskelet: { ad: 'İskelet', gorsel: 'iskelet', can: 40,  hiz: 70,  hasar: 6,  vurus: 0.8, altin: 8,  boy: 124, kafa: 0.22,
             kemik: 0.6, ipucu: 'Oklar kemiklerden kayar: kafasına vur.' },
  dev:     { ad: 'Dev',     gorsel: 'dev',     can: 220, hiz: 32,  hasar: 24, vurus: 1.6, altin: 20, boy: 196, kafa: 0.2,
             agir: true, ipucu: 'Çok dayanıklı. Askerlerle birlikte hep ona nişan al.' },
  yarasa:  { ad: 'Yarasa',  gorsel: 'yarasa',  can: 18,  hiz: 140, hasar: 7,  vurus: 0,   altin: 4,  boy: 50,  kafa: 1,
             ucan: true, ipucu: 'Kuleye dalar. Havada vur.' },
};

// Hangi dalgada hangi tür, hangi olasılıkla çıkar
function dusmanSec(n) {
  const sans = [
    ['dev', n >= 4 ? Math.min(0.2, 0.05 * (n - 3)) : 0],
    ['iskelet', n >= 3 ? Math.min(0.2, 0.05 * (n - 2)) : 0],
    ['kosucu', n >= 2 ? 0.25 : 0],
  ];
  let r = Math.random();
  for (const [tur, p] of sans) {
    if (r < p) return tur;
    r -= p;
  }
  return 'zombi';
}

// -------------------------------------------------------------
//  DÜKKÂN (dalga arası)
//  fiyat(seviye) → bir sonraki seviyenin fiyatı
// -------------------------------------------------------------
const YUKSELTMELER = [
  { id: 'hasar', ad: 'Keskin Uçlar', aciklama: 'Ok hasarı +%20', enFazla: 8, fiyat: s => Math.round(30 * Math.pow(1.6, s)) },
  { id: 'germe', ad: 'Hızlı Çekiş', aciklama: 'Yayı %12 daha hızlı gerersin', enFazla: 5, fiyat: s => Math.round(40 * Math.pow(1.7, s)) },
  { id: 'coklu', ad: 'Çoklu Ok', aciklama: 'Her atışta +1 ok', enFazla: 2, fiyat: s => [120, 300][s] },
  { id: 'asker', ad: 'Okçu Asker', aciklama: 'Sura bir okçu daha', enFazla: 5, fiyat: s => Math.round(60 * Math.pow(1.6, s)) },
  { id: 'sur', ad: 'Kalın Sur', aciklama: 'Sur canı +120', enFazla: 5, fiyat: s => Math.round(70 * Math.pow(1.6, s)) },
  { id: 'onarim', ad: 'Sur Onarımı', aciklama: 'Surun %35 canını onar', enFazla: 99, fiyat: (s, oyun) => 25 + 5 * oyun.dalga },
];

// Küçük yardımcılar
const kis = (v, a, b) => Math.max(a, Math.min(b, v));
const karis = (a, b, t) => a + (b - a) * t;
// Normal dağılımlı rastgele sayı (sapmalar için)
function gaussRastgele() {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}
