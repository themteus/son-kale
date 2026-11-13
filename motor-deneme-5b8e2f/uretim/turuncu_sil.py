# Gece varyantlarında çatı kenarı / tarla / çalı üzerindeki yanlış turuncu parıltıyı söner.
# Turuncu piksel, gündüz görselindeki karşılığı da sıcak renkliyse (ahşap, saman, buğday)
# gündüz pikselinin gece dönüşümüyle değiştirilir; pencere ışıkları (gündüzde soğuk cam) kalır.
import sys, colorsys
import numpy as np
from PIL import Image
kok, cikis = sys.argv[1], sys.argv[2]
def hsv(c): return colorsys.rgb_to_hsv(*(v/255 for v in c[:3]))
def turuncu(c, s0=0.4, v0=0.4):
    h,s,v=hsv(c); return 0.05<h<0.18 and s>s0 and v>v0
def sicak(c):
    h,s,v=hsv(c); return (0.0<=h<0.2) and s>0.2
for ad in sys.argv[3:]:
    g=np.array(Image.open(f'{kok}/varyant/{ad}_gece.png').convert('RGBA')).astype(float)
    b=np.array(Image.open(f'{kok}/{ad}.png').convert('RGBA')).astype(float)
    H,W=g.shape[:2]
    mask=np.zeros((H,W),bool)
    for y in range(H):
        for x in range(W):
            if g[y,x,3]>100 and b[y,x,3]>100 and turuncu(g[y,x]) and sicak(b[y,x]): mask[y,x]=True
    # gece = A*gündüz + c (kanal başına), turuncu olmayan opak piksellerden
    ok=(g[...,3]>200)&(b[...,3]>200)&~mask
    out=g.copy()
    for k in range(3):
        A=np.vstack([b[ok][:,k],np.ones(ok.sum())]).T
        m,c=np.linalg.lstsq(A,g[ok][:,k],rcond=None)[0]
        out[mask,k]=np.clip(b[mask,k]*m+c,0,255)
    # kalan sıcak (pas gibi) tonu gece mavisine çek: doygunluğu azalt, hafif soğut
    l=out[mask,:3].mean(axis=1,keepdims=True)
    out[mask,:3]=np.clip(l+(out[mask,:3]-l)*0.35+np.array([-3,0,6]),0,255)
    Image.fromarray(out.astype(np.uint8)).save(f'{cikis}/{ad}_gece.png')
    print(ad, int(mask.sum()))
