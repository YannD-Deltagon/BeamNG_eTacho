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

            <!-- Arc-placed readouts are positioned by radius and angle, so the
                 x/y sliders would mean nothing for them. -->
            <template v-if="sel.radius !== undefined">
              <SliderRow v-model="sel.radius" label="Radius" :min="0" :max="330" :step="1" />
              <SliderRow v-model="sel.angle" label="Angle" :min="-180" :max="180" :step="1" />
              <SliderRow v-if="sel.dy !== undefined" v-model="sel.dy" label="Caption offset" :min="-60" :max="60" :step="1" />
            </template>
            <template v-else-if="sel.x !== undefined">
              <SliderRow v-model="sel.x" label="X" :min="0" :max="660" :step="1" />
              <SliderRow v-model="sel.y" label="Y" :min="0" :max="660" :step="1" />
            </template>

            <SliderRow v-if="sel.size !== undefined" v-model="sel.size" label="Size" :min="6" :max="160" :step="0.5" />
            <SliderRow v-if="sel.w !== undefined" v-model="sel.w" label="Width" :min="10" :max="400" :step="1" />
            <SliderRow v-if="sel.h !== undefined" v-model="sel.h" label="Height" :min="2" :max="40" :step="1" />
            <SliderRow v-if="sel.rotate !== undefined" v-model="sel.rotate" label="Rotation" :min="-90" :max="90" :step="90" />
            <SliderRow :model-value="sel.opacity === undefined ? 1 : sel.opacity" label="Opacity"
              :min="0" :max="1" :step="0.05" @update:modelValue="v => (sel.opacity = v)" />

            <!-- A unit label with no colour of its own inherits the value's,
                 which is the point of linking them: one setting, both texts. -->
            <div v-if="'color' in sel" class="et-colour">
              <span>Colour</span>
              <div class="et-swatches">
                <button v-for="c in PALETTE" :key="c" :style="{ background: c }" @click="sel.color = c"></button>
              </div>
              <input v-model="sel.color" class="et-hex" spellcheck="false" />
            </div>
            <p v-else-if="selSection === 'units'" class="et-note">
              Inherits the colour of the readout it labels.
            </p>

            <BngButton :accent="ACCENTS.outlined" @click="resetOne">Reset this readout</BngButton>
          </section>
        </div>

        <footer>
          <label class="et-row">
            <span>Hide units above (km/h)</span>
            <BngSlider v-model="config.options.unitsHideAboveKmh" :min="0" :max="120" :step="1" />
            <b>{{ config.options.unitsHideAboveKmh }}</b>
          </label>
          <label class="et-row">
            <span>Icon scale</span>
            <BngSlider v-model="config.options.iconScale" :min="0.3" :max="1.5" :step="0.05" />
            <b>{{ round2(config.options.iconScale) }}</b>
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
import { ref, computed } from "vue"
import { BngButton, BngSwitch, BngSlider, ACCENTS } from "@/common/components/base"
import { config, saveConfig, resetConfig, resetElement } from "./config.js"
import SliderRow from "./sliderRow.vue"

defineProps({ open: Boolean })
defineEmits(["close"])

const PALETTE = ["#ffffff", "#c8ccd0", "#80ff89", "#ffeb80", "#80d4ff", "#ffb454", "#ff6b6b", "#6ee787"]

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
  if (item.section === "units" && e.for) {
    const owner = config.elements[e.for]
    if (owner && owner.color) return owner.color
  }
  return "#ffffff"
}

const round2 = v => Math.round(Number(v) * 100) / 100

function resetOne() {
  resetElement(selSection.value, selKey.value)
  saveConfig()
}

function onSave() {
  saveConfig()
}

function onReset() {
  resetConfig()
  saveConfig()
}
</script>

<style lang="scss" scoped>
.et-settings-backdrop {
  position: fixed;
  inset: 0;
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
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 14px 0;
  font-size: 13px;

  > span {
    width: 160px;
    flex: none;
    opacity: 0.85;
  }
}

.et-swatches {
  display: flex;
  gap: 5px;

  button {
    width: 20px;
    height: 20px;
    border: 0;
    border-radius: 4px;
    cursor: pointer;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
  }
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
