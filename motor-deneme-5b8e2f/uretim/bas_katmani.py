# Okçu yukarı nişanda (-80..-35°) kol/yay başı örtüyordu: 0° germe-0 karesindeki baş
# (kukuleta + yüz) bu karelerin üstüne yeniden çizilir. Omuz tüm karelerde 150,134 sabit.
import sys
from PIL import Image
giris, cikis = sys.argv[1], sys.argv[2]
im = Image.open(giris).convert('RGBA')
A = list(range(-80, 81, 5)); FW = 300; SUT = im.width // FW
def kutu(i): return ((i % SUT) * FW, (i // SUT) * FW, (i % SUT) * FW + FW, (i // SUT) * FW + FW)
kaynak = im.crop(kutu(A.index(0)))           # germe 0, 0°
X0, Y0, X1, Y1 = 130, 76, 182, 121
bas = Image.new('RGBA', (FW, FW))
px = kaynak.load(); bp = bas.load()
for y in range(Y0, Y1):
    for x in range(X0, X1):
        r, g, b, a = px[x, y]
        if a > 0: bp[x, y] = (r, g, b, a)
for sira in range(3):
    for a in A:
        if a > -35: continue
        i = sira * 33 + A.index(a)
        fr = im.crop(kutu(i)); fr.alpha_composite(bas); im.paste(fr, kutu(i)[:2])
im.save(cikis)
