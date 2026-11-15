// Embedded into hbac-card.js by scripts/build_frontend_i18n.py.
// Translation content is always rendered as text, never as HTML or executable code.
class HbacI18n {
  static cache = new Map();
  constructor() { this.strings = {...HBAC_EN_US}; this.language = "en-US"; }
  static normalize(value) {
    if (typeof value !== "string" || !/^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$/i.test(value)) return "en-US";
    try { return Intl.getCanonicalLocales(value)[0]; } catch (_) { return "en-US"; }
  }
  static placeholders(value) { return [...value.matchAll(/\{(\w+)\}/g)].map(m => m[1]).sort().join(","); }
  static async read(url) {
    if (!this.cache.has(url)) this.cache.set(url, (async () => {
      try {
        const response = await fetch(url, {credentials: "same-origin", cache: "no-cache", signal: AbortSignal.timeout(5000)});
        if (!response.ok) return {};
        const data = await response.json();
        if (!data || Array.isArray(data) || typeof data !== "object") return {};
        return Object.fromEntries(Object.entries(data).filter(([key, value]) =>
          typeof value === "string" && value.trim() && key !== "__proto__" && key !== "constructor" &&
          (!HBAC_EN_US[key] || this.placeholders(value) === this.placeholders(HBAC_EN_US[key]))));
      } catch (_) { return {}; }
    })());
    return this.cache.get(url);
  }
  async load(value) {
    const language = HbacI18n.normalize(value);
    const base = language.split("-")[0];
    // Merge from least to most specific; exact regional variants override base language.
    const candidates = [...new Set(["en-US", base, language])];
    const urls = candidates.flatMap(locale => [
      `/hbac/locales/${locale}.json?v=${HBAC_VERSION}`,
      `/local/hbac/locales/${locale}.json?v=${HBAC_VERSION}`,
    ]);
    const dictionaries = await Promise.all(urls.map(url => HbacI18n.read(url)));
    this.strings = Object.assign({}, HBAC_EN_US, ...dictionaries);
    this.language = language;
  }
  t(key, params = {}) {
    const template = this.strings[key] || HBAC_EN_US[key] || key;
    return template.replace(/\{(\w+)\}/g, (match, name) => params[name] === undefined ? match : String(params[name]));
  }
  message(value, depth = 0) {
    if (value && typeof value === "object" && typeof value.key === "string") {
      return this.t(value.key, value.params || {});
    }
    const text = String(value ?? "");
    if (depth > 3) return text;
    // Keep Beta 1's persisted German warning strings readable in every language.
    for (const [key, pattern, names] of HBAC_MESSAGE_PATTERNS) {
      const match = text.match(new RegExp(pattern, "s"));
      if (!match) continue;
      const params = Object.fromEntries(names.map((name, i) => {
        let v = match[i + 1];
        if (name === "field") v = this.message(v, depth + 1);
        if (name === "use" && HBAC_EN_US[`hop.${v}`]) v = this.t(`hop.${v}`);
        if (name === "type" && HBAC_EN_US[`rest.${v}`]) v = this.t(`rest.${v}`);
        if (name === "reasons") v = v.split(", ").map(r => this.t(`reason.${r}`)).join(", ");
        // Recipe names and ingredient labels remain untouched.
        return [name, v];
      }));
      return this.t(key, params);
    }
    return text; // Errors originating outside HBAC remain diagnostic text.
  }
}
window.HbacI18n = HbacI18n;
