<!--
  ENHANCED TACHO  --  IN-GAME SETTINGS PANEL

  Edits the live configuration store (config.js) in place. Every control is
  bound straight to the reactive object the dial renders from, so changes show
  on the gauge as you drag, with no apply step.

  WHY IT IS TELEPORTED
    AppHost clips its app with overflow: hidden, and a mod's CSS is always
    scoped, so a panel cannot escape the widget's box any other way. The app is
    300 x 300 by default -- unusable for a settings form. Teleport to body is
    explicitly supported by the runtime SFC compiler and is what the stock
    topLeftApps app does for the same reason.

  WHY NO COLOUR PICKER WIDGET
    BngColorPicker exists and would import fine, but it models colour as HSL in
    0..1 and mutates the object it is given, so it needs a conversion layer on
    each side of a hex string. Swatches plus a hex field do the same job with
    no conversion and nothing to get wrong. Swapping it in later is a contained
    change if the extra precision turns out to matter.
-->
<template>
  <Teleport to="body">
    <div v-if="open" class="et-settings-backdrop" @click.self="$emit('close')">
      <div class="et-settings">
        <header>
          <h2>Enhanced Tacho</h2>
          <BngButton :accent="ACCENTS.outlined" @click="$emit('close')">Close</BngButton>
        </header>

        <div class="et-body">
          <!-- Which readout is being edited. One list rather than a long form:
               23 readouts x 6 fields laid out at once is unreadable. -->
          <aside>
            <button
              v-for="item in items"
              :key="item.section + '.' + item.key"
              class="et-pick"
              :class="{ active: item.key === selKey && item.section === selSection }"
              @click="select(item)">
              <span class="et-swatch" :style="{ background: swatchOf(item) }"></span>
              <span class="et-name">{{ item.label }}</span>
              <span v-if="entryOf(item).visible === false" class="et-off">hidden</span>
            </button>
          </aside>

          <section v-if="sel" class="et-editor">
            <h3>{{ selLabel }}</h3>

            <label class="et-row">
              <span>Visible</span>
              <BngSwitch v-model="sel.visible" />
            </label>

            <!-- Arc-placed readouts are positioned by radius and angle(s), so
                 the x/y sliders would mean nothing for them. Each row guards on
                 its own field: the damage readouts sit at a single `angle`, the
                 pedal gauges span `angleStart`..`angleEnd`, and steering has
                 `sweep`/`span`/`lockDegrees` -- an unguarded row would show a
                 slider bound to undefined and display NaN. -->
            <template v-if="sel.radius !== undefined">
              <SliderRow v-model="sel.radius" label="Radius" :min="0" :max="330" :step="1" />
              <SliderRow v-if="sel.angle !== undefined" v-model="sel.angle" label="Angle" :min="-180" :max="180" :step="1" />
              <SliderRow v-if="sel.angleStart !== undefined" v-model="sel.angleStart" label="Angle start" :min="-180" :max="360" :step="1" />
              <SliderRow v-if="sel.angleEnd !== undefined" v-model="sel.angleEnd" label="Angle end" :min="-180" :max="360" :step="1" />
              <SliderRow v-if="sel.sweep !== undefined" v-model="sel.sweep" label="Sweep" :min="5" :max="90" :step="1" />
              <SliderRow v-if="sel.span !== undefined" v-model="sel.span" label="Marker span" :min="2" :max="30" :step="1" />
              <SliderRow v-if="sel.width !== undefined" v-model="sel.width" label="Thickness" :min="2" :max="30" :step="1" />
              <SliderRow v-if="sel.lockDegrees !== undefined" v-model="sel.lockDegrees" label="Steering lock" :min="90" :max="1080" :step="10" />
              <SliderRow v-if="sel.dy !== undefined" v-model="sel.dy" label="Caption offset" :min="-60" :max="60" :step="1" />
            </template>
            <template v-else-if="sel.x !== undefined">
              <SliderRow v-model="sel.x" label="X" :min="0" :max="660" :step="1" />
              <SliderRow v-model="sel.y" label="Y" :min="0" :max="660" :step="1" />
            </template>

            <SliderRow v-if="sel.size !== undefined" v-model="sel.size" label="Size" :min="6" :max="160" :step="0.5" />
            <SliderRow v-if="sel.rotate !== undefined" v-model="sel.rotate" label="Rotation" :min="-90" :max="90" :step="90" />
            <SliderRow v-if="sel.opacity !== undefined" v-model="sel.opacity" label="Opacity"
              :min="0" :max="1" :step="0.05" />

            <!-- A caption or unit with no colour of its own inherits the
                 value's, which is the point of linking them: one setting, both
                 texts. It stays overridable here, and revertible, rather than
                 being read-only as it was -- the panel simply hid the picker,
                 so the only way to recolour a unit was to edit layout.js. -->
            <div v-if="canColour" class="et-colour">
              <div class="et-colour-head">
                <span>Colour</span>
                <input :value="effectiveColour" @input="onHex" class="et-hex" spellcheck="false" />
                <BngButton
                  v-if="inherits"
                  :accent="ACCENTS.outlined"
                  :disabled="sel.color === undefined"
                  @click="unlinkColour">
                  {{ sel.color === undefined ? "Follows " + humanise(sel.for) : "Follow " + humanise(sel.for) }}
                </BngButton>
              </div>
              <!-- Swatches already on the dial are named underneath. With fifty
                   of them the handful the mod actually uses would otherwise be
                   impossible to find again after a change. -->
              <div class="et-swatches">
                <button
                  v-for="c in PALETTE"
                  :key="c"
                  :class="{ used: !!usedBy(c).length, current: isCurrent(c) }"
                  :title="usedBy(c).length ? c + ' — ' + usedBy(c).join(', ') : c"
                  @click="sel.color = c">
                  <span class="et-chip" :style="{ background: c }"></span>
                  <span class="et-chip-label">{{ usedLabel(c) }}</span>
                </button>
              </div>
            </div>
            <p v-else class="et-note">
              This readout has no colour of its own.
            </p>

            <BngButton :accent="ACCENTS.outlined" @click="resetOne">Reset this readout</BngButton>
          </section>
        </div>

        <footer>
          <label class="et-row">
            <span>Hide units above (km/h)</span>
            <BngSlider v-model="config.options.unitsHideAboveKmh" :min="0" :max="120" :step="1" :debounce="0" />
            <b>{{ config.options.unitsHideAboveKmh }}</b>
          </label>
          <label class="et-row">
            <span>Icon scale</span>
            <BngSlider v-model="config.options.iconScale" :min="0.3" :max="1.5" :step="0.05" :debounce="0" />
            <b>{{ round2(config.options.iconScale) }}</b>
          </label>
          <label class="et-row">
            <span>Units fade out (s)</span>
            <BngSlider v-model="config.options.unitsFadeOutSeconds" :min="0" :max="5" :step="0.1" :debounce="0" />
            <b>{{ round2(config.options.unitsFadeOutSeconds) }}</b>
          </label>
          <label class="et-row">
            <span>Units fade in (s)</span>
            <BngSlider v-model="config.options.unitsFadeInSeconds" :min="0" :max="5" :step="0.1" :debounce="0" />
            <b>{{ round2(config.options.unitsFadeInSeconds) }}</b>
          </label>
          <div class="et-actions">
            <BngButton :accent="ACCENTS.outlined" @click="onReset">Reset everything</BngButton>
            <BngButton @click="onSave">Save</BngButton>
          </div>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from "vue"
