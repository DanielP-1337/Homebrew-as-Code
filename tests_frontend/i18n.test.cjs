const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.textContent = ''; }
  append(child) { this.children.push(child); }
  replaceChildren() { this.children = []; }
  querySelectorAll(tag) { return this.children.flatMap(c => [...(c.tagName === tag ? [c] : []), ...c.querySelectorAll(tag)]); }
}
global.HTMLElement = class extends Element {
  constructor() { super('card'); }
  attachShadow() { this.shadowRoot = new Element('shadow'); }
};
global.document = {createElement: tag => new Element(tag)};
const registry = new Map();
global.customElements = {get: key => registry.get(key), define: (key, cls) => registry.set(key, cls)};
global.window = {};
const directory = path.join(__dirname, '../custom_components/hbac/frontend/locales');
const dictionaries = Object.fromEntries(fs.readdirSync(directory).map(file => [file.replace('.json', ''), JSON.parse(fs.readFileSync(path.join(directory, file), 'utf8'))]));
const custom = new Map();
const requested = [];
global.fetch = async url => {
  requested.push(url);
  const locale = url.split('/').at(-1).split('?')[0].replace('.json', '');
  const data = url.startsWith('/local/') ? custom.get(locale) : dictionaries[locale];
  if (data === 'malformed') return {ok: true, json: async () => { throw new Error('bad JSON'); }};
  return data ? {ok: true, json: async () => data} : {ok: false};
};
require('../custom_components/hbac/frontend/hbac-card.js');
const I18n = window.HbacI18n;
const fresh = () => { I18n.cache.clear(); return new I18n(); };
(async () => {
  const expected = ['de', 'en-US', 'es', 'fr', 'it', 'nl', 'pl', 'pt'];
  assert(expected.every(language => language in dictionaries));
  const keys = Object.keys(dictionaries['en-US']).sort();
  for (const locale of Object.keys(dictionaries)) {
    if (expected.includes(locale)) assert.deepEqual(Object.keys(dictionaries[locale]).sort(), keys, locale + ': missing keys');
    for (const key of Object.keys(dictionaries[locale])) {
      assert.equal(typeof dictionaries[locale][key], 'string');
      assert(dictionaries[locale][key].trim());
      assert.equal(I18n.placeholders(dictionaries[locale][key]), I18n.placeholders(dictionaries['en-US'][key]), `${locale}: ${key}`);
    }
    const t = fresh(); await t.load(locale);
    assert.equal(t.t('ui.upload'), dictionaries[locale]['ui.upload'] || dictionaries['en-US']['ui.upload']);
    assert.equal(t.message('Der gekürzte Gerätename ist bereits in der Liste vorhanden.'), dictionaries[locale]['runtime.duplicate'] || dictionaries['en-US']['runtime.duplicate']);
    assert.equal(t.message('Gerätename: Märzen → Maerzen'), t.t('runtime.name_changed', {original: 'Märzen', name: 'Maerzen'}));
    assert.equal(t.message('Rast 2, Temperatur: ganze Zahl zwischen 20 und 80 erforderlich.'),
      t.t('runtime.integer', {field: t.t('runtime.rest_temp', {index: 2}), low: 20, high: 80}));
    assert.equal(t.message('Wasser und Wasserchemie'), t.t('runtime.water'));
    const guide = new (registry.get('hbac-help-card'))();
    guide.setConfig({});
    guide.hass = {locale: {language: locale}, callWS: () => { throw new Error('Help must not call services'); }};
    await guide.localeReady;
    assert.equal(guide.shadowRoot.querySelectorAll('h2')[0].textContent, dictionaries[locale]['ui.help'] || dictionaries['en-US']['ui.help']);
    assert.equal(guide.shadowRoot.querySelectorAll('h3').length, 5);
  }
  let t = fresh(); await t.load('de-AT'); assert.equal(t.t('ui.upload'), dictionaries.de['ui.upload']);
  t = fresh(); await t.load('pt-BR'); assert.equal(t.t('ui.upload'), dictionaries.pt['ui.upload']);
  t = fresh(); await t.load('sv-SE'); assert.equal(t.t('ui.upload'), dictionaries['en-US']['ui.upload']);
  custom.set('sv', {'ui.upload': 'Ersätt alla platser', 'ui.queue': 'Missing placeholder', 'ui.loading': 3});
  t = fresh(); await t.load('sv-SE'); assert.equal(t.t('ui.upload'), 'Ersätt alla platser');
  assert.equal(t.t('ui.queue', {count: 2}), '3 · Upload list (2/9)');
  assert.equal(t.t('ui.loading'), dictionaries['en-US']['ui.loading']);
  custom.set('de-CH', {'ui.upload': 'Schweizer Text'});
  t = fresh(); await t.load('de-ch'); assert.equal(t.t('ui.upload'), 'Schweizer Text');
  assert.equal(t.t('ui.help'), dictionaries.de['ui.help']);
  custom.set('fr', 'malformed'); t = fresh(); await t.load('fr'); assert.equal(t.t('ui.upload'), dictionaries.fr['ui.upload']);
  const before = requested.length;
  t = fresh(); await t.load('../../private');
  assert(requested.slice(before).every(url => !url.includes('..')));
  // All fetches may fail; embedded en-US still covers the complete interface.
  const originalFetch = global.fetch;
  global.fetch = async () => { throw new Error('offline'); };
  t = fresh(); await t.load('nl'); assert.equal(t.t('ui.help'), dictionaries['en-US']['ui.help']);
  global.fetch = originalFetch;
  // Per-card override and live HA language changes do not trigger a new upload.
  const card = new (registry.get('hbac-card'))();
  card.setConfig({}); card.loaded = true;
  card.state = {queue: [], revision: 'kept', job: null}; card.confirmed = true;
  card.hass = {locale: {language: 'de'}, callWS: () => { throw new Error('Language change must not call services'); }};
  await card.localeReady;
  card.hass = {locale: {language: 'nl'}, callWS: () => { throw new Error('Language change must not call services'); }};
  await card.localeReady;
  assert.equal(card.i18n.language, 'nl'); assert.equal(card.state.revision, 'kept'); assert(card.confirmed);
  card.setConfig({language: 'fr'}); await card.localeReady; assert.equal(card.i18n.language, 'fr');
  console.log(`i18n checks passed: ${expected.length} languages × ${keys.length} complete keys, help rendering, legacy messages, regional/custom/per-key/offline fallbacks, malformed JSON, safe paths and live language changes.`);
})().catch(err => { console.error(err); process.exitCode = 1; });
