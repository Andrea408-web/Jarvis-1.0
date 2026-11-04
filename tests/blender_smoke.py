"""Optional real Blender integration. No downloads, no native Mac claims."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.models import recipe,write_scene
binary=shutil.which('blender')
if not binary:raise SystemExit('Blender is required for this optional check; nothing will be downloaded.')
script=Path(__file__).resolve().parents[1]/'backend/blender_scene.py'
with tempfile.TemporaryDirectory(prefix='astra-real-blender-') as folder:
    root=Path(folder)
    for label in ['Auto','Haus','Roboter']:
        target=root/label;scene=recipe('3D '+label);write_scene(target,scene)
        result=subprocess.run([binary,'--background','--factory-startup','--python',str(script),'--',str(target)],capture_output=True,text=True,timeout=60)
        progress=json.loads((target/'progress.json').read_text());assert result.returncode==0,(result.returncode,result.stderr[-500:]);assert progress['state']=='done',progress
        output=target/'Astra-Modell.blend';assert output.read_bytes().startswith(b'BLENDER');assert output.stat().st_size>10000
        check=root/'inspect.py';check.write_text("import bpy,json,sys\nfrom pathlib import Path\nPath(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps({'meshes':len([o for o in bpy.data.objects if o.type=='MESH']),'vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH')}))\n")
        inspection=target/'inspection.json';r=subprocess.run([binary,'--background',str(output),'--python',str(check),'--',str(inspection)],capture_output=True,text=True,timeout=60);assert r.returncode==0
        info=json.loads(inspection.read_text());assert info['meshes']==len(scene['parts']);assert info['vertices']>len(scene['parts'])*7
        print('PASS real Blender:',label,info,'saved bytes',output.stat().st_size)
    target=root/'stopped';write_scene(target,recipe('3D Roboter'));(target/'cancel').touch()
    subprocess.run([binary,'--background','--factory-startup','--python',str(script),'--',str(target)],capture_output=True,timeout=60,check=True)
    progress=json.loads((target/'progress.json').read_text());assert progress['state']=='stopped' and progress['completed']==0;assert not (target/'Astra-Modell.blend').exists()
    print('PASS real Blender: cancelled before first mesh, no completed model claimed.')

# Exercise the real Desktop worker and download validation too; only the display
# mode is adapted to this Linux runner. The production Mac uses Blender's GUI.
from unittest.mock import patch
from backend.server import Application
with tempfile.TemporaryDirectory(prefix='astra-desktop-blender-') as folder:
    app=Application(folder);app.desktop.blender_binary=lambda:binary
    original_popen=subprocess.Popen
    def headless_popen(command,*args,**kwargs):
        if command[0]==binary:command=[binary,'--background',*command[1:]]
        return original_popen(command,*args,**kwargs)
    try:
        plan=app.desktop.prepare({'goal':'Erstelle ein 3D Auto in Blender'})['plan']
        with patch('backend.desktop.subprocess.Popen',side_effect=headless_popen):
            app.desktop.start(plan['id']);app.desktop.thread.join(30)
        state=app.desktop.snapshot()['plan'];assert state['state']=='done',state
        assert app.desktop.model_file().startswith(b'BLENDER');assert state['completed']==6
        print('PASS real Blender: Desktop prepare -> checked start -> real Blender process -> six meshes -> verified downloadable .blend.')
    finally:app.desktop.stop();app.office.stop()
