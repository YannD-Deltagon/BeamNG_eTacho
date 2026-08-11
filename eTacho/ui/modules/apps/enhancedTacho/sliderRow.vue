<!--
  A labelled slider with its current value shown alongside.

  Exists only so the settings panel is not the same six lines of markup
  repeated a dozen times. The value readout matters more than it looks: a bare
  slider gives no way to reproduce a setting, and these are coordinates people
  will want to write down and share.
-->
<template>
  <label class="et-slider-row">
    <span class="et-label">{{ label }}</span>
    <BngSlider
      :model-value="Number(modelValue)"
      :min="min"
      :max="max"
      :step="step"
      :debounce="0"
      @update:modelValue="v => $emit('update:modelValue', Number(v))" />
    <b class="et-value">{{ display }}</b>
  </label>
</template>

<script setup>
import { computed } from "vue"
import { BngSlider } from "@/common/components/base"

const props = defineProps({
  modelValue: { type: [Number, String], default: 0 },
  label: { type: String, default: "" },
  min: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  step: { type: Number, default: 1 },
})

// BngSlider debounces at 500 ms by default, so the dial lagged half a second
// behind the drag. Zero makes the gauge follow the finger, which is the whole
// point of editing it live.

defineEmits(["update:modelValue"])

// Decimals follow the step, so a 0.05 step shows 0.75 rather than 0.7500001
// and a whole-number step shows no decimal point at all.
const display = computed(() => {
  const n = Number(props.modelValue)
  if (!isFinite(n)) return "-"
  const decimals = props.step >= 1 ? 0 : String(props.step).split(".")[1]?.length || 2
  return n.toFixed(decimals)
})
</script>

<style lang="scss" scoped>
.et-slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 13px;
}

.et-label {
  width: 160px;
  flex: none;
  opacity: 0.85;
}

.et-value {
  width: 52px;
  flex: none;
  text-align: right;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
</style>
