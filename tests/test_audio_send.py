import base64,io,json,os,subprocess,unittest,wave
from pathlib import Path
from unittest.mock import Mock,patch
from backend.confirmed_send import validate,ConfirmedSend,NativeSendError
from backend.audio_send import native_audio_send,SCRIPT

class AudioSendTests(unittest.TestCase):
 def audio(self):
  stream=io.BytesIO()
  with wave.open(stream,'wb') as wav:wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(b'\0\0'*800)
  return stream.getvalue()
 def payload(self,**extra):return {'kind':'mail','name':'Lea','address':'lea@example.test','subject':'','text':'','audio':{'mime':'audio/wav','data':base64.b64encode(self.audio()).decode()},**extra}
 def test_audio_validated_before_send_and_not_echoed_in_preview(self):
  sent=[];service=ConfirmedSend(sender=lambda p:sent.append(p));plan=service.prepare(self.payload(),'owner');self.assertEqual(sent,[]);self.assertEqual(plan['preview']['subject'],'Sprachnachricht');self.assertEqual(plan['preview']['audio']['size'],len(self.audio()));self.assertNotIn('bytes',plan['preview']['audio']);self.assertNotIn('data',plan['preview']['audio']);json.dumps(plan)
  service.execute({'id':plan['id'],'confirm':True},'owner');self.assertEqual(sent[0]['audio']['bytes'],self.audio());self.assertEqual(service.pending,{})
 def test_wrong_container_size_and_sms_audio_are_rejected(self):
  for audio in [{'mime':'audio/wav','data':'not base64'},{'mime':'audio/wav','data':base64.b64encode(b'not a wav file at all').decode()},{'mime':'text/html','data':base64.b64encode(self.audio()).decode()},{'mime':'audio/wav','data':'A'*6000000}]:
   with self.assertRaises(ValueError):validate(self.payload(audio=audio))
  with self.assertRaises(ValueError):validate(self.payload(kind='sms',address='+49000111'))
 def test_temporary_file_is_private_and_removed_on_success_and_error(self):
  for outcome in ['accepted','failure','timeout']:
   locations=[]
   def run(command,**kwargs):
    self.assertEqual(command,['/usr/bin/osascript','-e',SCRIPT]);data=json.loads(kwargs['input']);path=Path(data['attachment_path']);locations.append(path);self.assertEqual(path.read_bytes(),self.audio());self.assertEqual(path.stat().st_mode&0o777,0o600);self.assertEqual(path.parent.stat().st_mode&0o777,0o700);self.assertNotIn('lea@example.test',str(command))
    if outcome=='timeout':raise subprocess.TimeoutExpired(command,60)
    return Mock(returncode=0 if outcome=='accepted' else 1,stdout='accepted' if outcome=='accepted' else '')
   with patch('backend.audio_send.platform.system',return_value='Darwin'),patch('backend.audio_send.subprocess.run',side_effect=run):
    if outcome=='accepted':native_audio_send(validate(self.payload()))
    else:
     with self.assertRaises(NativeSendError):native_audio_send(validate(self.payload()))
   self.assertEqual(len(locations),1);self.assertFalse(locations[0].exists());self.assertFalse(locations[0].parent.exists())
