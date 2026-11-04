"""Trusted Blender render helper, only for the newly generated private scene."""
import sys,math
from pathlib import Path
import bpy
from mathutils import Vector
folder=Path(sys.argv[sys.argv.index('--')+1])
scene=bpy.context.scene
meshes=[o for o in scene.objects if o.type=='MESH']
points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
center=sum(points,Vector())/len(points);radius=max((p-center).length for p in points)
bpy.ops.object.camera_add(location=center+Vector((1,-1,.8))*max(radius*2,4))
camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
for location,power,size in [((3,-4,6),1300,5),((-4,-1,3),900,4)]:
 bpy.ops.object.light_add(type='AREA',location=center+Vector(location)*max(radius*.5,1));light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.cycles.device='CPU';scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(folder/'Vorschau.png')
scene.world.color=(.12,.12,.12)
for material in bpy.data.materials:
 color=material.diffuse_color[:];material.use_nodes=True;node=material.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=color;node.inputs['Roughness'].default_value=.38
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Astra-Modell.blend'),check_existing=False,compress=False)
bpy.ops.render.render(write_still=True)