import { BngButton, BngSwitch, BngSlider, ACCENTS } from "@/common/components/base"
import { config, saveConfig, resetConfig, resetElement } from "./config.js"
import SliderRow from "./sliderRow.vue"

const props = defineProps({ open: Boolean })
defineEmits(["close"])

// Closing the panel is the natural "I'm done" signal, so edits are persisted
// then as well as behind the explicit Save button. Losing half an hour of
// nudging to a missed Save click was this panel's most likely failure mode.
watch(
  () => props.open,
  (open, was) => {
    if (was && !open) saveConfig()
  }
)

// Fifty swatches, grouped by hue so the grid reads as a ramp rather than a
// jumble. The eight the dial ships with are all in here, at their exact hex,
// so an existing configuration still lines up with a swatch instead of
// landing between two of them.
const PALETTE = [
  // neutrals
  "#ffffff", "#e6edf3", "#c8ccd0", "#9da5b4", "#6e7681", "#484f58",
  // reds
  "#ffb3b3", "#ff6b6b", "#ff4d4d", "#e5484d", "#c9252d", "#8b1a1f",
  // oranges
  "#ffd6a5", "#ffb454", "#ff9e2c", "#f0883e", "#db6d28", "#a8500f",
  // yellows
  "#fff5b1", "#ffeb80", "#ffd93d", "#f2cc60", "#d9a406", "#a67c00",
  // greens
  "#b7f7c1", "#80ff89", "#6ee787", "#3fb950", "#2ea043", "#1a7f37", "#0f5323",
  // teals
  "#b3f0ff", "#80d4ff", "#56d4dd", "#39c5cf", "#1f9ea8", "#0b6e75",
  // blues
  "#a5d6ff", "#79c0ff", "#58a6ff", "#388bfd", "#1f6feb", "#0d419d",
  // purples
  "#d2a8ff", "#bc8cff", "#a371f7", "#8957e5",
  // pinks
  "#ffadda", "#ff8fc7", "#f778ba",
]

