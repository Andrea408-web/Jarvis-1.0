import json,threading,unittest
from unittest.mock import Mock,patch
from backend.confirmed_send import ConfirmedSend,NativeSendError,native_send,SCRIPT

class ConfirmedSendTests(unittest.TestCase):
 def payload(self,**changes):return {'kind':'mail','name':'Lea','address':'lea@example.test','subject':'Hallo','text':'Morgen passt es.',**changes}
 def test_prepare_does_not_send_and_preview_cannot_change_frozen_payload(self):
  sender=Mock();c=ConfirmedSend(sender=sender);original=self.payload();p=c.prepare(original,'owner');p['preview']['address']='changed@example.test';original['text']='changed';sender.assert_not_called()
  result=c.execute({'id':p['id'],'confirm':True},'owner');self.assertEqual(result['state'],'accepted');sender.assert_called_once_with(self.payload());self.assertEqual(c.pending,{})
  c.execute({'id':p['id'],'confirm':True},'owner');self.assertEqual(sender.call_count,1);self.assertNotIn('lea@example.test',json.dumps(c.receipts))
 def test_confirmation_actor_expiry_cancel_and_fields(self):
  now=[0];sender=Mock();c=ConfirmedSend(sender=sender,clock=lambda:now[0]);p=c.prepare(self.payload(),'owner')
  for body,actor in [({'id':p['id'],'confirm':False},'owner'),({'id':p['id'],'confirm':True},'other'),({'id':p['id'],'confirm':True,'text':'new'},'owner')]:
   with self.assertRaises(ValueError):c.execute(body,actor)
  now[0]=121
  with self.assertRaises(ValueError):c.execute({'id':p['id'],'confirm':True},'owner')
  p=c.prepare(self.payload(),'owner');c.cancel(p['id'],'owner')
  with self.assertRaises(ValueError):c.execute({'id':p['id'],'confirm':True},'owner')
  sender.assert_not_called()
 def test_simultaneous_confirmation_runs_sender_once(self):
  entered=threading.Event();release=threading.Event();calls=[]
  def sender(p):calls.append(p);entered.set();release.wait(2)
  c=ConfirmedSend(sender=sender);p=c.prepare(self.payload(),'owner');body={'id':p['id'],'confirm':True};t=threading.Thread(target=lambda:c.execute(body,'owner'));t.start();entered.wait(2)
  self.assertEqual(c.execute(body,'owner')['state'],'running');self.assertEqual(c.cancel(p['id'],'owner')['state'],'running');release.set();t.join(3);self.assertEqual(len(calls),1)
 def test_failures_are_not_reported_as_sent_or_retried(self):
  for uncertain in [False,True]:
   sender=Mock(side_effect=NativeSendError('not ready',uncertain));c=ConfirmedSend(sender=sender);p=c.prepare(self.payload(),'owner');body={'id':p['id'],'confirm':True};r=c.execute(body,'owner');self.assertEqual(r['state'],'uncertain' if uncertain else 'failed');self.assertEqual(c.execute(body,'owner'),r);self.assertEqual(sender.call_count,1)
 def test_invalid_recipient_and_text_refused_before_sender(self):
  c=ConfirmedSend(sender=Mock())
  for changes in [{'address':'a@example.test,b@example.test'},{'address':'a@example.test\nBcc:b@example.test'},{'subject':'a\nX: b'},{'text':''},{'kind':'sms','address':'phone; do something'},{'text':'\0'}]:
   with self.assertRaises(ValueError):c.prepare(self.payload(**changes),'owner')
 def test_native_uses_constant_script_and_stdin_not_personal_command_arguments(self):
  with patch('backend.confirmed_send.platform.system',return_value='Darwin'),patch('backend.confirmed_send.subprocess.run',return_value=Mock(returncode=0,stdout='{"accepted":true}')) as run:
   native_send(self.payload());self.assertEqual(run.call_args.args[0],['/usr/bin/osascript','-l','JavaScript','-e',SCRIPT]);self.assertNotIn('lea@example.test',str(run.call_args.args));self.assertEqual(json.loads(run.call_args.kwargs['input']),self.payload())
 def test_native_unclear_result_is_not_success(self):
  for stdout in ['invalid','{"accepted":false,"reason":"uncertain"}']:
   with patch('backend.confirmed_send.platform.system',return_value='Darwin'),patch('backend.confirmed_send.subprocess.run',return_value=Mock(returncode=0,stdout=stdout)):
    with self.assertRaises(NativeSendError) as error:native_send(self.payload())
    self.assertTrue(error.exception.uncertain)
