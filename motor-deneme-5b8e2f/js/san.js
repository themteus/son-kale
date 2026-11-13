// =============================================================
//  ŞAN (san.js)
//  Oyunlar arası ilerleme. Her oyunun sonunda dayandığın geceye göre
//  Şan kazanırsın; başarımlar ve günün görevleri de Şan verir.
//  Başlangıç menüsündeki "Şan Salonu"nda kalıcı ödüller alınır:
//  bir sonraki oyun biraz daha güçlü başlar.
//  Tarayıcıda saklanır (Kayit), kale düşse de silinmez.
// =============================================================

const SAN_ODULLERI = [
  { id: 'ambar', ad: 'Dolu Ambar', aciklama: 'Oyuna +60 okla başla', enFazla: 3, fiyat: [6, 15, 30] },
  { id: 'hazine', ad: 'Bey Hazinesi', aciklama: 'Oyuna +40 altınla başla', enFazla: 3, fiyat: [6, 15, 30] },
  { id: 'halk', ad: 'Kalabalık Sığınak', aciklama: 'Oyuna +2 kişiyle başla', enFazla: 3, fiyat: [8, 20, 40] },
  { id: 'ok', ad: 'Atalardan Kalma Yay', aciklama: 'Bütün okların hasarı +%5', enFazla: 3, fiyat: [10, 25, 50] },
  { id: 'sur', ad: 'Sağlam Temel', aciklama: 'Surun canı +%8', enFazla: 3, fiyat: [10, 25, 50] },
];

// Başarımlar: bir kez kazanılır. kontrol(o) gece bitince, kale düşünce ve kurtuluşta bakılır.
const BASARIMLAR = [
  { id: 'ilkgece', ad: 'İlk Gece', aciklama: 'İlk geceyi atlat', san: 1, kontrol: o => o.dalga >= 1 },
  { id: 'kombo10', ad: 'Ok Fırtınası', aciklama: '10\'lu kombo yap', san: 3, kontrol: o => o.enIyiKombo >= 10 },
  { id: 'ilkdev', ad: 'Birinci Höyük', aciklama: 'Taş Yürekli Ak Devi yık', san: 5, kontrol: o => o.dalga >= 10 && !o.patron() },
  { id: 'olay5', ad: 'Gece Bekçisi', aciklama: 'Bir oyunda 5 gece olayı atlat', san: 3, kontrol: o => (o.olayAtlatilan || 0) >= 5 },
  { id: 'kafa100', ad: 'Kafa Avcısı', aciklama: 'Bir oyunda 100 kafa vuruşu', san: 4, kontrol: o => o.kafaVurusu >= 100 },
  { id: 'barikatsiz', ad: 'Taş Üstünde Taş', aciklama: '20. geceyi hiç barikat kurmadan atlat', san: 5, kontrol: o => o.dalga >= 20 && !o.barikatSayisi },
  { id: 'ucdev', ad: 'Üç Höyük', aciklama: 'Üç Ak Devi de yık', san: 8, kontrol: o => o.dalga >= 30 && !o.patron() },
  { id: 'kurtulus', ad: 'Kuzey Ordusu', aciklama: 'Kaleyi kurtar', san: 10, kontrol: o => o.kurtuldu },
  { id: 'kabus', ad: 'Kâbusun Sonu', aciklama: 'Kabus zorlukta kaleyi kurtar', san: 20, kontrol: o => o.kurtuldu && o.zorlukAdi === 'kabus' },
];

// Oyun sonunda: dayanılan gece başına Şan (zorluğa göre)
const SAN_GECE = { kolay: 0.3, normal: 0.5, kabus: 0.8 };

const San = {
  toplam() { return +Kayit.oku('san', 0) || 0; },
  ekle(n) { Kayit.yaz('san', this.toplam() + n); },
  seviye(id) { return +Kayit.oku('sanOdul.' + id, 0) || 0; },
  kazanildi(id) { return Kayit.oku('basarim.' + id, '') === '1'; },

  satinAl(u) {
    const sv = this.seviye(u.id);
    if (sv >= u.enFazla || this.toplam() < u.fiyat[sv]) return false;
    Kayit.yaz('san', this.toplam() - u.fiyat[sv]);
    Kayit.yaz('sanOdul.' + u.id, sv + 1);
    return true;
  },

  // Yeni oyunun başında (devam edilen oyunda kayıt bunları ezer)
  uygula(o) {
    const E = o.ekonomi;
    E.kaynak.ok += 60 * this.seviye('ambar');
    o.altin += 40 * this.seviye('hazine');
    E.nufus += 2 * this.seviye('halk');
  },
  hasarCarpani() { return 1 + 0.05 * this.seviye('ok'); },
  surCarpani() { return 1 + 0.08 * this.seviye('sur'); },

  // Yeni kazanılan başarımlar: Şan eklenir, adları döner
  basarimKontrol(o) {
    const yeni = [];
    for (const b of BASARIMLAR) {
      if (this.kazanildi(b.id) || !b.kontrol(o)) continue;
      Kayit.yaz('basarim.' + b.id, '1');
      this.ekle(b.san);
      o.sanKazanilan = (o.sanKazanilan || 0) + b.san;
      yeni.push(b);
    }
    return yeni;
  },

  // Oyun bitti (kale düştü ya da kurtuldu): gece Şanı bir kez verilir
  // (kurtuluştan sonra savaşmaya devam edilirse kale düşünce yalnız fazladan geceler sayılır)
  oyunSonu(o) {
    const n = Math.floor((o.dalga - (o.sanDalga || 0)) * (SAN_GECE[o.zorlukAdi] || 0.5));
    o.sanDalga = o.dalga;
    this.ekle(n);
    o.sanKazanilan = (o.sanKazanilan || 0) + n;
    return n;
  },
};
