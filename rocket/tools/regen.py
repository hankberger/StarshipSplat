import sys, json; sys.path.insert(0,'tools'); from camlib import *
PROMPT="Aerial drone photograph of a tall steel lattice rocket launch tower holding a dark stainless steel rocket booster in its two mechanical arms, standing on flat coastal tidal marshland beside the ocean under an overcast grey sky. Clear, still air with sharp detail."
fr=real(); cl=[l.split() for l in open('req/clean_real.txt')]
def cctx(i):
    f=fr[i]; return {"imageAsset":{"assetId":f['imageAsset']['assetId']},"depth":{"depthAsset":{"assetId":cl[i][1]}},"camera":f['camera']}
rnd=sys.argv[1]
if rnd=='1':
    context=[cctx(i) for i in (14,17,20,23,26,29,32)]
    targets=[orbit(-62),orbit(-97),orbit(55),orbit(90), cam([C[0]+30,16,C[2]-3],[C[0],6,C[2]]), cam([C[0]+13,3.5,C[2]+2],[C[0],8,C[2]])]
else:
    v=json.load(open('views1b/operation.json'))['response']['frames']; ids=[l.split()[1] for l in open('req/clean_v1b.txt')]
    context=[{"imageAsset":{"assetId":f['imageAsset']['assetId']},"depth":{"depthAsset":{"assetId":ids[i]}},"camera":f['camera']} for i,f in enumerate(v)]+[cctx(i) for i in (14,23,32)]
    targets=[orbit(-135),orbit(-170),orbit(128),orbit(165), cam([C[0]-28,15,C[2]+4],[C[0],6,C[2]])]
json.dump({"contextFrames":context,"targetCameras":targets,"returnDepth":True},open(f'req/round{rnd}b.json','w'),indent=1)
