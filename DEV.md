# Notes de développement — BeamNG UI Apps

Référence technique pour le mod **enhancedTacho**.
Sauf mention contraire, tout ce qui suit a été **vérifié directement dans les fichiers du jeu**
(**v0.39.2.1**, build `20887` du 31/07/2026) et non simplement lu dans la doc.

---

## 1. Chemins sur cette machine

| Quoi | Chemin |
|---|---|
| Jeu | `C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive` |
| **Dossier utilisateur** | `C:\Users\compt\AppData\Local\BeamNG\BeamNG.drive\current\` |
| **Mods décompressés** | `…\BeamNG\BeamNG.drive\current\mods\unpacked\<nom_du_mod>\` |
| Apps du jeu (référence) | `<jeu>\ui\modules\apps\` |
| Log | `…\BeamNG\BeamNG.drive\current\beamng.log` |

⚠️ **Attention au dossier piège.** Il existe deux emplacements qui se ressemblent :

- `%LOCALAPPDATA%\BeamNG.drive\{0.36, 0.37}\` — **ancien layout, obsolète** (résidus de 09/2025).
  Le jeu ne l'utilise plus.
- `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\` — **le vrai**, layout actuel du launcher.

Confirmé par le jeu lui-même dans `beamng.log` :

```
Virtual Filesystem: user path: C:\Users\compt\AppData\Local\BeamNG\BeamNG.drive\current\ (Default behaviour)
```

Le launcher ne nomme plus le dossier par numéro de version : il maintient un dossier `current`
(un vrai répertoire, **pas** une jonction NTFS) et archive les précédents sous
`<date>__v<ancienne>__update_to_v<nouvelle>\`. Le `version.txt` à la racine est un artefact du
launcher et peut être périmé (il indique `0.36.4.0` alors que le jeu est en 0.39.2.1) — ne pas s'y fier.

Le sous-dossier `mods\unpacked\` n'existe pas encore, il faut le créer.
Le nom du dossier de mod est libre ; c'est l'arborescence `ui/modules/apps/...` à l'intérieur qui compte.

**Copier `Test V4.00\*` vers `…\current\mods\unpacked\enhancedTacho\`** →
on obtient `mods\unpacked\enhancedTacho\ui\modules\apps\enhancedTacho\app.json`, etc.

Le scan de ce dossier est fait par `lua/ge/extensions/core/modmanager.lua:626` :
`FS:findFiles("/mods/unpacked/", "*", 0, false, true)`.

Penser à désactiver la version `.zip` du mod dans le gestionnaire pour éviter les doublons
dans le sélecteur d'apps.

---

## 2. Boucle de développement

| Touche | Effet |
|---|---|
| `~` | Console in-game. Trois contextes au choix dans le menu déroulant : **GE-Lua**, **Vehicle-Lua**, **CEF/UI - JS** |
| `F5` | Recharge l'UI (CEF) |
| `Ctrl+L` | Recharge le Lua véhicule / GE |
| `Ctrl+R` | Respawn du véhicule |
| `F11` | World Editor |

**Piège majeur :** par défaut le CEF met les `.js` en cache. Les modifications de `app.html`/template
sont prises en compte au `F5`, **mais pas celles de `app.js` ni de `svg-script.js`**.
→ Ouvrir les DevTools UI, onglet **Network → Disable cache**, garder la fenêtre ouverte.
Après ça, `F5` applique bien les changements JS.

Pour le contexte `CEF/UI - JS` de la console, on peut inspecter à chaud :
```js
angular.element(document.querySelector('enhanced-tacho')).scope()
```

Le jeu embarque aussi `<jeu>\ui\uidevtools\` (serveur Vite, ports 8085/8086) qui enregistre les
messages Lua reçus par l'UI — utile pour inspecter les hooks, pas indispensable ici.

---

## 3. Anatomie d'une UI app

BeamNG utilise **Chromium Embedded Framework** + **AngularJS 1.5.8** pour les apps historiques.

```
ui/modules/apps/<MonApp>/
├── app.json     manifeste
├── app.js       directive Angular
├── app.png      icône du sélecteur
├── app.css      styles / @font-face (optionnel)
└── app.svg      cadran (optionnel — cf. §4)
```

### Champs de `app.json`

```json
{
  "domElement": "<enhanced-tacho></enhanced-tacho>",
  "directive":  "enhancedTacho",
  "name":       "Enhanced Tacho",
  "description":"Advanced Tacho, with more informations",
  "author":     "YDeltagon",
  "version":    "4.0",
  "types":      ["ui.apps.categories.vehicle_info"],
  "css":        { "width": "300px", "height": "300px", "bottom": "0px", "right": "0px" },
  "preserveAspectRatio": true,

  "category":    "Dashboard",
  "isAuxiliary": false,
  "interactive": "no"
}
```

- `directive` doit correspondre **exactement** au nom passé à `.directive()` dans `app.js`
  (camelCase), et `domElement` à sa version kebab-case.
- `category` / `isAuxiliary` / `interactive` sont des champs **récents** : toutes les apps du jeu
  en 0.39 les portent, y compris les anciennes apps Angular (`SimpleTacho`, `Compass`).
  Les app.json du mod ne les ont pas encore.
- ⚠️ `name` passe par le système de traduction. Une valeur du type `ui.apps.xxx.name` doit
  **exister** dans `locales/translations/<lang>/main.translation.json`, sinon la clé brute
  s'affiche dans le sélecteur. Les clés `ui.apps.enhancedTacho.name` et
  `ui.apps.enhancedForcedinduction.name` **n'existent pas** dans le jeu (vérifié).
  → mettre un libellé littéral, comme le fait déjà `Tacho2Classic` (`"name": "Tacho2 classic"`).

### Directive minimale

```js
angular.module('beamng.apps')
  .directive('monApp', [function () {
    return {
      template: '<svg ...>…</svg>',
      replace: true,
      restrict: 'EA',
      link: function (scope, element, attrs) {
        const streamsList = ['engineInfo', 'electrics'];
        StreamsManager.add(streamsList);

        scope.$on('streamsUpdate', function (event, streams) { /* … */ });

        scope.$on('$destroy', function () {
          StreamsManager.remove(streamsList);
        });
      }
    };
  }]);
