"""Read-only explanations of a real server snapshot; no cleanup or diagnosis claims."""
import re


def requested(text):
    return bool(re.fullmatch(r'(?:status|systemstatus|mac[- ]?check|system[- ]?check|prüfe (?:(?:bitte )?meinen |den )?(?:mac|computer|rechner)|warum ist mein (?:mac|computer|rechner) (?:so )?langsam|wie geht es meinem (?:mac|computer|rechner))[.!? ]*', text.strip(), re.I))


def explain(system):
    lines=['Sir, hier ist die Momentaufnahme des verbundenen Jarvis-Rechners.']
    if not system.get('is_macos'):
        lines.append('Das ist kein Mac: '+str(system.get('system') or 'Betriebssystem unbekannt')+'. Die Werte beschreiben diesen Server, nicht automatisch dein Handy oder deinen Mac.')
    cpu=system.get('cpu_percent')
    if isinstance(cpu,(float,int)):
        lines.append(f'CPU: {cpu:.1f} %. '+('Gerade stark ausgelastet. Prüfe in der Aktivitätsanzeige unter „CPU“, welcher Prozess oben steht.' if cpu>=85 else 'Diese einzelne Messung zeigt keine dauerhaft hohe Auslastung; bei Ruckeln prüfe mehrere Messungen in der Aktivitätsanzeige.'))
    else:
        lines.append('CPU: Noch keine Messung verfügbar. Frage nach einigen Sekunden erneut; ich erfinde keinen Wert.')
    used,total=system.get('memory_used_bytes'),system.get('memory_total_bytes')
    if isinstance(used,(int,float)) and isinstance(total,(int,float)) and total>0:
        lines.append(f'Arbeitsspeicher: {used/1073741824:.1f} von {total/1073741824:.1f} GB belegt. '+('Bei Verzögerungen unbenutzte Apps schließen und in der Aktivitätsanzeige den Speicherdruck prüfen.' if used/total>=.85 else 'Die Belegung allein zeigt keinen Speichermangel. Unter macOS ist zusätzlich der Speicherdruck wichtig.'))
    else:lines.append('Arbeitsspeicher: Messwerte nicht verfügbar.')
    free,disk=system.get('disk_free_bytes'),system.get('disk_total_bytes')
    if isinstance(free,(int,float)) and isinstance(disk,(int,float)) and disk>0:
        lines.append(f'Speicherplatz: {free/1073741824:.1f} GB frei. '+('Wenig freier Platz: Prüfe Systemeinstellungen → Allgemein → Speicher; vor dem Löschen Dateien ansehen.' if free/disk<.1 else 'Auf dem gemessenen Laufwerk ist mehr als ein Zehntel frei.'))
    else:lines.append('Speicherplatz: Messwerte nicht verfügbar.')
    lines.append('Ich habe nichts verändert oder gelöscht. Für eine genaue Ursache beschreibe, welche App langsam ist und seit wann.')
    return {'reply':'\n'.join(lines),'proposals':[]}