// Turns camelCase keys into something readable without maintaining a second
// list that would drift out of step with layout.js.
function humanise(key) {
  return key.replace(/([A-Z])/g, " $1").replace(/^./, c => c.toUpperCase())
}

const items = computed(() => {
  const out = []
  for (const key of Object.keys(config.elements)) {
    out.push({ section: "elements", key, label: humanise(key) })
  }
  for (const key of Object.keys(config.units)) {
    out.push({ section: "units", key, label: humanise(key) + " unit" })
  }
  return out
})

const selSection = ref("elements")
const selKey = ref(Object.keys(config.elements)[0])

const sel = computed(() => config[selSection.value] && config[selSection.value][selKey.value])
const selLabel = computed(() => humanise(selKey.value) + (selSection.value === "units" ? " unit" : ""))

function select(item) {
  selSection.value = item.section
  selKey.value = item.key
}

function entryOf(item) {
  return config[item.section][item.key] || {}
}

// Units without a colour of their own show the colour they inherit, so the
// list reflects what is actually on screen.
function swatchOf(item) {
  const e = entryOf(item)
  if (e.color) return e.color
  // Captions inherit through `for` exactly as unit labels do, so the lookup is
  // not restricted to the units section.
  const owner = e.for && config.elements[e.for]
  return (owner && owner.color) || "#ffffff"
}

// Which palette colours are already on the dial, and what is using them.
// Recomputed from the live config, so changing a readout's colour immediately
// moves its name to the swatch it now sits on.
const usedColours = computed(() => {
  const map = {}
  const note = (hex, name) => {
    if (!hex) return
    const key = String(hex).toLowerCase()
    ;(map[key] || (map[key] = [])).push(name)
  }
  for (const key of Object.keys(config.elements)) note(config.elements[key].color, humanise(key))
  // Units mostly inherit their owner's colour; only the ones overriding it
  // have a colour of their own to report here.
  for (const key of Object.keys(config.units)) note(config.units[key].color, humanise(key) + " unit")
  return map
})

const usedBy = c => usedColours.value[c.toLowerCase()] || []

// Anything that paints text can be recoloured: either it carries its own
// colour, or it names the readout it inherits from and can override it.
const inherits = computed(() => !!sel.value && typeof sel.value.for === "string")
const canColour = computed(() => !!sel.value && ("color" in sel.value || inherits.value))

// What is actually on screen for this entry, which is what the picker and the
// hex field must show -- an inherited colour is still a colour.
const effectiveColour = computed(() => {
  const e = sel.value
  if (!e) return "#ffffff"
  if (e.color) return e.color
  const owner = e.for && config.elements[e.for]
  return (owner && owner.color) || "#ffffff"
})

// Dropping the key rather than writing the inherited value back: the entry has
// to keep following its readout, so that recolouring the readout later still
// carries the caption with it.
function unlinkColour() {
  if (sel.value) delete sel.value.color
}

// One name fits under a swatch; the rest go in the tooltip.
function usedLabel(c) {
  const names = usedBy(c)
  if (!names.length) return ""
  return names.length > 1 ? names[0] + " +" + (names.length - 1) : names[0]
}

