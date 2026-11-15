// Interaction tests for the shipped card with a minimal DOM and mocked HA WS.
const assert = require('node:assert/strict');
class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.value = ''; this.textContent = ''; }
  append(child) { child.parent = this; this.children.push(child); }
  replaceChildren() { this.children = []; }
  remove() { this.parent.children = this.parent.children.filter(c => c !== this); }
  querySelectorAll(tag) { return this.children.flatMap(c => [...(c.tagName === tag ? [c] : []), ...c.querySelectorAll(tag)]); }
  querySelector(id) { return this.children.flatMap(c => [c, ...c.all()]).find(c => c.id === id.slice(1)); }
  all() { return this.children.flatMap(c => [c, ...c.all()]); }
}
global.HTMLElement = class extends Element {
  constructor() { super('hbac-card'); }
  attachShadow() { this.shadowRoot = new Element('shadow'); return this.shadowRoot; }
};
global.document = {createElement: tag => new Element(tag)};
const registry = new Map();
global.customElements = {get: key => registry.get(key), define: (key, cls) => registry.set(key, cls)};
global.window = {confirm: () => true};
require('../custom_components/hbac/frontend/hbac-card.js');

const flush = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  const card = new (registry.get('hbac-card'))();
  const calls = [];
  const preview = {preview_id: 'p1', source: {name: '<img src=x onerror=alert(1)>', kind: 'batches', id: 'b1'},
    program: {name: 'Batch Test', mash_in_temperature: 63, rests: [{temperature: 63, minutes: 40}],
      boil_minutes: 60, boil_temperature: 103, hop_additions: [60, 15]}, warnings: ['Test warning'], not_transferred: ['Gärung']};
  let state = {entry_id: 'h1', queue: [], revision: 'rev1', job: null};
  card.setConfig({entry_id: 'h1'});
  card.hass = {callWS: async msg => {
    calls.push(msg);
    assert.equal(msg.service_data.entry_id, 'h1');
    assert.equal(msg.return_response, true);
    switch (msg.service) {
      case 'state': break;
      case 'catalog': return {response: {items: [{id: 'b1', name: 'Batch Test', batch_no: 7}]}};
      case 'preview': return {response: structuredClone(preview)};
      case 'add': state.queue.push(structuredClone(preview)); state.revision = 'rev2'; break;
      case 'upload':
        assert.equal(msg.service_data.replace_all, true);
        assert.equal(msg.service_data.revision, 'rev2');
        state.job = {result: 'queued', job_id: 'j1', written: 0}; break;
      case 'status': state.job = {...state.job, result: 'confirmed', content_verification: 'matched'}; break;
      default: throw new Error('Unexpected action: ' + msg.service);
    }
    return {response: structuredClone(state)};
  }};
  await flush();
  const button = label => card.shadowRoot.querySelectorAll('button').find(b => b.textContent === label);
  const click = async label => { const b = button(label); assert(b, label); assert(!b.disabled, label); b.onclick(); await flush(); };
  assert(button('Alle Geräteplätze ersetzen').disabled);
  const source = card.shadowRoot.querySelectorAll('select')[0];
  source.value = 'batches'; source.onchange();
  await click('Liste aus Brewfather laden');
  const selection = card.shadowRoot.querySelectorAll('select')[1];
  selection.value = 'b1'; selection.onchange();
  await click('Abrufen und Vorschau erstellen');
  assert.equal(calls.at(-1).service_data.kind, 'batches');
  assert.equal(calls.at(-1).service_data.source_id, 'b1');
  assert(!('mash_in' in calls.at(-1).service_data));
  await click('Geprüft · Zur Upload-Liste hinzufügen');
  assert.equal(card.state.queue.length, 1);
  assert(button('Alle Geräteplätze ersetzen').disabled);
  assert(!card.shadowRoot.querySelectorAll('img').length, 'Source names must remain text');
  const check = card.shadowRoot.querySelectorAll('input').find(e => e.type === 'checkbox');
  check.checked = true; check.onchange();
  await click('Alle Geräteplätze ersetzen');
  assert.equal(calls.filter(c => c.service === 'upload').length, 1);
  assert(button('Alle Geräteplätze ersetzen').disabled);
  assert.equal(card.confirmed, false);
  await click('Auftragsstatus erneut abfragen');
  assert(card.statusBox.all().some(e => e.textContent === 'Inhalt durch Rücklesen bestätigt'));
  await click('Abrufen und Vorschau erstellen');
  const mash = card.shadowRoot.querySelectorAll('input').find(e => e.type === 'number' && e.min === 20);
  mash.value = '55'; mash.oninput();
  assert.equal(card.preview, null);
  assert(!button('Geprüft · Zur Upload-Liste hinzufügen'));
  await click('Abrufen und Vorschau erstellen');
  assert.equal(calls.at(-1).service_data.mash_in, 55);
  console.log('Card interactions passed: batch selection, preview, review, confirmation, single upload, status, editable mash-in, source text escaping.');
})().catch(error => { console.error(error); process.exitCode = 1; });
