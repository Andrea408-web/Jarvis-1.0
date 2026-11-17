"""Confirmed audio mail: restricted temporary file, deleted after native handoff.
No audio library, recording log or voice profile. The Mail app manages sent copies.
"""
import json,os,platform,subprocess,tempfile
from pathlib import Path
from .confirmed_send import NativeSendError

SCRIPT=r'''use framework "Foundation"
use scripting additions
on run
 set inputHandle to current application's NSFileHandle's fileHandleWithStandardInput()
 set incoming to inputHandle's readDataToEndOfFile()
 set payload to current application's NSJSONSerialization's JSONObjectWithData:incoming options:0 |error|:(missing value)
 set recipientAddress to (payload's objectForKey:"address") as text
 set messageSubject to (payload's objectForKey:"subject") as text
 set messageText to (payload's objectForKey:"text") as text
 set audioPath to (payload's objectForKey:"attachment_path") as text
 tell application "Mail"
  if (count of accounts) is 0 then return "no_account"
  set outgoingMessage to make new outgoing message with properties {subject:messageSubject, content:messageText & return, visible:true}
  tell outgoingMessage
   make new to recipient at end of to recipients with properties {address:recipientAddress}
   tell content
    make new attachment with properties {file name:(POSIX file audioPath)} at after last paragraph
   end tell
  end tell
  activate
  delay 1
  set didSend to send outgoingMessage
  if didSend is true then return "accepted"
  return "uncertain"
 end tell
end run'''

def native_audio_send(payload):
 if platform.system()!='Darwin':raise NativeSendError('Audio-Versand benötigt Apple Mail auf dem verbundenen Mac.')
 audio=payload['audio']
 # Only a generated, format-derived basename may be created here.
 if audio['filename'] not in {'Jarvis-Sprachnachricht.wav','Jarvis-Sprachnachricht.m4a','Jarvis-Sprachnachricht.webm','Jarvis-Sprachnachricht.ogg'}:raise NativeSendError('Ungültiges Audioformat.')
 with tempfile.TemporaryDirectory(prefix='jarvis-send-audio-') as folder:
  os.chmod(folder,0o700);path=Path(folder)/audio['filename']
  with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:stream.write(audio['bytes'])
  params={key:payload[key] for key in ['name','address','subject','text']};params['attachment_path']=str(path)
  try:result=subprocess.run(['/usr/bin/osascript','-e',SCRIPT],input=json.dumps(params,ensure_ascii=False),text=True,capture_output=True,timeout=60)
  except subprocess.TimeoutExpired:raise NativeSendError('Audio-Versandstatus unklar. Bitte Apple Mail vor einem neuen Versuch prüfen. Die temporäre Jarvis-Datei wird entfernt.',True) from None
  except OSError:raise NativeSendError('Apple Mail konnte nicht gestartet werden. Die temporäre Datei wird entfernt.') from None
  if result.returncode:raise NativeSendError('Die Audio-Übergabe wurde nicht bestätigt. Bitte Apple Mail und dessen macOS-Freigabe prüfen.',True)
  status=result.stdout.strip()
  if status=='accepted':return
  if status=='no_account':raise NativeSendError('In Apple Mail ist kein Konto eingerichtet.')
  raise NativeSendError('Audio-Versand nicht bestätigt. Bitte Apple Mail vor einem neuen Versuch prüfen.',True)
