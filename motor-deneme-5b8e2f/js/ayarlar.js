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
    { x: 80, ayakY: 580 },
    { x: 122, ayakY: 380 },
    { x: 30, ayakY: 580 },  // ekran kenarından taşmasın, yanındakiyle üst üste binmesin
    // Sur yükseldikçe açılan yerler (SUR.askerYeri)
    { x: 326, ayakY: 580 },
    { x: 247, ayakY: 380 },
    { x: 55, ayakY: 580 },
    { x: 163, ayakY: 380 },
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

  // Barikat: sur yıkılınca halk odunla son bir barikat kurar (dalga başına bir kez)
  barikat: { canOrani: 0.25, odun: 40 },

  // Kafa serisi: art arda bu kadar kafa vuruşu → sıradaki ok "keskin" olur
  // Keskin ok: hasar ×2 ve önündeki düşmanların içinden geçer. Iska seriyi bozar.
  keskin: { seri: 3, hasar: 2, delip: 3 },

  // Vuruş hissi: kısa donma (hit-stop), kombo, ağır çekim
  his: {
    donmaKafa: 0.05,    // Kafadan öldürünce oyun bu kadar sn neredeyse durur
    donmaAgir: 0.09,    // Dev/kalkanlı dev/Ak Dev ölünce
    donmaHizi: 0.08,    // Donarken zaman bu hızla akar
    komboSure: 1.6,     // İki öldürme arası bu kadar sn içindeyse kombo sürer
    komboEnAz: 3,       // Bu kombodan sonra her öldürme +altın verir
    komboAltin: 1,      // Kombo başına ek altın (kombo − komboEnAz + 1) × bu
    komboTavan: 10,     // Bir öldürmede komboyla en çok bu kadar ek altın
    agirCekimSure: 0.9, // Dalganın son düşmanı / Ak Dev ölünce ağır çekim (sn)
    agirCekimHizi: 0.3,
    hasarSayisi: true,  // Oyuncunun oklarında hasar sayısı uçar
  },

  dalga: {
    temel: 4,          // 1. dalgadaki zombi ~ temel + artis
    artis: 2.6,        // Her dalgada eklenen zombi
    canArtisi: 0.14,   // Her dalgada zombi canı %14 artar...
    bilesik: 0.04,     // ...üstüne bileşik %4
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
  kurt:    { ad: 'Kurt',    gorsel: 'kurt',    can: 34,  hiz: 150, hasar: 5,  vurus: 0.5, altin: 8,  boy: 70,  kafa: 0.45, en: 110,
             ipucu: 'Çok hızlı koşar ama alçaktan gelir. Önüne nişan al.' },
  kalkanli:{ ad: 'Kalkanlı', gorsel: 'kalkanli', can: 90, hiz: 40,  hasar: 10, vurus: 1.1, altin: 12, boy: 120, kafa: 0.24,
             kalkan: 0.6, ipucu: 'Kalkan gövdeye gelen oku tutar. Kafasına ya da delici okla vur.' },
  okcuiskelet: { ad: 'Okçu İskelet', gorsel: 'okcuiskelet', can: 45, hiz: 48, hasar: 9, vurus: 2.6, altin: 10, boy: 122, kafa: 0.22,
             kemik: 0.6, menzil: [1120, 1520], ipucu: 'Uzakta durup sura ok atar. Okları havada vurabilirsin.' },
  tirmanici:{ ad: 'Tırmanıcı', gorsel: 'tirmanici', can: 60, hiz: 64, hasar: 18, vurus: 1.0, altin: 12, boy: 112, kafa: 0.28,
             tirman: 28, ipucu: 'Sura tırmanır, tepeye çıkınca sert vurur. Tırmanırken düşür.' },
  patlayan:{ ad: 'Patlayan', gorsel: 'patlayan', can: 40,  hiz: 60,  hasar: 50, vurus: 1,   altin: 9,  boy: 112, kafa: 0.26,
             patlar: 160, ipucu: 'Sura varınca patlar. Uzakta vur: ölünce yanındakileri de patlatır.' },
  sifaci:  { ad: 'Şifacı',  gorsel: 'sifaci',  can: 55,  hiz: 44,  hasar: 0,  vurus: 2,   altin: 15, boy: 118, kafa: 0.26,
             menzil: [1200, 1520], sifa: 0.12, sifaAlan: 360, ipucu: 'Geride durup sürüyü iyileştirir. Önce onu vur.' },
  kalkanlidev: { ad: 'Kalkanlı Dev', gorsel: 'kalkanlidev', can: 300, hiz: 28, hasar: 34, vurus: 1.7, altin: 32, boy: 200, kafa: 0.2,
             agir: true, kalkan: 0.7, ipucu: 'Kocaman kalkan oku tutar. Kafasına ya da delici okla vur.' },
  patron:  { ad: 'Ak Dev',  gorsel: 'patron',  can: 1400, hiz: 22, hasar: 60, vurus: 2.0, altin: 150, boy: 250, kafa: 0.18,
             agir: true, patron: true },
};

