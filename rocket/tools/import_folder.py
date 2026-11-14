import sys, json, subprocess, pathlib
folder=pathlib.Path(sys.argv[1]).resolve()
fr=json.load(open(folder/'operation.json'))['response']['frames']
tmpl=open('tools/import_one.py').read()
for i,f in enumerate(fr):
    p=folder/f'cam_{i:02d}.json'; json.dump({"frames":[f]},open(p,'w'))
    open('tools/_imp.py','w').write(tmpl.replace(r"A:\Coding\Projects\atlastest\rocket\scene\cam_IDX.json", str(p)))
    out=subprocess.run([sys.executable,'tools/bl.py','tools/_imp.py','120'],capture_output=True,text=True).stdout
    print(i, 'ok' if '"status": "ok"' in out else out[:300])
open('tools/_save.py','w').write("import bpy\ndef _s():\n    bpy.ops.wm.save_mainfile()\n    return None\nbpy.app.timers.register(_s, first_interval=0.5)\nresult={'queued':True}\n")
subprocess.run([sys.executable,'tools/bl.py','tools/_save.py','60'])
