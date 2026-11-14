import sys, json; sys.path.insert(0,'tools'); from camlib import *
fr=real()
# sanity: lookat for real cam 16 vs its own quaternion
print('real q16',[round(x,3) for x in fr[16]['camera']['extrinsics']['quaternion']],'lookat',[round(x,3) for x in lookat(fr[16]['camera']['extrinsics']['position'],C)])
targets=[orbit(-62),orbit(-97),orbit(55),orbit(90), cam([C[0]+30,16,C[2]-3],[C[0],6,C[2]]), cam([C[0]+13,3.5,C[2]+2],[C[0],8,C[2]])]
json.dump({"contextFrames":[ctx(f) for f in fr[::4]],"targetCameras":targets,"returnDepth":True},open('req/round1.json','w'),indent=1)
