import unittest
from backend.media import search,video_id

class MediaTests(unittest.TestCase):
 def test_ids_require_exact_https_hosts_and_complete_video_ids(self):
  for url in ['https://www.youtube.com/watch?v=AbC123_efGh','https://youtu.be/AbC123_efGh','https://www.youtube.com/shorts/AbC123_efGh','https://www.youtube.com/live/AbC123_efGh']:
   self.assertEqual(video_id(url),'AbC123_efGh')
  for url in ['http://youtube.com/watch?v=AbC123_efGh','https://youtube.com.evil.invalid/watch?v=AbC123_efGh','https://user:pass@youtube.com/watch?v=AbC123_efGh','https://youtube.com:444/watch?v=AbC123_efGh','https://127.0.0.1/watch?v=AbC123_efGh','https://youtu.be/short','javascript:alert(1)','https://youtube.com/watch?v=AbC123_efGhMORE']:
   self.assertIsNone(video_id(url),url)
 def test_results_only_come_from_valid_youtube_links_not_generated_titles(self):
  urls=[]
  html='<a class="result__a" href="https://www.youtube.com/watch?v=AbC123_efGh">Erstes Video</a><a class="result__a" href="https://youtu.be/AbC123_efGh">Doppelt</a><a class="result__a" href="https://youtube.com.evil.invalid/watch?v=XbC123_efGh">Falsch</a><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DBbC123_efGh">Zweites Video</a>'
  result=search({'query':'Sonnensystem'},lambda url:(urls.append(url)or html,url))
  self.assertEqual([x['title']for x in result['items']],['Erstes Video','Zweites Video']);self.assertEqual(len(urls),1);self.assertIn('site%3Ayoutube.com%2Fwatch',urls[0])
 def test_unavailable_search_returns_honest_empty_result_and_recovery_link(self):
  def fail(url):raise OSError('private transport detail')
  result=search({'query':'Mein Video'},fail);self.assertFalse(result['available']);self.assertEqual(result['items'],[]);self.assertNotIn('private',result['message']);self.assertIn('youtube.com/results',result['search_url'])
 def test_invalid_queries_never_fetch(self):
  for body in [{},{'query':''},{'query':'x'*181},{'query':'ok','url':'https://127.0.0.1'},None,{'query':True}]:
   with self.subTest(body=body),self.assertRaises(ValueError):search(body,lambda url:self.fail('must not fetch'))
 def test_youtube_page_fallback_when_public_search_has_no_matches(self):
  import json
  payload={'contents':{'items':[{'videoRenderer':{'videoId':'AbC123_efGh','title':{'runs':[{'text':'Originales YouTube-Ergebnis'}]}}}]}}
  calls=[]
  def read(url):
   calls.append(url)
   return ('<html>Keine Treffer / Suchdienst blockiert</html>'if len(calls)==1 else'<script>var ytInitialData = '+json.dumps(payload)+';</script>',url)
  data=search({'query':'Weltraum'},read);self.assertEqual(len(calls),2);self.assertEqual(data['source'],'YouTube-Suche');self.assertEqual(data['items'][0]['title'],'Originales YouTube-Ergebnis');self.assertTrue(calls[-1].startswith('https://www.youtube.com/results?search_query='))
 def test_youtube_page_parser_never_executes_scripts_or_accepts_invalid_ids(self):
  from backend.media import youtube_results
  self.assertEqual(youtube_results('<script>var ytInitialData = alert(1);</script>'),[])
  self.assertEqual(youtube_results('<script>var ytInitialData = {"videoRenderer":{"videoId":"bad","title":{"simpleText":"Fake"}}};</script>'),[])