```

`StreamsManager.add()` / `.remove()` sont **comptés par référence** : chaque `add` doit avoir son
`remove`, sinon les streams continuent d'être calculés côté véhicule après fermeture de l'app.

### Persistance des réglages

Le canal officiel n'est pas `localStorage` mais le contrôleur parent :

```js
require: '^bngApp',
link: function (scope, element, attrs, ctrl) {
  let appSettings = null;
  element.ready(() => ctrl.getSettings().then(s => { appSettings = s; }));
  scope.$on('$destroy', () => ctrl.saveSettings(appSettings));
}
```

Ce mod utilise `localStorage` à la place (clés `tachometerData`, `forcedInductionData`) — ça marche,
mais c'est global au profil et pas rattaché à l'instance de l'app (deux instances partagent l'état).

---

## 4. Le pattern « SVG externe » (celui de ce mod)

Deux variantes coexistent chez BeamNG :

**a) Template SVG inline** — `SimpleTacho` du jeu. Le SVG est une chaîne dans `app.js`, tout le code
tourne dans le document principal. Simple, mais illisible dès que le cadran est complexe.

**b) SVG externe via `<object>`** — ce mod, et l'ancien `Tacho2`. Le SVG est un **document séparé** :

```js
template: '<object type="image/svg+xml" data="/ui/modules/apps/enhancedTacho/app.svg"></object>'
```

Conséquences à bien avoir en tête :

- Le SVG charge **ses propres scripts** via des balises `<script href>` en fin de fichier.
  C'est là que `models.js`, `controllers.js` et `svg-script.js` sont chargés — pas par Angular.
- Le pont entre les deux mondes est `element[0].contentDocument`. `svg-script.js` accroche ses
  fonctions sur `document` (`document.update`, `document.reset`, `document.getStreams`,
  `document.saveData`, `document.vehicleChanged`, `document.isStreamValid`) et `app.js` les appelle.
- Il faut attendre l'événement `load` de l'`<object>` avant de toucher à `contentDocument`.
- Les chemins des `<script href>` sont **absolus depuis la racine UI** (`/ui/common/...`) ou
  relatifs au SVG (`svg-script.js`).
- Le SVG a son propre contexte JS : pas de `UiUnits`, pas de `bngApi`, pas de `$scope` dedans.
  D'où le `document.wireThroughUnitSystem(callback)` qui injecte le convertisseur d'unités depuis
  `app.js`.
- Les `onclick="..."` dans le SVG appellent des fonctions globales définies dans `svg-script.js`.

**Technique de rendu des jauges** — pas d'animation CSS, tout est calculé :
- arcs : `stroke-dasharray` / `stroke-dashoffset` sur un `<path>`
- aiguille : `setAttribute('transform', 'rotate(angle, cx, cy)')`
- graduations et textes RPM : `getTotalLength()` + `getPointAtLength()` sur un `<path>` guide
  invisible (`rpmtextline`), ce qui permet de repositionner les chiffres selon le régime max
  du véhicule courant.

---

## 5. Streams

Souscription : `StreamsManager.add(['electrics', 'engineInfo', 'stats'])`.
Réception : `scope.$on('streamsUpdate', (event, streams) => …)` à la fréquence de l'UI.

### `engineInfo` — table d'index vérifiée (0.39.2.1)

Source : `lua/vehicle/controller/vehicleController/vehicleController.lua`, bloc
`if streams.willSend("engineInfo")`. **Attention** : Lua indexe à partir de 1, le tableau JS à
partir de 0 → l'index JS vaut l'index Lua **moins 1**.

| JS | Contenu | Unité |
|---:|---|---|
| `[0]` | `idleRPM` | tr/min |
| `[1]` | `maxRPM` (régime max) | tr/min |
| `[4]` | `rpm` | tr/min |
| `[5]` | `gearName` (rapport courant) | nombre ou chaîne |
| `[6]` | `maxGearIndex` (nb de rapports) | — |
| `[7]` | `minGearIndex` | — |
| `[8]` | `flywheelTorque` (couple volant moteur) | N·m |
| `[9]` | `gearboxTorque` | N·m |
| `[10]` | `airspeed` (`obj:getGroundSpeed()`) | m/s |
| `[11]` | `fuelVolume` (carburant restant, 0 si contact coupé) | L |
| `[12]` | `fuelCapacity` | L |
| `[13]` | type de boîte (`"manual"`, …) | chaîne |
| `[16]` | `gearIndex` | — |
| `[17]` | `isEngineRunning` | 0/1 |
| `[18]` | `engineLoad` | 0–1 |
| `[19]` | `wheelTorque` | N·m |
| `[20]` | `wheelPower` (aux roues) | ch |
| `[21]` | `flywheelPower` (au volant moteur) | ch |

Les index `[20]`/`[21]` sont déjà convertis côté Lua : `kW × 0.001 × 1.35962` → chevaux.
C'est cohérent avec le README du mod qui annonce la puissance « at the flywheel ».

Les index non listés (`[2]`, `[3]`, `[14]`, `[15]`) ne sont pas alimentés par ce bloc et
restent à leur valeur d'initialisation.

### `electrics` — valeurs utilisées par le mod (toutes présentes en 0.39.2.1)

`wheelspeed`, `airspeed`, `rpmTacho` (RPM lissé pour l'affichage — `rpmSmoother`), `gear_A`,
`watertemp`, `oiltemp`, `odometer`, `fuel`, `parkingbrake`, `abs`, `hasABS`, `signal_L`,
`signal_R`, `lowbeam`, `highbeam`, `boost`, `boostMax`.

`hasABS` est calculé dans `lua/vehicle/wheels.lua` : vrai si au moins une roue a l'ABS
**et** que le mode ABS n'est pas `off`, ou si le mode est `arcade`.

### `stats`

Fournit `total_weight` (masse du véhicule, kg). Non défini dans les `.lua` non packés — il vient
du moteur. Pas de garantie qu'il soit présent dès la première frame : prévoir une valeur de repli.

### `forcedInductionInfo`

Produit par `lua/vehicle/powertrain/turbocharger.lua` et `supercharger.lua`.
Champs : `rpm`, `coef`, `boost`, `maxBoost`, `pulses`, `loss`.
`boost` et `maxBoost` sont en **kPa** (`psi × psiToPascal × 0.001`).
Le stream n'est **émis que si** le véhicule a un turbo ou compresseur → d'où le
`isStreamValid()` qui masque l'app.

---

## 6. Parler au Lua depuis l'UI

Pour tout ce qui n'est pas dans un stream :

```js
// Contexte véhicule actif
bngApi.activeObjectLua('(function() return { ... } end)()', data => { /* callback */ });

