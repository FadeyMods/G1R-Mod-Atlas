// Gemeinsame Oberfläche für Webseite und Desktop-App.
// In der App stellt pywebview window.pywebview.api bereit (Installieren, Updaten, Spiel starten).

const CATS = ["VOXEL", "QOL", "UI", "GAMEPLAY", "CONTENT", "BALANCE", "ART", "AUDIO", "TRANSLATION", "TOTAL_CONVERSION", "LIBRARY", "TOOL", "CART", "OTHER"];
const STATUSES = ["active", "inactive", "wip", "abandoned", "archived", "deleted"];
const SOURCES = ["index", "github", "gamebanana", "discord"];
const VISIBLE_KINDS = ["mod", "cart", "tool"];
const CAT_COLOR = {
  VOXEL: ["#5b3cc4", "#2fa9e0"], QOL: ["#1f9d6b", "#7bd389"], UI: ["#2b5fa8", "#5fb0ff"], GAMEPLAY: ["#c2410c", "#f59e0b"],
  CONTENT: ["#9d174d", "#f472b6"], BALANCE: ["#4d7c0f", "#a3e635"], ART: ["#b45309", "#fcd34d"], AUDIO: ["#0f766e", "#2dd4bf"],
  TRANSLATION: ["#1e40af", "#93c5fd"], TOTAL_CONVERSION: ["#7f1d1d", "#ef4444"], LIBRARY: ["#374151", "#9ca3af"],
  TOOL: ["#334155", "#64748b"], CART: ["#6b21a8", "#e879f9"], OTHER: ["#3f3f46", "#a1a1aa"],
};
const PAGE = 48;

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const locale = () => I18N[LANG]._locale;
const fmtDate = (iso) => (iso ? new Date(iso).toLocaleDateString(locale(), { day: "2-digit", month: "short", year: "numeric" }) : "–");
const num = (n) => Number(n || 0).toLocaleString(locale());
const vnorm = (v) => String(v || "").trim().replace(/^v/i, "");

let data = null;
let byId = {};
let mods = [];             // nur Haupteinträge
let view = "browse";
let shown = PAGE;
const sel = { cat: new Set(), gen: new Set(), status: new Set(), src: new Set() };
let api = null;            // Desktop-App-Brücke
let appState = { installed: {}, settings: {} };

// ---------------------------------------------------------------- Daten

function primaryMods() {
  const showHidden = $("#show-hidden").checked;
  return data.mods.filter((m) => m.family === m.id && (showHidden ? m.kind !== "discussion" : VISIBLE_KINDS.includes(m.kind)));
}

function isInstallable(m) {
  const u = (m.latest && m.latest.url) || "";
  return !!u && m.status !== "deleted" && !m.id.startsWith("dc:");
}

function ownRec(m) { return appState.installed[m.id] || (m.manifest_id && appState.installed["manifest:" + m.manifest_id]); }
// Auch eine installierte Variante (anderer Fork/Spiegel) zählt als "installiert"
function installedRec(m) {
  return ownRec(m) || (m.variants || []).map((v) => byId[v] && ownRec(byId[v])).find(Boolean);
}
function hasUpdate(m) {
  const r = ownRec(m);
  return !!(r && m.latest && m.latest.version && vnorm(r.version) !== vnorm(m.latest.version));
}

// ---------------------------------------------------------------- Filter

function chips(el, key, entries) {
  el.innerHTML = entries.map(([v, label, n]) =>
    `<button class="chip${sel[key].has(v) ? " on" : ""}" data-k="${key}" data-v="${esc(v)}">${esc(label)}<small>${n}</small></button>`).join("");
}

function counts(list, fn) {
  const c = {};
  for (const m of list) for (const v of fn(m)) c[v] = (c[v] || 0) + 1;
  return c;
}

function baseList() {
  let list = mods;
  if (view === "installed") return list.filter((m) => installedRec(m));
  if ($("#only-installable").checked) list = list.filter(isInstallable);
  return list;
}

function renderFilters() {
  const base = baseList();
  const gc = counts(base, (m) => m.gens || []);
  chips($("#f-gen"), "gen", [1, 2, 3].filter((g) => gc[g]).map((g) => [String(g), t(`gen.${g}`), gc[g]]));
  const cc = counts(base, (m) => [m.categories[0]]);
  chips($("#f-cat"), "cat", CATS.filter((k) => cc[k]).map((k) => [k, t(`cat.${k}`), cc[k]]));
  const sc = counts(base, (m) => [m.status]);
  chips($("#f-status"), "status", STATUSES.filter((k) => sc[k]).map((k) => [k, t(`status.${k}`), sc[k]]));
  const rc = counts(base, (m) => Object.keys(m.sources || {}));
  chips($("#f-src"), "src", SOURCES.filter((k) => rc[k]).map((k) => [k, t(`src.${k}`), rc[k]]));
}

