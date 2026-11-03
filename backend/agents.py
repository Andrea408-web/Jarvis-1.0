"""User-started local writing jobs, one model worker, persistent real status."""
import threading
import uuid

from .providers import ProviderError
from .storage import utc_now

ROLES = {
    'studio': {'name':'STUDIO','title':'Werbeclip','instruction':'Schreibe genau drei kurze Szenentexte für einen Werbeclip. Pro Szene eine Zeile, maximal 100 Zeichen. Keine erfundenen Produkteigenschaften.'},
    'builder': {'name':'BAUER','title':'Mini-App','instruction':'Erstelle eine konkrete interaktive Checkliste zum Auftrag. Pro Zeile einen kurzen anklickbaren Arbeitsschritt. Keine Programmcodeblöcke.'},
    'planner': {'name':'ATLAS', 'title':'Planung', 'instruction':'Erstelle einen konkreten, übersichtlichen Arbeitsplan mit sinnvollen nächsten Schritten.'},
    'writer': {'name':'NOVA', 'title':'Entwurf', 'instruction':'Erstelle einen brauchbaren Textentwurf zum Auftrag. Trenne Annahmen von bekannten Angaben.'},
    'reviewer': {'name':'SENTINEL', 'title':'Prüfung', 'instruction':'Prüfe den übergebenen Text auf Fehler und Unklarheiten. Nenne konkrete Verbesserungen. Ohne Text frage danach.'},
}

class AgentOffice:
    def __init__(self, app):
        self.app=app
        self.lock=threading.Lock()
        self.wake=threading.Event()
        self.closed=threading.Event()
        self.thread=None
        with app.store._connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS agent_jobs (
                id TEXT PRIMARY KEY, role TEXT NOT NULL, task TEXT NOT NULL,
                status TEXT NOT NULL, result TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''')
            db.execute("UPDATE agent_jobs SET status='interrupted', result=?, updated_at=? WHERE status IN ('queued','running')",
                       ('Durch Serverneustart unterbrochen. Bitte bewusst neu beauftragen.',utc_now()))

    def snapshot(self):
        with self.app.store._connect() as db:
            jobs=[dict(row) for row in db.execute("SELECT * FROM agent_jobs ORDER BY CASE WHEN status IN ('queued','running') THEN 0 ELSE 1 END, created_at DESC LIMIT 60")]
        return {'roles':[{ 'id':key,'name':value['name'],'title':value['title']} for key,value in ROLES.items()],
                'jobs':jobs,'execution':'Ein lokales Textmodell; Aufträge werden nacheinander verarbeitet. Keine Websuche oder Geräteaktionen.'}

    def submit(self, body):
        if not isinstance(body,dict) or set(body)!={'role','task'}:
            raise ValueError('Bitte Agent und Auftrag angeben.')
        role,task=body['role'],body['task']
        if not isinstance(role,str) or role not in ROLES or not isinstance(task,str) or not 1<=len(task.strip())<=3000:
            raise ValueError('Bitte einen vorhandenen Agenten und 1 bis 3.000 Zeichen für den Auftrag wählen.')
        if self.app.store.settings()['ai_provider'] not in {'ollama','llamacpp'}:
            raise ProviderError('Agenten verwenden nur deine lokale KI. Bitte zuerst die kleine KI oder Ollama auswählen. Keine kostenpflichtige Ausweichroute.',409)
        with self.lock:
            if self.closed.is_set():raise ProviderError('Die Agentenwerkstatt wird beendet.',409)
            with self.app.store._connect() as db:
                if db.execute("SELECT count(*) FROM agent_jobs WHERE status IN ('queued','running')").fetchone()[0]>=8:
                    raise ProviderError('Die Warteschlange ist voll. Bitte einen Auftrag abwarten oder abbrechen.',409)
                identifier=uuid.uuid4().hex;now=utc_now()
                db.execute("INSERT INTO agent_jobs(id,role,task,status,created_at,updated_at) VALUES(?,?,?,'queued',?,?)",(identifier,role,task.strip(),now,now))
            if self.thread is None or not self.thread.is_alive():
                self.thread=threading.Thread(target=self._run,daemon=True,name='jarvis-office');self.thread.start()
            self.wake.set()
        return {'id':identifier,'status':'queued'}

    def cancel(self, identifier):
        if not isinstance(identifier,str) or len(identifier)!=32:raise ValueError('Ungültiger Auftrag.')
        with self.app.store._connect() as db:
            count=db.execute("UPDATE agent_jobs SET status='cancelled',result=?,updated_at=? WHERE id=? AND status IN ('queued','running')",
                             ('Abgebrochen. Eine bereits laufende Modellberechnung kann noch auslaufen; ihr Ergebnis wird verworfen.',utc_now(),identifier)).rowcount
        if not count:raise ValueError('Auftrag nicht gefunden oder bereits beendet.')
        return {'ok':True}

    def _run(self):
        while not self.closed.is_set():
            self.wake.wait(.5);self.wake.clear()
            with self.app.store._connect() as db:
                row=db.execute("SELECT * FROM agent_jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
            if row is None:continue
            # Share the same resource lock as chat. Queue waiting is real, never fake progress.
            if not self.app.chat_lock.acquire(timeout=.5):
                self.wake.set();continue
            try:
                if self.closed.is_set():break
                with self.app.store._connect() as db:
                    updated=db.execute("UPDATE agent_jobs SET status='running',updated_at=? WHERE id=? AND status='queued'",(utc_now(),row['id'])).rowcount
                if not updated:continue
                try:
                    provider=self.app.store.settings()['ai_provider']
                    client={'llamacpp':self.app.llamacpp,'ollama':self.app.local_ai}.get(provider)
                    if client is None:raise ProviderError('Lokale KI wurde abgewählt. Kein Cloud-Aufruf ausgeführt.',409)
                    prompt=ROLES[row['role']]['instruction']+'\nAuftrag:\n'+row['task']
                    response=client.chat(prompt,conversation='agent_'+row['id'])
                    result=response.get('reply')
                    if not isinstance(result,str) or not result.strip():raise ProviderError('Die lokale KI hat keinen Text geliefert.',502)
                    status='completed'
                except ProviderError as error:status,result='failed',str(error)
                except Exception:status,result='failed','Auftrag konnte nicht abgeschlossen werden. Bitte die lokale KI prüfen.'
                with self.app.store._connect() as db:
                    db.execute("UPDATE agent_jobs SET status=?,result=?,updated_at=? WHERE id=? AND status='running'",(status,result,utc_now(),row['id']))
            finally:self.app.chat_lock.release()
            self.wake.set()

    def stop(self):
        self.closed.set();self.wake.set()
        if self.thread:self.thread.join(timeout=1)
        with self.app.store._connect() as db:
            db.execute("UPDATE agent_jobs SET status='interrupted',result=?,updated_at=? WHERE status IN ('queued','running')",('Durch Serverende unterbrochen.',utc_now()))