// Hangi dalgada hangi tür, hangi olasılıkla çıkar (önce yazılan önce denenir)
function dusmanSec(n) {
  const sans = [
    ['dev', n >= 4 ? Math.min(0.16, 0.04 * (n - 3)) : 0],
    ['okcuiskelet', n >= 3 ? Math.min(0.14, 0.04 * (n - 2)) : 0],
    ['iskelet', n >= 3 ? Math.min(0.12, 0.04 * (n - 2)) : 0],
    ['kurt', n >= 5 ? Math.min(0.14, 0.04 * (n - 4)) : 0],
    ['kalkanli', n >= 6 ? Math.min(0.14, 0.04 * (n - 5)) : 0],
    ['tirmanici', n >= 7 ? Math.min(0.12, 0.04 * (n - 6)) : 0],
    ['patlayan', n >= 9 ? Math.min(0.07, 0.02 * (n - 8)) : 0],
    ['sifaci', n >= 11 ? Math.min(0.05, 0.015 * (n - 10)) : 0],
    ['kalkanlidev', n >= 13 ? Math.min(0.06, 0.015 * (n - 12)) : 0],
    ['kosucu', n >= 2 ? 0.2 : 0],
  ];
  let r = Math.random();
  for (const [tur, p] of sans) {
    if (r < p) return tur;
    r -= p;
  }
  return 'zombi';
}

// Her 10. dalga patron dalgası
const PATRON_ARASI = 10;

// Üç Ak Dev: 10, 20 ve 30. gecede sırayla gelir (sonsuz kuşatmada yeniden döner).
// Aynı görsel, farklı renk ve saldırı tarzı.
//  govde  : gövdeye gelen okun hasar oranı (kafa normal vurur)
//  kukreme: aralıkla kükrer, yakındaki düşmanlar bir süre hızlanır
//  cagir  : aralıkla yanında yerden ölü kaldırır
//  zirh   : canı bu eşiklerin altına inince sise bürünür (gövde hasarı × oran); kafa vuruşu sisi dağıtır
//  ofke   : canı bu oranın altına inince hızlanır
const AK_DEVLER = [
  { ad: 'Taş Yürekli Ak Dev', renk: null, govde: 0.6,
    kukreme: { aralik: 9, sure: 3.5, hiz: 1.6, alan: 760 },
    ipucu: 'Gövdesi taş gibi: oklar az işler. Kafasına nişan al! Kükreyince sürü hızlanır.' },
  { ad: 'Ölü Çağıran Ak Dev', renk: 0xc4dcae, govde: 1,
    cagir: { aralik: 6.5, sayi: 2, tur: 'zombi', enCok: 14 },
    ipucu: 'Yürüdükçe yerden ölü kaldırır. Sur dibine varmadan düşür!' },
  { ad: 'Sisli Ak Dev', renk: 0xb4c4f0, govde: 1,
    zirh: { esik: [0.75, 0.5, 0.25], sure: 5, oran: 0.15 },
    ofke: { esik: 0.3, hiz: 1.8 },
    ipucu: 'Canı azaldıkça sise bürünür: kafa vuruşu sisi dağıtır. Son nefeste öfkelenir.' },
];
// n. dalganın Ak Devi
function akDev(n) { return AK_DEVLER[(Math.max(1, Math.round(n / PATRON_ARASI)) - 1) % AK_DEVLER.length]; }