function matches(m, q) {
  if (sel.cat.size && !sel.cat.has(m.categories[0])) return false;
  if (sel.gen.size && !(m.gens || []).some((g) => sel.gen.has(String(g)))) return false;
  if (sel.status.size && !sel.status.has(m.status)) return false;
  if (sel.src.size && !Object.keys(m.sources || {}).some((s) => sel.src.has(s))) return false;
  if (!q) return true;
  return `${m.name} ${m.author} ${m.summary} ${m.repo || ""}`.toLowerCase().includes(q);
}

function sortList(list) {
  const pop = (m) => (m.downloads || 0) + (m.stars || 0) * 50;
  const by = {
    activity: (a, b) => (b.last_activity || "").localeCompare(a.last_activity || ""),
    popular: (a, b) => pop(b) - pop(a),
    new: (a, b) => (b.first_seen || "").localeCompare(a.first_seen || "") || (b.last_activity || "").localeCompare(a.last_activity || ""),
    name: (a, b) => a.name.localeCompare(b.name, locale()),
  }[$("#sort").value];
  return list.sort(by);
}

function currentList() {
  const q = $("#q").value.trim().toLowerCase();
  return sortList(baseList().filter((m) => matches(m, q)));
}

// ---------------------------------------------------------------- Karten

function initials(name) {
  const w = name.replace(/[\[\(].*?[\]\)]/g, "").replace(/[^A-Za-z0-9 ]/g, " ").trim().split(/\s+/);
  return ((w[0] || "?")[0] + (w[1] ? w[1][0] : (w[0] || "")[1] || "")).toUpperCase();
}

function thumb(m, big) {
  const [a, b] = CAT_COLOR[m.categories[0]] || CAT_COLOR.OTHER;
  const ph = `<div class="ph" style="background:linear-gradient(135deg,${a},${b})">${esc(initials(m.name))}</div>`;
  const img = m.thumbnail ? `<img loading="lazy" src="${esc(m.thumbnail)}" alt="" onerror="this.remove()">` : "";
  return `<div class="thumb">${ph}${img}${big ? "" : badges(m)}</div>`;
}

function badges(m) {
  let right = "";
  if (api && hasUpdate(m)) right = `<span class="pill upd">${t("update")}</span>`;
  else if (api && installedRec(m)) right = `<span class="pill inst">${t("installed")}</span>`;
  return `<div class="badges"><span class="pill st-${m.status}">${esc(t(`status.${m.status}`))}</span>${right}</div>`;
}

function card(m) {
  const ver = m.latest && m.latest.version ? esc(m.latest.version) : "";
  const v = m.variants && m.variants.length ? `<span class="more-var">${t("variants", { n: m.variants.length })}</span>` : "";
  return `<article class="card" data-id="${esc(m.id)}" tabindex="0">
    ${thumb(m)}
    <div class="body">
      <div class="title">${esc(m.name)}</div>
      ${m.author ? `<div class="by">${t("by")} ${esc(m.author)}</div>` : ""}
      ${m.summary ? `<div class="sum">${esc(m.summary)}</div>` : ""}
      <div class="foot-row">
        <div class="tags"><span class="tag">${esc(t(`cat.${m.categories[0]}`))}</span>${(m.gens || []).map((g) => `<span class="tag">G${g}</span>`).join("")}</div>
        <span class="ver">${ver}</span>
      </div>
      ${v}
    </div>
  </article>`;
}

function render() {
  if (!data) return;
  const list = currentList();
  $("#count").innerHTML = t("count", { n: num(list.length) });
  const grid = $("#grid");
  if (!list.length) {
    grid.innerHTML = `<p class="empty">${view === "installed" ? t("installedEmpty") : t("noResults")}</p>`;
    return;
  }
  grid.innerHTML = list.slice(0, shown).map(card).join("");
}

function rerender() { shown = PAGE; renderFilters(); render(); }

// ---------------------------------------------------------------- Detailansicht

