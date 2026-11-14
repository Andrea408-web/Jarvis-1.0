import tempfile,threading,unittest
from backend.storage import Store
from backend.persona import name,correct_identity
class AerisModeTests(unittest.TestCase):
 def test_identity_is_scoped_and_does_not_leak_between_threads_or_after_errors(self):
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder);entered=threading.Event();release=threading.Event();seen=[]
   def worker():
    with store.identity_context('aeris'):entered.set();release.wait(2);seen.append(name(store));seen.append(correct_identity('Ich bin JARVIS.',store))
   thread=threading.Thread(target=worker);thread.start();self.assertTrue(entered.wait(1));self.assertEqual(name(store),'JARVIS');release.set();thread.join(2);self.assertEqual(seen,['AERIS','Ich bin AERIS.'])
   with self.assertRaises(ValueError):
    with store.identity_context('aeris'):raise ValueError('test')
   self.assertEqual(name(store),'JARVIS')

 def test_switch_to_aeris_overrides_an_old_question(self):
  from backend.server import Application
  with tempfile.TemporaryDirectory() as folder:
   app=Application(folder)
   try:
    app.chat('Erstelle eine Notiz');result=app.chat('Wechsel zu Aeris');self.assertEqual(result['view'],'aeris');self.assertIsNone(app.dialogue.get());self.assertIsNone(app.desktop.plan)
   finally:app.office.stop()
