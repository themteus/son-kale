// =============================================================
//  YAPILAR (yapilar.js)
//  İç kaledeki şapel, kışla ve ahır artık iş görür:
//   Şapel : rahipler moral yükseltir, şölen verilir (moral → üretim)
//   Kışla : askerler daha hızlı ve sert atar, yatak (nüfus sınırı)
//   Ahır  : boştaki halk sefere çıkar, ertesi gün ganimetle döner
//  Sayılar ayarlar.js → YAPILAR, KISLA, MORAL, SEFER.
//  Görseller ic_susler.js'in koyduğu süsler (ks_ic2/sapel ...).
// =============================================================

const Yapilar = {
  // ---------- Ekonomi ----------
  yukseltBedeli(E, k) { return YAPILAR[k].yukselt[E.yapi[k].seviye - YAPILAR[k].bas.seviye] || null; },
  yukselt(E, k, oyun, tamamla) {
    const b = this.yukseltBedeli(E, k);
    if (!b || !(tamamla ? E.tamamlaVeOde(b, oyun) : E.ode(b, oyun))) return false;
    E.yapi[k].seviye++;
    return true;
  },
  rahipYeri(E) { return YAPILAR.sapel.yer[E.yapi.sapel.seviye - 1]; },
  rahipEkle(E, n) {
    const y = E.yapi.sapel;
    if (n > 0 && (E.bosta <= 0 || y.isci >= this.rahipYeri(E))) return false;
    if (n < 0 && y.isci <= 0) return false;
    y.isci += n;
    return true;
  },

  // Askerlerin kışla çarpanları (okcu.js)
  asker(oyun) {
    const sv = oyun.ekonomi.yapi ? oyun.ekonomi.yapi.kisla.seviye : 0;
    return { bekleme: 1 / (1 + KISLA.hiz * sv), hasar: 1 + KISLA.hasar * sv };
  },

  // Rahiplerin günlük moral katkısı
  rahipMorali(E) { return Math.round(E.yapi.sapel.isci * MORAL.rahip * (1 + 0.5 * (E.yapi.sapel.seviye - 1))); },

  // Gün sonunda moral ne kadar değişir
  moralDegisimi(E, oyun, d) {
    const M = MORAL;
    // Tok halkın morali kendiliğinden ancak tavana (60) kadar çıkar; ötesi rahip ve şölen ister
    let m = d.aclik ? M.aclik : E.moral < M.tavan ? M.tok : 0;
    m += d.olen * M.olum;
    if (oyun.barikatKuruldu) m += M.barikat;
    if (oyun.surCan < oyun.surEnFazla * 0.4) m += M.hasarliSur;
    m += this.rahipMorali(E);
    return m;
  },

  solen(E, oyun) {
    const S = MORAL.solen;
    if (E.solenYapildi || E.moral >= 100 || E.kaynak.yiyecek < S.yiyecek || oyun.altin < S.altin) return false;
    E.kaynak.yiyecek -= S.yiyecek;
    oyun.altin -= S.altin;
    E.moral = Math.min(100, E.moral + S.moral);
    E.solenYapildi = true;
    return true;
  },

  // ---------- Sefer ----------
  seferAcik(oyun) { return oyun.dalga + 1 >= SEFER.ilkGun; },
  seferRiski(E, oyun) {
    return Math.max(0.02, SEFER.risk - SEFER.riskAzalma * (E.yapi.ahir.seviye - 1)) * (1 + oyun.dalga * SEFER.riskArtisi);
  },
  // Gönderilecek kişiyi ayarla (boştakilerden)
  seferAyarla(E, oyun, n) {
    if (!this.seferAcik(oyun)) return false;
    const yeni = E.sefer + n;
    if (n > 0 && (E.bosta <= 0 || yeni > SEFER.enCok)) return false;
    if (n < 0 && E.sefer <= 0) return false;
    E.sefer = Math.max(0, yeni);
    return true;
  },
  // Gün sonu: seferdekiler döner. Tahminde (uygula = false) hiçbir şey dönmez.
  seferSonu(E, oyun, uygula) {
    if (!uygula || E.sefer <= 0) return null;
    if (E.sefer < SEFER.enAz) return null; // tek kişi gitmez: işine döner
    const risk = this.seferRiski(E, oyun);
    let olen = 0;
    for (let i = 0; i < E.sefer; i++) if (Math.random() < risk) olen++;
    const donen = E.sefer - olen;
    const carpan = (1 + SEFER.seviyeBonus * (E.yapi.ahir.seviye - 1)) * (1 + SEFER.gunBonus * oyun.dalga);
    const ganimet = {};
    for (const [k, v] of Object.entries(SEFER.ganimet)) {
      const n = Math.round(donen * v * carpan * (0.6 + Math.random() * 0.8));
      if (n > 0) ganimet[k] = n;
    }
    const liste = Object.entries(ganimet).map(([k, v]) => `${v} ${k === 'altin' ? 'altın' : KAYNAKLAR[k].ad.toLowerCase()}`).join(', ');
    const yazi = `Sefer döndü: ${liste || 'eli boş'}.` + (olen ? ` ${olen} kişi dönmedi.` : '');
    return { ganimet, olen, gonderilen: E.sefer, yazi };
  },

  // ---------- İç kale sahnesi ----------
  // Süs olarak çizilmiş yapıları tıklanır yapar ve üstlerine ad yazar
  kur(sahne) {
    for (const k of Object.keys(YAPILAR)) {
      const sp = sahne.children.list.find(c => c.texture && c.texture.key === 'ks_ic2/' + k);
      if (!sp) continue;
      sp.setInteractive({ pixelPerfect: true, useHandCursor: true })
        .on('pointerover', () => sahne.etiket[k].setColor('#ffe08a'))
        .on('pointerout', () => sahne.etiket[k].setColor(sahne.secili === k ? '#ffe08a' : '#efe6d2'))
        .on('pointerdown', () => sahne.sec(k));
      // Ad binanın üstüne yazılır (kışla eskiden oduncunun altında kaldığı için alta yazılıyordu)
      const alta = false;
      sahne.etiket[k] = sahne.add.text(sp.x - (alta ? 40 : 0), alta ? sp.y + 6 : sp.y - sp.displayHeight + 2, '',
        stil('govde', DOKUNMATIK ? 28 : 22, { fontStyle: 'bold', backgroundColor: '#1a1410cc', padding: { x: 8, y: 3 } }))
        .setOrigin(0.5, alta ? 0 : 1).setDepth(90);
    }
  },
  etiketYenile(sahne) {
    const E = sahne.E;
    const yazi = {
      sapel: `Şapel  ${E.yapi.sapel.isci}/${this.rahipYeri(E)}`,
      kisla: E.yapi.kisla.seviye ? `Kışla ${E.yapi.kisla.seviye}` : 'Kışla (boş)',
      ahir: E.sefer ? `Ahır · seferde ${E.sefer}` : 'Ahır',
    };
    for (const k in yazi) if (sahne.etiket[k]) sahne.etiket[k].setText(yazi[k]);
  },

  // Sağdaki panel (kale.js panelKur içinden)
  panel(sahne, p, k) {
    const E = sahne.E, o = sahne.oyun, Y = YAPILAR[k];
    const sv = p.yazi(p.ust, '', 30, '#c9a24a', { fontStyle: 'bold' });
    p.yazi(p.ust + 44, Y.aciklama, 24, '#c8bca4');
    const satirlar = [];
    if (k === 'sapel') {
      const ml = p.yazi(p.ust + 150, '', 30, '#efe6d2', { fontStyle: 'bold' });
      const rp = p.yazi(p.ust + 196, '', 26);
      p.dugme(-190, p.ust + 280, 110, 64, '−', () => this.rahipEkle(E, -1), 40);
      p.dugme(-60, p.ust + 280, 110, 64, '+', () => this.rahipEkle(E, 1), 40);
      const S = MORAL.solen;
      const sl = p.dugme(-40, p.ust + 370, 440, 64, '', () => this.solen(E, o) && o.sesCal('coin', 0.5), 24);
      satirlar.push(() => {
        const c = E.moralCarpani;
        ml.setText(`Moral ${Math.round(E.moral)} / 100   ·   üretim ×${c.toFixed(2)}`);
        ml.setColor(E.moral < MORAL.siginmaciAlt ? '#ff9a7a' : E.moral >= 70 ? '#a0e0a0' : '#efe6d2');
        rp.setText(`Rahip: ${E.yapi.sapel.isci} / ${this.rahipYeri(E)}  (günde +${this.rahipMorali(E)} moral, boşta ${E.bosta})`);
        const olur = !E.solenYapildi && E.kaynak.yiyecek >= S.yiyecek && o.altin >= S.altin && E.moral < 100;
        sl.yazi.setText(E.solenYapildi ? 'Bugün şölen verildi' : `Şölen: +${S.moral} moral · ${S.yiyecek} yiyecek, ${S.altin} altın`)
          .setColor(olur ? '#ffd76a' : '#7a7060');
      });
      p.yazi(p.ust + 420, 'Açlık, ölüm, barikat ve yıkık sur morali düşürür. Moral 25\'in altına inerse sığınmacı gelmez.', 22, '#a89c84');
    } else if (k === 'kisla') {
      const t = p.yazi(p.ust + 150, '', 28, '#efe6d2', { fontStyle: 'bold' });
      satirlar.push(() => {
        const sv = E.yapi.kisla.seviye;
        t.setText(sv ? `Askerler %${Math.round(KISLA.hiz * sv * 100)} hızlı, %${Math.round(KISLA.hasar * sv * 100)} sert atar.\n${sv * KISLA.yatak} kişilik yatak.`
          : 'Kışla boş. Kurunca askerler daha\nhızlı atar ve 4 kişi daha barınır.');
      });
    } else if (k === 'ahir') {
      const t = p.yazi(p.ust + 150, '', 28, '#efe6d2', { fontStyle: 'bold' });
      const r = p.yazi(p.ust + 196, '', 24, '#c8bca4');
      p.dugme(-190, p.ust + 290, 110, 64, '−', () => this.seferAyarla(E, o, -1), 40);
      p.dugme(-60, p.ust + 290, 110, 64, '+', () => this.seferAyarla(E, o, 1), 40);
      satirlar.push(() => {
        if (!this.seferAcik(o)) { t.setText(`Sefer ${SEFER.ilkGun}. günden sonra açılır.`); r.setText(''); return; }
        t.setText(`Sefere gidecek: ${E.sefer} kişi  (boşta ${E.bosta})`);
        r.setText(`${SEFER.enAz}-${SEFER.enCok} kişi gider, ertesi gün döner. Kişi başı kayıp riski %${Math.round(this.seferRiski(E, o) * 100)}.` +
          (E.sefer > 0 && E.sefer < SEFER.enAz ? `\nEn az ${SEFER.enAz} kişi gerek.` : ''));
        r.setColor(E.sefer > 0 && E.sefer < SEFER.enAz ? '#ff9a7a' : '#c8bca4');
      });
    }
    satirlar.push(sahne.yukseltSatiri(p, p.ust + (k === 'sapel' ? 530 : 470), () => this.yukseltBedeli(E, k), t => this.yukselt(E, k, o, t) && o.sesCal('level_up', 0.4)));
    sahne.panelYenile = () => {
      const s = E.yapi[k].seviye;
      sv.setText(s ? `Seviye ${s}` : 'Kurulmadı');
      for (const f of satirlar) f();
    };
  },
};
