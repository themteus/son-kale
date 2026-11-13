// =============================================================
//  KENAR (kenar.js)
//  Scale.FIT oyunu ekrana sığdırır; ekran 16:9 değilse yanlarda (ya da
//  altta/üstte) boşluk kalır. O boşluğu düz siyah bırakmak yerine oyunun
//  kendisinin küçük, bulanık ve koyu bir kopyasıyla doldururuz.
//  Kopya her çizimden hemen sonra alınır (WebGL tamponu henüz silinmemişken),
//  en çok saniyede 4 kez. Ekran tam 16:9 ise hiçbir şey yapılmaz.
// =============================================================

(() => {
  const kenar = document.getElementById('kenar');
  if (!kenar || typeof oyun === 'undefined') return;
  const ctx = kenar.getContext('2d');
  const ARALIK = 250;
  let son = 0;
  const bosVar = () => Math.abs(innerWidth / innerHeight - AYAR.en / AYAR.boy) > 0.02;
  oyun.events.on('postrender', () => {
    const t = performance.now();
    if (t - son < ARALIK || !bosVar() || !oyun.canvas) return;
    son = t;
    try { ctx.drawImage(oyun.canvas, 0, 0, kenar.width, kenar.height); } catch (e) { /* sessiz geç */ }
  });
})();
