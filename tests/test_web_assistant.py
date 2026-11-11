"""Public web facts, missing-input turns, site confirmation and private-URL rejection."""
import json,socket,tempfile,threading,unittest
from datetime import datetime
from unittest.mock import Mock,patch
from zoneinfo import ZoneInfo
from backend.server import Application
from backend.web_assistant import CINEMA,SEARCH,Page,fetch_public,public_url,restaurant_rows,screenings
NOW=datetime(2026,11,5,18,0,tzinfo=ZoneInfo('Europe/Berlin'))
def html(data):return '<script type="application/ld+json">'+json.dumps(data)+'</script>'
def event(name,age,time='20:00',date='2026-11-05'):
 return {'@type':'ScreeningEvent','workPresented':{'name':name,'contentRating':'FSK '+str(age)},'startDate':date+'T'+time+':00+01:00','location':{'name':'Cineplex Neufahrn'}}

class WebTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.app=Application(self.temp.name);self.app.web.clock=lambda:NOW;self.app.selected_client=Mock(side_effect=AssertionError('Web facts must not be invented by the model'))
 def tearDown(self):self.app.office.stop();self.temp.cleanup()
 def reader(self,url):
  if url.startswith(SEARCH):return '',url
  return html([event('Familienfilm',6),event('Zu spät freigegeben',16),event('Schon vorbei',0,'14:00'),event('Erst morgen',0,date='2026-11-06')]),url
 def test_cinema_age_followup_filters_fsk_date_time_and_offers_site(self):
  self.app.web.reader=self.reader
  question=self.app.chat('Jarvis, welche Filme kann ich jetzt im Cineplex Neufarhn sehen?');self.assertEqual(question['pending']['kind'],'web_details')
  answer=self.app.chat('zwölf');self.assertIn('Familienfilm – 20:00, FSK 6',answer['reply']);self.assertNotIn('Zu spät',answer['reply']);self.assertNotIn('Schon vorbei',answer['reply']);self.assertNotIn('Erst morgen',answer['reply']);self.assertEqual(answer['sources'][0]['url'],CINEMA)
  opened=self.app.chat('ja bitte');self.assertEqual(opened['open_url'],CINEMA);self.assertIsNone(self.app.dialogue.get());self.assertIsNone(self.app.desktop.plan)
 def test_blocked_web_has_no_invented_times_and_can_decline_opening(self):
  self.app.web.reader=Mock(side_effect=OSError('blocked'))
  result=self.app.chat('Welche Filme ab 12 kann ich jetzt im Cineplex Neufahrn sehen?');self.assertIn('nicht mit lesbaren Spielzeiten',result['reply']);self.assertEqual(result['sources'][0]['url'],CINEMA)
  self.assertNotIn('open_url',self.app.chat('nein danke'));self.assertIsNone(self.app.dialogue.get())
 def test_food_remembers_plain_place_people_budget_and_scope(self):
  calls=[]
  def reader(url):calls.append(url);return '',url
  self.app.web.reader=reader
  self.assertIn('Ort',self.app.chat('Wo kann ich jetzt günstig Pizza essen?')['reply'])
  self.assertIn('wie viele',self.app.chat('München')['reply'])
  self.assertIn('höchstens',self.app.chat('drei')['reply'])
  self.assertIn('pro Person oder insgesamt',self.app.chat('15 Euro')['reply'])
  result=self.app.chat('pro Person');self.assertEqual(result['pending']['kind'],'web_open');self.assertIn('M%C3%BCnchen',calls[0]);self.assertIn('3+Personen',calls[0]);self.assertIn('15+Euro+pro+Person',calls[0])
 def test_web_disabled_and_chat_clear_remove_pending_question(self):
  self.app.chat('Wo kann ich jetzt Pizza essen?');self.app.clear_chat();self.assertIsNone(self.app.dialogue.get())
  self.app.store.update_settings({'web_enabled':False});self.app.web.reader=Mock(side_effect=AssertionError('Disabled'))
  self.assertIn('ausgeschaltet',self.app.chat('Welche Filme laufen heute im Cineplex Neufahrn?')['reply'])
 def test_general_chat_still_uses_normal_client(self):
  client=Mock();client.chat.return_value={'reply':'Ein Regenbogen entsteht durch Lichtbrechung.'};self.app.selected_client=Mock(return_value=client)
  self.assertIn('Lichtbrechung',self.app.chat('Warum gibt es Regenbögen?')['reply']);client.chat.assert_called_once()
 def test_late_web_result_cannot_restore_cleared_pending_state(self):
  entered=threading.Event();release=threading.Event();errors=[]
  def reader(url):entered.set();release.wait(2);return self.reader(url)
  self.app.web.reader=reader
  def worker():
   try:self.app.chat('Welche Filme ab 12 im Cineplex Neufahrn laufen jetzt?')
   except ValueError as error:errors.append(str(error))
  thread=threading.Thread(target=worker);thread.start();self.assertTrue(entered.wait(1));self.app.clear_chat();release.set();thread.join(3)
  self.assertFalse(thread.is_alive());self.assertTrue(errors);self.assertIsNone(self.app.dialogue.get());self.assertEqual(self.app.store.history(),[])
 def test_no_false_screening_from_other_location(self):
  record=event('Andere Stadt',0);record['location']={'name':'Cineplex Berlin'}
  self.assertEqual(screenings([record],NOW,12,place='Neufahrn'),[])
 def test_schema_restaurant_hours_and_group_price_are_qualified(self):
  data={'@type':'Restaurant','name':'Testküche','openingHoursSpecification':[{'dayOfWeek':'Thursday','opens':'17:00','closes':'23:00'}],'hasOfferCatalog':{'itemListElement':[{'@type':'Offer','name':'Pizza Margherita','price':'8.50','priceCurrency':'EUR'}]}}
  rows=restaurant_rows([data],NOW,3,'10 Euro pro Person');self.assertTrue(rows[0][0]);self.assertIn('25.50',rows[0][1]);self.assertNotIn('über eurem',rows[0][1])
  self.assertIn('über eurem',restaurant_rows([data],NOW,3,'20 Euro insgesamt')[0][1])
 def test_private_urls_dns_and_redirects_are_rejected(self):
  for url in ['https://127.0.0.1/','https://192.168.1.2/','http://example.com/','https://user:pass@example.com/','https://server.local/','javascript:alert(1)']:self.assertFalse(public_url(url),url)
  with patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]),self.assertRaises(ValueError):fetch_public('https://example.com/')
 def test_search_parser_strips_tracking_and_script_text(self):
  page=Page();page.feed('<script>not visible</script><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2F">Testküche</a><a class="result__snippet">Pizza ab 8 Euro.</a>')
  self.assertEqual(page.links[0]['url'],'https://example.com/');self.assertEqual(page.links[0]['snippet'],'Pizza ab 8 Euro.');self.assertNotIn('not visible',page.text)
