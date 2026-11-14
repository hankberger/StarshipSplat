import os; os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import cv2, json, numpy as np
fr=json.load(open('scene/operation.json'))['response']['frames']
def q2R(q):
    x,y,z,w=q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
pts=[]
for f in fr[::2]:
    c=f['camera']; K=c['intrinsics']; R=q2R(c['extrinsics']['quaternion']); t=np.array(c['extrinsics']['position'])
    d=cv2.imread('scene/'+f['depth']['depthAsset']['path'],cv2.IMREAD_UNCHANGED); d=d if d.ndim==2 else d[...,0]
    v,u=np.mgrid[0:720:3,0:1280:3]; z=d[::3,::3]; ok=np.isfinite(z)&(z>0)&(z<30)
    P=np.stack([(u-K['cx'])/K['fx']*z,-(v-K['cy'])/K['fy']*z,-z],-1)[ok]; pts.append(P@R.T+t)
W=np.concatenate(pts); print('near pts',len(W))
for a,n in zip(range(3),'xyz'): print(n,np.percentile(W[:,a],[1,5,25,50,75,95,99]).round(1))
cams=np.array([f['camera']['extrinsics']['position'] for f in fr])
c=np.median(W,axis=0); print('center',c.round(2))
r=np.linalg.norm((cams-c)[:,[0,2]],axis=1); ang=np.degrees(np.arctan2(cams[:,2]-c[2],cams[:,0]-c[0]))
print('radius',r.round(1)[::4]); print('angle',ang.round(1)[::4]); print('cam y',cams[:,1].round(1)[::8])
# ground height near tower: points 30-80 away