function actionButtons(m) {
  const out = [];
  if (api) {
    const rec = installedRec(m);
    if (rec) {
      if (hasUpdate(m)) out.push(`<button class="btn upd" data-act="install" data-id="${esc(m.id)}">${t("update")} → ${esc(m.latest.version)}</button>`);
      else out.push(`<button class="btn ok" disabled>✓ ${t("installed")} ${esc(rec.version || "")}</button>`);
      out.push(`<button class="btn ghost" data-act="open" data-id="${esc(m.id)}">${t("openFolder")}</button>`);
      out.push(`<button class="btn ghost" data-act="uninstall" data-id="${esc(m.id)}">${t("uninstall")}</button>`);
    } else if (isInstallable(m)) {
      out.push(`<button class="btn primary" data-act="install" data-id="${esc(m.id)}">${t("install")} ${esc(m.latest.version || "")}</button>`);
    }
  } else if (isInstallable(m)) {
    out.push(`<a class="btn primary" href="${esc(m.latest.url)}">${t("download")} ${esc(m.latest.version || "")}</a>`);
  }
  return out.join("");
}

function linkList(m) {
  const s = m.sources || {};
  const l = [];
  if (s.github) l.push(`<a href="${esc(s.github)}" target="_blank">GitHub</a>`);
  if (s.index) l.push(`<a href="${esc(s.index)}" target="_blank">${t("src.index")}</a>`);
  if (s.gamebanana) l.push(`<a href="${esc(s.gamebanana)}" target="_blank">GameBanana</a>`);
  if (s.discord) l.push(`<a href="${esc(s.discord)}" target="_blank">Discord</a>`);
  if (m.repo && m.status !== "deleted") l.push(`<a href="https://github.com/${esc(m.repo)}/fork" target="_blank">${t("fork")}</a>`);
  if (m.repo && m.status === "deleted") {
    l.push(`<a target="_blank" href="https://archive.softwareheritage.org/browse/origin/directory/?origin_url=${encodeURIComponent("https://github.com/" + m.repo)}">${t("archive")}</a>`);
    l.push(`<a target="_blank" href="https://github.com/search?q=${encodeURIComponent(m.repo.split("/")[1])}&type=repositories">${t("findForks")}</a>`);
  }
  return l.join("");
}

function variantRow(v) {
  const s = v.sources || {};
  const link = s.github ? `<a target="_blank" href="${esc(s.github)}">GitHub</a>` : s.gamebanana ? `<a target="_blank" href="${esc(s.gamebanana)}">GameBanana</a>` : s.discord ? `<a target="_blank" href="${esc(s.discord)}">Discord</a>` : "";
  const ver = v.latest && v.latest.version ? ` · ${esc(v.latest.version)}` : "";
  let btn = "";
  if (isInstallable(v)) {
    btn = api
      ? ` <button class="btn ghost" data-act="install" data-id="${esc(v.id)}">${t("install")}</button>`
      : ` <a class="btn ghost" href="${esc(v.latest.url)}">${t("download")}</a>`;
  }
  return `<div class="var"><span>${esc(v.name)} <span class="by">${esc(v.repo || v.id)}</span></span>
    <span class="by">${esc(t(`status.${v.status}`))}${ver}${link ? " · " + link : ""}${btn}</span></div>`;
}

function openDrawer(id) {
  const m = byId[id];
  if (!m) return;
  const notes = [];
  if (m.status === "deleted") notes.push(t("deletedNote"));
  if (m.status === "wip" && !isInstallable(m)) notes.push(t("wipNote"));
  if (isInstallable(m) && /\/archive\//.test(m.latest.url)) notes.push(t("sourceZipNote"));
  const vars = (m.variants || []).map((vid) => byId[vid]).filter(Boolean);
  const facts = [
    [t("version"), (m.latest && m.latest.version) || "–"],
    [t("updatedOn"), fmtDate(m.last_activity)],
    [t("games"), (m.gens || []).map((g) => "Gen " + g).join(", ")],
    [t("category"), t(`cat.${m.categories[0]}`)],
    [t("statusLabel"), t(`status.${m.status}`)],
    m.downloads ? [t("downloads"), num(m.downloads)] : m.stars != null ? [t("stars"), num(m.stars)] : null,
  ].filter(Boolean);
  $("#drawer-panel").innerHTML = `
    <button class="x" data-close aria-label="×">×</button>
    ${thumb(m, true)}
    <div class="d-in">
      <div><h2>${esc(m.name)}</h2>${m.author ? `<div class="by">${t("by")} ${esc(m.author)} · ${m.in_index ? t("inIndex") : t("notInIndex")}</div>` : ""}</div>
      <div class="actions">${actionButtons(m)}</div>
      ${notes.map((n) => `<div class="note">${esc(n)}</div>`).join("")}
      <div class="facts">${facts.map(([k, v]) => `<div class="fact"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join("")}</div>
      ${m.summary ? `<div class="desc">${esc(m.summary)}</div>` : ""}
      <div class="desc" id="long-desc"></div>
      <div class="linklist">${linkList(m)}</div>
      ${vars.length ? `<div><h4>${t("variantsTitle")}</h4><div class="vars">${vars.map(variantRow).join("")}</div></div>` : ""}
    </div>`;
  $("#drawer").hidden = false;
  history.replaceState(null, "", "#mod=" + encodeURIComponent(m.id));
  loadLongDescription(m);
}

async function loadLongDescription(m) {
  const folder = m.sources && m.sources.index && m.sources.index.split("#")[1];
  if (!folder) return;
  try {
    const r = await fetch(`https://bryanthaboi.github.io/gen1recomp-mod-index/data/mods/${folder}/description.md`);
    if (!r.ok) return;
    const md = (await r.text()).replace(/!\[[^\]]*\]\([^)]*\)/g, "").replace(/[#*_`>]/g, "").trim();
    const el = $("#long-desc");
    if (el) el.textContent = md.slice(0, 2500);
  } catch {}
}

