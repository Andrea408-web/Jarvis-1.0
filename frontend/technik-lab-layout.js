/* Presentation only. Project instructions and progress belong to the lab controller. */
export const PROJECT_CARDS = [
  {id:'stand',title:'Handyhalter aus Pappe',description:'Aus vorhandener Pappe etwas Nützliches bauen und die Stabilität selbst prüfen.',icon:'stand',tag:'Einfach anfangen'},
  {id:'gripper',title:'Mechanischer Greifer',description:'Mit Pappteilen eine einfache Bewegung übertragen – ohne Motor oder Programmierung.',icon:'gripper',tag:'Bewegung verstehen'},
  {id:'light',title:'Lichtobjekt mit USB-Modul',description:'Eine eigene Hülle für ein fertiges USB-Lichtmodul entwerfen. Keine Netzteil- oder Lötarbeiten.',icon:'light',tag:'Gestalten & ausprobieren'}
];

const icon = name => '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><use href="/technik-lab-icons.svg#'+name+'"></use></svg>';

export function labMarkup(){
  return `
  <div class="tl-shell">
    <header class="tl-header tl-head">
      <div>
        <p class="tl-kicker">JARVIS / TECHNIKLABOR</p>
        <h1 class="tl-title" id="tl-title">Eine Idee. Ein echter nächster Schritt.</h1>
        <p class="tl-subtitle" id="tl-summary">Wähle einen Einstieg oder besprich deine eigene Idee. Du brauchst dafür kein 3D-Modell.</p>
      </div>
      <button id="tl-close" type="button" class="tl-close" aria-label="Techniklabor schließen">Schließen ×</button>
    </header>

      <div class="tl-voice" aria-label="Sprache im Techniklabor">
        <div class="tl-toolbar tl-actions">
          <button id="tl-talk" type="button" class="tl-primary" aria-pressed="false">Mit Jarvis sprechen</button>
          <button id="tl-mute" type="button" class="tl-secondary">Stimme stoppen</button>
          <label class="tl-read-label"><input id="tl-read" type="checkbox" checked> Mit Thorsten antworten</label>
        </div>
        <label class="tl-consent"><input id="tl-consent" type="checkbox"> Browser-Spracherkennung erlauben; sie kann Audio online verarbeiten.</label>
        <p id="tl-voice-status" class="tl-status" role="status">Mikrofon aus. Einschalten ist freiwillig.</p>
      </div>

    <section class="tl-chooser" id="tl-chooser" aria-labelledby="tl-chooser-title">
      <div class="tl-section-heading">
        <div><p class="tl-kicker">DEIN EINSTIEG</p><h2 id="tl-chooser-title">Was möchtest du ausprobieren?</h2></div>
        <p class="tl-muted">Das sind Bauideen, keine bereits erledigten Projekte.</p>
      </div>
      <div class="tl-project-grid tl-projects" id="tl-projects">
        ${PROJECT_CARDS.map(project=>`<button type="button" class="tl-project-card" data-project="${project.id}"><span class="tl-project-icon">${icon(project.icon)}</span><span class="tl-project-tag">${project.tag}</span><strong>${project.title}</strong><span>${project.description}</span><span class="tl-project-open">Projekt ansehen ↗</span></button>`).join('')}
      </div>
      <p class="tl-muted tl-own-idea">Etwas anderes im Kopf? Schreib oder sprich deine Idee unten mit Jarvis durch. Eigene Vorhaben sind willkommen.</p>
    </section>

    <section class="tl-workspace" id="tl-workspace" hidden aria-label="Aktuelles Bauprojekt">
      <div class="tl-project-heading">
        <div><p class="tl-kicker">DEIN PROJEKT</p><h2 id="tl-project-title">Dein ausgewähltes Projekt</h2><p class="tl-muted" id="tl-project-summary"></p></div>
        <button id="tl-project-change" type="button" class="tl-secondary">Anderes Projekt</button>
      </div>
      <div class="tl-layout">
        <div class="tl-main">
          <article class="tl-step tl-card" aria-labelledby="tl-step-title">
            <div class="tl-step-heading"><p id="tl-step-count" class="tl-step-count">Schritt für Schritt</p><span class="tl-step-icon">${icon('build')}</span></div>
            <h3 id="tl-step-title" class="tl-step-title" tabindex="-1">Dein nächster Schritt</h3>
            <div id="tl-step-copy" class="tl-step-copy"></div>
            <ul id="tl-step-check" class="tl-step-check" aria-label="Darauf achten"></ul>
            <div class="tl-step-actions tl-actions">
              <button id="tl-prev" type="button" class="tl-secondary">← Zurück</button>
              <button id="tl-done" type="button" class="tl-primary" aria-pressed="false">${icon('check')} Schritt erledigt</button>
              <button id="tl-next" type="button" class="tl-secondary">Weiter →</button>
            </div>
            <p class="tl-muted tl-step-note">„Erledigt“ hält nur deinen Fortschritt fest. Jarvis prüft den Aufbau nicht automatisch.</p>
          </article>
        </div>
        <aside class="tl-sidebar" aria-label="Fortschritt und Vorbereitung">
          <section class="tl-progress-card tl-card" aria-labelledby="tl-progress-title">
            <p class="tl-kicker">DEIN WEG</p><h3 id="tl-progress-title">Ein Schritt nach dem anderen</h3>
            <ol id="tl-progress" class="tl-progress" aria-label="Projektschritte"></ol>
          </section>
          <details class="tl-materials tl-card" id="tl-preparation">
            <summary>Material & Werkzeug</summary>
            <h4>Was du brauchst</h4><ul id="tl-materials"></ul>
            <h4>Werkzeug</h4><ul id="tl-tools"></ul>
          </details>
          <p id="tl-limits" class="tl-muted tl-limits"></p>
        </aside>
      </div>
    </section>

    <section class="tl-conversation tl-card" aria-labelledby="tl-chat-title">
      <div class="tl-section-heading">
        <div><p class="tl-kicker">JARVIS BLEIBT DABEI</p><h2 id="tl-chat-title">Frag einfach weiter.</h2></div>
        <p class="tl-muted">Zum Beispiel: „Warum hält das noch nicht?“</p>
      </div>
      <div id="tl-chat" class="tl-chat" aria-live="polite" aria-relevant="additions" aria-label="Gespräch mit Jarvis"></div>
      <form id="tl-form" class="tl-form">
        <label for="tl-input" class="tl-input-label">Deine Frage oder eigene Idee</label>
        <textarea id="tl-input" maxlength="1400" rows="2" placeholder="Zum Beispiel: Ich habe nur dünne Pappe. Wie kann ich den Halter stabiler machen?"></textarea>
        <div class="tl-actions"><button id="tl-send" type="submit" class="tl-primary">Jarvis fragen</button><button id="tl-stop" type="button" class="tl-secondary">Anfrage stoppen</button></div>
      </form>
      <p id="tl-status" class="tl-status" role="status">Beschreibe dein Ziel. Es wird nichts gebaut oder angeschlossen, nur weil du eine Frage stellst.</p>
    </section>
  </div>`;
}
