import cv2, numpy as np, glob, sys, json
out={}
for n,f in enumerate(sorted(glob.glob('rocket2/*.mkv')),1):
    cap=cv2.VideoCapture(f); fps=cap.get(cv2.CAP_PROP_FPS); N=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); step=int(round(fps/4)); s=''; rows=[]
    i=0
    while True:
        ok=cap.grab()
        if not ok: break
        if i%step==0:
            ok,fr=cap.retrieve(); g=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY)
            inset = g[100:1000,-6:].mean()<10 or g[100:1000,:6].mean()<10 or g[:14,200:1700].mean()<25
            hsv=cv2.cvtColor(fr[900:955,1530:1905],cv2.COLOR_BGR2HSV); wm=((hsv[...,2]>236)&(hsv[...,1]<14)).mean()
            band=g[940:1075,100:1820]; rowmax=(band>225).mean(1).max()     # player progress bar
            dark = g.mean()<45
            split = g[200:900,:40].mean()<8 and g[40:160,300:1600].mean()<8   # cutaway layout
            c = 'X' if (dark or split) else 'I' if inset else 'W' if wm>0.01 else 'P' if rowmax>0.5 else '.'
            s+=c; rows.append((round(i/fps,2),c,round(float(wm),3),round(float(rowmax),2)))
        i+=1
    out[n]=rows; print(n,f[-12:-4],len(s)); [print('  ',k*10//4,'s',s[k:k+40]) for k in range(0,len(s),40)]
json.dump(out,open('r2/scan.json','w'))
