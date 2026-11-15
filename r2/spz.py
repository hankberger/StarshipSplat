import gzip, struct, numpy as np
def read(path):
    raw=gzip.open(path,'rb').read()
    magic,ver,n,shd,frac,flags,res=struct.unpack('<IIIBBBB',raw[:16])
    assert magic==0x5053474e, hex(magic)
    shdim={0:0,1:3,2:8,3:15}[shd]; rot=4 if ver>=3 else 3
    sizes=[('pos',9),('alpha',1),('color',3),('scale',3),('rot',rot),('sh',shdim*3)]
    assert len(raw)==16+n*sum(s for _,s in sizes), (len(raw),n,ver,shd)
    d={'ver':ver,'shd':shd,'frac':frac,'flags':flags,'n':n}; o=16
    for k,s in sizes:
        d[k]=np.frombuffer(raw,np.uint8,n*s,o).reshape(n,s) if s else np.zeros((n,0),np.uint8); o+=n*s
    return d
def positions(d):
    p=d['pos'].reshape(-1,3,3).astype(np.int32); v=p[...,0]|(p[...,1]<<8)|(p[...,2]<<16); v=np.where(v&0x800000,v-0x1000000,v)
    return v.astype(np.float32)/(1<<d['frac'])
def scales(d): return np.exp(d['scale'].astype(np.float32)/16-10)
def write(path,d,keep):
    n=int(keep.sum()); hdr=struct.pack('<IIIBBBB',0x5053474e,d['ver'],n,d['shd'],d['frac'],d['flags'],0)
    body=b''.join(d[k][keep].tobytes() for k in ('pos','alpha','color','scale','rot','sh'))
    with gzip.open(path,'wb',compresslevel=6) as f: f.write(hdr+body)
    return n
if __name__=="__main__":
    import sys; d=read(sys.argv[1]); P=positions(d); S=scales(d); a=d['alpha'][:,0]
    print({k:d[k] for k in ('ver','shd','frac','flags','n')})
    print('pos pct x',np.percentile(P[:,0],[0,1,50,99,100]).round(1)); print('pos pct y',np.percentile(P[:,1],[0,1,10,50,90,99,100]).round(1)); print('pos pct z',np.percentile(P[:,2],[0,1,50,99,100]).round(1))
    dist=np.linalg.norm(P[:,[0,2]]-np.array([0.56,0.88]),axis=1); print('horiz dist pct',np.percentile(dist,[10,50,90,99,100]).round(1))
    print('max scale pct',np.percentile(S.max(1),[50,90,99,99.9,100]).round(2),'alpha pct',np.percentile(a,[10,50,90]))
    for lo,hi in ((0,30),(30,80),(80,200),(200,1e9)):
        m=(dist>=lo)&(dist<hi); print(f'dist {lo}-{hi}: n={m.sum()}  y pct',np.percentile(P[m,1],[5,50,95]).round(1) if m.any() else None)