// ---------------------------------------------------------------- Änderungen

async function renderChanges() {
  const el = $("#changes");
  try {
    const hist = api ? await api.get_changes() : await (await fetch("data/changes.json", { cache: "no-store" })).json();
    if (!hist || !hist.length) { el.innerHTML = `<p class="empty">${t("noRuns")}</p>`; return; }
    const li = (arr, f) => arr.length
      ? `<ul>${arr.slice(0, 40).map(f).join("")}</ul>${arr.length > 40 ? `<p class="empty">${t("andMore", { n: arr.length - 40 })}</p>` : ""}`
      : `<p class="empty">${t("none")}</p>`;
    el.innerHTML = hist.slice(0, 20).map((r) => `<div class="run"><h3>${new Date(r.date).toLocaleString(locale())}</h3>
      <b>${t("updates")} (${r.updated.length})</b>${li(r.updated, (x) => `<li>${esc(x.name)}: ${esc(x.from)} → ${esc(x.to)}</li>`)}
      <b>${t("newFound")} (${r.new.length})</b>${li(r.new, (x) => `<li>${esc(x.name)}</li>`)}
      <b>${t("statusChanges")} (${r.status_changed.length})</b>${li(r.status_changed, (x) => `<li>${esc(x.name)}: ${esc(t(`status.${x.from}`))} → ${esc(t(`status.${x.to}`))}</li>`)}
    </div>`).join("");
  } catch {
    el.innerHTML = `<p class="empty">${t("noChanges")}</p>`;
  }
}

// ---------------------------------------------------------------- App-Aktionen

function toast(msg, ms = 3200) {
  const el = $("#toast");
  el.textContent = msg; el.hidden = false;
  clearTimeout(toast._t); toast._t = setTimeout(() => (el.hidden = true), ms);
}

async function refreshState() {
  appState = await api.get_state();
  const n = Object.keys(appState.installed).filter((k) => !k.startsWith("manifest:")).length;
  $("#n-installed").textContent = n || "";
}

async function doAction(act, id) {
  const m = byId[id];
  if (act === "install") {
    toast(`${t("installing")} ${m.name}`, 60000);
    const r = await api.install(m);
    toast(r.ok ? `${t("done")}: ${m.name} ${r.version || ""}` : `${t("failed")}: ${r.error}`, r.ok ? 3200 : 8000);
  } else if (act === "uninstall") {
    if (!confirm(t("confirmUninstall"))) return;
    const r = await api.uninstall(m);
    toast(r.ok ? t("done") : `${t("failed")}: ${r.error}`);
  } else if (act === "open") {
    await api.open_folder(m);
    return;
  }
  await refreshState();
  openDrawer(byId[id].family || id);
  rerender();
}

async function checkUpdates() {
  await refreshState();
  const upd = mods.filter(hasUpdate);
  if (!upd.length) { toast(t("noUpdates")); return; }
  if (confirm(`${t("updatesAvailable", { n: upd.length })}\n\n${upd.map((m) => `• ${m.name}: ${installedRec(m).version} → ${m.latest.version}`).join("\n")}\n\n${t("updateAll")}?`)) {
    for (const m of upd) {
      toast(`${t("installing")} ${m.name}`, 60000);
      await api.install(m);
    }
    await refreshState(); rerender(); toast(t("done"));
  }
}

function openSettings() {
  $("#set-save").value = appState.settings.save_dir || "";
  $("#set-exe").value = appState.settings.game_exe || "";
  $("#set-feed").value = appState.settings.feed_url || "";
  $("#settings").hidden = false;
}

