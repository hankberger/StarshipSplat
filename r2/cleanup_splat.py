import numpy as np, sys; import spz
d=spz.read('splats/refinedSplats_2000000.spz'); P=spz.positions(d); S=spz.scales(d).max(1)
AX=np.array([0.56,0.88]); dist=np.linalg.norm(P[:,[0,2]]-AX,axis=1); y=P[:,1]
V=0.5; prox=np.load('proxy.npy')
def key(Q): q=np.floor(Q/V).astype(np.int64); return (q[:,0]+2000)*16000000+(q[:,1]+2000)*4000+(q[:,2]+2000)
occ=np.unique(np.concatenate([key(prox+np.array([dx,dy,dz])) for dx in (-V,0,V) for dy in (-V,0,V) for dz in (-V,0,V)]))
struct=np.isin(key(P),occ)
ground=(y>-2.5)&(y<2.5+0.02*dist)
rgb=((d['color'].astype(np.float32)/255-0.5)/0.15*0.282+0.5)*255
skyc=np.array([152.,167.,176.])
far=(dist>120)&(y>-2.5)&~ground
far&=(rgb.mean(1)>90)&((rgb.max(1)-rgb.min(1))<32)&(S<25)
import json
def q2R(q):
    x,yy,z,w=q; return np.array([[1-2*(yy*yy+z*z),2*(x*yy-z*w),2*(x*z+yy*w)],[2*(x*yy+z*w),1-2*(x*x+z*z),2*(yy*z-x*w)],[2*(x*z-yy*w),2*(yy*z+x*w),1-2*(x*x+yy*yy)]])
seen=np.zeros(len(P),np.int32)
for f in json.load(open('scene/operation.json'))['response']['frames']:
    c=f['camera']; K=c['intrinsics']; pc=(P-np.array(c['extrinsics']['position'],np.float32))@q2R(c['extrinsics']['quaternion']).astype(np.float32); z=-pc[:,2]
    with np.errstate(divide='ignore',invalid='ignore'):
        u=K['cx']+K['fx']*pc[:,0]/z; v=K['cy']-K['fy']*pc[:,1]/z
    seen+=((z>0.3)&(u>=0)&(u<1280)&(v>=0)&(v<720))
covered=(dist<50)|(seen>=8)
print('uncovered beyond 50:',(~covered).sum())
keep=(ground|struct)&~((S>6)&(dist<120))&covered
sat=rgb.max(1)-rgb.min(1)
speck=(dist>80)&(y>0.5+0.005*dist)&((sat>26)|(rgb.mean(1)>200)|(rgb.mean(1)<45)|(S>4)|(d['alpha'][:,0]<50))
keep&=~speck; print('speckles removed',speck.sum())
tw=(dist<7)&(y>2)&(y<19)
print('keep',keep.sum(),'of',len(P),'| struct',struct.sum(),'ground',ground.sum(),'far',far.sum())
print('tower cylinder: total',tw.sum(),'kept',(tw&keep).sum(),'removed',(tw&~keep).sum())
rm=~keep; print('removed: near-air',(rm&(dist<120)&(y>=2.5+0.02*dist)).sum(),'underground',(rm&(y<=-2.5)).sum())
c=(d['color'][far&(y>15)].astype(np.float32)/255-0.5)/0.15*0.282+0.5; print('far sky colour',(c.mean(0)*255).round(0) if len(c) else None)
import os; os.makedirs('../rocket/splats_r2',exist_ok=True)
print('wrote',spz.write('../rocket/splats_r2/cleaned.spz',d,keep))
