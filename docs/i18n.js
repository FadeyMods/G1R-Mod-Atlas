// Übersetzungen. Neue Sprache: Block kopieren, Code + Name anpassen, Texte übersetzen.
// Fehlt ein Schlüssel, wird Englisch verwendet.
const I18N = {
  en: {
    _name: "English", _locale: "en-US",
    unmaintainedTag: "Unmaintained", unmaintainedText: "This project is no longer maintained. Anyone is welcome to fork it and keep the website and the app going.", unmaintainedLink: "Fork on GitHub →",
    tabAll: "Discover", tabInstalled: "Installed", tabChanges: "New & updates",
    search: "Search mods, authors, repos …", sortLabel: "Sort",
    sortActivity: "Recently updated", sortPopular: "Most popular", sortNew: "Newly discovered", sortName: "Name",
    fGame: "Game", fCategory: "Category", fStatus: "Status", fSource: "Source",
    onlyInstallable: "Only installable", showHidden: "Show copies, ports & lists", resetFilters: "Reset filters",
    count: "<b>{n}</b> mods", checkUpdates: "Check updates", play: "Play", settings: "Settings",
    saveDir: "Gen1Recomp save folder", saveDirHint: "Mods are installed into the mods folder inside it.",
    change: "Change", gameExe: "Game (gen1recomp.exe)", feedUrl: "Mod list URL",
    feedHint: "Leave empty to use the built-in list.", saveSettings: "Save",
    asOf: "Data as of", gameFeed: "Feed for the in-game mod browser",
    disclaimer: "Unofficial community project. Mods belong to their authors.",
    by: "by", install: "Install", installed: "Installed", update: "Update", uninstall: "Remove",
    installing: "Installing …", done: "Done", failed: "Failed", openFolder: "Open folder",
    download: "Download", fork: "Fork on GitHub", archive: "Archive (Software Heritage)", findForks: "Search forks",
    variants: "+{n} more copies", variantsTitle: "Copies, forks & mirrors", version: "Version", updatedOn: "Last update",
    stars: "Stars", downloads: "Downloads", inIndex: "In the official index", notInIndex: "Not in the official index",
    games: "Games", category: "Category", statusLabel: "Status",
    deletedNote: "The original repository was deleted. Check the archive or search for forks.",
    wipNote: "Work in progress – no download yet. Follow it on Discord.",
    sourceZipNote: "No release – this downloads the current source code.",
    confirmUninstall: "Remove this mod from your mods folder?",
    updatesAvailable: "{n} updates available", noUpdates: "All installed mods are up to date.", updateAll: "Update all",
    gameNotFound: "Game not found – set the path in the settings.",
    newFound: "Newly discovered", updates: "Updates", statusChanges: "Status changes", none: "none", andMore: "… and {n} more",
    noRuns: "No runs yet.", noChanges: "Change log not available.", loadError: "Could not load data.",
    noResults: "No mods match these filters.", installedEmpty: "No mods installed yet.",
    cat: { VOXEL: "Voxel / 3D", QOL: "Quality of life", UI: "UI", GAMEPLAY: "Gameplay", CONTENT: "Content", BALANCE: "Balance", ART: "Art", AUDIO: "Audio", TRANSLATION: "Translation", TOTAL_CONVERSION: "Total conversion", LIBRARY: "Library", TOOL: "Tool", CART: "Custom cart", OTHER: "Other" },
    status: { active: "Active", inactive: "Inactive", wip: "Work in progress", abandoned: "Abandoned", archived: "Archived", deleted: "Deleted" },
    src: { index: "Mod index", github: "GitHub", gamebanana: "GameBanana", discord: "Discord" },
    gen: { 1: "Gen 1 · Red/Blue/Yellow", 2: "Gen 2 · Gold/Silver/Crystal", 3: "Gen 3 · FR/LG · R/S/E" },
  },
  de: {
    _name: "Deutsch", _locale: "de-DE",
    unmaintainedTag: "Nicht mehr gepflegt", unmaintainedText: "Dieses Projekt wird nicht mehr weiterentwickelt. Wer Lust hat, darf es gern forken und Webseite und App weiterführen.", unmaintainedLink: "Auf GitHub forken →",
    tabAll: "Entdecken", tabInstalled: "Installiert", tabChanges: "Neu & Updates",
    search: "Mods, Autoren, Repos suchen …", sortLabel: "Sortierung",
    sortActivity: "Zuletzt aktualisiert", sortPopular: "Am beliebtesten", sortNew: "Neu entdeckt", sortName: "Name",
    fGame: "Spiel", fCategory: "Kategorie", fStatus: "Status", fSource: "Quelle",
    onlyInstallable: "Nur installierbare", showHidden: "Kopien, Ports & Listen zeigen", resetFilters: "Filter zurücksetzen",
    count: "<b>{n}</b> Mods", checkUpdates: "Updates prüfen", play: "Spielen", settings: "Einstellungen",
    saveDir: "Gen1Recomp-Speicherordner", saveDirHint: "Mods werden in den mods-Ordner darin installiert.",
    change: "Ändern", gameExe: "Spiel (gen1recomp.exe)", feedUrl: "Adresse der Mod-Liste",
    feedHint: "Leer lassen für die eingebaute Liste.", saveSettings: "Speichern",
    asOf: "Datenstand", gameFeed: "Feed für den Mod-Browser im Spiel",
    disclaimer: "Inoffizielles Community-Projekt. Mods gehören ihren Autoren.",
    by: "von", install: "Installieren", installed: "Installiert", update: "Updaten", uninstall: "Entfernen",
    installing: "Installiere …", done: "Fertig", failed: "Fehlgeschlagen", openFolder: "Ordner öffnen",
    download: "Download", fork: "Auf GitHub forken", archive: "Archiv (Software Heritage)", findForks: "Forks suchen",
    variants: "+{n} weitere Kopien", variantsTitle: "Kopien, Forks & Spiegel", version: "Version", updatedOn: "Letztes Update",
    stars: "Sterne", downloads: "Downloads", inIndex: "Im offiziellen Index", notInIndex: "Nicht im offiziellen Index",
    games: "Spiele", category: "Kategorie", statusLabel: "Status",
    deletedNote: "Das Original-Repo wurde gelöscht. Schau ins Archiv oder suche nach Forks.",
    wipNote: "In Arbeit – noch kein Download. Verfolge es auf Discord.",
    sourceZipNote: "Keine Release – geladen wird der aktuelle Quellcode.",
    confirmUninstall: "Diesen Mod aus deinem mods-Ordner entfernen?",
    updatesAvailable: "{n} Updates verfügbar", noUpdates: "Alle installierten Mods sind aktuell.", updateAll: "Alle updaten",
    gameNotFound: "Spiel nicht gefunden – Pfad in den Einstellungen setzen.",
    newFound: "Neu entdeckt", updates: "Updates", statusChanges: "Statuswechsel", none: "keine", andMore: "… und {n} weitere",
    noRuns: "Noch keine Läufe.", noChanges: "Änderungsprotokoll nicht verfügbar.", loadError: "Daten konnten nicht geladen werden.",
    noResults: "Keine Mods passen zu diesen Filtern.", installedEmpty: "Noch keine Mods installiert.",
    cat: { QOL: "Quality of Life", ART: "Grafik", TRANSLATION: "Übersetzung", TOTAL_CONVERSION: "Total Conversion", CART: "Custom Cart", OTHER: "Sonstiges" },
    status: { active: "Aktiv", inactive: "Inaktiv", wip: "In Arbeit", abandoned: "Aufgegeben", archived: "Archiviert", deleted: "Gelöscht" },
    src: { index: "Mod-Index" },
    gen: { 1: "Gen 1 · Rot/Blau/Gelb", 2: "Gen 2 · Gold/Silber/Kristall", 3: "Gen 3 · FR/BG · R/S/S" },
  },
  es: {
    _name: "Español", _locale: "es-ES",
    unmaintainedTag: "Sin mantenimiento", unmaintainedText: "Este proyecto ya no se mantiene. Cualquiera puede hacer un fork y continuar la web y la app.", unmaintainedLink: "Fork en GitHub →",
    tabAll: "Explorar", tabInstalled: "Instalados", tabChanges: "Novedades",
    search: "Buscar mods, autores, repos …", sortLabel: "Ordenar",
    sortActivity: "Actualizados recientemente", sortPopular: "Más populares", sortNew: "Recién descubiertos", sortName: "Nombre",
    fGame: "Juego", fCategory: "Categoría", fStatus: "Estado", fSource: "Fuente",
    onlyInstallable: "Solo instalables", showHidden: "Mostrar copias, ports y listas", resetFilters: "Restablecer filtros",
    count: "<b>{n}</b> mods", checkUpdates: "Buscar actualizaciones", play: "Jugar", settings: "Ajustes",
    saveDir: "Carpeta de guardado de Gen1Recomp", saveDirHint: "Los mods se instalan en su carpeta mods.",
    change: "Cambiar", gameExe: "Juego (gen1recomp.exe)", feedUrl: "URL de la lista de mods",
    feedHint: "Déjalo vacío para usar la lista incluida.", saveSettings: "Guardar",
    asOf: "Datos del", gameFeed: "Feed para el navegador de mods del juego",
    disclaimer: "Proyecto comunitario no oficial. Los mods pertenecen a sus autores.",
    by: "por", install: "Instalar", installed: "Instalado", update: "Actualizar", uninstall: "Quitar",
    installing: "Instalando …", done: "Listo", failed: "Error", openFolder: "Abrir carpeta",
    download: "Descargar", fork: "Hacer fork en GitHub", archive: "Archivo (Software Heritage)", findForks: "Buscar forks",
    variants: "+{n} copias más", variantsTitle: "Copias, forks y espejos", version: "Versión", updatedOn: "Última actualización",
    stars: "Estrellas", downloads: "Descargas", inIndex: "En el índice oficial", notInIndex: "Fuera del índice oficial",
    games: "Juegos", category: "Categoría", statusLabel: "Estado",
    deletedNote: "El repositorio original fue eliminado. Revisa el archivo o busca forks.",
    wipNote: "En desarrollo: aún sin descarga. Síguelo en Discord.",
    sourceZipNote: "Sin release: se descarga el código fuente actual.",
    confirmUninstall: "¿Quitar este mod de tu carpeta mods?",
    updatesAvailable: "{n} actualizaciones disponibles", noUpdates: "Todos los mods instalados están al día.", updateAll: "Actualizar todo",
    gameNotFound: "Juego no encontrado: indica la ruta en los ajustes.",
    newFound: "Recién descubiertos", updates: "Actualizaciones", statusChanges: "Cambios de estado", none: "ninguno", andMore: "… y {n} más",
    noRuns: "Todavía no hay ejecuciones.", noChanges: "Registro no disponible.", loadError: "No se pudieron cargar los datos.",
    noResults: "Ningún mod coincide con estos filtros.", installedEmpty: "Aún no hay mods instalados.",
    cat: { QOL: "Calidad de vida", ART: "Arte", CONTENT: "Contenido", TRANSLATION: "Traducción", TOTAL_CONVERSION: "Conversión total", LIBRARY: "Librería", TOOL: "Herramienta", CART: "Cartucho personalizado", OTHER: "Otros", BALANCE: "Equilibrio" },
    status: { active: "Activo", inactive: "Inactivo", wip: "En desarrollo", abandoned: "Abandonado", archived: "Archivado", deleted: "Eliminado" },
    src: { index: "Índice de mods" },
    gen: { 1: "Gen 1 · Rojo/Azul/Amarillo", 2: "Gen 2 · Oro/Plata/Cristal", 3: "Gen 3 · RF/VH · R/Z/E" },
  },
  pt: {
    _name: "Português", _locale: "pt-BR",
    unmaintainedTag: "Sem manutenção", unmaintainedText: "Este projeto não é mais mantido. Qualquer pessoa pode fazer um fork e continuar o site e o app.", unmaintainedLink: "Fork no GitHub →",
    tabAll: "Explorar", tabInstalled: "Instalados", tabChanges: "Novidades",
    search: "Buscar mods, autores, repos …", sortLabel: "Ordenar",
    sortActivity: "Atualizados recentemente", sortPopular: "Mais populares", sortNew: "Recém-descobertos", sortName: "Nome",
    fGame: "Jogo", fCategory: "Categoria", fStatus: "Status", fSource: "Fonte",
    onlyInstallable: "Só instaláveis", showHidden: "Mostrar cópias, ports e listas", resetFilters: "Limpar filtros",
    count: "<b>{n}</b> mods", checkUpdates: "Verificar atualizações", play: "Jogar", settings: "Configurações",
    saveDir: "Pasta de saves do Gen1Recomp", saveDirHint: "Os mods são instalados na pasta mods dentro dela.",
    change: "Alterar", gameExe: "Jogo (gen1recomp.exe)", feedUrl: "URL da lista de mods",
    feedHint: "Deixe vazio para usar a lista embutida.", saveSettings: "Salvar",
    asOf: "Dados de", gameFeed: "Feed para o navegador de mods do jogo",
    disclaimer: "Projeto comunitário não oficial. Os mods pertencem aos seus autores.",
    by: "por", install: "Instalar", installed: "Instalado", update: "Atualizar", uninstall: "Remover",
    installing: "Instalando …", done: "Pronto", failed: "Falhou", openFolder: "Abrir pasta",
    download: "Baixar", fork: "Fazer fork no GitHub", archive: "Arquivo (Software Heritage)", findForks: "Procurar forks",
    variants: "+{n} cópias", variantsTitle: "Cópias, forks e espelhos", version: "Versão", updatedOn: "Última atualização",
    stars: "Estrelas", downloads: "Downloads", inIndex: "No índice oficial", notInIndex: "Fora do índice oficial",
    games: "Jogos", category: "Categoria", statusLabel: "Status",
    deletedNote: "O repositório original foi excluído. Veja o arquivo ou procure forks.",
    wipNote: "Em desenvolvimento – ainda sem download. Acompanhe no Discord.",
    sourceZipNote: "Sem release – baixa o código-fonte atual.",
    confirmUninstall: "Remover este mod da sua pasta mods?",
    updatesAvailable: "{n} atualizações disponíveis", noUpdates: "Todos os mods instalados estão atualizados.", updateAll: "Atualizar tudo",
    gameNotFound: "Jogo não encontrado – defina o caminho nas configurações.",
    newFound: "Recém-descobertos", updates: "Atualizações", statusChanges: "Mudanças de status", none: "nenhum", andMore: "… e mais {n}",
    noRuns: "Nenhuma execução ainda.", noChanges: "Registro indisponível.", loadError: "Não foi possível carregar os dados.",
    noResults: "Nenhum mod corresponde a esses filtros.", installedEmpty: "Nenhum mod instalado ainda.",
    cat: { QOL: "Qualidade de vida", ART: "Arte", CONTENT: "Conteúdo", TRANSLATION: "Tradução", TOTAL_CONVERSION: "Conversão total", LIBRARY: "Biblioteca", TOOL: "Ferramenta", CART: "Cartucho personalizado", OTHER: "Outros", BALANCE: "Balanceamento" },
    status: { active: "Ativo", inactive: "Inativo", wip: "Em desenvolvimento", abandoned: "Abandonado", archived: "Arquivado", deleted: "Excluído" },
    src: { index: "Índice de mods" },
    gen: { 1: "Gen 1 · Red/Blue/Yellow", 2: "Gen 2 · Gold/Silver/Crystal", 3: "Gen 3 · FR/LG · R/S/E" },
  },
  fr: {
    _name: "Français", _locale: "fr-FR",
    unmaintainedTag: "Plus maintenu", unmaintainedText: "Ce projet n'est plus maintenu. Chacun est libre de le forker et de poursuivre le site et l'application.", unmaintainedLink: "Forker sur GitHub →",
    tabAll: "Découvrir", tabInstalled: "Installés", tabChanges: "Nouveautés",
    search: "Rechercher des mods, auteurs, dépôts …", sortLabel: "Trier",
    sortActivity: "Mis à jour récemment", sortPopular: "Les plus populaires", sortNew: "Récemment découverts", sortName: "Nom",
    fGame: "Jeu", fCategory: "Catégorie", fStatus: "Statut", fSource: "Source",
    onlyInstallable: "Installables uniquement", showHidden: "Afficher copies, ports et listes", resetFilters: "Réinitialiser",
    count: "<b>{n}</b> mods", checkUpdates: "Vérifier les mises à jour", play: "Jouer", settings: "Paramètres",
    saveDir: "Dossier de sauvegarde de Gen1Recomp", saveDirHint: "Les mods sont installés dans son dossier mods.",
    change: "Modifier", gameExe: "Jeu (gen1recomp.exe)", feedUrl: "URL de la liste des mods",
    feedHint: "Laisser vide pour la liste intégrée.", saveSettings: "Enregistrer",
    asOf: "Données du", gameFeed: "Flux pour le navigateur de mods du jeu",
    disclaimer: "Projet communautaire non officiel. Les mods appartiennent à leurs auteurs.",
    by: "par", install: "Installer", installed: "Installé", update: "Mettre à jour", uninstall: "Retirer",
    installing: "Installation …", done: "Terminé", failed: "Échec", openFolder: "Ouvrir le dossier",
    download: "Télécharger", fork: "Forker sur GitHub", archive: "Archive (Software Heritage)", findForks: "Chercher des forks",
    variants: "+{n} autres copies", variantsTitle: "Copies, forks et miroirs", version: "Version", updatedOn: "Dernière mise à jour",
    stars: "Étoiles", downloads: "Téléchargements", inIndex: "Dans l'index officiel", notInIndex: "Absent de l'index officiel",
    games: "Jeux", category: "Catégorie", statusLabel: "Statut",
    deletedNote: "Le dépôt d'origine a été supprimé. Consultez l'archive ou cherchez des forks.",
    wipNote: "En cours – pas encore de téléchargement. Suivez-le sur Discord.",
    sourceZipNote: "Pas de release – télécharge le code source actuel.",
    confirmUninstall: "Retirer ce mod de votre dossier mods ?",
    updatesAvailable: "{n} mises à jour disponibles", noUpdates: "Tous les mods installés sont à jour.", updateAll: "Tout mettre à jour",
    gameNotFound: "Jeu introuvable – indiquez le chemin dans les paramètres.",
    newFound: "Récemment découverts", updates: "Mises à jour", statusChanges: "Changements de statut", none: "aucun", andMore: "… et {n} de plus",
    noRuns: "Aucune exécution pour l'instant.", noChanges: "Journal indisponible.", loadError: "Impossible de charger les données.",
    noResults: "Aucun mod ne correspond à ces filtres.", installedEmpty: "Aucun mod installé pour l'instant.",
    cat: { QOL: "Confort de jeu", ART: "Graphismes", CONTENT: "Contenu", TRANSLATION: "Traduction", TOTAL_CONVERSION: "Conversion totale", LIBRARY: "Bibliothèque", TOOL: "Outil", CART: "Cartouche perso", OTHER: "Autres", BALANCE: "Équilibrage" },
    status: { active: "Actif", inactive: "Inactif", wip: "En cours", abandoned: "Abandonné", archived: "Archivé", deleted: "Supprimé" },
    src: { index: "Index des mods" },
    gen: { 1: "Gen 1 · Rouge/Bleu/Jaune", 2: "Gen 2 · Or/Argent/Cristal", 3: "Gen 3 · RF/VF · R/S/É" },
  },
};

let LANG = "en";

function pickLang() {
  let saved = null;
  try { saved = localStorage.getItem("atlas-lang"); } catch {}
  if (saved && I18N[saved]) return saved;
  for (const l of navigator.languages || [navigator.language || "en"]) {
    const code = l.toLowerCase().split("-")[0];
    if (I18N[code]) return code;
  }
  return "en";
}

function t(key, vars) {
  const [a, b] = key.split(".");
  let v = b ? ((I18N[LANG][a] || {})[b] ?? (I18N.en[a] || {})[b]) : (I18N[LANG][a] ?? I18N.en[a]);
  if (v == null) v = key;
  if (vars) for (const [k, x] of Object.entries(vars)) v = v.replace(`{${k}}`, x);
  return v;
}

function applyStatic() {
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
}

function setLang(code) {
  LANG = I18N[code] ? code : "en";
  try { localStorage.setItem("atlas-lang", LANG); } catch {}
  applyStatic();
}

LANG = pickLang();
