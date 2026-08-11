<!--
  ENHANCED TACHO  --  APP SHELL

  Thin wrapper around `tacho.vue`. It owns everything that talks to the game
  and nothing that draws: stream subscription, unit-system wiring, vehicle
  lifecycle events, the fade in/out when telemetry becomes (un)available, and
  the settings panel's open/closed state.

  This split mirrors the stock app -- `app.vue` is the bridge, `tacho.vue` is
  the dial -- so a future game update to the stock shell can still be diffed
  against this file cleanly.

  This is a STANDALONE app: its own folder, directive and DOM element, so it
  sits alongside the game's own Tacho2 in the app selector rather than taking
  its place. Shadowing a stock app is not accepted on the BeamNG repository,
  and it would also mean a game update to that app silently changing this one.

  "interactive": "yes" in app.json is required, not cosmetic: without it
  AppHost keeps the widget at pointer-events: none and the settings button can
  never be clicked.
-->
<template>
  <div class="tacho-container" :style="{ opacity: visible ? 1 : 0 }">
    <tacho ref="tachoRef"></tacho>

    <!-- Settings button. Faint at rest, solid on hover. It is the only part
         of the widget that takes the mouse: the container opts out of pointer
         events so clicks pass through everywhere else. -->
    <button
      class="et-gear"
      :class="{ 'et-gear--shown': settingsOpen }"
      title="Enhanced Tacho settings"
      @click="settingsOpen = true">
      <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
        <path
          fill="currentColor"
          d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm9.4 4a7.6 7.6 0 0 1-.1 1.2l2 1.6a.5.5 0 0 1 .1.6l-1.9 3.3a.5.5 0 0 1-.6.2l-2.4-1a7.4 7.4 0 0 1-2 1.2l-.4 2.5a.5.5 0 0 1-.5.4h-3.8a.5.5 0 0 1-.5-.4l-.4-2.5a7.4 7.4 0 0 1-2-1.2l-2.4 1a.5.5 0 0 1-.6-.2L2.5 15.4a.5.5 0 0 1 .1-.6l2-1.6a7.6 7.6 0 0 1 0-2.4l-2-1.6a.5.5 0 0 1-.1-.6l1.9-3.3a.5.5 0 0 1 .6-.2l2.4 1a7.4 7.4 0 0 1 2-1.2l.4-2.5a.5.5 0 0 1 .5-.4h3.8a.5.5 0 0 1 .5.4l.4 2.5a7.4 7.4 0 0 1 2 1.2l2.4-1a.5.5 0 0 1 .6.2l1.9 3.3a.5.5 0 0 1-.1.6l-2 1.6c.06.4.1.8.1 1.2z" />
      </svg>
    </button>

    <TachoSettings :open="settingsOpen" @close="settingsOpen = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import { useBridge } from "@/bridge"
import { useEvents, useStreams } from "@/services/events"
import tacho from "./tacho.vue"
import TachoSettings from "./settings.vue"

const { units } = useBridge()
const events = useEvents()

const HIDE_DELAY = 500 // ms

const tachoRef = ref(null)
const visible = ref(false)
const settingsOpen = ref(false)
let hideTimer = null

function clearHideTimer() {
  if (!hideTimer) return
  clearTimeout(hideTimer)
  hideTimer = null
}

function show() {
  clearHideTimer()
  if (!visible.value) visible.value = true
}

function hide() {
  // Guard on `hideTimer` as well as `visible`: without it every frame of a
  // telemetry gap would queue another timeout.
  if (!visible.value || hideTimer) return
  hideTimer = setTimeout(() => {
    visible.value = false
    hideTimer = null
  }, HIDE_DELAY)
}

// Named rather than inline, purely so they can be passed to events.off() on
// unmount. An anonymous handler cannot be removed, and these fire for the whole
// session: the AngularJS version of this mod registered a fresh listener on
// every VehicleChange and never removed any, so after a dozen vehicle swaps the
// same work ran a dozen times per frame. Structurally impossible here.
function onVehicleChange() {
  tachoRef.value?.vehicleChanged()
}

function onVehicleFocusChanged(data) {
  // mode === true means this vehicle just became the player's active one.
  // Other modes (spectating, camera-only) must not trigger a re-init.
  if (data?.mode === true) tachoRef.value?.vehicleChanged()
}

onMounted(() => {
  // Hand the dial a converter it can call as callback(value, "speed"),
  // callback(value, "power") and so on. The dial stores every reading in its
  // base unit and converts only at draw time, which is what lets a player
  // switch between metric and imperial without a reload.
  tachoRef.value.wireThroughUnitSystem((val, func) => units[func](val))

  events.on("VehicleChange", onVehicleChange)
  events.on("VehicleFocusChanged", onVehicleFocusChanged)
})

onUnmounted(() => {
  clearHideTimer()
  events.off("VehicleChange", onVehicleChange)
  events.off("VehicleFocusChanged", onVehicleFocusChanged)
})

// Streams consumed by the dial:
//   electrics    speeds, RPM, oil temperature, odometer, pedals, steering
//   engineInfo   max RPM, gear, gear count, fuel, torque, power
//   stats        total_weight and the beam counts behind the damage readouts
//
// useStreams subscribes on mount and unsubscribes on unmount for us; stream
// registration is reference-counted engine-side, so leaking one would leave the
// vehicle computing telemetry nobody reads.
useStreams(["electrics", "engineInfo", "stats"], streams => {
  if (!tachoRef.value) return
  // update() returns false when the payload is unusable (no engine, vehicle
  // still spawning). That is the signal to fade out rather than draw garbage.
  if (tachoRef.value.update(streams)) {
    show()
  } else {
    hide()
  }
})
</script>

<style lang="scss" scoped>
.tacho-container {
  position: relative;
  width: 100%;
  height: 100%;
  /* app.json sets interactive: "yes" so the settings button can be clicked,
     but that turns the WHOLE 300x300 widget into a click target and stops
     anything behind it receiving the mouse. Opting the container out and the
     button back in restores the pass-through everywhere except the button
     itself -- CSS hit-testing allows an `auto` descendant under a `none`
     ancestor. */
  pointer-events: none;
  // Matches HIDE_DELAY closely enough that the fade finishes just as the
  // element is considered hidden, with no visible snap.
  transition: opacity 200ms ease-in-out;

  &:hover .et-gear {
    opacity: 1;
  }
}

.et-gear {
  position: absolute;
  top: 2%;
  right: 2%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #c8ccd0;
  cursor: pointer;
  pointer-events: auto;
  /* Faintly visible at rest rather than fully hidden: with no hover there is
     no way to discover it exists. This is what the stock VehicleRadar app
     does with its own settings button. */
  opacity: 0.18;
  transition: opacity 150ms ease;

  &:hover {
    color: #ffffff;
    background: rgba(0, 0, 0, 0.8);
  }
}

.et-gear--shown {
  opacity: 1;
}
</style>
