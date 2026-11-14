"""Clean posed frames: remove depth from sky, from background seen through/around the tower, and mask vapour."""
import os, sys; os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import cv2, json, numpy as np
NEAR=35.0
def q2R(q):
    x,y,z,w=q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def clean(folder, f, vapour=False):
    img=cv2.imread(f'{folder}/'+f['imageAsset']['path'])
    d=cv2.imread(f'{folder}/'+f['depth']['depthAsset']['path'],cv2.IMREAD_UNCHANGED); d=(d if d.ndim==2 else d[...,0]).astype(np.float32)
    K=f['camera']['intrinsics']; R=q2R(f['camera']['extrinsics']['quaternion'])
    v,u=np.mgrid[0:720,0:1280]; diry=(R[1,0]*(u-K['cx'])/K['fx']+R[1,1]*(-(v-K['cy'])/K['fy'])-R[1,2])
    ok=np.isfinite(d)&(d>0); near=ok&(d<NEAR)
    out=d.copy(); out[~ok]=np.nan
    out[(diry>0.004)&~near]=np.nan                       # sky is not a surface
    k=np.ones((3,3),np.uint8)
    blob=cv2.dilate(near.astype(np.uint8),k,iterations=6)
    small=cv2.resize(img,(320,180),interpolation=cv2.INTER_AREA); bs=cv2.resize(blob,(320,180),interpolation=cv2.INTER_NEAREST)
    bg=cv2.resize(cv2.inpaint(small,bs,5,cv2.INPAINT_TELEA),(1280,720),interpolation=cv2.INTER_CUBIC)
    diff=np.abs(cv2.GaussianBlur(img,(0,0),1.2).astype(int)-bg.astype(int)).max(-1)
    bglike=cv2.morphologyEx((diff<16).astype(np.uint8),cv2.MORPH_OPEN,k)
    out[near&(bglike>0)&(diry>-0.10)]=np.nan                          # background showing through or around the structure
    keep=cv2.erode((np.isfinite(out)&near).astype(np.uint8),k,iterations=1)>0
    out[near&~keep]=np.nan                               # trim silhouette edges
    alpha=np.full(d.shape,255,np.uint8)
    if vapour:
        t=np.array(f['camera']['extrinsics']['position']); ang=np.linspace(0,2*np.pi,48)
        pts=np.array([[-5.3+5.0*np.cos(a),y,1.0+5.0*np.sin(a)] for a in ang for y in (7.55,8.25)])
        pc=(pts-t)@R; uv=np.stack([K['cx']+K['fx']*pc[:,0]/-pc[:,2],K['cy']-K['fy']*pc[:,1]/-pc[:,2]],1)
        m=np.zeros(d.shape,np.uint8); cv2.fillConvexPoly(m,cv2.convexHull(uv.astype(np.int32)),1); vap=m>0
        alpha[vap]=0; out[vap]=np.nan
    return img,d,out,alpha
if __name__=="__main__":
    folder=sys.argv[1]; vap_idx=set(range(0,14)) if folder=='scene' else set()
    fr=json.load(open(f'{folder}/operation.json'))['response']['frames']; os.makedirs(f'{folder}/clean',exist_ok=True); tiles=[]
    for i,f in enumerate(fr):
        img,d,out,alpha=clean(folder,f,i in vap_idx)
        cv2.imwrite(f'{folder}/clean/depth_{i:02d}.exr',out,[cv2.IMWRITE_EXR_TYPE,cv2.IMWRITE_EXR_TYPE_HALF])
        cv2.imwrite(f'{folder}/clean/mask_{i:02d}.png',alpha)
        if i%max(1,len(fr)//5)==0:
            vis=img.copy(); vis[~np.isfinite(out)]=(vis[~np.isfinite(out)]*0.25).astype(np.uint8); vis[alpha==0]=(0,0,255)
            tiles.append(np.hstack([cv2.resize(img,(640,360)),cv2.resize(vis,(640,360))]))
        print(i,'valid before',round(float((np.isfinite(d)&(d>0)).mean()),2),'after',round(float(np.isfinite(out).mean()),2),'masked',round(float((alpha==0).mean()),3))
    cv2.imwrite(f'probe/clean_{folder}.jpg',np.vstack(tiles))