// ---------------------------------------------------------------- Start

function setView(v) {
  view = v;
  document.querySelectorAll(".view").forEach((b) => b.classList.toggle("on", b.dataset.view === v));
  $("#v-browse").hidden = v === "changes";
  $("#v-changes").hidden = v !== "changes";
  if (v === "changes") renderChanges(); else rerender();
}

function load(d) {
  data = d;
  byId = Object.fromEntries(d.mods.map((m) => [m.id, m]));
  mods = primaryMods();
  $("#gen-at").textContent = new Date(d.generated_at).toLocaleString(locale());
  rerender();
  // Teilbarer Link auf einen Mod: ...#mod=<id>
  const h = decodeURIComponent(location.hash || "");
  if (h.startsWith("#mod=") && byId[h.slice(5)]) openDrawer(byId[h.slice(5)].family || h.slice(5));
}

function renderAll() {
  applyStatic();
  if (data) { $("#gen-at").textContent = new Date(data.generated_at).toLocaleString(locale()); rerender(); }
  if (view === "changes") renderChanges();
}

document.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (chip) {
    const set = sel[chip.dataset.k];
    set.has(chip.dataset.v) ? set.delete(chip.dataset.v) : set.add(chip.dataset.v);
    chip.classList.toggle("on"); shown = PAGE; render(); return;
  }
  const c = e.target.closest(".card");
  if (c) { openDrawer(c.dataset.id); return; }
  if (e.target.closest("[data-close]")) { e.target.closest(".drawer").hidden = true; history.replaceState(null, "", location.pathname + location.search); return; }
  const v = e.target.closest(".view");
  if (v) { setView(v.dataset.view); return; }
  const a = e.target.closest("[data-act]");
  if (a && api) { doAction(a.dataset.act, a.dataset.id); }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") document.querySelectorAll(".drawer").forEach((d) => (d.hidden = true));
  if (e.key === "Enter" && e.target.classList.contains("card")) openDrawer(e.target.dataset.id);
});
$("#q").addEventListener("input", () => { shown = PAGE; render(); });
$("#sort").addEventListener("change", () => { shown = PAGE; render(); });
$("#only-installable").addEventListener("change", rerender);
$("#show-hidden").addEventListener("change", () => { mods = primaryMods(); rerender(); });
$("#reset").addEventListener("click", () => { Object.values(sel).forEach((s) => s.clear()); $("#q").value = ""; rerender(); });
new IntersectionObserver((es) => { if (es[0].isIntersecting && data) { shown += PAGE; render(); } }, { rootMargin: "600px" }).observe($("#sentinel"));

const langSel = $("#lang");
langSel.innerHTML = Object.entries(I18N).map(([c, d]) => `<option value="${c}">${esc(d._name)}</option>`).join("");
langSel.value = LANG;
langSel.addEventListener("change", () => { setLang(langSel.value); renderAll(); });
applyStatic();

async function startApp() {
  api = window.pywebview.api;
  document.querySelectorAll(".app-only").forEach((el) => (el.hidden = false));
  $("#only-installable").checked = true;
  $("#btn-play").addEventListener("click", async () => { const r = await api.launch(); if (!r.ok) toast(t("gameNotFound"), 6000); });
  $("#btn-updates").addEventListener("click", checkUpdates);
  $("#btn-settings").addEventListener("click", openSettings);
  $("#pick-save").addEventListener("click", async () => { const p = await api.pick_folder(); if (p) $("#set-save").value = p; });
  $("#pick-exe").addEventListener("click", async () => { const p = await api.pick_exe(); if (p) $("#set-exe").value = p; });
  $("#save-settings").addEventListener("click", async () => {
    await api.save_settings({ save_dir: $("#set-save").value, game_exe: $("#set-exe").value, feed_url: $("#set-feed").value.trim() });
    $("#settings").hidden = true; await refreshState(); load(await api.get_data()); toast(t("done"));
  });
  await refreshState();
  try { load(await api.get_data()); } catch { $("#count").textContent = t("loadError"); }
}

// In der App meldet sich pywebview per Event; bis dahin (und im Browser) werden die Daten normal geladen.
let appStarted = false;
const startOnce = () => { if (!appStarted && window.pywebview && window.pywebview.api) { appStarted = true; startApp(); } };
window.addEventListener("pywebviewready", startOnce);
startOnce();
if (!appStarted) {
  fetch("data/mods.json", { cache: "no-store" })
    .then((r) => r.json()).then((d) => { if (!data) load(d); })
    .catch(() => { if (!data) $("#count").textContent = t("loadError"); });
}
