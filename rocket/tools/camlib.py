import json, numpy as np
C=np.array([-5.34, 9.0, 1.2])
K={"width":1280,"height":720,"fx":1461.0,"fy":1461.0,"cx":640,"cy":360}
def lookat(pos, target, up=(0,1,0)):
    pos=np.array(pos,float); b=pos-np.array(target,float); b/=np.linalg.norm(b)
    r=np.cross(up,b); r/=np.linalg.norm(r); u=np.cross(b,r)
    R=np.stack([r,u,b],1); return mat2q(R)
def mat2q(R):
    t=np.trace(R)
    if t>0: s=np.sqrt(t+1)*2; q=[(R[2,1]-R[1,2])/s,(R[0,2]-R[2,0])/s,(R[1,0]-R[0,1])/s,s/4]
    elif R[0,0]>R[1,1] and R[0,0]>R[2,2]: s=np.sqrt(1+R[0,0]-R[1,1]-R[2,2])*2; q=[s/4,(R[0,1]+R[1,0])/s,(R[0,2]+R[2,0])/s,(R[2,1]-R[1,2])/s]
    elif R[1,1]>R[2,2]: s=np.sqrt(1+R[1,1]-R[0,0]-R[2,2])*2; q=[(R[0,1]+R[1,0])/s,s/4,(R[1,2]+R[2,1])/s,(R[0,2]-R[2,0])/s]
    else: s=np.sqrt(1+R[2,2]-R[0,0]-R[1,1])*2; q=[(R[0,2]+R[2,0])/s,(R[1,2]+R[2,1])/s,s/4,(R[1,0]-R[0,1])/s]
    return [float(x) for x in q]
def orbit(ang_deg, r=19.5, y=9.0, target=None, k=None):
    a=np.radians(ang_deg); pos=[C[0]+r*np.cos(a), y, C[2]+r*np.sin(a)]
    return cam(pos, C if target is None else target, k)
def cam(pos, target, k=None):
    return {"extrinsics":{"position":[float(x) for x in pos],"quaternion":lookat(pos,target),"coordinateSystem":"rub"},"intrinsics":k or K}
def ctx(f):
    return {"imageAsset":{"assetId":f['imageAsset']['assetId']},"depth":{"depthAsset":{"assetId":f['depth']['depthAsset']['assetId']}},"camera":f['camera']}
def real(): return json.load(open('scene/operation.json'))['response']['frames']
