"""Compile with official Luau and run the actual configured plugin in a Studio API mock.
This verifies object/script installation and cancellation, not Roblox physics or visuals.
"""
import json,subprocess,tempfile,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from backend.studio_bridge import StudioBridge
from backend.roblox_plan import city
ROOT=Path(__file__).resolve().parents[1];LUAU=Path('/tmp/jarvis-luau/luau');COMPILER=LUAU.with_name('luau-compile')
def literal(v):
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(k)+']='+literal(x)for k,x in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(literal(x)for x in v)+'}'
 if v is True:return 'true'
 if v is False:return 'false'
 if v is None:return 'nil'
 return json.dumps(v,ensure_ascii=False)
@unittest.skipUnless(LUAU.exists(),'Official Luau test tool is optional and not downloaded by the test suite.')
class RobloxLuauTests(unittest.TestCase):
 def source(self):
  b=StudioBridge();self.addCleanup(b.stop);return ET.fromstring(b.prepare('test')['plugin']).find('.//ProtectedString').text
 def test_real_configured_plugin_compiles_and_installs_game_scripts_in_studio_objects(self):
  plan=city({'name':'Own Hero City','buildings':8});job={'id':'a'*32,'scene':plan};source=self.source()
  suffix='''
assert(#results>1,"no progress")
assert(results[#results].status=="done","not completed")
assert(results[#results].gameplay_ready==true,"gameplay not installed")
assert(results[#results].count==#JOB.scene.parts,"geometry incomplete")
local server,client,parts=0,0,0
for _,obj in ipairs(made)do
 if obj.class=="Script" then server=server+1;assert(string.find(obj.Source,"JarvisRacePoint",1,true)) end
 if obj.class=="LocalScript" then client=client+1;assert(obj.Parent==scripts);assert(obj:GetAttribute("JarvisWorld"));assert(string.find(obj.Source,"RopeConstraint",1,true));assert(string.find(obj.Source,"JarvisHeroHUD",1,true)) end
 if obj.class=="Part" or obj.class=="SpawnLocation" then parts=parts+1 end
end
assert(server==1 and client==1,"missing actual Roblox script instances")
assert(parts==#JOB.scene.parts,"wrong part count")
print("PASS: actual plugin installed city, server Script and LocalScript; completion follows installation")
'''
  with tempfile.TemporaryDirectory()as d:
   path=Path(d)/'mock.luau';path.write_text('local JOB='+literal(job)+'\nlocal CANCEL_AFTER=nil\n'+(ROOT/'tests/luau/studio_mock.lua').read_text()+source+suffix)
   result=subprocess.run([str(LUAU),str(path)],capture_output=True,text=True,timeout=15);self.assertEqual(result.returncode,0,result.stderr+result.stdout)
   plugin=Path(d)/'plugin.luau';plugin.write_text(source)
   for target in [plugin,ROOT/'frontend/roblox-hero-client.lua',ROOT/'frontend/roblox-hero-server.lua']:
    r=subprocess.run([str(COMPILER),str(target)],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr)
 def test_actual_plugin_stops_after_cancellation_without_false_done(self):
  job={'id':'b'*32,'scene':city({'name':'Cancellation','buildings':8})}
  with tempfile.TemporaryDirectory()as d:
   path=Path(d)/'cancel.luau';path.write_text('local JOB='+literal(job)+'\nlocal CANCEL_AFTER=4\n'+(ROOT/'tests/luau/studio_mock.lua').read_text()+self.source()+'''\nfor _,r in ipairs(results)do assert(r.status~="done","false success after cancel");assert(r.count<=4,"kept building after cancel")end\nprint("PASS: cancellation stops actual plugin build")\n''')
   r=subprocess.run([str(LUAU),str(path)],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr+r.stdout)

 def test_script_permission_failure_rolls_back_only_own_new_model(self):
  job={'id':'c'*32,'scene':city({'name':'Permission failure','buildings':8})}
  with tempfile.TemporaryDirectory()as d:
   path=Path(d)/'denied.luau';path.write_text('local JOB='+literal(job)+'\nlocal CANCEL_AFTER=nil\nlocal FAIL_SCRIPT_SOURCE=true\n'+(ROOT/'tests/luau/studio_mock.lua').read_text()+'\nlocal old=Instance.new("Model");old.Name="Existing user model";old.Parent=workspace\n'+self.source()+'''\nassert(not old.destroyed,"deleted existing user model")
local rolled=false;for _,o in ipairs(made)do if o.class=="Model" and o~=old and o.destroyed then rolled=true end end
assert(rolled,"did not roll back failed own model")
assert(results[#results].status=="error","false success after permission failure")
print("PASS: script permission failure rolls back only the new build")
''')
   r=subprocess.run([str(LUAU),str(path)],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr+r.stdout)
