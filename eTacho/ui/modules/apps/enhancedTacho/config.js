// =============================================================================
//  ENHANCED TACHO  --  LIVE CONFIGURATION STORE
// =============================================================================
//
//  Sits between layout.js (the defaults, shipped with the mod) and the dial.
//
//  layout.js stays the source of truth for what the mod looks like out of the
//  box. This module deep-copies it into a reactive object, then layers any
//  edits the player made in the in-game panel on top. Nothing here writes back
//  to layout.js -- that file is read-only at runtime, so a mod update can ship
//  a new default layout and only the settings a player actually touched are
//  preserved.
//
//  The store is a module-level singleton on purpose: two copies of the dial in
//  the same HUD must show the same thing, and both must react to an edit made
//  in either one's settings panel.
// =============================================================================

import { reactive } from "vue"
import { CONFIG as DEFAULTS } from "./layout.js"

// Bump when a change to layout.js would make older saved overrides nonsense
// (a renamed element, a field that changed meaning). Saved data from an older
// version is discarded rather than merged, which is the safe direction: the
// player loses their tweaks instead of getting a dial laid out from a mix of
// two incompatible schemas.
const SCHEMA_VERSION = 1
const STORAGE_KEY = "enhancedTacho.config.v" + SCHEMA_VERSION

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

// Only leaf values are copied. A key missing from the defaults is accepted
// when its value is a primitive -- the panel legitimately introduces such
// fields, e.g. setting an opacity on an element that never declared one, and
// refusing them silently discarded those edits on the next reload. Objects
// under unknown keys are still rejected, so a crafted save cannot graft whole
// new structures onto the config and blow up deep inside the render.
function mergeInto(target, patch) {
  if (!patch || typeof patch !== "object") return
  for (const key of Object.keys(patch)) {
    const b = patch[key]
    if (!(key in target)) {
      if (typeof b === "number" || typeof b === "string" || typeof b === "boolean") {
        target[key] = b
      }
      continue
    }
    const a = target[key]
    if (Array.isArray(a) && Array.isArray(b)) {
      target[key] = clone(b)
    } else if (a && typeof a === "object" && b && typeof b === "object") {
      mergeInto(a, b)
    } else if (typeof a === typeof b) {
      target[key] = b
    }
  }
}

// The runtime storage helpers the mod compiler injects, when present. Falling
// back to raw localStorage keeps this working in the UI workbench, where those
// globals do not exist.
function readRaw() {
  try {
    if (typeof storageRead === "function") return storageRead(STORAGE_KEY)
    return localStorage.getItem(STORAGE_KEY)
  } catch (e) {
    return null
  }
}

function writeRaw(text) {
  try {
    if (typeof storageWrite === "function") return storageWrite(STORAGE_KEY, text)
    localStorage.setItem(STORAGE_KEY, text)
  } catch (e) {
    // A locked-down profile makes settings session-only. Not worth failing over.
  }
}

const config = reactive(clone(DEFAULTS))

const saved = readRaw()
if (saved) {
  try {
    mergeInto(config, JSON.parse(saved))
  } catch (e) {
    // Corrupt save: keep the shipped defaults rather than a half-applied state.
  }
}

// Persists only what differs from the defaults. Writing the whole object
// would pin every current default into the save, and a later layout.js
// shipping a better position would then be silently overridden by it --
// exactly the opposite of what this module exists for.
function diffFrom(current, base) {
  const out = {}
  for (const key of Object.keys(current)) {
    const a = current[key]
    const b = base ? base[key] : undefined
    if (a && typeof a === "object" && !Array.isArray(a)) {
      const sub = diffFrom(a, b || {})
      if (Object.keys(sub).length) out[key] = sub
    } else if (JSON.stringify(a) !== JSON.stringify(b)) {
      out[key] = a
    }
  }
  return out
}

export function saveConfig() {
  writeRaw(JSON.stringify(diffFrom(config, DEFAULTS)))
}

// Restores a single element, leaving every other tweak alone. Wholesale
// rather than a merge: fields the panel added on top of the defaults (an
// opacity the element never declared) must go too, or "reset" leaves
// invisible state behind that resurfaces on the next edit.
export function resetElement(section, key) {
  const src = DEFAULTS[section] && DEFAULTS[section][key]
  const dst = config[section] && config[section][key]
  if (!src || !dst) return
  for (const k of Object.keys(dst)) delete dst[k]
  Object.assign(dst, clone(src))
}

// Restores everything to what layout.js ships, and clears the save so a later
// mod update is picked up cleanly. Element by element, through resetElement,
// for the same panel-added-fields reason.
export function resetConfig() {
  for (const section of ["elements", "units"]) {
    for (const key of Object.keys(DEFAULTS[section] || {})) resetElement(section, key)
  }
  mergeInto(config.options, clone(DEFAULTS.options))
  try {
    if (typeof storageWrite === "function") storageWrite(STORAGE_KEY, "")
    else localStorage.removeItem(STORAGE_KEY)
  } catch (e) {
    // See writeRaw.
  }
}

export { config, DEFAULTS }
export default config
