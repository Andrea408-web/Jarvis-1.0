/* Presentation only: existing controls retain their handlers and storage. */
(()=>{
 const $=id=>document.getElementById(id),device=document.body.hasAttribute('data-device-app');
 if(!device&&!document.body.classList.contains('mac-console'))return;
 const settings=document.createElement('details');settings.id='hud-settings';settings.innerHTML='<summary aria-label="Ansicht, Verbindung und Spracheinstellungen"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 3v18M12 3v18M19 3v18M2 8h6M9 16h6M16 7h6"/></svg><span>Einstellungen</span></summary><div id="hud-settings-content"><small>ANSICHT & VERBINDUNG</small></div>';
 const header=document.querySelector(device?'body>header':'.topbar');header.append(settings);
 const content=$('hud-settings-content');
 function move(id,parent){const node=$(id);if(node&&node.parentElement!==parent)parent.append(node);}
 function label(text,target){if(content.querySelector('[for="'+target+'"]'))return;const node=document.createElement('label');node.htmlFor=target;node.textContent=text;content.append(node);}
 function arrange(){
  if(device){const mark=document.querySelector('.wordmark .mark');if(mark&&!mark.querySelector('svg'))mark.innerHTML='<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.2" aria-hidden="true"><circle cx="16" cy="16" r="12"/><circle cx="16" cy="16" r="7"/><circle cx="16" cy="16" r="2" fill="currentColor"/><path d="M16 1v5M16 26v5M1 16h5M26 16h5"/></svg>';const paths={chat:'M4 4h16v12H9l-5 5V4Zm4 4h8M8 12h5',notes:'M6 3h12v18H6V3Zm3 5h6M9 12h6M9 16h4',brands:'m3 12 9-9h8v8l-9 10-8-9Zm13-5h1',desk:'M4 5h16v15H4V5Zm0 9h5l1 2h4l1-2h5M8 9h8',more:'M5 12h.01M12 12h.01M19 12h.01'};for(const b of document.querySelectorAll('.rail>button,.rail>details>summary')){if(b.querySelector('svg'))continue;const d=paths[b.dataset.view]||paths.more;const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');svg.innerHTML='<path d="'+d+'"/>';if(b.firstChild?.nodeType===Node.TEXT_NODE)b.firstChild.textContent='';b.prepend(svg);}const send=$('chat-send');if(send&&!send.querySelector('svg'))send.innerHTML='Senden <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h16m-6-6 6 6-6 6"/></svg>';}

  const apps=$('jarvis-app-open');if(apps&&apps.parentElement!==header)header.insertBefore(apps,settings);
  if(device){move('device-layout-switch',content);move('offline-ready',content);label('KI-Ausführung','engine-mode');move('engine-mode',content);label('Stimme prüfen','device-voice-retry');move('device-voice-retry',content);if($('quick-bar')){let tools=$('hud-device-tools');if(!tools){tools=document.createElement('details');tools.id='hud-device-tools';tools.innerHTML='<summary>Weitere Werkzeuge</summary>';content.append(tools);}move('quick-bar',tools);}}
  else{move('jarvis-utility-row',content);for(const node of document.querySelectorAll('.audio-module .voice-clap-note'))content.append(node);const tools=$('desktop-tools-host');if(tools){const shortcuts=document.querySelector('.jarvis-area-shortcuts');if(shortcuts&&shortcuts.parentElement!==tools)tools.append(shortcuts);move('quick-bar',tools);}}
 }
 arrange();addEventListener('jarvis:apps-ready',arrange);addEventListener('jarvis:shell-ready',arrange);
 // Menus close after navigation without resetting any user preference.
 document.addEventListener('click',e=>{if(!settings.contains(e.target))settings.open=false;});
 document.addEventListener('keydown',e=>{if(e.key==='Escape')settings.open=false;});
})();