// Contexte moteur de jeu (GE)
bngApi.engineLua('extensions.monExtension.maFonction()', data => {});
```

C'est ce que fait `updateVehiculeStats()` pour récupérer `maxPower` / `maxTorque` via
`powertrain.getDevicesByCategory("engine")[1]` — ces valeurs ne sont dans aucun stream.

Dans l'autre sens, le Lua pousse vers l'UI avec :
```lua
guihooks.trigger("MonEvenement", payload)
```
reçu côté JS par `scope.$on('MonEvenement', (ev, data) => …)`.

**Convention conseillée :** préfixer ses événements (`ETMonEvenement`) pour éviter les collisions
avec les événements internes du jeu.

### Événements de cycle de vie utiles

| Événement | Quand |
|---|---|
| `streamsUpdate` | à chaque frame UI, avec les streams souscrits |
| `VehicleChange` | changement de véhicule |
| `VehicleFocusChanged` | changement de caméra/véhicule suivi (`data.mode`) |
| `$destroy` | app fermée → **libérer les streams ici** |

⚠️ Ces événements se déclenchent plusieurs fois par session. **Ne jamais enregistrer un `scope.$on`
à l'intérieur d'un handler** de `load` / `VehicleChange` : les listeners s'accumulent et le code
s'exécute N fois par frame. (C'est le bug actuel de `updateVehiculeStats()`.)

---

## 7. Le virage Vue de BeamNG — état des lieux 0.39.2.1

Important pour la suite du mod :

- BeamNG migre les apps vers **Vue** (`ui/ui-vue/`). Les apps migrées ont un `app.vue` et
  `"vue": true` dans leur `app.json`.
- Le `Tacho2` du jeu **a déjà été migré** : `ui/modules/apps/Tacho2/` ne contient plus que
  `app.json`, `app.png`, `app.vue`, `tacho.vue` et `mockdata`. Plus de `app.js`, plus de `.svg`.
  Idem pour `Forcedinduction` (`app.vue` + `forcedInduction.vue` + `forcedinduction.svg`).
- **Mais l'ancien système Angular n'est pas mort** : sur 117 dossiers d'apps en 0.39,
  **82 utilisent encore `angular.module('beamng.apps')`** et 49 seulement ont un `app.vue`.
  L'architecture de ce mod reste donc parfaitement supportée.
- Bonne nouvelle : le `tacho.vue` du jeu utilise **exactement les mêmes index `engineInfo`**
  que le mod (`[1]` régime max, `[5]` rapport, `[11]`/`[12]` carburant, `[13] == "manual"`).
  Aucune migration d'index à prévoir.
- Conséquence sur la stratégie « override » (dossiers `Tacho2/` et `Forcedinduction/` du dépôt) :
  écraser `ui/modules/apps/Tacho2/` reviendrait aujourd'hui à remplacer une app Vue par une app
  Angular. Ça peut fonctionner, mais c'est fragile à chaque mise à jour du jeu.
  La v4.0 a d'ailleurs abandonné cette approche (ces dossiers ne sont pas dans le zip livré).
- Le dossier du jeu s'appelle bien `Forcedinduction` (minuscule sur le `i` de « induction »),
  alors que `Forcedinduction/app.js` du dépôt pointe vers `/ui/modules/apps/forcedInduction/app.svg`.
  Sans effet sous Windows (casse ignorée), mais faux.

---

## 8. Packaging pour publication

Le zip livré doit contenir l'arborescence à partir de `ui/`, sans dossier racine :

```
YDeltagon_eTacho.zip
└── ui/
    ├── common/EnhancedTacho/{models.js, controllers.js}
    └── modules/apps/{enhancedTacho, enhancedForcedinduction, Tacho2Classic}/
