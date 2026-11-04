"""Optional OpenAI chat via verified HTTPS; no SDK or automatic calls."""
import base64
import json
import os
import re

from .persona import instruction as persona_instruction
from .ai import GeminiClient, FUNCTIONS, SYSTEM_INSTRUCTION, _validated_proposal
from .providers import ProviderError, request_json, reserve


def _schema(value):
    if isinstance(value, dict):
        return {k: v.lower() if k == 'type' and isinstance(v, str) else _schema(v) for k, v in value.items()}
    return [_schema(v) for v in value] if isinstance(value, list) else value


class OpenAIClient(GeminiClient):
    def __init__(self, store, transport=None):
        self.store = store
        self.transport = transport or request_json

    def _generate(self, text, conversation, image=None):
        if not isinstance(text, str) or not text.strip() or len(text) > 12000:
            raise ProviderError('Bitte 1 bis 12.000 Zeichen eingeben.')
        if not isinstance(conversation, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', conversation):
            raise ProviderError('Ungültige Gesprächskennung.')
        settings = self.store.settings()
        if not settings['cloud_enabled']:
            raise ProviderError('Cloud-KI ist deaktiviert. Bitte bewusst in den Einstellungen aktivieren.', 409)
        key = os.environ.get('OPENAI_API_KEY')
        if not key:
            raise ProviderError('OpenAI-Schlüssel fehlt. Einstellungen → OpenAI → Schlüssel hinterlegen.', 409)
        model = settings['openai_model']
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,99}', model):
            raise ProviderError('Ungültiger OpenAI-Modellname.')
        context, remaining = [], 36000
        for item in reversed(self.store.history(conversation)[-24:]):
            if item['role'] not in {'user', 'assistant'}:
                continue
            if len(item['text']) > remaining:
                break
            remaining -= len(item['text'])
            context.append({'role': item['role'], 'content': item['text']})
        content = text.strip()
        if image is not None:
            encoded = base64.b64encode(image[0]).decode('ascii')
            content = [{'type': 'text', 'text': content}, {'type': 'image_url', 'image_url': {'url': f'data:{image[1]};base64,{encoded}'}}]
        payload = {'model': model, 'messages': [{'role': 'system', 'content': SYSTEM_INSTRUCTION.replace('Du bist JARVIS','Du bist ASTRA' if self.store.settings().get('assistant_identity')=='astra' else 'Du bist JARVIS')+'\n'+persona_instruction(self.store)}, *reversed(context), {'role': 'user', 'content': content}],
                   'max_completion_tokens': 1536, 'store': False}
        if image is None:
            payload['tools'] = [{'type': 'function', 'function': _schema(f)} for f in FUNCTIONS]
        reserve(self.store, 'openai_requests', 1, settings['openai_daily_limit'])
        result = self.transport('https://api.openai.com/v1/chat/completions', payload, {'Authorization': 'Bearer ' + key})
        try:
            message = result['choices'][0]['message']
            calls = message.get('tool_calls') or []
            if not isinstance(calls, list) or len(calls) > 5 or (image is not None and calls):
                raise ValueError()
            proposals = []
            for call in calls:
                function = call['function']
                proposals.append(_validated_proposal({'name': function['name'], 'args': json.loads(function['arguments'])}))
            reply = ('Die Aktion ist vorbereitet, Sir. Bitte bestätigen Sie sie; ausgeführt wurde noch nichts.'
                     if proposals else message.get('content'))
            if not isinstance(reply, str) or not reply.strip() or len(reply) > 24000:
                raise ValueError()
        except (KeyError, IndexError, ValueError, TypeError):
            raise ProviderError('OpenAI hat keine verwendbare Antwort geliefert.', 502) from None
        stored = text.strip() + ('\n[Bild übermittelt; Bilddaten werden nicht gespeichert.]' if image else '')
        self.store.append('user', stored, conversation)
        self.store.append('assistant', reply, conversation)
        return {'reply': reply, 'proposed_actions': proposals, 'conversation': conversation}
