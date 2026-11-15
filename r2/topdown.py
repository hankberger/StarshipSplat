import os; os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import cv2, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fr=json.load(open('scene/operation.json'))['response']['frames']; names=[u['file'] for u in json.load(open('req/uploads.json'))]
clip=np.array([int(n.split('_c')[1][0]) for n in names])
def q2R(q):
    x,y,z,w=q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
cams=np.array([f['camera']['extrinsics']['position'] for f in fr]); fx=np.array([f['camera']['intrinsics']['fx'] for f in fr])
for c in (1,2,3,4): print('clip',c,'n',(clip==c).sum(),'fx',fx[clip==c].min().round(0),fx[clip==c].max().round(0),'y',cams[clip==c,1].min().round(1),cams[clip==c,1].max().round(1))
# nearest-surface point along each camera's centre ray region -> tower estimate
pts=[];cols=[]
fig,ax=plt.subplots(1,3,figsize=(27,9))
for i,f in enumerate(fr):
    c=f['camera']; K=c['intrinsics']; R=q2R(c['extrinsics']['quaternion']); t=np.array(c['extrinsics']['position'])
    if i%6==0:
        d=cv2.imread('scene/'+f['depth']['depthAsset']['path'],cv2.IMREAD_UNCHANGED); d=d if d.ndim==2 else d[...,0]
        img=cv2.imread('scene/'+f['imageAsset']['path'])[...,::-1]/255.
        v,u=np.mgrid[0:720:5,0:1280:5]; z=d[::5,::5]; ok=np.isfinite(z)&(z>0)&(z<np.nanpercentile(z[np.isfinite(z)],40))
        P=np.stack([(u-K['cx'])/K['fx']*z,-(v-K['cy'])/K['fy']*z,-z],-1)[ok]; W=P@R.T+t; pts.append(W); cols.append(img[::5,::5][ok])
W=np.concatenate(pts); C=np.concatenate(cols)
ctr=np.median(cams,axis=0); span=np.percentile(np.abs(cams-ctr),95)*2.2
m=(np.abs(W[:,0]-ctr[0])<span)&(np.abs(W[:,2]-ctr[2])<span)
ax[0].scatter(W[m,0],-W[m,2],s=.2,c=C[m]); ax[1].scatter(W[m,0],W[m,1],s=.2,c=C[m]); ax[2].scatter(-W[m,2],W[m,1],s=.2,c=C[m])
colr={1:'red',2:'orange',3:'magenta',4:'cyan'}
for i,f in enumerate(fr):
    t=cams[i]; fw=q2R(f['camera']['extrinsics']['quaternion'])@np.array([0,0,-1]); L=span*0.06
    ax[0].plot(t[0],-t[2],'.',color=colr[clip[i]]); ax[0].plot([t[0],t[0]+fw[0]*L],[-t[2],-t[2]-fw[2]*L],color=colr[clip[i]],lw=.6)
    ax[1].plot(t[0],t[1],'.',color=colr[clip[i]]); ax[2].plot(-t[2],t[1],'.',color=colr[clip[i]])
for a,tt in zip(ax,('top (x,-z)  red=clip1 orange=2 magenta=3 cyan=4','side (x,y)','side (-z,y)')): a.set_title(tt); a.set_aspect('equal'); a.grid(alpha=.3)
plt.tight_layout(); plt.savefig('probe/topdown.jpg',dpi=65)
np.save('probe/cams.npy',cams)
