"""Hub UI uses controlled public-source fixtures; no real follower counts asserted."""
import sys,tempfile,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.server import Application,JarvisServer
from tests.test_hub import RSS
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory() as folder:
    app=Application(folder);app.store.update_settings({'ai_provider':'llamacpp','voice_enabled':False})
    channel='UC'+'a'*22
    yt=('var ytInitialData = '+json.dumps({'meta':{'channelMetadataRenderer':{'externalId':channel,'title':'Fixture Kanal'}},'header':{'subscriberCountText':{'simpleText':'123 Abonnenten'}}})+';').encode()
    feed=b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015"><entry><title>Fixture Video</title><yt:videoId>abcdefghijk</yt:videoId></entry></feed>'
    tt=('<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">'+json.dumps({'data':{'user':{'uniqueId':'test_tt','nickname':'Fixture TikTok'},'stats':{'followerCount':456}}})+'</script>').encode()
    app.hub.reader=lambda url:RSS if 'tagesschau.de' in url else feed if '/feeds/' in url else tt if 'tiktok.com' in url else yt
    started=threading.Event();release=threading.Event()
    def transport(*args,**kwargs):
        started.set();release.wait(15);return {'choices':[{'finish_reason':'stop','message':{'content':'Fertiger Testplan'}}]}
    app.llamacpp.endpoint_transport=transport
    server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.route('https://**/*',lambda route:route.abort())
            page.add_init_script("window.SpeechRecognition=class{constructor(){window.fakeRecognition=this}start(){this.onstart?.()}stop(){}};if(navigator.mediaDevices)navigator.mediaDevices.getUserMedia=async()=>{throw Error('No waveform fixture');};")
            page.goto('http://127.0.0.1:'+str(server.server_port));page.get_by_text('LOKALE VERBINDUNG AKTIV',exact=True).wait_for()
            page.get_by_role('button',name='Mini-Hub',exact=True).click();page.get_by_text('Deutschland: Testmeldung',exact=True).first.wait_for()
            page.locator('#mini-hub').get_by_role('button',name='Nachrichten',exact=True).click();page.locator('#hub-country').select_option('DE');assert page.locator('#hub-articles article').count()==1
            page.locator('#mini-hub').get_by_role('button',name='Meine Kanäle',exact=True).click()
            page.locator('#mini-hub input[name=youtube_channel]').fill('@test_yt');page.locator('#mini-hub input[name=tiktok_channel]').fill('@test_tt')
            page.get_by_role('button',name='Speichern & öffentlich laden',exact=True).click();page.get_by_text('123 Abonnenten',exact=True).wait_for();page.get_by_text('456 Follower',exact=True).wait_for()
            page.get_by_role('button',name='Im Hub ansehen',exact=True).click();assert 'youtube-nocookie.com' in page.locator('#hub-player iframe').get_attribute('src')
            assert app.store.settings()['youtube_channel']=='@test_yt';assert app.store.settings()['tiktok_channel']=='@test_tt'
            page.locator('#mini-hub').get_by_role('button',name='Planer',exact=True).click()
            page.locator('[data-panel=planner] input:not([type])').fill('Testtermin')
            page.locator('[data-panel=planner] input[type=datetime-local]').fill('2026-12-01T18:00')
            page.get_by_role('button',name='Termin speichern',exact=True).click();page.get_by_text('Testtermin',exact=True).wait_for();page.get_by_role('button',name='Erledigt',exact=True).click();page.get_by_text('Erledigt',exact=False).first.wait_for()
            page.locator('#mini-hub').get_by_role('button',name='Überblick',exact=True).click()
            page.evaluate("()=>window.JarvisBridge.api('/api/agents',{method:'POST',body:JSON.stringify({role:'planner',task:'Plane etwas'})})")
            assert started.wait(3);page.locator('#hub-brain[data-working=true]').wait_for(timeout=7000)
            page.locator('#mini-hub').get_by_role('button',name='Mit Jarvis sprechen',exact=True).click();page.locator('#allow-mic').click()
            page.wait_for_function('()=>window.JarvisConversation.active()')
            page.locator('#mini-hub').get_by_role('button',name='Gespräch beenden',exact=True).click()
            assert app.office.snapshot()['jobs'][0]['status']=='running';release.set()
            page.screenshot(path='/tmp/jarvis-mini-hub.png')
            page.set_viewport_size({'width':390,'height':844});assert page.locator('#mini-hub').evaluate('(node)=>node.scrollWidth<=node.clientWidth+1')
            page.locator('#mini-hub').get_by_role('button',name='Schließen',exact=True).click();page.reload();page.get_by_role('button',name='Mini-Hub',exact=True).click()
            page.locator('#mini-hub').get_by_role('button',name='Meine Kanäle',exact=True).click();assert page.locator('#mini-hub input[name=youtube_channel]').input_value()=='@test_yt'
            assert not errors,errors
            print('PASS: hub news map/filter and images, stored channel handles/count fixtures, embedded video, persisted planner, actual running-job brain indicator, conversation stop preserves job, mobile width.')
            browser.close()
    finally:release.set();app.office.stop();server.shutdown();server.server_close();thread.join(timeout=3)
