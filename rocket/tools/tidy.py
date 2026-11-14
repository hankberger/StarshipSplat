import bpy
for n in ("Cube", "Light", "Camera"):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o)
result = {"n": len(bpy.data.objects), "cams": len([o for o in bpy.data.objects if o.type=="CAMERA"]),
          "collections": [c.name for c in bpy.data.collections]}
