/* HBAC 0.4.0-beta.1. No third-party scripts; credentials stay in HA. */
class HbacCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
    this.kind = this.kind || "recipes";
    this.items = this.items || [];
    this.selected = this.selected || "";
    this.mash = this.mash || "";
    this.boil = this.boil || "103";
    if (!this.shadowRoot) this.attachShadow({mode: "open"});
    this.render();
  }
  set hass(value) {
    this._hass = value;
    if (!this.loaded && this.config && !this.busy) {
      this.loaded = true;
      this.run(async () => { this.state = await this.call("state"); });
    }
  }
  connectedCallback() {
    this.timer = setInterval(async () => {
      if (!this._hass || this.busy || !this.loaded) return;
      try {
        const state = await this.call("state");
        if (this.state && state.revision !== this.state.revision) {
          this.state = state;
          this.confirmed = false;
          this.render();
        } else {
          this.state = state;
          this.renderStatus();
        }
      } catch (_) { /* Explicit actions surface connection errors. */ }
    }, 2000);
  }
  disconnectedCallback() { clearInterval(this.timer); }
  getCardSize() { return 10; }
  static getStubConfig() { return {}; }
  async call(service, data = {}) {
    const result = await this._hass.callWS({type: "call_service", domain: "hbac", service,
      service_data: {...(this.config.entry_id ? {entry_id: this.config.entry_id} : {}), ...data},
      return_response: true});
    return result.response;
  }
  async run(fn) {
    if (this.busy) return;
    this.busy = true;
    this.error = "";
    this.shadowRoot.querySelectorAll("button").forEach(b => b.disabled = true);
    try { await fn(); } catch (err) { this.error = err.message || String(err); }
    finally { this.busy = false; this.render(); }
  }
  node(tag, text, parent, cls) {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (cls) el.className = cls;
    if (parent) parent.append(el);
    return el;
  }
  button(parent, text, fn, disabled = false) {
    const b = this.node("button", text, parent);
    b.disabled = disabled || this.busy;
    b.onclick = () => this.run(fn);
    return b;
  }
  field(parent, label, value, oninput, type = "text") {
    const wrapper = this.node("label", label, parent);
    const input = this.node("input", undefined, wrapper);
    input.type = type;
    input.value = value;
    input.oninput = () => oninput(input.value);
    return input;
  }
  program(parent, preview) {
    const p = preview.program;
    this.node("strong", p.name, parent);
    this.node("p", `Einmaischen ${p.mash_in_temperature} °C · Kochen ${p.boil_minutes} min bei ${p.boil_temperature} °C`, parent);
    this.node("p", "Rasten: " + p.rests.map(r => `${r.temperature} °C / ${r.minutes} min`).join(" → "), parent);
    this.node("p", "Hopfenalarme (Restkochzeit): " + (p.hop_additions.join(", ") || "keine") + " min", parent);
    const list = this.node("ul", undefined, parent);
    preview.warnings.forEach(w => this.node("li", w, list));
    this.node("p", "Nicht übertragen: " + preview.not_transferred.join(", "), parent, "muted");
  }
  render() {
    if (!this.shadowRoot || !this.config) return;
    this.shadowRoot.replaceChildren();
    this.node("style", `
      :host {display:block} ha-card {padding:20px;color:var(--primary-text-color)}
      h2{margin:0 0 8px} h3{margin:24px 0 10px} p{line-height:1.5;margin:8px 0}
      label{display:block;margin:12px 0;font-size:14px} input,select{display:block;box-sizing:border-box;
      width:100%;padding:10px;margin-top:6px;border:1px solid var(--divider-color);border-radius:6px;
      color:var(--primary-text-color);background:var(--card-background-color)}
      button{padding:10px 14px;margin:4px 6px 4px 0;border:1px solid var(--divider-color);border-radius:6px;
      color:var(--primary-text-color);background:var(--secondary-background-color);cursor:pointer}
      button:disabled{opacity:.45;cursor:default} .box{border:1px solid var(--divider-color);border-radius:8px;padding:12px;margin:12px 0}
      .muted{color:var(--secondary-text-color);font-size:13px}.error{color:var(--error-color);white-space:pre-wrap}
      li{margin:5px 0} input[type=checkbox]{display:inline-block;width:auto;margin-right:8px}
      .check{display:flex;align-items:center} details{margin:8px 0} summary{cursor:pointer}
    `, this.shadowRoot);
    const card = this.node("ha-card", undefined, this.shadowRoot);
    this.node("h2", "HBAC · Brewfather", card);
    this.node("p", "Rezepte prüfen und auf den Braumeister übertragen", card, "muted");
    if (this.error) this.node("p", this.error, card, "error");
    if (!this.state) {
      this.node("p", "HBAC-Verbindung laden …", card);
      this.button(card, "Erneut verbinden", async () => { this.state = await this.call("state"); });
      return;
    }
    this.node("h3", "1 · Rezept oder Batch auswählen", card);
    const sourceLabel = this.node("label", "Quelle", card);
    const source = this.node("select", undefined, sourceLabel);
    for (const [v, label] of [["recipes", "Rezepte"], ["batches", "Batches (eigenes Batch-Rezept)"]]) {
      const option = this.node("option", label, source); option.value = v;
    }
    source.value = this.kind;
    source.onchange = () => { this.kind = source.value; this.items = []; this.selected = ""; this.preview = null; this.mash = ""; this.render(); };
    this.button(card, "Liste aus Brewfather laden", async () => {
      this.items = (await this.call("catalog", {kind: this.kind, refresh: true})).items;
      this.catalogLoaded = this.kind;
    });
    if (this.items.length) {
      const listLabel = this.node("label", "Auswahl", card);
      const select = this.node("select", undefined, listLabel);
      const blank = this.node("option", "Bitte auswählen", select); blank.value = "";
      this.items.forEach(item => {
        const option = this.node("option", `${item.batch_no != null ? "#" + item.batch_no + " · " : ""}${item.name}${item.status ? " · " + item.status : ""}`, select);
        option.value = item.id;
      });
      select.value = this.selected;
      select.onchange = () => { this.selected = select.value; this.preview = null; this.mash = ""; this.render(); };
    } else if (this.catalogLoaded === this.kind) this.node("p", "Keine Einträge gefunden. Alternativ eine bekannte ID eingeben.", card);
    this.field(card, "Rezept-/Batch-ID (auch direkt eingebbar)", this.selected, value => {
      this.selected = value.trim(); this.preview = null; this.mash = "";
      this.shadowRoot.querySelector("#preview-box")?.remove();
    });
    const mash = this.field(card, "Einmaischtemperatur °C – leer: erste Rast", this.mash, value => {
      this.mash = value; this.preview = null; this.shadowRoot.querySelector("#preview-box")?.remove();
    }, "number"); mash.min = 20; mash.max = 80; mash.step = 1;
    const boil = this.field(card, "Kochtemperatur °C", this.boil, value => {
      this.boil = value; this.preview = null; this.shadowRoot.querySelector("#preview-box")?.remove();
    }, "number"); boil.min = 95; boil.max = 105; boil.step = 1;
    this.button(card, "Abrufen und Vorschau erstellen", async () => {
      if (!this.selected) throw new Error("Bitte Rezept oder Batch auswählen bzw. ID eingeben.");
      this.preview = await this.call("preview", {kind: this.kind, source_id: this.selected,
        ...(this.mash !== "" ? {mash_in: Number(this.mash)} : {}), boil_temperature: Number(this.boil)});
    });
    if (this.preview) {
      const box = this.node("div", undefined, card, "box"); box.id = "preview-box";
      this.node("h3", "2 · Konvertierung prüfen", box);
      this.program(box, this.preview);
      this.button(box, "Geprüft · Zur Upload-Liste hinzufügen", async () => {
        this.state = await this.call("add", {preview_id: this.preview.preview_id, revision: this.state.revision});
        this.preview = null; this.confirmed = false;
      }, this.state.queue.length >= 9);
    }
    this.node("h3", `3 · Upload-Liste (${this.state.queue.length}/9)`, card);
    this.state.queue.forEach((item, index) => {
      const box = this.node("div", undefined, card, "box");
      this.node("strong", `${index + 1}. ${item.source.name}`, box);
      const detail = this.node("details", undefined, box);
      this.node("summary", "Geräteprogramm und Hinweise", detail); this.program(detail, item);
      const change = async (service, data) => {
        this.state = await this.call(service, {...data, revision: this.state.revision}); this.confirmed = false;
      };
      this.button(box, "↑", () => change("move", {index, target: index - 1}), index === 0).ariaLabel = "Rezept nach oben";
      this.button(box, "↓", () => change("move", {index, target: index + 1}), index === this.state.queue.length - 1).ariaLabel = "Rezept nach unten";
      this.button(box, "Entfernen", () => change("remove", {index}));
    });
    if (!this.state.queue.length) this.node("p", "Noch keine Rezepte hinzugefügt.", card, "muted");
    this.node("p", "Der Upload ersetzt ALLE Rezepte auf dem Gerät durch diese Liste in der gezeigten Reihenfolge.", card);
    const checkLabel = this.node("label", undefined, card, "check");
    const check = this.node("input", undefined, checkLabel); check.type = "checkbox"; check.checked = !!this.confirmed;
    this.node("span", "Ich habe die Liste geprüft und möchte alle Geräteplätze ersetzen.", checkLabel);
    check.onchange = () => { this.confirmed = check.checked; this.render(); };
    this.button(card, "Gerätebereitschaft prüfen", async () => { this.state = await this.call("readiness"); });
    this.button(card, "Alle Geräteplätze ersetzen", async () => {
      this.confirmed = false;
      this.state = await this.call("upload", {revision: this.state.revision, replace_all: true});
    }, !this.confirmed || !this.state.queue.length || ["queued", "sending", "submitting", "outcome_unknown"].includes(this.state.job?.result));
    this.statusBox = this.node("div", undefined, card, "box");
    this.renderStatus();
  }
  renderStatus() {
    const box = this.statusBox;
    if (!box || !this.state) return;
    box.replaceChildren();
    this.node("strong", "Gerät und Uploadauftrag", box);
    const readiness = this.state.readiness;
    const reasons = {upload_disabled: "Upload in Bridge deaktiviert", device_status_stale: "Gerätestatus veraltet",
      device_status_unreadable: "Gerätestatus nicht lesbar", device_not_idle: "Hauptmenü erforderlich, Pumpe und Heizung aus", busy: "Gerät beschäftigt"};
    if (readiness) this.node("p", readiness.ready_for_upload ? "Bei letzter Prüfung bereit (wird vor Upload erneut geprüft)." :
      "Nicht bereit: " + (readiness.blocking_reasons || []).map(r => reasons[r] || r).join(", "), box);
    const job = this.state.job;
    if (job) {
      const labels = {queued: "In Warteschlange", sending: "Übertragung läuft", submitting: "Upload wird angefordert",
        confirmed: "Rezeptanzahl vom Gerät bestätigt", state_changed: "Abgebrochen: Gerätezustand geändert",
        unconfirmed: "Übertragung nicht bestätigt", outcome_unknown: "Uploadausgang unklar – nicht erneut senden",
        manually_released: "Nach manueller Geräteprüfung freigegeben"};
      this.node("p", labels[job.result] || job.result, box);
      if (job.job_id) this.node("p", `Auftrag: ${job.job_id} · bestätigte Plätze: ${job.written ?? "–"}`, box, "muted");
      const verification = {matched: "Inhalt durch Rücklesen bestätigt", mismatch: "FEHLER: zurückgelesener Inhalt weicht ab", not_available: "Inhaltsprüfung steht aus / kein Rücklesen verfügbar"};
      this.node("p", verification[job.content_verification || "not_available"], box, job.content_verification === "mismatch" ? "error" : "muted");
      if (job.job_id) this.button(box, "Auftragsstatus erneut abfragen", async () => { this.state = await this.call("status"); });
      if (["outcome_unknown", "queued", "sending"].includes(job.result)) {
        const details = this.node("details", undefined, box);
        this.node("summary", "Manuelle Wiederherstellung", details);
        this.node("p", "Nur verwenden, wenn du am Gerät und an der Bridge geprüft hast, dass kein Auftrag mehr läuft. Ein abgebrochener Upload kann eine unvollständige Rezeptliste hinterlassen.", details);
        this.button(details, "Gerät geprüft, Auftrag beendet · Sperre aufheben", async () => {
          if (!window.confirm("Kein Upload läuft mehr und das Gerät wurde manuell geprüft? Dies sendet kein Rezept.")) return;
          this.state = await this.call("acknowledge_unknown", {device_checked: true}); this.confirmed = false;
        });
      }
    } else this.node("p", "Noch kein Upload gestartet.", box, "muted");
    if (this.state.error) this.node("p", this.state.error, box, "error");
  }
}
if (!customElements.get("hbac-card")) customElements.define("hbac-card", HbacCard);
window.customCards = window.customCards || [];
window.customCards.push({type: "hbac-card", name: "HBAC · Brewfather", description: "Rezepte und Batches prüfen und über die Braumeister Bridge hochladen"});
