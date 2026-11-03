// =============================================================
//  BAŞLAT (main.js)
//  Phaser oyununu kurar: 1920x1080 sahne, ekrana sığacak şekilde
//  ölçeklenir, piksel görünüm (bulanıklık yok).
// =============================================================

const oyun = new Phaser.Game({
  type: Phaser.WEBGL,
  parent: 'oyun',
  width: AYAR.en,
  height: AYAR.boy,
  backgroundColor: '#0d0b10',
  pixelArt: true,
  scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
  input: { activePointers: 3 },
  scene: [YukleSahnesi, SavasSahnesi],
});