// Compared against the effective colour, so an inherited one is outlined too.
const isCurrent = c => effectiveColour.value.toLowerCase() === c.toLowerCase()

const round2 = v => Math.round(Number(v) * 100) / 100

// Only commit a hex the browser can actually parse. Without this an invalid
// string ("#ff", "rouge") was applied to the SVG fill AND persisted, leaving a
// readout permanently invisible with no clue why.
function onHex(e) {
  const v = e.target.value.trim()
  if (/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(v)) sel.value.color = v
}

function resetOne() {
  resetElement(selSection.value, selKey.value)
  saveConfig()
}

function onSave() {
  saveConfig()
}

function onReset() {
  // Deliberately no saveConfig() here: resetConfig() clears the stored file,
  // and saving straight after would write it back immediately.
  resetConfig()
}
</script>

<style lang="scss" scoped>
.et-settings-backdrop {
  position: fixed;
  inset: 0;
  /* Teleported to body, outside the app container that opts out of pointer
     events -- but stated explicitly so a future change there cannot silently
     make the panel unclickable. */
  pointer-events: auto;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
}

.et-settings {
  width: min(880px, 92vw);
  height: min(620px, 88vh);
  display: flex;
  flex-direction: column;
  background: #16191d;
  color: #e6edf3;
  border-radius: 10px;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.6);
  font-family: "Open Sans", sans-serif;
  overflow: hidden;

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid #262c33;

    h2 {
      margin: 0;
      font-size: 17px;
    }
  }

  footer {
    padding: 10px 16px;
    border-top: 1px solid #262c33;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}

.et-body {
  flex: 1;
  display: flex;
  min-height: 0;

  aside {
    width: 220px;
    overflow-y: auto;
    border-right: 1px solid #262c33;
    padding: 6px;
  }
}

.et-pick {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  background: none;
  border: 0;
  border-radius: 5px;
  color: inherit;
  font: inherit;
  font-size: 13px;
  text-align: left;
  cursor: pointer;

  &:hover {
    background: #1f242a;
  }

  &.active {
    background: #2b333c;
  }
}

.et-swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex: none;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
}

.et-name {
  flex: 1;
}

.et-off {
  font-size: 11px;
  opacity: 0.5;
}

.et-editor {
  flex: 1;
  padding: 14px 18px;
  overflow-y: auto;

  h3 {
    margin: 0 0 12px;
    font-size: 15px;
  }
}

.et-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 13px;

  > span {
    width: 160px;
    flex: none;
    opacity: 0.85;
  }

  > b {
    width: 52px;
    text-align: right;
    font-weight: 600;
  }
}

.et-colour {
  margin: 14px 0;
  font-size: 13px;
}

.et-colour-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;

  > span {
    width: 160px;
    flex: none;
    opacity: 0.85;
  }
}

/* Auto-fill rather than a fixed column count: the panel is sized against the
   viewport, and a fixed grid either overflowed it or wasted half its width. */
.et-swatches {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(56px, 1fr));
  gap: 7px 5px;

  button {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 0;
    border: 0;
    background: none;
    color: inherit;
    cursor: pointer;
  }

  button.used .et-chip {
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.85);
  }

  /* The readout's own colour, so you can see where you are before choosing. */
  button.current .et-chip {
    box-shadow: inset 0 0 0 2px #ffffff, 0 0 0 2px rgba(255, 255, 255, 0.35);
  }
}

.et-chip {
  height: 18px;
  border-radius: 4px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
}

/* Kept at a fixed height whether or not there is a name, so the rows stay
   aligned across a grid where most swatches are unlabelled. */
.et-chip-label {
  min-height: 11px;
  font-size: 8.5px;
  line-height: 11px;
  text-align: center;
  opacity: 0.7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.et-hex {
  width: 92px;
  padding: 4px 6px;
  background: #0f1216;
  border: 1px solid #2b333c;
  border-radius: 4px;
  color: inherit;
  font-family: monospace;
  font-size: 12px;
}

.et-note {
  margin: 12px 0;
  font-size: 12px;
  opacity: 0.6;
}

.et-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
