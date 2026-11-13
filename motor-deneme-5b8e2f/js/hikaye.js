// =============================================================
//  HİKÂYE (hikaye.js)
//  Oyunun hikâyesi: açılış, günlere bağlı kronik sayfaları,
//  Ak Dev geceleri, zafer ve yenilgi sonları.
//  Metinleri değiştirmek için yalnızca HIKAYE nesnesine bak.
//
//  Kronik sayfası alanları:
//   id     : benzersiz ad (kayıtta "okundu" diye tutulur)
//   gun    : bu günün sabahı iç kalede açılır (1. gün = ilk savaştan önce)
//   kalan  : kurtuluşa bu kadar gün kala açılır (zorluğa göre kayar)
//   sonra  : kurtuluştan bu kadar gün sonra açılır (sonsuz kuşatma)
//   baslik, kim (konuşan), metin
//  Metindeki {kurtulus} {kalan} {gun} yerine sayılar yazılır.
// =============================================================

const HIKAYE = {
  // Yeni oyunda, iç kaleye girmeden önce
  giris: [
    { baslik: 'Üç Höyük', kim: 'Kâtip Selim\'in defterinden',
      metin: 'Ilgın Beyliği\'nin son baharıydı. Veba şehirleri boşaltırken saray hekimi Ağan bir çare aradı ve aradığını kuzeydeki Üç Höyük\'te buldu.\n\nHöyüklerin altında, atalarımızın "Ak Devler" dediği üç devin kemikleri yatıyordu. Kemiklerin dibinde soluk, ağır bir sis vardı. Hekim o sisi şişelere doldurdu ve ilk ölüsünü "iyileştirdi".' },
    { baslik: 'Solgun Sis', kim: 'Kâtip Selim\'in defterinden',
      metin: 'Sis bir ayda bütün vadiye yayıldı. Ölenler kalktı, mezarlar boşaldı, ormandaki kurtlar bile gözlerinin ışığını yitirdi. Şehirler birer birer sustu.\n\nKaçabilenler güneydeki Karataş Hisarı\'na sığındı. Halk ona artık başka bir ad veriyor: Son Kale.' },
    { baslik: 'Sen', kim: 'Kâtip Selim\'in defterinden',
      metin: 'Bey Oruç yaralı. Muhafızların çoğu yolda kaldı; kulede yay tutabilen bir sen kaldın.\n\nKuzey Beyliği\'ne kuzgun gönderildi. Cevap gelene dek gündüz halkı işe koşacak, ambarı dolduracaksın. Gece ise surdasın.' },
  ],

  kronik: [
    { id: 'ilk-sabah', gun: 1, baslik: 'İlk Sabah', kim: 'Bey Oruç',
      metin: 'Ambarda ok sayılı, surda okçu yok. Halkı çiftliğe, oduncuya, yaycıya dağıt; elini çabuk tut.\n\nUnutma: attığın her ok ambardan gider. Boşa giden ok, yarın elinde olmayacak oktur. Akşam olunca surdasın.' },
    { id: 'kosucular', gun: 2, baslik: 'Koşanlar', kim: 'Gözcübaşı Halil',
      metin: 'İlk gece geçti, ama döndüler. Bu sefer aralarında koşanlar var: yeni ölenler. Sis onları henüz çürütmemiş, bacakları sağlam.\n\nAyaklarına değil, başlarına nişan al. Başına isabet eden ok iki kat acıtır.' },
    { id: 'mezarlik', gun: 3, baslik: 'Mezarlık Boşaldı', kim: 'Kâtip Selim',
      metin: 'Aşağı köyün mezarlığı bu gece boş kaldı. Sis yalnız yeni ölüleri değil, yüz yıllık kemikleri de kaldırıyor.\n\nAralarında Dikmen Kalesi\'nin okçuları var. Etleri gitmiş, yaylarını unutmamışlar. Okları kemiklerinden kayar; kafalarını hedef al.' },
    { id: 'ilk-kuzgun', gun: 4, baslik: 'Kuzgun Döndü', kim: 'Atabey Gökbörü\'nün mektubu',
      metin: '"Kuzey Beyliği ordusunu topluyor. Geçitler açılınca yola çıkacağız. {kurtulus} gün dayanın. Geleceğiz."\n\nBey Oruç mektubu meydanda okuttu. O gece kimse uyumadı, ama kimse ağlamadı da. Gözcüler ormanda ağaçları deviren iri gölgeler görmüş.' },
    { id: 'kurtlar', gun: 5, baslik: 'Sönük Gözler', kim: 'Gözcübaşı Halil',
      metin: 'Ormanın kurtları da sise yenildi. Gözleri sönük, karınları hep aç.\n\nAlçaktan ve çok hızlı gelirler. Durdukları yere değil, varacakları yere nişan al.' },
    { id: 'muhafizlar', gun: 6, baslik: 'Eski Muhafızlar', kim: 'Kâtip Selim',
      metin: 'Yaz geldi, sis dağılmadı. Bu gece gelenler başkentin muhafızları: kalkanlarını hâlâ taşıyorlar.\n\nBey Oruç surdan onlardan birini tanıdı, adıyla çağırdı. Cevap gelmedi. Kalkan gövdeye gelen oku tutar; başa ya da delici okla vur.' },
    { id: 'madenciler', gun: 7, baslik: 'Taşa Tırmananlar', kim: 'Kâtip Selim',
      metin: 'Batıdaki ocağın madencileri de kalkmış. Ölüm onlara taşa tırmanmayı unutturmamış.\n\nDuvarcılar surun dibini katranla kaplıyor. Bey Oruç\'un yarası kötüleşti; bugün kuleye çıkamadı, emirleri yatağından veriyor.' },
    { id: 'atlilar', gun: 8, baslik: 'Atlılar', kim: 'Seyis Durmuş',
      metin: 'Sis gündüzleri seyreliyor. Ahırdaki atlarla yakın köyleri dolaşabiliriz: bir ambar, bir demirhane, bir kiler. Ne bulursak getiririz.\n\nBoştaki halkı bana ver. Hepsini geri getireceğime söz veremem, ama elimizden geleni getiririz.' },
    { id: 'kara-iksir', gun: 9, baslik: 'Kara İksir', kim: 'Hekim çırağı',
      metin: 'Kapıya yarı yanık bir hekim çırağı geldi. Ağan\'ın ölülerin içini kara iksirle doldurduğunu anlattı.\n\n"Sura varınca patlarlar," dedi titreyerek. "Uzakta vurun. Biri patlarsa yanındakileri de götürür."' },
    { id: 'birinci-hoyuk', gun: 10, baslik: 'Birinci Höyük', kim: 'Hekim çırağı',
      metin: 'Çırak bir şey daha söyledi: Hekim, Ak Devlerin ilkini uyandırmış. Bu gece yer sarsılacak.\n\n"Yüreği taş gibidir," dedi. "Ama kafası bir insanınki kadar kırılgan. Kafasına vurun."' },
    { id: 'bey-oruc', gun: 11, baslik: 'Bey Oruç', kim: 'Kâtip Selim',
      metin: 'Ak Dev surun dibinde düştü. Sabaha karşı Bey Oruç da gözlerini kapadı. Son sözü sana oldu: "Kale artık senin. Halkı say, oku say, günü say."\n\nGözcüler sürünün ardında beyaz giysili ölüler görmüş: Hekim\'in şifacıları. Düşeni yeniden kaldıran onlar. Önce onları vur.' },
    { id: 'kalkanli-dev', gun: 13, baslik: 'Kemik Kalkan', kim: 'Demirci Hasan',
      metin: 'Hekim, Ak Devin kemiklerinden kalkan dövdürmüş. Gözcüler bu gece kapı kanadı kadar bir kalkanın ardında yürüyen bir dev gördü.\n\nBana demir getir, uçları sertleştireyim. Delici oklar olmadan o kalkanı geçemezsin.' },
    { id: 'defter', gun: 15, baslik: 'Defterin Yarısı', kim: 'Kâtip Selim',
      metin: 'Defterin yarısı doldu. Ölenlerin adları, bu hafta doğan iki çocuğun adı, sura giden her taş.\n\nBiri bunu bir gün okuyacak. Kale düşse bile. Kurtuluşa {kalan} gün var.' },
    { id: 'kis', gun: 16, baslik: 'Kar', kim: 'Kâtip Selim',
      metin: 'Kar yağdı. Ölüler soğuğu hissetmez; biz hissederiz.\n\nAmbarda yiyecek azalırsa halk önce umudunu, sonra kendini yer. Çiftliği boş bırakma, şapelin mumlarını söndürme.' },
    { id: 'kuzgunsuz', gun: 18, baslik: 'Kuzgunsuz Günler', kim: 'Kâtip Selim',
      metin: 'Kuzey\'den haber yok. Bir kuzgun kanadı kopuk döndü; ayağındaki mektup kanla silinmişti.\n\nMeydanda fısıltı dolaşıyor: "Ya ordu hiç gelmezse?" Bu sorunun cevabı surda verilecek.' },
    { id: 'ikinci-hoyuk', gun: 20, baslik: 'İkinci Höyük', kim: 'Gözcübaşı Halil',
      metin: 'İkinci höyükten sis yükseliyor. İkinci Ak Dev birincisinden yaşlı, birincisinden ağır.\n\nBu gece kimse surdan inmesin. Ok taşıyan çocuklar bile.' },
    { id: 'ikinci-kuzgun', gun: 21, baslik: 'İkinci Kuzgun', kim: 'Atabey Gökbörü\'nün mektubu',
      metin: '"Geçitte karla boğuştuk, atlarımızın yarısını yitirdik. Ama yoldayız. {kalan} gün."\n\nMektup meydanda okunurken halk ilk kez güldü. Kâtip Selim o gülüşü de deftere yazdı.' },
    { id: 'hekimin-sesi', gun: 23, baslik: 'Hekimin Sesi', kim: 'Kâtip Selim',
      metin: 'Gece sisin içinden bir ses kaleye seslendi: Hekim Ağan.\n\n"Kapıyı açın. Kimse acı çekmeyecek. Ölüm bir hastalıktır, ben onu iyileştirdim."\n\nSurdaki askerler cevap olarak yaylarını gerdi.' },
    { id: 'ucuncu-hoyuk', gun: 30, baslik: 'Üçüncü Höyük', kim: 'Gözcübaşı Halil',
      metin: 'Üçüncü höyük de açıldı. Ak Devlerin en büyüğü vadiden iniyor.\n\nGözcüler omzunda beyaz giysili birinin oturduğunu söylüyor. Hekim Ağan bu gece savaşı kendi gözüyle görmek istiyor.' },
    { id: 'son-gece', kalan: 0, baslik: 'Son Gece', kim: 'Seyis Durmuş',
      metin: 'Atlılar ufukta duman gördü: ordu bir günlük yolda! Bu gece son gece.\n\nHekim de biliyor. Elinde ne varsa bu gece gönderecek.' },
    // Kurtuluştan sonra savaşmaya devam edilirse
    { id: 'ordu-kuzeye', sonra: 1, baslik: 'Ordu Kuzeye Yürüdü', kim: 'Kâtip Selim',
      metin: 'Atabey Gökbörü yaralıları ve çocukları güneye yolladı, ordusuyla Üç Höyük\'e yürüdü.\n\nKale yine sende. Sis çekilene dek kapıyı tut; ordunun dönebileceği bir yer kalsın.' },
    { id: 'hoyukten-haber', sonra: 10, baslik: 'Höyükten Haber', kim: 'Atabey Gökbörü\'nün mektubu',
      metin: '"Höyüklere vardık. Sis buradan doğuyor, buradan besleniyor. Hekim\'in izini bulduk ama kendisini bulamadık."\n\n"Dayanın. Kuyu kapanana dek ölüler gelmeye devam edecek."' },
  ],

  // Ak Dev gecesi duyurusu (dalga başında)
  patronYazi(n) {
    if (n === 10) return 'Birinci höyük açıldı... Ak Dev geliyor!';
    if (n === 20) return 'İkinci Ak Dev uyandı. Yer inliyor!';
    if (n === 30) return 'Üçüncü höyük de açıldı: Ak Devlerin en büyüğü!';
    return 'Höyükten bir Ak Dev daha kalktı!';
  },

  // Zafer (kurtuluş dalgası atlatılınca)
  zafer(oyun) {
    const ucuncu = oyun.dalga >= 30;
    return [
      { baslik: 'Şafak', kim: 'Kâtip Selim\'in defterinden',
        metin: 'Şafak söktüğünde vadiden borular yükseldi. Atabey Gökbörü\'nün atlıları sisin içine daldı; ölüler ikinci kez, bu sefer gerçekten öldü.\n\nSurdaki askerler yaylarını indirdi. Kimse bağırmadı. Önce bir kadın ağladı, sonra bütün meydan.' },
      { baslik: ucuncu ? 'Üçüncü Dev' : 'Üçüncü Höyük', kim: 'Kâtip Selim\'in defterinden',
        metin: ucuncu
          ? 'Ak Devlerin sonuncusu surun dibinde yatıyordu, kafasında senin okun.\n\nHekim Ağan\'ın sesi bir daha duyulmadı. Kimi kuzeye kaçtığını söyledi, kimi kendi sisinde boğulduğunu.'
          : 'Üçüncü höyük hâlâ açık, Hekim Ağan hâlâ kuzeyde bir yerde.\n\nAma artık vadide bir ordu var ve ölüler o ordunun arkasındaki kaleyi geçemedi.' },
      { baslik: 'Son Kale', kim: 'Kâtip Selim\'in defterinden',
        metin: `Defterin son sayfasına tek satır yazdım:\n\n"Karataş Hisarı ${oyun.dalga} gece kuşatıldı ve düşmedi. Halk ona hâlâ Son Kale diyor; çünkü son kalan, ayakta kalandır."` },
    ];
  },

  // Yenilgi sonu (oyun sonu penceresinin altına yazılır)
  yenilgi(oyun) {
    if (oyun.neden === 'Halk tükendi')
      return 'Ambar boşaldı, meydan sustu. Sur ayakta, ama ardında koruyacak kimse kalmadı. Kâtip Selim defteri şapelin taşının altına sakladı.';
    return `Sur çöktü. Kâtip Selim defteri şapelin taşının altına sakladı. Belki bir gün Kuzey ordusu onu bulur ve burada ${oyun.dalga} gece kimlerin dayandığını okur.`;
  },
};

