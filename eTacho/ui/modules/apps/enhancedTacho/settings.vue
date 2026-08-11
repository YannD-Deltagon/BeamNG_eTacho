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
               35 entries x 6 fields laid out at once is unreadable. The list
               shows GROUPS -- a value with its caption and its unit -- because
               that is the thing you actually want to move. -->
          <aside>
            <button class="et-pick et-global" :class="{ active: showGlobal }" @click="showGlobal = true">
              <span class="et-name">Global settings</span>
            </button>
            <button
              v-for="g in groups"
              :key="g.key"
              class="et-pick"
              :class="{ active: group && g.key === group.key }"
              @click="showGlobal = false; selectGroup(g)">
              <span class="et-swatch" :style="{ background: swatchOf(g.members[0]) }"></span>
              <span class="et-name">{{ g.label }}</span>
              <span v-if="g.members.length > 1" class="et-count">{{ g.members.length }}</span>
              <span v-if="entryOf(g.members[0]).visible === false" class="et-off">hidden</span>
            </button>
          </aside>

          <section class="et-editor">
            <!-- Global rules first, then the selected group. Both live in the
                 scrolling body: the footer cannot hold settings, it is the one
                 part of the panel that is not allowed to scroll. -->
            <template v-if="showGlobal">
              <h3>Global settings</h3>
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
            <!-- The rule every caption and unit label follows unless it has
                 unlinked a parameter for itself. -->
            <h4>Labels</h4>
            <label class="et-row">
              <span>Label opacity</span>
              <BngSlider v-model="config.options.label.opacity" :min="0" :max="1" :step="0.05" :debounce="0" />
              <b>{{ round2(config.options.label.opacity) }}</b>
            </label>
            <label class="et-row">
              <span>Lighten to white</span>
              <BngSlider v-model="config.options.label.lighten" :min="0" :max="1" :step="0.05" :debounce="0" />
              <b>{{ round2(config.options.label.lighten) }}</b>
            </label>

            <h4>Legibility</h4>
            <label class="et-row">
              <span>Effect</span>
              <span class="et-modes">
                <button
                  v-for="m in ['none', 'outline', 'shadow']"
                  :key="m"
                  :class="{ active: config.options.textEffect.mode === m }"
                  @click="config.options.textEffect.mode = m">{{ m }}</button>
              </span>
            </label>
            <template v-if="config.options.textEffect.mode !== 'none'">
              <label v-if="config.options.textEffect.mode === 'outline'" class="et-row">
                <span>Outline width</span>
                <BngSlider v-model="config.options.textEffect.width" :min="0" :max="0.4" :step="0.01" :debounce="0" />
                <b>{{ round2(config.options.textEffect.width) }}</b>
              </label>
              <template v-else>
                <label class="et-row">
                  <span>Shadow offset Y</span>
                  <BngSlider v-model="config.options.textEffect.dy" :min="-0.3" :max="0.3" :step="0.01" :debounce="0" />
                  <b>{{ round2(config.options.textEffect.dy) }}</b>
                </label>
                <label class="et-row">
                  <span>Shadow blur</span>
                  <BngSlider v-model="config.options.textEffect.blur" :min="0" :max="0.4" :step="0.01" :debounce="0" />
                  <b>{{ round2(config.options.textEffect.blur) }}</b>
                </label>
              </template>
              <label class="et-row">
                <span>Effect strength</span>
                <BngSlider v-model="config.options.textEffect.opacity" :min="0" :max="1" :step="0.05" :debounce="0" />
                <b>{{ round2(config.options.textEffect.opacity) }}</b>
              </label>
              <label class="et-row">
                <span>Effect colour</span>
                <input :value="config.options.textEffect.color" @input="onEffectHex" class="et-hex" spellcheck="false" />
              </label>
            </template>
            </template>

            <template v-else-if="sel">
            <h3>{{ selLabel }}</h3>

            <!-- Acts on the whole group: this is the part that keeps a caption
                 welded to the value it belongs to. -->
            <div class="et-group-block">
              <label class="et-row">
                <span>Whole group visible</span>
                <BngSwitch v-model="groupVisible" />
              </label>

              <template v-if="groupValue && groupValue.x !== undefined">
                <SliderRow v-model="groupX" label="Move group X" :min="0" :max="660" :step="1" />
                <SliderRow v-model="groupY" label="Move group Y" :min="0" :max="660" :step="1" />
              </template>
              <template v-else-if="groupValue && groupValue.radius !== undefined">
                <SliderRow v-model="groupRadius" label="Move group radius" :min="0" :max="330" :step="1" />
                <SliderRow v-if="groupValue.angle !== undefined" v-model="groupAngle"
                  label="Move group angle" :min="-180" :max="180" :step="1" />
              </template>

              <div class="et-colour">
                <div class="et-colour-head">
                  <span>Group colour</span>
                  <input :value="groupColour" @input="onGroupHex" class="et-hex" spellcheck="false" />
                </div>
                <div class="et-swatches">
                  <button
                    v-for="c in PALETTE"
                    :key="'g' + c"
                    :class="{ used: !!usedBy(c).length, current: isGroupColour(c) }"
                    :title="usedBy(c).length ? c + ' — ' + usedBy(c).join(', ') : c"
                    @click="setGroupColour(c)">
                    <span class="et-chip" :style="{ background: c }"></span>
                    <span class="et-chip-label">{{ usedLabel(c) }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Then the individual parts, for the fine tuning the group
                 controls deliberately cannot express. -->
            <nav v-if="group && group.members.length > 1" class="et-members">
              <button
                v-for="(m, i) in group.members"
                :key="m.section + '.' + m.key"
                :class="{ active: i === selMember }"
                @click="selMember = i">{{ m.role }}</button>
            </nav>

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

            <!-- The label rule, one parameter at a time. Each row follows the
                 global setting until you unlink it, and unlinking seeds the
                 value from the rule so nothing jumps on screen. Per parameter
                 rather than per entry, so a caption can carry a heavier
                 outline while its opacity still tracks the rule. -->
            <template v-if="inherits">
              <div v-for="p in LABEL_PARAMS" :key="p.key" class="et-sync-row">
                <SliderRow
                  v-model="p.model.value"
                  :label="p.label"
                  :min="p.min" :max="p.max" :step="p.step" />
                <button
                  class="et-sync"
                  :class="{ on: isSynced(p.key) }"
                  :title="isSynced(p.key) ? 'Following the global rule' : 'Set for this label only — click to follow the rule again'"
                  @click="toggleSync(p.key, config.options[p.source])">
                  {{ isSynced(p.key) ? "synced" : "custom" }}
                </button>
              </div>
            </template>

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
            </template>
          </section>
        </div>

        <footer>
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

// A readout, its caption and its unit are one thing on the dial, and were
// three unrelated rows in this list -- so moving "brake temperature" meant
// finding three entries and nudging each by hand until they lined up again.
// They are grouped by the link the data already carries: `for` naming the
// value an entry belongs to. Nothing is hand-listed here, so a readout added
// to layout.js appears grouped without touching this file.
const groups = computed(() => {
  const out = []
  for (const key of Object.keys(config.elements)) {
    if (config.elements[key].for) continue
    const members = [{ section: "elements", key, role: "Value" }]
    for (const k of Object.keys(config.elements)) {
      if (config.elements[k].for === key) members.push({ section: "elements", key: k, role: "Label" })
    }
    for (const k of Object.keys(config.units)) {
      if (config.units[k].for === key) members.push({ section: "units", key: k, role: "Unit" })
    }
    out.push({ key, label: humanise(key), members })
  }
  return out
})

const showGlobal = ref(false)
const selGroup = ref(null)
const selMember = ref(0)

const group = computed(() => {
  const list = groups.value
  return list.find(g => g.key === selGroup.value) || list[0] || null
})

const member = computed(() => {
  const g = group.value
  if (!g) return null
  return g.members[Math.min(selMember.value, g.members.length - 1)] || null
})

// Every per-entry control below still edits ONE entry: the group layer only
// decides which, and adds the few operations that act on all of them.
const sel = computed(() => {
  const m = member.value
  return m ? config[m.section][m.key] : null
})

const selLabel = computed(() => {
  const g = group.value
  const m = member.value
  return g && m ? g.label + " — " + m.role.toLowerCase() : ""
})

function selectGroup(g) {
  selGroup.value = g.key
  selMember.value = 0
}

function entryOf(item) {
  return config[item.section][item.key] || {}
}

// The group's value: what its colour, its position and its swatch read from.
const groupValue = computed(() => (group.value ? config.elements[group.value.key] : null))

// Moving the group moves every member by the same delta, so the caption and
// the unit keep the offsets they were placed at instead of collapsing onto the
// value. The damage readouts are placed on the arc and carry radius/angle
// rather than x/y; the same rule applies to whichever axis an entry has.
function moveGroup(axis, next) {
  const g = group.value
  const anchor = groupValue.value
  if (!g || !anchor || anchor[axis] === undefined) return
  const delta = Number(next) - anchor[axis]
  if (!delta) return
  for (const m of g.members) {
    const e = config[m.section][m.key]
    if (e && e[axis] !== undefined) e[axis] = round2(e[axis] + delta)
  }
}

const groupAxis = axis =>
  computed({
    get: () => (groupValue.value && groupValue.value[axis]) || 0,
    set: v => moveGroup(axis, v),
  })

const groupX = groupAxis("x")
const groupY = groupAxis("y")
const groupRadius = groupAxis("radius")
const groupAngle = groupAxis("angle")

// Colouring the group colours the group: a member that had broken away with a
// colour of its own is put back in step, otherwise "change the colour" would
// visibly miss half the thing. The captions then re-derive their own shade
// from the value through the global label rule.
function setGroupColour(c) {
  const g = group.value
  if (!g) return
  for (const m of g.members) {
    const e = config[m.section][m.key]
    if (!e) continue
    if (m.role === "Value") e.color = c
    else delete e.color
  }
}

const groupVisible = computed({
  get: () => !!(groupValue.value && groupValue.value.visible),
  set: v => {
    const g = group.value
    if (g) for (const m of g.members) config[m.section][m.key].visible = v
  },
})

// ---- per-parameter synchronisation -----------------------------------------
// A caption follows the global rule for a parameter until it holds a value of
// its own for it. Desyncing seeds the override from the rule so nothing jumps
// on screen; syncing deletes the key, which is what hands the parameter back
// to the rule permanently rather than freezing today's value into the entry.
function styleBag() {
  const e = sel.value
  if (!e) return null
  if (!e.style) e.style = {}
  return e.style
}

const isSynced = key => !sel.value || !sel.value.style || sel.value.style[key] === undefined

function toggleSync(key, source) {
  const bag = styleBag()
  if (!bag) return
  if (bag[key] === undefined) bag[key] = source[key]
  else delete bag[key]
}

const override = (key, sourceName) =>
  computed({
    get: () => {
      const e = sel.value
      const own = e && e.style && e.style[key]
      return own !== undefined ? own : config.options[sourceName][key]
    },
    set: v => {
      const bag = styleBag()
      if (bag) bag[key] = v
    },
  })

const ovOpacity = override("opacity", "label")
const ovLighten = override("lighten", "label")
const ovEffectWidth = override("width", "textEffect")

// Declared as data so the template renders one row per parameter with its own
// sync toggle, rather than three near-identical blocks of markup.
const LABEL_PARAMS = [
  { key: "opacity", source: "label", label: "Label opacity", min: 0, max: 1, step: 0.05, model: ovOpacity },
  { key: "lighten", source: "label", label: "Lighten to white", min: 0, max: 1, step: 0.05, model: ovLighten },
  { key: "width", source: "textEffect", label: "Outline width", min: 0, max: 0.4, step: 0.01, model: ovEffectWidth },
]

// The group's colour is the value's colour: the captions derive from it.
const groupColour = computed(() => (groupValue.value && groupValue.value.color) || "#ffffff")
const isGroupColour = c => groupColour.value.toLowerCase() === c.toLowerCase()

function onGroupHex(e) {
  const v = e.target.value.trim()
  if (/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(v)) setGroupColour(v)
}

function onEffectHex(e) {
  const v = e.target.value.trim()
  if (/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(v)) config.options.textEffect.color = v
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
    /* flex:none, sans quoi le pied prend sa hauteur SUR le corps, qui est le
       seul element retrecissable. C'est ce qui avait fait disparaitre la
       liste et l'editeur quand des reglages y avaient ete ajoutes. */
    flex: none;
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

/* Group-wide controls, boxed so it is obvious which controls move everything
   and which edit only the part selected below them. */
.et-global {
  margin-bottom: 6px;
  border-bottom: 1px solid #262c33;
  padding-bottom: 8px;
}

.et-group-block {
  padding: 12px 14px;
  margin-bottom: 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
}

.et-members {
  display: flex;
  gap: 4px;
  margin-bottom: 14px;

  button {
    padding: 5px 12px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    background: none;
    color: inherit;
    font-size: 12px;
    cursor: pointer;

    &.active {
      background: rgba(255, 255, 255, 0.16);
      border-color: rgba(255, 255, 255, 0.4);
    }
  }
}

.et-count {
  margin-left: auto;
  padding: 0 5px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 10px;
  opacity: 0.8;
}

/* The slider keeps its row; the toggle sits after it, same width as the value
   readout so the sliders stay aligned with the ungated rows above. */
.et-sync-row {
  display: flex;
  align-items: center;
  gap: 8px;

  > label {
    flex: 1;
    min-width: 0;
  }
}

.et-sync {
  width: 62px;
  flex: none;
  padding: 3px 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  background: none;
  color: inherit;
  font-size: 10px;
  cursor: pointer;
  opacity: 0.6;

  &.on {
    border-color: rgba(126, 231, 135, 0.5);
    color: #7ee787;
    opacity: 1;
  }
}

.et-modes {
  display: flex;
  gap: 4px;

  button {
    padding: 4px 10px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    background: none;
    color: inherit;
    font-size: 12px;
    cursor: pointer;

    &.active {
      background: rgba(255, 255, 255, 0.16);
      border-color: rgba(255, 255, 255, 0.4);
    }
  }
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
