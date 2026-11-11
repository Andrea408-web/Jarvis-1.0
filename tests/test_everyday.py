import tempfile,unittest
from unittest.mock import Mock
from backend.server import Application
from backend.everyday import arithmetic,film_ideas

class EverydayTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.app=Application(self.temp.name)
 def tearDown(self):self.app.office.stop();self.temp.cleanup()
 def test_math_overrides_stale_web_question_without_search(self):
  self.app.chat('Welche Filme kann ich jetzt im Cineplex Neufahrn sehen?');self.app.web.reader=Mock(side_effect=AssertionError('No math search'))
  result=self.app.chat('Was ist eins plus eins?');self.assertIn('= 2',result['reply']);self.assertNotIn('bestätigen',result['reply']);self.assertIsNone(self.app.dialogue.get())
  self.assertIn('= 4',self.app.chat('Jarvis, zwei plus zwei bitte')['reply']);self.assertIsNone(arithmetic('In welchem Ort?'))
 def test_film_ideas_are_local_cards_not_fake_showtimes_or_search_urls(self):
  self.app.web.reader=Mock(side_effect=AssertionError('No live search for general film ideas'))
  result=self.app.chat('Was kann ich für einen Film angucken?');self.assertEqual(result['view'],'discover');self.assertEqual(len(result['cards']),3);self.assertEqual(result['sources'],[]);self.assertIn('keine bestätigten',result['reply'])
  self.assertIsNone(film_ideas('Was ist ein Film?'))
 def test_news_country_is_filtered_in_both_visual_and_spoken_reply(self):
  self.app.hub.news=lambda:{'items':[{'title':'Deutschland-Meldung','summary':'Ein Test.','countries':['DE'],'url':'https://www.tagesschau.de/test'},{'title':'Amerika-Meldung','summary':'Nicht vorlesen.','countries':['US'],'url':'https://www.tagesschau.de/test2'}]}
  result=self.app.chat('Lies mir Nachrichten aus Deutschland vor');self.assertEqual(result['country'],'DE');self.assertTrue(result['speak_requested']);self.assertIn('Deutschland-Meldung',result['reply']);self.assertNotIn('Amerika-Meldung',result['reply']);self.assertEqual(len(result['articles']),1)
 def test_no_news_or_films_hijack_a_complete_note_request(self):
  result=self.app.chat('Erstelle eine Notiz: Nachrichten Deutschland anschauen');self.assertEqual(result['desktop']['plan']['kind'],'note')
