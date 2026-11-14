import os; os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import cv2, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fr=json.load(open('scene/operation.json'))['response']['frames']
def q2R(q):
    x,y,z,w=q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
fig,ax=plt.subplots(1,3,figsize=(27,9))
stats=[]
for i,f in enumerate(fr):
    c=f['camera']; K=c['intrinsics']; R=q2R(c['extrinsics']['quaternion']); t=np.array(c['extrinsics']['position'])
    d=cv2.imread('scene/'+f['depth']['depthAsset']['path'],cv2.IMREAD_UNCHANGED); d=d if d.ndim==2 else d[...,0]
    img=cv2.imread('scene/'+f['imageAsset']['path'])[...,::-1]/255.
    v,u=np.mgrid[0:720:6,0:1280:6]; z=d[::6,::6]; ok=np.isfinite(z)&(z>0)
    stats.append((i,round(float(ok.mean()),2),round(float(np.nanmin(z[ok])),1),round(float(np.nanmedian(z[ok])),1),round(float(np.nanmax(z[ok])),1), round(float(d[300:420,600:680][np.isfinite(d[300:420,600:680])].mean()),1) if np.isfinite(d[300:420,600:680]).any() else None))
    if i%4: continue
    P=np.stack([(u-K['cx'])/K['fx']*z,-(v-K['cy'])/K['fy']*z,-z],-1)[ok]; W=P@R.T+t; col=img[::6,::6][ok]
    ax[0].scatter(W[:,0],-W[:,2],s=.3,c=col); ax[1].scatter(W[:,0],W[:,1],s=.3,c=col)
    near=np.linalg.norm(W-t,axis=1)<60
    ax[2].scatter(W[near,0],-W[near,2],s=.5,c=col[near])
for f in fr:
    t=f['camera']['extrinsics']['position']; fw=q2R(f['camera']['extrinsics']['quaternion'])@np.array([0,0,-1])
    for a in (ax[0],ax[2]): a.plot(t[0],-t[2],'r.'); a.arrow(t[0],-t[2],fw[0]*3,-fw[2]*3,color='r',width=.05)
    ax[1].plot(t[0],t[1],'r.')
ax[0].set_title('top (x, -z)'); ax[1].set_title('side (x, y)'); ax[2].set_title('top, within 60 units'); 
for a in ax: a.set_aspect('equal'); a.grid(alpha=.3)
plt.tight_layout(); plt.savefig('probe/topdown.jpg',dpi=70)
print('i valid min med max centerdepth'); [print(*s) for s in stats[::3]]
