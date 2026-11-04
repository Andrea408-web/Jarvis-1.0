"""Run only inside Blender. Trusted geometry builder; scene JSON is never code."""
import sys,json,math
from pathlib import Path
import bpy

folder=Path(sys.argv[sys.argv.index('--')+1]).resolve()
scene=json.loads((folder/'scene.json').read_text())
parts=scene['parts'];index=0;headless=bpy.app.background

def report(state,message):
    path=folder/'progress.json';temp=path.with_suffix('.tmp');temp.write_text(json.dumps({'state':state,'completed':index,'total':len(parts),'message':message}));temp.replace(path)

def setup():
    # A separate Blender process owns this new scene. Existing Blender files stay open separately.
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    report('running','Blender erstellt echte Mesh-Objekte.')

def add(item):
    shape=item['shape'];args={'location':item['location'],'rotation':item['rotation']}
    if shape=='cube':bpy.ops.mesh.primitive_cube_add(size=2,**args)
    elif shape=='sphere':bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,**args)
    elif shape=='cylinder':bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=1,depth=2,**args)
    elif shape=='cone':bpy.ops.mesh.primitive_cone_add(vertices=4 if item['name']=='Dach' else 32,radius1=1,radius2=0,depth=2,**args)
    elif shape=='torus':bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=12,major_radius=1,minor_radius=.25,**args)
    else:raise ValueError('Ungültige Form.')
    obj=bpy.context.object;obj.name=item['name'];obj.scale=item['scale']
    material=bpy.data.materials.new(item['name']);material.diffuse_color=(*item['color'],1);obj.data.materials.append(material)
    return obj

def finish():
    bpy.ops.object.select_all(action='SELECT')
    if not headless and bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.shading.color_type='MATERIAL'
                try:
                    with bpy.context.temp_override(area=area):bpy.ops.view3d.view_selected(use_all_regions=False)
                except RuntimeError:pass
    output=folder/'Astra-Modell.blend';bpy.ops.wm.save_as_mainfile(filepath=str(output),check_existing=False,compress=False)
    report('done','Blender-Modell gespeichert: '+output.name)

def tick():
    global index
    try:
        if (folder/'cancel').exists():report('stopped','Modellierung gestoppt; vorhandene Objekte bleiben sichtbar.');return None
        if index<len(parts):
            add(parts[index]);index+=1;report('running','Objekt '+str(index)+' von '+str(len(parts)))
            return .16
        finish();return None
    except Exception as error:report('error',str(error)[:300]);return None

try:
    setup()
    if headless:
        while tick() is not None:pass
    else:bpy.app.timers.register(tick,first_interval=.5)
except Exception as error:report('error',str(error)[:300]);raise