// -------------------------------------------------------------
//  GECE OLAYLARI: bazı gecelerin kendine özgü kuralı olur.
//  Gözcüler bir gün önceden haber verir (iç kalede yazar).
//   enAz: bu dalgadan önce çıkmaz · hiz/altin: düşman hızı ve altın çarpanı
//   kafa: kafa vuruşu çarpanı · atesYok: ateşli ok yakmaz · ruzgar: o gecenin rüzgârı
//   ekle: dalgaya eklenen düşmanlar · sis: sağ yarı sisle örtülür
// -------------------------------------------------------------
const GECE_OLAYLARI = {
  kanayi:  { ad: 'Kan Ayı',    enAz: 4, hiz: 1.2, altin: 1.5, renk: 0x7a1010, renkOran: 0.18, ay: 0xff6a50, ayOlcek: 1.1,
             aciklama: 'Ölüler azgın ve hızlı. Ama her biri bir buçuk kat altın düşürür.' },
  sis:     { ad: 'Sisli Gece', enAz: 3, sis: true,
             aciklama: 'Solgun Sis vadiye çöktü: sürü sisin içinden çıkıp gelir.' },
  saganak: { ad: 'Sağanak',    enAz: 3, hiz: 0.85, atesYok: true, ruzgar: 0,
             aciklama: 'Yağmur çamura çevirdi: düşmanlar yavaş, rüzgâr yok. Ateşli oklar tutuşmaz.' },
  dolunay: { ad: 'Dolunay',    enAz: 5, kafa: 1.5, renk: 0xc8d8ff, renkOran: 0.08, ay: 0xffffff, ayOlcek: 1.3,
             aciklama: 'Gece aydınlık: kafa vuruşları bir buçuk kat daha sert.' },
  kurt:    { ad: 'Kurt Gecesi', enAz: 6, ekle: { kurt: 6 },
             aciklama: 'Ormandan bir kurt sürüsü indi. Önlerine nişan al.' },
};
const OLAY_OLASILIK = 0.35; // Ak Dev gecesi dışında bir gecenin olaylı olma olasılığı

// -------------------------------------------------------------
//  ZORLUK (başlangıçta seçilir)
//   can/hiz/cikis: düşman canı, hızı, geliş aralığı çarpanı
//   altin: kazanılan altın çarpanı · kurtulus: bu dalga atlatılınca kazanırsın
// -------------------------------------------------------------
const ZORLUKLAR = {
  kolay:  { ad: 'Kolay',  can: 0.7, hiz: 0.9, cikis: 1.3, altin: 1.25, kurtulus: 25 },
  normal: { ad: 'Normal', can: 1.08, hiz: 1,  cikis: 0.95,   altin: 1,    kurtulus: 30 },
  kabus:  { ad: 'Kabus',  can: 1.25, hiz: 1.1, cikis: 0.85, altin: 0.9, kurtulus: 30 },
};

// -------------------------------------------------------------
//  OK TÜRLERİ (1-2-3 tuşu ya da ekrandaki düğmeler)
// -------------------------------------------------------------
const OK_TURLERI = {
  normal: { ad: 'Ok', renk: 0xbfc4c8 },
  ates:   { ad: 'Ateşli', renk: 0xff8a30, yanma: 0.35, yanmaSure: 3, aciklama: 'Düşmanı tutuşturur: 3 sn yanar' },
  delici: { ad: 'Delici', renk: 0x8ad0ff, delip: 3, aciklama: 'Kalkanı deler, 3 düşmandan geçer' },
};

// Ok Yağmuru (dükkândan açılır, Q ya da düğme)
const YAGMUR = { bekleme: 20, temelOk: 12, seviyeBasi: 8, hasarOrani: 0.8, yayilma: 220 };