```

C'est exactement la structure de `Test V4.00/` → il suffit de zipper **le contenu** du dossier.

---

## 9. Pièges rencontrés dans ce mod

| Fichier | Problème |
|---|---|
| `Tacho2Classic/svg-script.js:397` | `getElementById('wheelspeed')` — l'id n'existe pas dans `app.svg` → `TypeError` à chaque chargement |
| `Tacho2Classic/app.js:80-86` | accolade mal placée : `svg.vehicleChanged()` est hors du garde `if (svg && …)` |
| `enhancedTacho/app.js:34` | `scope.$on('streamsUpdate')` enregistré dans `updateVehiculeStats()`, elle-même appelée à chaque `load` / `VehicleChange` / `VehicleFocusChanged` → accumulation de listeners |
| `enhancedForcedinduction/svg-script.js:49` | `initialized = false` crée une globale implicite au lieu de `forcedInduction.initialized` → le ré-init au changement d'unité ne se produit jamais |
| `common/EnhancedTacho/controllers.js:341,355` | utilise les globales `width` / `pressureTextCount` au lieu des champs de l'instance |
| `common/EnhancedTacho/models.js:252` | typo `pressureNeedlelOn` (jamais relue) |
| `controllers.js:119-123` | `Math.floor(parseFloat(undefined))` → affiche `NaN` si le stream `stats` arrive en retard |
| `*/app.json` | clés de traduction inexistantes ; champs `category` / `isAuxiliary` / `interactive` absents ; versions désynchronisées (4.0 vs 3.5.5) |

---

## Sources

- [Creating an app — BeamNG Documentation](https://documentation.beamng.com/modding/ui/app_creation/)
- [Programming — BeamNG Documentation](https://documentation.beamng.com/modding/programming/)
- [UI Apps (HTML) — BeamMP Docs](https://docs.beammp.com/beamng/dev/modding/ui-apps/)
- [Development Environment Setup — BeamMP Docs](https://docs.beammp.com/guides/beammp-dev/beammp-dev/)
- [Testing & Debugging Your Mod — RLS Studios](https://www.rlsstudios.dev/docs/guides/getting-started/testing-debugging)
- [Reloading UI apps without restarting the game — forum BeamNG](https://www.beamng.com/threads/reloading-ui-apps-in-development-without-restarting-the-game.104214/)
- [BeamNG/ui — GitHub (ancienne UI)](https://github.com/BeamNG/ui)
- Fichiers du jeu installé, build 20887 (31/07/2026)
