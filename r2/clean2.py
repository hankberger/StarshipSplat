"""Keep depth only where it lands on the ground or on structure seen in the sharp, ground-backed frames."""
import os, sys; os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import cv2, json, numpy as np
V=0.5
def q2R(q):
    x,y,z,w=q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def load(folder,f):
    d=cv2.imread(f'{folder}/'+f['depth']['depthAsset']['path'],cv2.IMREAD_UNCHANGED); d=(d if d.ndim==2 else d[...,0]).astype(np.float32)
    K=f['camera']['intrinsics']; R=q2R(f['camera']['extrinsics']['quaternion']); t=np.array(f['camera']['extrinsics']['position'])
    v,u=np.mgrid[0:720,0:1280]; x=(u-K['cx'])/K['fx']; y=-(v-K['cy'])/K['fy']
    diry=R[1,0]*x+R[1,1]*y-R[1,2]; ok=np.isfinite(d)&(d>0); z=np.where(ok,d,0)
    W=np.stack([x*z,y*z,-z],-1)@R.T+t
    return d,ok,W,diry
def build(folder,fr):
    pts=[];n=0
    for f in fr:
        d,ok,W,diry=load(folder,f)
        if (diry>0).mean()>0.03: continue
        n+=1; m=ok&(d<70)&(W[...,1]>2.0); pts.append(W[m][::2].astype(np.float32))
    P=np.concatenate(pts); q=np.unique(np.round(P/0.08).astype(np.int32),axis=0); P=(q*0.08).astype(np.float32)
    print('sharp frames',n,'proxy points',len(P)); return P
def clean(folder,f,P):
    d,ok,W,diry=load(folder,f)
    K=f['camera']['intrinsics']; R=q2R(f['camera']['extrinsics']['quaternion']); t=np.array(f['camera']['extrinsics']['position'])
    pc=(P-t)@R; z=-pc[:,2]; m=z>0.5
    u=np.round(K['cx']+K['fx']*pc[m,0]/z[m]).astype(int); v=np.round(K['cy']-K['fy']*pc[m,1]/z[m]).astype(int); z=z[m]
    inb=(u>=0)&(u<1280)&(v>=0)&(v<720); zb=np.full(720*1280,np.inf,np.float32); np.minimum.at(zb,v[inb]*1280+u[inb],z[inb]); zb=zb.reshape(720,1280)
    zb=cv2.erode(zb,np.ones((5,5),np.uint8))            # min-filter: fill gaps between projected points
    dist=np.linalg.norm(W-t,axis=-1)
    ground=ok&(W[...,1]<2.0+0.03*dist)&(diry<-0.002)
    struct=ok&np.isfinite(zb)&(np.abs(d-zb)<np.maximum(1.0,0.06*zb))
    out=np.where(ground|struct,d,np.nan).astype(np.float32); return d,ok,out
if __name__=="__main__":
    folder=sys.argv[1]; fr=json.load(open(f'{folder}/operation.json'))['response']['frames']
    occ=build('scene',json.load(open('scene/operation.json'))['response']['frames']) if not os.path.exists('proxy.npy') else np.load('proxy.npy'); np.save('proxy.npy',occ)
    os.makedirs(f'{folder}/clean',exist_ok=True); tiles=[]; show=set(int(x) for x in sys.argv[2].split(',')) if len(sys.argv)>2 else set()
    for i,f in enumerate(fr):
        d,ok,out=clean(folder,f,occ)
        cv2.imwrite(f'{folder}/clean/depth_{i:03d}.exr',out,[cv2.IMWRITE_EXR_TYPE,cv2.IMWRITE_EXR_TYPE_HALF])
        if i in show:
            img=cv2.imread(f'{folder}/'+f['imageAsset']['path']); vis=img.copy(); bad=~np.isfinite(out); vis[bad]=(vis[bad]*0.25).astype(np.uint8)
            tiles.append(cv2.resize(vis,(640,360))); print(i,'valid',ok.mean().round(2),'->',np.isfinite(out).mean().round(2))
    if tiles: cv2.imwrite(f'probe/clean_{folder}.jpg',np.vstack([np.hstack(tiles[k:k+3]) for k in range(0,len(tiles),3)]))