// -------------------------------------------------------------
//  DÜKKÂN (dalga arası)
//  fiyat(seviye) → bir sonraki seviyenin fiyatı
// -------------------------------------------------------------
const YUKSELTMELER = [
  { id: 'hasar', ad: 'Keskin Uçlar', aciklama: 'Ok hasarı +%20', enFazla: 8, fiyat: s => Math.round(30 * Math.pow(1.6, s)) },
  { id: 'germe', ad: 'Hızlı Çekiş', aciklama: 'Yayı %12 daha hızlı gerersin', enFazla: 5, fiyat: s => Math.round(40 * Math.pow(1.7, s)) },
  { id: 'coklu', ad: 'Çoklu Ok', aciklama: 'Her atışta +1 ok (stoktan da 1 fazla düşer)', enFazla: 2, fiyat: s => [120, 300][s] },
  { id: 'yagmur', ad: 'Ok Yağmuru', aciklama: 'Q: gökten ok yağdır (oklar ambardan gider)', enFazla: 3, fiyat: s => [150, 260, 420][s] },
  { id: 'egitim', ad: 'Okçu Eğitimi', aciklama: 'Askerlerin hasarı +%15, daha az sapar', enFazla: 8, fiyat: s => Math.round(150 * Math.pow(1.7, s)) },
  { id: 'payanda', ad: 'Sur Payandası', aciklama: 'Surun en yüksek canı +%10', enFazla: 8, fiyat: s => Math.round(200 * Math.pow(1.7, s)) },
  { id: 'ates', ad: 'Ateşli Ok ×10', aciklama: 'Düşmanı tutuşturur (2 tuşu)', enFazla: 99, fiyat: () => 40, stok: true },
  { id: 'delici', ad: 'Delici Ok ×10', aciklama: 'Kalkanı deler, sıra sıra geçer (3 tuşu)', enFazla: 99, fiyat: () => 50, stok: true },
];

// =============================================================
//  İÇ KALE EKONOMİSİ (ekonomi.js, kale.js)
//  Her dalga = bir gün. Gün sonunda binalar üretir, halk yer,
//  duvarcılar suru onarır, savaş alanından oklar toplanır.
//  Her atılan ok ambardan düşer; ok biterse okçular susar.
// =============================================================
const KAYNAKLAR = {
  odun:    { ad: 'Odun',    renk: 0x9a6a3a },
  tas:     { ad: 'Taş',     renk: 0x9a968c },
  demir:   { ad: 'Demir',   renk: 0x6a7a8a },
  yiyecek: { ad: 'Yiyecek', renk: 0xc8a040 },
  uc:      { ad: 'Ok ucu',  renk: 0xb8c0c8 },
  ok:      { ad: 'Ok',      renk: 0xe8dcc0 },
  yay:     { ad: 'Yay',     renk: 0xb07840 },
};

const EKONOMI = {
  baslangic: { odun: 80, tas: 60, demir: 12, yiyecek: 40, uc: 40, ok: 260, yay: 2 },
  nufus: 14,          // Başlangıç nüfusu
  yemek: 1,           // Kişi başı günlük yiyecek
  enFazlaGelen: 3,    // Günde en fazla kaç sığınmacı gelir (evde yer olmalı)
  gelenBasiYiyecek: 12, // Ambardaki her 12 yiyecek bir sığınmacı çeker
  aclikOlum: 3,       // Her 3 eksik yiyecek bir kişinin ölümü
  iskaToplama: 0.8,   // Iskalanan okların toplanan oranı
  isabetToplama: 0.3, // Düşmana saplanan okların toplanan oranı (çoğu kırılır)
  enAzNufus: 5,       // Halk bunun altına inerse kale düşer
  seviyeBonus: 0.2,   // Bina her seviyede işçi başı üretimi %20 artırır
  acilOnarim: 1.5,    // Altınla onarım: 1 can kaç altın (günde surun en çok yarısı)
  tamamlaZam: 1.3,    // Yükseltmede eksik malzemeyi altınla tamamlarken pazar fiyatına zam
};

