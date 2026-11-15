import cv2, numpy as np, glob, json, os
fs=sorted(glob.glob('rocket2/*.mkv')); scan=json.load(open('r2/scan.json'))
plan={1:(14.6,22.4,0.8),2:(0.4,33.6,1.0),3:(0.5,90.4,1.5),4:(8.5,62.0,1.3)}
os.makedirs('r2/frames',exist_ok=True)
for old in glob.glob('r2/frames/*.jpg'): os.remove(old)
gain=np.load('r2/gain.npy')
tagmask=np.zeros((720,1280),np.uint8); tagmask[32:106,0:224]=255
n=0; log=[]
for c,(t0,t1,dt) in plan.items():
    rows=scan[str(c)]; cap=cv2.VideoCapture(fs[c-1])
    for t in np.arange(t0,t1,dt):
        cand=sorted(rows,key=lambda r:abs(r[0]-t))
        pick=next((r for r in cand if r[1] in '.I' and abs(r[0]-t)<=dt/2),None)
        if not pick: log.append((c,round(float(t),1),'skipped')); continue
        cap.set(cv2.CAP_PROP_POS_MSEC,pick[0]*1000); ok,fr=cap.read()
        if not ok: continue
        g=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY)
        inset = g[100:1000,-6:].mean()<10 or g[:14,200:1700].mean()<25
        if inset:
            M=np.float32([[1/0.9657,0,-33.02/0.9657],[0,1/0.9657,-39.72/0.9657]])
            fr=cv2.warpAffine(fr,M,(1920,1080),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        fr=cv2.resize(fr[6:1074,11:1909],(1280,720),interpolation=cv2.INTER_AREA)   # trim recording border evenly
        fr=np.clip(fr.astype(np.float32)/gain[...,None],0,255).astype(np.uint8)
        fr=cv2.inpaint(fr,tagmask,5,cv2.INPAINT_TELEA)
        cv2.imwrite(f'r2/frames/f{n:03d}_c{c}_{pick[0]:06.2f}{"i" if inset else ""}.jpg',fr,[cv2.IMWRITE_JPEG_QUALITY,95]); n+=1
print(n,'frames; skipped:',log)
