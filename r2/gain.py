import cv2, numpy as np, glob, json
fs=sorted(glob.glob('rocket2/*.mkv')); scan=json.load(open('r2/scan.json'))
def norm(fr):
    g=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY)
    if g[100:1000,-6:].mean()<10 or g[:14,200:1700].mean()<25:
        M=np.float32([[1/0.9657,0,-33.02/0.9657],[0,1/0.9657,-39.72/0.9657]]); fr=cv2.warpAffine(fr,M,(1920,1080),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    return cv2.resize(fr[6:1074,11:1909],(1280,720),interpolation=cv2.INTER_AREA)
if __name__=="__main__":
    acc=np.zeros((720,1280),np.float64); n=0
    spans={1:(14.6,22.4),2:(0.4,33.6),3:(0.5,90.4),4:(8.5,62.0)}
    for c,(t0,t1) in spans.items():
        cap=cv2.VideoCapture(fs[c-1])
        for r in scan[str(c)][::2]:
            if t0<=r[0]<=t1 and r[1] in '.I':
                cap.set(cv2.CAP_PROP_POS_MSEC,r[0]*1000); ok,fr=cap.read()
                if ok: acc+=cv2.cvtColor(norm(fr),cv2.COLOR_BGR2GRAY); n+=1
    M=acc/n; mir=M[:,::-1]
    g=np.clip(M/np.maximum(mir,1),0.2,1.0); g[:, 640:]=1.0
    box=np.zeros((720,1280),np.uint8); box[20:118,0:238]=255
    g=cv2.inpaint((g*255).astype(np.uint8),box,9,cv2.INPAINT_TELEA).astype(np.float32)/255
    g=cv2.GaussianBlur(g,(0,0),6)
    np.save('r2/gain.npy',g); cv2.imwrite('r2/probe/gain.png',(g*255).astype(np.uint8)); cv2.imwrite('r2/probe/mean.png',M.astype(np.uint8))
    print(n,'frames'); print('gain rows 0..200 step 20 at x=30,150,300,450,600:'); [print(y,[round(float(g[y,x]),2) for x in (30,150,300,450,600)]) for y in range(0,220,20)]