// -------------------------------------------------------------
//  Hikâye penceresi ve kronik yardımcıları
// -------------------------------------------------------------
const Hikaye = {
  acik: false, // pencere açıkken klavye kısayolları çalışmasın

  // {kurtulus} {kalan} {gun} yerine sayıları yaz
  // gun: sayfanın açıldığı gün (verilmezse bugün)
  doldur(metin, oyun, gun = oyun.dalga + 1) {
    const kurtulus = oyun.zorluk.kurtulus;
    return metin.replace(/\{kurtulus\}/g, kurtulus).replace(/\{kalan\}/g, Math.max(0, kurtulus - gun)).replace(/\{gun\}/g, gun);
  },

  // Bu sabah açılacak kronik sayfaları (henüz okunmamış olanlar)
  bugun(oyun) {
    const gun = oyun.dalga + 1, kurtulus = oyun.zorluk.kurtulus;
    const okunan = oyun.hikaye.okunan;
    return HIKAYE.kronik.filter(k => {
      if (okunan.includes(k.id)) return false;
      if (k.gun !== undefined) return k.gun === gun && gun <= kurtulus; // kurtuluştan sonra eski günlük sayfalar açılmaz
      if (k.kalan !== undefined) return kurtulus - gun === k.kalan;
      if (k.sonra !== undefined) return gun - kurtulus === k.sonra;
      return false;
    });
  },

  // Sayfanın açıldığı gün
  sayfaGunu(k, oyun) {
    const kurtulus = oyun.zorluk.kurtulus;
    return k.gun !== undefined ? k.gun : k.kalan !== undefined ? kurtulus - k.kalan : kurtulus + (k.sonra || 0);
  },

  // Okunan sayfalar (kronik penceresi için, okunma sırasıyla)
  okunanlar(oyun) {
    return oyun.hikaye.okunan.map(id => HIKAYE.kronik.find(k => k.id === id)).filter(Boolean);
  },

  // Bugünün sayfalarını göster, okundu say; bitince devam()
  sabah(sahne, oyun, devam) {
    const sayfalar = this.bugun(oyun);
    if (!sayfalar.length) return devam();
    for (const k of sayfalar) oyun.hikaye.okunan.push(k.id);
    this.goster(sahne, sayfalar.map(k => ({ ...k, metin: this.doldur(k.metin, oyun) })), devam);
  },

  // Ortada kitap sayfası gibi pencere. sayfalar: [{baslik, kim, metin}]
  // ayar.bas: hangi sayfadan başlansın · ayar.geriDon: Geri düğmesi olsun mu
  goster(sahne, sayfalar, bitince, ayar = {}) {
    if (!sayfalar.length) { if (bitince) bitince(); return; }
    const { en, boy } = AYAR;
    const T = DOKUNMATIK;
    const W = 1320, H = 760, D = 300;
    let i = ayar.bas || 0;
    this.acik = true;
    const kap = sahne.add.container(en / 2, boy / 2).setDepth(D);
    const perde = sahne.add.rectangle(0, 0, en, boy, 0x07060a, 0.72).setInteractive();
    const arka = sahne.add.rectangle(0, 0, W, H, 0x1c1612, 0.98).setStrokeStyle(4, 0xc9a24a);
    const ic = sahne.add.rectangle(0, 0, W - 24, H - 24).setStrokeStyle(1, 0x6a5430);
    const cizgi = sahne.add.graphics();
    cizgi.lineStyle(2, 0x6a5430).lineBetween(-W / 2 + 80, -H / 2 + 196, W / 2 - 80, -H / 2 + 196);
    const baslik = sahne.add.text(0, -H / 2 + 92, '', stil('baslik', 72)).setOrigin(0.5);
    const kim = sahne.add.text(0, -H / 2 + 160, '', stil('govde', T ? 30 : 28, { color: '#c9a24a', fontStyle: 'italic' })).setOrigin(0.5);
    const metinUst = -H / 2 + 228, metinEn = W - 180, metinBoy = H - 228 - 140;
    const metin = sahne.add.text(-metinEn / 2, metinUst, '', stil('govde', 34, { lineSpacing: 10, wordWrap: { width: metinEn } }));
    const sayac = sahne.add.text(-W / 2 + 60, H / 2 - 70, '', stil('govde', 26, { color: '#8a806c' })).setOrigin(0, 0.5);
    kap.add([perde, arka, ic, cizgi, baslik, kim, metin, sayac]);

    // Düğmeler (arayüzdekilerle aynı görünüm)
    const dugme = (x, w, yazi, fn) => {
      const b = sahne.add.container(x, H / 2 - 70);
      const r = sahne.add.rectangle(0, 0, w, 76, 0x2a211a, 0.95).setStrokeStyle(3, 0xc9a24a);
      const t = sahne.add.text(0, 0, yazi, stil('govde', 32, { fontStyle: 'bold' })).setOrigin(0.5);
      b.add([r, t]);
      r.setInteractive({ useHandCursor: true })
        .on('pointerover', () => r.setFillStyle(0x4a3a28, 0.95))
        .on('pointerout', () => r.setFillStyle(0x2a211a, 0.95))
        .on('pointerdown', (p, lx, ly, e) => { e && e.stopPropagation(); if (sahne.sesCal) sahne.sesCal('ui', 0.4); else if (sahne.oyun) sahne.oyun.sesCal('ui', 0.4); fn(); });
      b.yazi = t;
      kap.add(b);
      return b;
    };
    const ileriD = dugme(W / 2 - 190, 300, '', () => ileri());
    const atlaD = dugme(W / 2 - 470, 220, 'Atla', () => kapat());
    const geriD = ayar.geriDon ? dugme(W / 2 - 720, 220, '◀ Geri', () => { if (i > 0) { i--; ciz(); } }) : null;

    const ciz = () => {
      const s = sayfalar[i];
      baslik.setText(s.baslik || '');
      kim.setText(s.kim || '');
      // Uzun metin pencereye sığana dek küçülür
      let boyut = T ? 38 : 34;
      metin.setFontSize(boyut).setText(s.metin);
      while (metin.height > metinBoy && boyut > 22) { boyut -= 2; metin.setFontSize(boyut); }
      sayac.setText(sayfalar.length > 1 ? `${i + 1} / ${sayfalar.length}` : '');
      const son = i === sayfalar.length - 1;
      ileriD.yazi.setText(son ? (ayar.sonYazi || 'Devam ▶') : 'İleri ▶');
      atlaD.setVisible(!son);
      if (geriD) geriD.setVisible(i > 0);
      sahne.tweens.killTweensOf([metin, baslik]);
      metin.setAlpha(0); baslik.setAlpha(0);
      sahne.tweens.add({ targets: baslik, alpha: 1, duration: 300 });
      sahne.tweens.add({ targets: metin, alpha: 1, duration: 600, delay: 120 });
    };
    const ileri = () => { if (i < sayfalar.length - 1) { i++; ciz(); } else kapat(); };
    let kapandi = false;
    const kapat = () => {
      if (kapandi) return;
      kapandi = true;
      sahne.input.keyboard.off('keydown', tus);
      kap.destroy();
      this.acik = false;
      if (bitince) bitince();
    };
    // Boşluk / Enter ileri, Esc atla
    const tus = e => {
      if (e.repeat) return;
      if (e.key === ' ' || e.key === 'Enter') ileri();
      else if (e.key === 'Escape') kapat();
    };
    // Pencereyi açan tuş basışı hemen ileri saymasın
    sahne.time.delayedCall(150, () => { if (!kapandi) sahne.input.keyboard.on('keydown', tus); });
    sahne.events.once('shutdown', () => { this.acik = false; });
    kap.setAlpha(0);
    sahne.tweens.add({ targets: kap, alpha: 1, duration: 250 });
    ciz();
    return kap;
  },

  // Kronik: şimdiye dek okunan bütün sayfalar (son sayfadan başlar)
  kronikAc(sahne, oyun, bitince) {
    const l = this.okunanlar(oyun).map(k => ({ ...k, kim: `${this.sayfaGunu(k, oyun)}. gün · ${k.kim}`, metin: this.doldur(k.metin, oyun, this.sayfaGunu(k, oyun)) }));
    if (!l.length) l.push({ baslik: 'Kronik', kim: 'Kâtip Selim', metin: 'Defter henüz boş.' });
    this.goster(sahne, l, bitince, { bas: l.length - 1, geriDon: true, sonYazi: 'Kapat' });
  },
};
