"""Remove sky-coloured splats (bright and bluish) that sit above the ground."""
import numpy as np, spz, sys
BR,BL=float(sys.argv[1]) if len(sys.argv)>1 else 115, float(sys.argv[2]) if len(sys.argv)>2 else 9
d=spz.read('../rocket/splats_r2/cleaned_disc.spz'); P=spz.positions(d)
rgb=((d['color'].astype(np.float32)/255-0.5)/0.15*0.282+0.5)*255
sky=(P[:,1]>2.5)&(rgb.mean(1)>BR)&((rgb[:,2]-rgb[:,0])>BL)
print('removed',sky.sum(),'kept',spz.write('../rocket/splats_r2/cleaned_disc_nosky.spz',d,~sky))