// Binalar. yerlesim: iç kale sahnesindeki yer (assets/kale/kale.json)
//   yer   : seviyeye göre en fazla işçi
//   uretim: işçi başı günlük üretim · tuketim: işçi başı günlük gider
//   yukselt: 2. ve 3. seviyenin bedeli
const BINALAR = {
  ciftlik: { ad: 'Çiftlik', is: 'çiftçi', aciklama: 'Yiyecek üretir. Herkes günde 1 yiyecek yer.',
    yer: [5, 7, 10], uretim: { yiyecek: 4 },
    yukselt: [{ odun: 25, tas: 10, altin: 65 }, { odun: 50, tas: 40, altin: 190 }], bas: { seviye: 1, isci: 4 } },
  oduncu: { ad: 'Oduncu', is: 'oduncu', aciklama: 'Odun keser: ok gövdesi, yay, onarım ve inşaat için.',
    yer: [3, 5, 7], uretim: { odun: 8 },
    yukselt: [{ odun: 10, tas: 20, altin: 50 }, { odun: 30, tas: 50, demir: 5, altin: 160 }], bas: { seviye: 1, isci: 2 } },
  tasocagi: { ad: 'Taş Ocağı', is: 'taşçı', aciklama: 'Taş çıkarır: sur onarımı ve yükseltmesi için.',
    yer: [3, 5, 7], uretim: { tas: 5 },
    yukselt: [{ odun: 25, tas: 10, altin: 50 }, { odun: 40, tas: 40, demir: 5, altin: 160 }], bas: { seviye: 1, isci: 1 } },
  maden: { ad: 'Maden', is: 'madenci', aciklama: 'Az ama değerli demir çıkarır. Demir olmadan ok ucu olmaz.',
    yer: [2, 3, 4], uretim: { demir: 4 },
    yukselt: [{ odun: 30, tas: 40, altin: 95 }, { odun: 55, tas: 80, demir: 10, altin: 255 }], bas: { seviye: 1, isci: 1 } },
  demirci: { ad: 'Demirci', is: 'demirci', aciklama: 'Demirden ok ucu döver. Seviyesi uçları sertleştirir: bütün okların hasarı artar.',
    yer: [2, 3, 4], tuketim: { demir: 2 }, uretim: { uc: 50 }, // uc: bir demirden kaç uç
    yukselt: [{ odun: 25, tas: 30, demir: 10, altin: 130 }, { odun: 50, tas: 60, demir: 25, altin: 320 }], bas: { seviye: 1, isci: 1 },
    kalite: [{ ad: 'Demir uç', hasar: 1 }, { ad: 'Çelik uç', hasar: 1.15 }, { ad: 'Zırh delen uç', hasar: 1.35 }] },
  yayci: { ad: 'Yaycı', is: 'yaycı', aciklama: 'Odun ve uçtan ok yapar, askerlere yay yapar. Seviyesi askerlerin yayını güçlendirir.',
    yer: [3, 5, 7], tuketim: { odun: 4, uc: 40 }, uretim: { ok: 40 },
    yukselt: [{ odun: 35, tas: 10, demir: 5, altin: 130 }, { odun: 70, tas: 30, demir: 15, altin: 320 }], bas: { seviye: 1, isci: 1 },
    yayBedeli: { odun: 6 },
    kalite: [{ ad: 'Avcı yayı', hasar: 1 }, { ad: 'Kompozit yay', hasar: 1.2 }, { ad: 'Uzun yay', hasar: 1.4 }] },
  duvarci: { ad: 'Duvarcı', is: 'duvarcı', aciklama: 'Hasarlı suru taş ve odunla onarır. Yarıdan çok yıkılmış sur iki kat hızlı onarılır.',
    yer: [2, 4, 6], tuketim: { tas: 3, odun: 1 }, onarim: 40, azsaHizli: 0.5,
    yukselt: [{ odun: 20, tas: 30, altin: 65 }, { odun: 35, tas: 70, altin: 190 }], bas: { seviye: 1, isci: 1 } },
  ev: { ad: 'Evler', aciklama: 'Nüfus sınırı. Evde yer yoksa sığınmacı alınamaz.',
    barinak: [22, 32, 46],
    yukselt: [{ odun: 30, tas: 20, altin: 120 }, { odun: 60, tas: 50, altin: 300 }], bas: { seviye: 1, isci: 0 } },
};

