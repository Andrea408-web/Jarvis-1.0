"""Bounded, owner-scoped in-memory workshop work; no model output on disk."""
import copy
import json
import re
import secrets
import threading
import time

class WorkshopCancelled(RuntimeError):pass

def checkpoint(progress,cancelled,stage,message):
    if cancelled and cancelled():raise WorkshopCancelled()
    if progress:progress(stage,message)

class WorkshopJobs:
    def __init__(self,app):
        self.app=app
        self.lock=threading.RLock()
        self.jobs={}
        self.running=None

    def _prune(self):
        now=time.monotonic()
        for key in list(self.jobs):
            job=self.jobs[key]
            if key!=self.running and now-job['updated']>900:del self.jobs[key]
        # Running requests and cancellation tombstones count toward the bound.
        while len(self.jobs)>=24:
            key=next((key for key in self.jobs if key!=self.running),None)
            if key is None:break
            del self.jobs[key]

    def _id(self,key):
        if not isinstance(key,str)or not re.fullmatch(r'[0-9a-f]{32}',key):raise ValueError('Ungültige Werkstatt-Auftragskennung.')

    def _get(self,key,owner):
        self._id(key)
        job=self.jobs.get(key)
        if not job or job['owner']!=owner:raise ValueError('Dieser Werkstatt-Auftrag ist nicht verfügbar. Bitte erneut starten.')
        return job

    def _snapshot(self,job):
        data={k:copy.deepcopy(job[k])for k in ['id','state','stage','message']}
        data['elapsed']=round(time.monotonic()-job['created'],1)
        for key in ['result','error','error_stage']:
            if key in job:data[key]=copy.deepcopy(job[key])
        return data

    def submit(self,body,owner):
        if not isinstance(body,dict)or set(body)!={'id','request'}:raise ValueError('Ungültiger Werkstatt-Auftrag.')
        key=body['id'];self._id(key)
        request=body['request']
        if not isinstance(request,dict):raise ValueError('Ein Bauwunsch fehlt.')
        try:encoded=json.dumps(request,allow_nan=False)
        except (ValueError,TypeError):raise ValueError('Ungültige Entwurfsdaten.')from None
        if len(encoded)>200000:raise ValueError('Der Entwurf enthält zu viele Daten für eine Überarbeitung.')
        request=copy.deepcopy(request)
        with self.lock:
            self._prune()
            if key in self.jobs:return self._snapshot(self._get(key,owner))
            if self.running:
                from .providers import ProviderError
                raise ProviderError('Die Werkstatt arbeitet noch. Bitte den laufenden Auftrag abwarten.',409)
            now=time.monotonic()
            job={'id':key,'owner':owner,'created':now,'updated':now,'state':'running','stage':'starting','message':'Bauwunsch wird geprüft.','cancel':threading.Event()}
            self.jobs[key]=job;self.running=key
            threading.Thread(target=self._run,args=(key,request),name='jarvis-workshop',daemon=True).start()
            return self._snapshot(job)

    def status(self,key,owner):
        with self.lock:
            self._prune()
            return self._snapshot(self._get(key,owner))

    def cancel(self,key,owner):
        self._id(key)
        with self.lock:
            self._prune()
            if key not in self.jobs:
                # A click on Stop may arrive before the create request.
                now=time.monotonic()
                self.jobs[key]={'id':key,'owner':owner,'created':now,'updated':now,'state':'cancelled','stage':'cancelled','message':'Auftrag gestoppt.','cancel':threading.Event()}
            job=self._get(key,owner)
            if job['state']=='running':
                job['cancel'].set();job['state']='cancelled';job['stage']='cancelled';job['message']='Auftrag gestoppt. Die laufende Modellberechnung kann noch auslaufen; ihr Ergebnis wird verworfen.';job['updated']=time.monotonic()
            return self._snapshot(job)

    def _run(self,key,request):
        job=self.jobs[key]
        def progress(stage,message):
            with self.lock:
                if job['cancel'].is_set():raise WorkshopCancelled()
                job.update(stage=stage,message=message,updated=time.monotonic())
        try:
            from .workshop import design
            result=design(request,self.app,progress,job['cancel'].is_set)
            with self.lock:
                if not job['cancel'].is_set():job.update(state='done',stage='done',message='Entwurf fertig.'if not result.get('needs_details')else'Jarvis hat eine Rückfrage.',result=result)
        except WorkshopCancelled:pass
        except Exception as error:
            from .providers import ProviderError
            # Only user-facing validation/provider errors are exposed.
            message=str(error)if isinstance(error,(ValueError,ProviderError))else'Die Werkstatt konnte den Auftrag nicht abschließen. Bitte Jarvis neu starten.'
            with self.lock:
                if not job['cancel'].is_set():job.update(state='error',error_stage=job['stage'],stage='error',message=message,error=message)
        finally:
            with self.lock:
                job['updated']=time.monotonic()
                if self.running==key:self.running=None

    def stop(self):
        with self.lock:
            for job in self.jobs.values():job['cancel'].set()
