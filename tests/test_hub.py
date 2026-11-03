import json
import tempfile
import unittest
from backend.hub import MiniHub,normalize_handle,parse_news,youtube_data,tiktok_data
from backend.storage import Store

RSS=b'''<rss xmlns:media="http://search.yahoo.com/mrss/"><channel>
<item><title>Deutschland: Testmeldung</title><description>Testinhalt ohne Live-Behauptung.</description><link>https://www.tagesschau.de/inland/test-100.html</link><media:content url="https://images.tagesschau.de/test.jpg"/></item>
<item><title>Ukraine: Zweite Testmeldung</title><link>https://www.tagesschau.de/ausland/test-100.html</link></item>
<item><title>Unsafe link</title><link>javascript:bad()</link></item>
</channel></rss>'''

class HubTests(unittest.TestCase):
    def test_news_country_images_and_unsafe_feed_content(self):
        items=parse_news(RSS);self.assertEqual(len(items),2);self.assertEqual(items[0]['countries'],['DE']);self.assertEqual(items[1]['countries'],['UA'])
        self.assertEqual(items[0]['image'],'https://images.tagesschau.de/test.jpg')
        with self.assertRaises(ValueError):parse_news(b'<!DOCTYPE rss [<!ENTITY x SYSTEM "file:///private">]><rss/>')

    def test_profiles_validate_and_persist_without_triggering_network(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(folder);store.update_settings({'youtube_channel':'https://www.youtube.com/@meinKanal','tiktok_channel':'mein.kanal'})
            restored=Store(folder);self.assertEqual(restored.settings()['youtube_channel'],'@meinKanal');self.assertEqual(restored.settings()['tiktok_channel'],'@mein.kanal')
            hub=MiniHub(store,reader=lambda url:self.fail('snapshot must not connect'))
            self.assertIsNone(hub.snapshot()['channels']['youtube']['subscribers'])
            for value in ['https://evil.test/@name','../../private','name with spaces']:
                with self.assertRaises(ValueError):normalize_handle(value,'youtube')

    def test_news_failure_keeps_source_timestamp_never_invents_freshness(self):
        with tempfile.TemporaryDirectory() as folder:
            hub=MiniHub(Store(folder),reader=lambda url:RSS);fresh=hub.news();self.assertFalse(fresh['stale'])
            hub.reader=lambda url:(_ for _ in ()).throw(OSError('offline'))
            stale=hub.news();self.assertTrue(stale['stale']);self.assertEqual(stale['updated_at'],fresh['updated_at']);self.assertTrue(stale['error'])
            restored=MiniHub(hub.store,reader=lambda url:self.fail('no automatic network'));self.assertEqual(len(restored.snapshot()['news']['items']),2)

    def test_public_youtube_data_and_videos_are_parsed_not_executed(self):
        channel='UC'+'a'*22
        page=('var ytInitialData = '+json.dumps({'meta':{'channelMetadataRenderer':{'externalId':channel,'title':'Testkanal'}},'header':{'subscriberCountText':{'simpleText':'123 Abonnenten'}}})+';').encode()
        feed=b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015"><entry><title>Testvideo</title><yt:videoId>abcdefghijk</yt:videoId></entry></feed>'
        result=youtube_data('@test',lambda url:feed if '/feeds/' in url else page)
        self.assertEqual(result['subscribers'],'123 Abonnenten');self.assertEqual(result['videos'][0]['id'],'abcdefghijk')

    def test_tiktok_zero_is_known_but_blocked_counts_stay_unknown(self):
        data={'data':{'user':{'uniqueId':'test','nickname':'Test'},'stats':{'followerCount':0}}}
        page=('<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">'+json.dumps(data)+'</script>').encode()
        self.assertEqual(tiktok_data('@test',lambda url:page)['followers'],0)
        unavailable=tiktok_data('@test',lambda url:b'<html>Login required</html>')
        self.assertIsNone(unavailable['followers']);self.assertTrue(unavailable['error'])

    def test_changing_handle_does_not_show_old_follower_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(folder);store.update_settings({'tiktok_channel':'old'})
            hub=MiniHub(store);hub.cache['tiktok']={'handle':'@old','followers':99,'videos':[]}
            store.update_settings({'tiktok_channel':'new'})
            self.assertIsNone(hub.snapshot()['channels']['tiktok']['followers'])

class HubHTTPTests(unittest.TestCase):
    def test_authenticated_hub_read_refresh_and_profile_save(self):
        import http.client
        import threading
        from backend.server import Application,JarvisServer
        with tempfile.TemporaryDirectory() as folder:
            app=Application(folder);app.hub.reader=lambda url:RSS
            server=JarvisServer(('127.0.0.1',0),app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(path,method='GET',body=None,authorized=True):
                client=http.client.HTTPConnection(*server.server_address,timeout=3)
                headers={'Content-Type':'application/json'}
                if authorized:headers['X-Jarvis-Token']=app.token
                try:
                    client.request(method,path,json.dumps(body) if body is not None else None,headers);response=client.getresponse();return response.status,json.loads(response.read())
                finally:client.close()
            try:
                self.assertEqual(request('/api/hub',authorized=False)[0],401)
                self.assertEqual(request('/api/hub/news','POST',{},False)[0],401)
                status,data=request('/api/hub/news','POST',{});self.assertEqual(status,200);self.assertEqual(len(data['items']),2)
                status,data=request('/api/settings','PUT',{'youtube_channel':'@test','tiktok_channel':'mein.kanal'})
                self.assertEqual(status,200);self.assertEqual(data['settings']['youtube_channel'],'@test')
                self.assertEqual(request('/api/hub')[1]['channels']['tiktok']['handle'],'@mein.kanal')
                self.assertEqual(request('/api/hub/news','POST',{'url':'https://private.test'})[0],400)
            finally:server.shutdown();server.server_close();thread.join(timeout=3)