// Sur ve kuleler: seviyeye göre en yüksek can, yükseltme bedeli
const SUR = {
  can: [500, 650, 820, 1000, 1200],
  askerYeri: [5, 6, 7, 8, 9],  // Surdaki okçu yeri (seviyeye göre)
  yukselt: [{ tas: 60, odun: 20, altin: 50 }, { tas: 110, odun: 40, altin: 120 }, { tas: 170, odun: 60, demir: 10, altin: 230 }, { tas: 240, odun: 80, demir: 20, altin: 380 }],
};

// Pazar: altınla bir parti al ya da sat. Aldıkça o gün pahalanır.
const PAZAR = {
  odun:    { parti: 20, fiyat: 16 },
  tas:     { parti: 15, fiyat: 18 },
  demir:   { parti: 6,  fiyat: 22 },
  yiyecek: { parti: 20, fiyat: 15 },
  ok:      { parti: 50, fiyat: 30 },
  satis: 0.5,   // Satarken alış fiyatının yarısı
  artis: 0.15,  // Her alışta fiyat %15 artar (her gün yarı yarıya geri iner)
};


// =============================================================
//  YAPILAR (yapilar.js): iç kaledeki şapel, kışla ve ahır
//  Görselleri assets/kale/sus/ic2 içinde; tıklanınca paneli açılır.
// =============================================================
const YAPILAR = {
  sapel: { ad: 'Şapel', is: 'rahip', aciklama: 'Rahipler halkın moralini yükseltir. Moral yüksekse bütün binalar daha çok üretir.',
    yer: [1, 2, 3], bas: { seviye: 1, isci: 0 },
    yukselt: [{ odun: 30, tas: 50, altin: 180 }, { odun: 60, tas: 100, demir: 10, altin: 450 }] },
  kisla: { ad: 'Kışla', aciklama: 'Askerler burada talim yapar ve yatar. Her seviye: askerler daha hızlı ve sert atar, 4 kişilik yatak.',
    bas: { seviye: 0 },
    yukselt: [{ odun: 40, tas: 60, altin: 150 }, { odun: 70, tas: 110, demir: 15, altin: 420 }, { odun: 100, tas: 160, demir: 30, altin: 900 }] },
  ahir: { ad: 'Ahır', aciklama: 'Atlılar boştaki halkla sefere çıkar: ertesi gün ganimetle döner. Ahır büyüdükçe ganimet artar, kayıp azalır.',
    bas: { seviye: 1 },
    yukselt: [{ odun: 50, tas: 30, altin: 200 }, { odun: 90, tas: 60, demir: 10, altin: 550 }] },
};

// Kışla: seviye başına
const KISLA = { hiz: 0.1, hasar: 0.1, yatak: 4 };

// Moral (0-100). Üretim çarpanı: moral 50'de 1, 0'da 0.85, 100'de 1.15
const MORAL = {
  baslangic: 60, etki: 0.3,
  tok: 2,            // Herkes doyunca günde (moral tavanın altındaysa)
  tavan: 60,
  aclik: -15,        // Yiyecek yetmezse
  olum: -4,          // Açlıktan ya da seferde ölen her kişi
  barikat: -10,      // Sur yıkılıp barikat kurulduysa
  hasarliSur: -5,    // Gün sonunda sur %40'ın altındaysa
  rahip: 3,          // Rahip başına günde (şapel seviyesiyle artar)
  siginmaciAlt: 25,  // Moral bunun altındaysa sığınmacı gelmez
  solen: { yiyecek: 30, altin: 20, moral: 15 }, // Şölen: günde bir kez
};

// Sefer (ahır): boştaki kişiler bir gün yağmaya gider
const SEFER = {
  enAz: 2, enCok: 8, ilkGun: 3,       // ilkGun: bu günden önce gönderilemez
  risk: 0.16, riskAzalma: 0.05,       // kişi başı ölüm olasılığı, ahır seviyesi başına azalır
  riskArtisi: 1 / 40,                 // her dalga riski biraz artırır
  ganimet: { odun: 6, tas: 4, demir: 1.5, yiyecek: 8, altin: 9 }, // kişi başı ortalama
  seviyeBonus: 0.3, gunBonus: 0.04,
};

// Telefon/tablet (dokunmatik): yazılar ve paneller büyür
const DOKUNMATIK = (() => { try { return window.matchMedia('(pointer: coarse)').matches; } catch (e) { return false; } })();

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
