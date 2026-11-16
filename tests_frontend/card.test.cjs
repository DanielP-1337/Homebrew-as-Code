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
const fs = require('node:fs');
const path = require('node:path');
global.fetch = async url => {
  if (!url.startsWith('/hbac/locales/')) return {ok: false};
  const file = path.join(__dirname, '../custom_components/hbac/frontend/locales', url.split('/').at(-1).split('?')[0]);
  return fs.existsSync(file) ? {ok: true, json: async () => JSON.parse(fs.readFileSync(file, 'utf8'))} : {ok: false};
};
require('../custom_components/hbac/frontend/hbac-card.js');

const flush = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  const card = new (registry.get('hbac-card'))();
  const calls = [];
  let reviewSteps = [{name: 'Rest', temperature: 63, minutes: 40}];
  const preview = {preview_id: 'p1', source: {name: '<img src=x onerror=alert(1)>', kind: 'batches', id: 'b1'},
    program: {name: 'Batch Test', mash_in_temperature: 63, rests: [{temperature: 63, minutes: 40}],
      boil_minutes: 60, boil_temperature: 103, hop_additions: [60, 15]}, warnings: ['Test warning'], not_transferred: ['Gärung']};
  let state = {entry_id: 'h1', queue: [], revision: 'rev1', job: null};
  card.setConfig({entry_id: 'h1'});
  card.hass = {locale: {language: 'de'}, callWS: async msg => {
    calls.push(msg);
    assert.equal(msg.service_data.entry_id, 'h1');
    assert.equal(msg.return_response, true);
    switch (msg.service) {
      case 'state': break;
      case 'import_file':
        assert.equal(Buffer.from(msg.service_data.content, 'base64').toString(), '<RECIPES/>');
        return {response: {items: [{id: 'token:0', name: 'XML Recipe'}]}};
      case 'open_file':
        assert.equal(msg.service_data.filename, 'one.xml');
        return {response: {items: [{id: 'filetoken:0', name: 'Folder Recipe'}]}};
      case 'catalog':
        if (msg.service_data.kind === 'beerxml_folder') return {response: {items: [{id: 'one.xml', name: 'one.xml'}]}};
        return {response: {items: [{id: 'b1', name: 'Batch Test', batch_no: 7}]}};
      case 'preview':
        if (msg.service_data.review_steps) return {response: {source_token: 'snapshot', steps: reviewSteps}};
        assert.equal(msg.service_data.source_token, 'snapshot');
        assert.equal(msg.service_data.step_roles.length, reviewSteps.length);
        return {response: structuredClone(preview)};
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
  await card.localeReady;
  await flush();
  const button = label => card.shadowRoot.querySelectorAll('button').find(b => b.textContent === label);
  const click = async label => { const b = button(label); assert(b, label); assert(!b.disabled, label); b.onclick(); await flush();
    if (label === 'Abrufen und Vorschau erstellen') {
      assert(card.stepReview); assert.equal(card.preview, null);
      const convert = button('Programmvorschau erstellen'); assert(convert && !convert.disabled);
      convert.onclick(); await flush();
    }
  };
  assert(button('Alle Geräteplätze ersetzen').disabled);
  const source = card.shadowRoot.querySelectorAll('select')[0];
  source.value = 'batches'; source.onchange();
  await click('Quellenliste laden');
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
  const previousUploads = calls.filter(c => c.service === 'upload').length;
  card.state.sources = ['recipes', 'batches', 'brewersfriend', 'beerxml_folder', 'beerxml_upload'];
  card.render();
  const changeSource = kind => {
    const select = card.shadowRoot.querySelectorAll('select')[0];
    select.value = kind; select.onchange();
  };
  changeSource('brewersfriend');
  await click('Quellenliste laden');
  assert.equal(calls.at(-1).service_data.kind, 'brewersfriend');
  changeSource('beerxml_upload');
  let file = card.shadowRoot.querySelectorAll('input').find(e => e.type === 'file');
  file.files = [{size: 10, arrayBuffer: async () => Buffer.from('<RECIPES/>')}];
  file.onchange(); await flush();
  let recipeSelect = card.shadowRoot.querySelectorAll('select')[1];
  recipeSelect.value = 'token:0'; recipeSelect.onchange();
  await click('Abrufen und Vorschau erstellen');
  assert.equal(calls.at(-1).service_data.kind, 'beerxml_upload');
  assert.equal(calls.at(-1).service_data.source_id, 'token:0');
  file = card.shadowRoot.querySelectorAll('input').find(e => e.type === 'file');
  file.files = [{size: 512 * 1024 + 1, arrayBuffer: () => { throw new Error('Must reject before reading'); }}];
  const beforeOversize = calls.length;
  file.onchange(); await flush();
  assert.equal(calls.length, beforeOversize);
  assert(card.error.includes('512'));
  changeSource('beerxml_folder');
  await click('Quellenliste laden');
  const folderSelect = card.shadowRoot.querySelectorAll('select')[1];
  folderSelect.value = 'one.xml'; folderSelect.onchange();
  await click('Ausgewählte Datei einlesen');
  recipeSelect = card.shadowRoot.querySelectorAll('select')[2];
  recipeSelect.value = 'filetoken:0'; recipeSelect.onchange();
  await click('Abrufen und Vorschau erstellen');
  assert.equal(calls.at(-1).service_data.kind, 'beerxml_folder');
  assert.equal(calls.at(-1).service_data.source_id, 'filetoken:0');
  assert.equal(calls.filter(c => c.service === 'upload').length, previousUploads);
  reviewSteps = [{name: 'Rest', temperature: 67.2222, minutes: 60}, {name: 'Sparge', temperature: 76.6667, minutes: 10}];
  changeSource('brewersfriend'); card.selected = '42'; card.render();
  button('Abrufen und Vorschau erstellen').onclick(); await flush();
  assert(button('Programmvorschau erstellen').disabled, 'Sparge requires an explicit choice');
  assert(!button('Geprüft · Zur Upload-Liste hinzufügen'));
  let stepSelect = card.shadowRoot.querySelector('#step-review').querySelectorAll('select')[1];
  stepSelect.value = 'manual_sparge'; stepSelect.onchange();
  await click('Programmvorschau erstellen');
  assert.deepEqual(calls.at(-1).service_data.step_roles, ['rest', 'manual_sparge']);
  stepSelect = card.shadowRoot.querySelector('#step-review').querySelectorAll('select')[1];
  stepSelect.value = 'rest'; stepSelect.onchange();
  assert.equal(card.preview, null, 'Changed step role invalidates program preview');
  assert(!button('Geprüft · Zur Upload-Liste hinzufügen'));
  assert.equal(calls.filter(c => c.service === 'upload').length, previousUploads);
  console.log('Card interactions passed: batch selection, preview, review, confirmation, single upload, status, editable mash-in, source text escaping.');
})().catch(error => { console.error(error); process.exitCode = 1; });
