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

// Only leaf values are copied, and only into keys that already exist in the
// defaults. That way a saved file cannot inject unknown elements or replace an
// object with a scalar -- both of which would throw somewhere deep in the
// render, far from the actual cause.
function mergeInto(target, patch) {
  if (!patch || typeof patch !== "object") return
  for (const key of Object.keys(patch)) {
    if (!(key in target)) continue
    const a = target[key]
    const b = patch[key]
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

export function saveConfig() {
  writeRaw(JSON.stringify(config))
}

// Restores everything to what layout.js ships, and clears the save so a later
// mod update is picked up cleanly.
export function resetConfig() {
  mergeInto(config, clone(DEFAULTS))
  try {
    if (typeof storageWrite === "function") storageWrite(STORAGE_KEY, "")
    else localStorage.removeItem(STORAGE_KEY)
  } catch (e) {
    // See writeRaw.
  }
}

// Restores a single element, leaving every other tweak alone.
export function resetElement(section, key) {
  const src = DEFAULTS[section] && DEFAULTS[section][key]
  if (src) mergeInto(config[section][key], clone(src))
}

export { config, DEFAULTS }
export default config
