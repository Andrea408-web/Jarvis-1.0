"""Focus clock, decision arithmetic and non-destructive task backups in a real browser."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as folder:
 app=Application(folder);app.store.update_settings({'voice_enabled':False})
 server=JarvisServer(('127.0.0.1',0),app)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   page=browser.new_page(viewport={'width':1300,'height':1000},accept_downloads=True)
   errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.clock.install();page.goto('http://127.0.0.1:'+str(server.server_port)+'/tablet')
   page.evaluate("async()=>await DeviceStore.set('quick-tasks-v1',[{id:'saved-task',title:'Angebot vorbereiten',done:false}])")
   page.locator('#quick-open').click();page.get_by_role('button',name='Fokus',exact=True).click()
   page.get_by_label('Woran arbeitest du gerade?').fill('Angebot für meine Marke')
   page.get_by_label('Fokuszeit in Minuten (1–180)').fill('1')
   page.get_by_role('button',name='Fokus starten / fortsetzen',exact=True).click()
   page.wait_for_function("async()=>(await DeviceStore.get('quick-focus-v1'))?.state==='running'")
   page.clock.fast_forward(10000)
   page.get_by_role('button',name='Pausieren',exact=True).click()
   page.wait_for_function("async()=>(await DeviceStore.get('quick-focus-v1'))?.state==='paused'")
   paused=page.locator('#quick-focus-clock').inner_text()
   page.clock.fast_forward(60000);assert page.locator('#quick-focus-clock').inner_text()==paused
   page.reload();page.locator('#quick-open').click();page.get_by_role('button',name='Fokus',exact=True).click()
   assert page.locator('#quick-focus-clock').inner_text()==paused
   page.get_by_role('button',name='Fokus starten / fortsetzen',exact=True).click()
   page.wait_for_function("async()=>(await DeviceStore.get('quick-focus-v1'))?.state==='running'")
   page.clock.fast_forward(61000)
   page.wait_for_function("async()=>(await DeviceStore.get('quick-focus-v1'))?.state==='done'")
   assert page.locator('#quick-focus-clock').inner_text()=='00:00'
   page.get_by_role('button',name='Timer zurücksetzen',exact=True).click()
   page.wait_for_function("async()=>(await DeviceStore.get('quick-focus-v1'))===undefined")
   page.get_by_label('Fokuszeit in Minuten (1–180)').fill('25')
   page.get_by_label('Woran arbeitest du gerade?').fill('Eine Werbeidee fertig planen')
   page.get_by_role('button',name='Fokus starten / fortsetzen',exact=True).click()
   page.wait_for_function("async()=>(await DeviceStore.get('quick-focus-v1'))?.state==='running'")
   page.mouse.move(0,0);page.clock.fast_forward(300)
   page.screenshot(path=str(root/'artifacts/jarvis-fokus.png'))
   page.get_by_role('button',name='Schließen',exact=True).click();page.clock.fast_forward(1501000)
   page.wait_for_function("async()=>(await DeviceStore.get('quick-focus-v1'))?.state==='done'")
   page.locator('#quick-open').click();page.get_by_role('button',name='Ideenvergleich',exact=True).click()
   page.get_by_label('Idee A',exact=True).fill('Design-Service')
   page.get_by_label('Idee B',exact=True).fill('Eigener Online-Shop')
   for key in ['value','easy','budget']:
    page.locator('[data-score="'+key+'-a"]').fill('10')
    page.locator('[data-score="'+key+'-b"]').fill('0')
   page.get_by_role('button',name='Ideen vergleichen',exact=True).click()
   assert 'Design-Service liegt' in page.locator('#quick-compare-result').inner_text()
   assert page.locator('#quick-compare-result meter').evaluate_all('(items)=>items.map(x=>x.value)')==[100,0]
   page.locator('#quick-compare-result').scroll_into_view_if_needed();page.mouse.move(0,0);page.clock.fast_forward(300)
   page.screenshot(path=str(root/'artifacts/jarvis-ideenvergleich.png'))
   for key in ['value','easy','budget']:page.locator('[data-score="'+key+'-weight"]').fill('0')
   assert not page.locator('#quick-compare-result').inner_text()
   page.get_by_role('button',name='Ideen vergleichen',exact=True).click()
   page.get_by_text('Mindestens ein Gewicht muss größer als 0 sein.',exact=True).wait_for()
   page.get_by_role('button',name='Aufgaben sichern',exact=True).click()
   with page.expect_download() as event:page.get_by_role('button',name='Aufgaben-Datei herunterladen',exact=True).click()
   exported=json.loads(Path(event.value.path()).read_text())
   assert set(exported)=={'format','tasks'} and len(exported['tasks'])==1
   upload=page.get_by_label('Aufgaben-Datei auswählen',exact=True)
   def choose(data):upload.set_input_files({'name':'Aufgaben.json','mimeType':'application/json','buffer':json.dumps(data).encode()})
   choose(exported);page.get_by_text('1 Aufgaben gelesen.',exact=False).wait_for()
   assert len(page.evaluate("async()=>await DeviceStore.get('quick-tasks-v1')"))==1
   page.get_by_role('button',name='Import bestätigen',exact=True).click()
   page.get_by_text('0 Aufgaben ergänzt. Bestehende Aufgaben wurden erhalten.',exact=True).wait_for()
   page.get_by_role('button',name='Aufgaben sichern',exact=True).click()
   changed={'format':exported['format'],'tasks':[{'id':'saved-task','title':'Geänderte importierte Aufgabe','done':True}]}
   choose(changed);page.get_by_role('button',name='Import bestätigen',exact=True).click()
   page.wait_for_function("async()=>(await DeviceStore.get('quick-tasks-v1')).length===2")
   tasks=page.evaluate("async()=>await DeviceStore.get('quick-tasks-v1')")
   assert tasks[0]==exported['tasks'][0] and tasks[1]['id']!='saved-task'
   page.get_by_role('button',name='Aufgaben sichern',exact=True).click()
   choose({'format':exported['format'],'tasks':[{'id':'bad','title':'Invalid','done':'yes'}]})
   page.get_by_text('Die Aufgabensicherung enthält ungültige oder doppelte Einträge.',exact=True).wait_for()
   assert page.get_by_role('button',name='Import bestätigen',exact=True).count()==0
   assert page.evaluate("async()=>await DeviceStore.get('quick-tasks-v1')")==tasks
   page.get_by_role('button',name='Schließen',exact=True).click();page.locator('#quick-open').click()
   page.get_by_role('button',name='Ideenvergleich',exact=True).click()
   assert page.get_by_label('Idee A',exact=True).input_value()==''
   page.set_viewport_size({'width':390,'height':844})
   assert page.locator('#quick-help').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
   assert not errors,errors
   browser.close();print('PASS: focus pause/reload/resume/finish and closed-dialog deadline; weighted scores and zero-weight rejection; private comparisons cleared; backup preview, identical import deduplication, conflicting IDs preserve original, malformed import cannot mutate tasks; mobile fit.')
 finally:
  app.office.stop();app.desktop.stop();server.shutdown();server.server_close();thread.join(3)
