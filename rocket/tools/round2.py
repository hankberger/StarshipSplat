import sys, json; sys.path.insert(0,'tools'); from camlib import *
fr=real(); v1=json.load(open('views1/operation.json'))['response']['frames']
targets=[orbit(-135),orbit(-170),orbit(128),orbit(165), cam([C[0]-28,15,C[2]+4],[C[0],6,C[2]])]
json.dump({"contextFrames":[ctx(f) for f in v1]+[ctx(fr[i]) for i in (0,16,32)],"targetCameras":targets,"returnDepth":True},open('req/round2.json','w'),indent=1)
