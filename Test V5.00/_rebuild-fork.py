"""Build the Enhanced Tacho dial by forking the stock BeamNG 0.39 tacho.vue.

WHY A PATCH SCRIPT RATHER THAN A COPY
    The dial is a 2700-line single-file component owned by BeamNG. Keeping our
    own full copy would silently freeze it at 0.39: every later fix, new icon
    or gauge-maths change from the developers would be lost. Instead we apply a
    small set of surgical, anchored edits to a freshly read stock file. The
    result diffs against the stock component in ~250 lines, and when the game
    updates you re-run this script: either it applies cleanly, or it stops on
    the exact anchor that moved and tells you which one.

WHAT THE FORK CHANGES
    - Repositions four stock elements (wheel speed, speed unit, gear, RPM
      legend) and drives them from layout.js.
    - Adds ten readouts of its own, also driven from layout.js.
    - Routes every value through the game's unit system, so metric/imperial
      switching needs no code change.
    The dial artwork -- ring, arcs, needle, icons, tick maths -- is untouched.

USAGE
    python _rebuild-fork.py [path/to/output/tacho.vue]

    The output defaults to this folder's own build. Set BEAMNG_DIR if the game
    is not in the default Steam location:
        BEAMNG_DIR="D:/Games/BeamNG.drive" python _rebuild-fork.py
"""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Read the stock component fresh every run, so the fork always rebases onto
# whatever version of the game is currently installed. The install path is not
# hard-coded: this script is version-controlled and has to run on a machine
# that is not the author's.
CANDIDATES = [
    os.environ.get("BEAMNG_DIR"),
    r"C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive",
    r"C:\Program Files\Steam\steamapps\common\BeamNG.drive",
    r"D:\Steam\steamapps\common\BeamNG.drive",
    r"D:\SteamLibrary\steamapps\common\BeamNG.drive",
    r"E:\SteamLibrary\steamapps\common\BeamNG.drive",
]
STOCK = os.path.join("ui", "modules", "apps", "Tacho2", "tacho.vue")

SRC = None
for base in CANDIDATES:
    if base and os.path.isfile(os.path.join(base, STOCK)):
        SRC = os.path.join(base, STOCK)
        break

if SRC is None:
    raise SystemExit(
        "Stock tacho.vue introuvable.\n"
        "Cherche dans :\n  " + "\n  ".join(c for c in CANDIDATES if c) + "\n"
        "Indique l'installation du jeu avec la variable BEAMNG_DIR, par exemple :\n"
        '  BEAMNG_DIR="D:/Games/BeamNG.drive" python _rebuild-fork.py'
    )

DST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, "ui", "modules", "apps", "Tacho2", "tacho.vue")

s = io.open(SRC, encoding="utf-8").read()
applied = []


def patch_block(name, selector, old, new, count):
    """Rewrite `old` -> `new` inside one CSS block only.

    The icon rules repeat their colour across a dozen paths, and the warning
    variants a few hundred lines below repeat the same shape with a different
    literal. A whole-file replace would be both ambiguous and wrong, so the
    block is located by selector and the count inside it is asserted.
    """
    global s
    head = "\n  " + selector + " {"
    i = s.find(head)
    if i < 0:
        raise SystemExit("CSS BLOCK NOT FOUND for '%s'" % selector)
    depth, j = 0, i
    while True:
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    block = s[i:j + 1]
    if block.count(old) != count:
        raise SystemExit("CSS BLOCK '%s': %d x %r, %d attendues"
                         % (selector, block.count(old), old, count))
    s = s[:i] + block.replace(old, new) + s[j + 1:]
    applied.append(name)


def patch(name, anchor, replacement, count=1):
    """Replace `anchor` with `replacement`, refusing anything ambiguous.

    A silent no-op or a partial match would produce a component that compiles
    but misbehaves in ways that are painful to trace, so both a missing anchor
    and an unexpected number of matches abort the build loudly.
    """
    global s
    if anchor not in s:
        raise SystemExit("ANCHOR NOT FOUND for '%s':\n%s" % (name, anchor[:200]))
    if s.count(anchor) != count:
        raise SystemExit("AMBIGUOUS ANCHOR for '%s': %d matches" % (name, s.count(anchor)))
    s = s.replace(anchor, replacement, count)
    applied.append(name)


# =============================================================================
# 1. Stock elements, repositioned and driven from layout.js
#
#    Position and size are bound as INLINE STYLE rather than through a CSS
#    rule. That is deliberate: the stock stylesheet nests its rules under
#    `.layer6`, giving them (0,2,0) specificity, so a flat `.tacho2-gear`
#    override loses. Worse, the gear's size is set twice -- once on the <text>
#    and once again on the <tspan> inside it via `.layer6 .text` -- so a single
#    override silently only half-works. Inline style sidesteps the whole
#    specificity question.
# =============================================================================

patch(
    "stock: wheel speed -> config",
    '''      <text xml:space="preserve" class="text1" x="329.88641" y="289.30463" id="tspan4449-43">
        <tspan ref="speedTextRef" id="tacho2speed" class="tacho2-speed" x="329.88641" y="289.30463">0</tspan>
      </text>''',
    '''      <text v-show="C.wheelSpeed.visible" xml:space="preserve" class="text1" :x="C.wheelSpeed.x" :y="C.wheelSpeed.y" :style="styles.wheelSpeed" id="tspan4449-43">
        <tspan ref="speedTextRef" id="tacho2speed" class="tacho2-speed" :x="C.wheelSpeed.x" :y="C.wheelSpeed.y" :style="styles.wheelSpeed">0</tspan>
      </text>''',
)

patch(
    "stock: speed unit -> config",
    '''      <text xml:space="preserve" id="speed_units" class="speed-units" x="330" y="348">
        <tspan ref="speedUnitTextRef" id="speedunit" x="330" y="348">mph</tspan>
      </text>''',
    '''      <text v-show="C.speedUnit.visible" xml:space="preserve" id="speed_units" class="speed-units" :x="C.speedUnit.x" :y="C.speedUnit.y" :style="[styles.speedUnit, unitsFade]">
        <tspan ref="speedUnitTextRef" id="speedunit" :x="C.speedUnit.x" :y="C.speedUnit.y" :style="styles.speedUnit">mph</tspan>
      </text>''',
)

# The gear keeps the stock italic slant, applied as matrix(1,0,-0.13142611,1,0,0).
# A shear like that makes the on-screen abscissa x - 0.13142611*y, so a raw x
# from layout.js would land the glyph well left of where the author intended.
# `gearX` compensates, letting the config express the position as it is seen.
patch(
    "stock: gear -> config",
    '''      <text
        xml:space="preserve"
        id="tspan4449-4-3"
        class="tacho2-gear"
        x="386.67343"
        y="457.94861"
        transform="matrix(1,0,-0.13142611,1,0,0)">
        <tspan ref="gearTextRef" id="tacho2gear" class="text" x="386.67343" y="457.94861">4</tspan>
      </text>''',
    '''      <text
        v-show="C.gear.visible"
        xml:space="preserve"
        id="tspan4449-4-3"
        class="tacho2-gear"
        :x="gearX"
        :y="C.gear.y"
        :style="styles.gear"
        transform="matrix(1,0,-0.13142611,1,0,0)">
        <tspan ref="gearTextRef" id="tacho2gear" class="text" :x="gearX" :y="C.gear.y" :style="styles.gear">4</tspan>
      </text>''',
)

patch(
    "stock: RPM legend -> option",
    '''      <text xml:space="preserve" x="330.09229" y="498.18045" id="text4447-2-4" class="rpm-text-legend">
        <tspan ref="rpmLegendTextRef" id="tspan4449-3-1" x="330.09229" y="498.18045">x1000 RPM</tspan>
      </text>''',
    '''      <text v-show="O.showRpmLegend" xml:space="preserve" x="330.09229" y="498.18045" id="text4447-2-4" class="rpm-text-legend">
        <tspan ref="rpmLegendTextRef" id="tspan4449-3-1" x="330.09229" y="498.18045">x1000 RPM</tspan>
      </text>''',
)

# =============================================================================
# 2. The mod's own readouts
#
#    Appended as the LAST child of the root <svg>, not inside a layer. SVG has
#    no z-index: paint order is document order. The revcurve mask (layer3)
#    covers the entire canvas and the tick ring sits on top of it, so anything
#    added earlier in the tree is silently painted over -- which is exactly
#    what happened to the weight readout during development.
#
#    Values use Vue interpolation rather than the imperative setSvgText() the
#    stock component uses for its own elements. That is only worth the extra
#    machinery for elements redrawn every frame; ten text nodes reconciled by
#    Vue cost nothing measurable and the template stays readable.
# =============================================================================
TPL_NEW = """
      <!-- Mod readouts. Every position, size, colour and visibility lives in
           layout.js. Kept last in the root so it paints over the revcurve mask
           and the tick ring, which would otherwise hide it. -->
      <g ref="etLayerRef" id="et_readouts" class="et-readouts">
        <text v-show="C.weight.visible" :x="C.weight.x" :y="C.weight.y" :style="styles.weight">{{ V.weight }}</text>

        <text v-show="C.peakPower.visible" :x="C.peakPower.x" :y="C.peakPower.y" :style="styles.peakPower">{{ V.peakPower }}</text>
        <text v-show="C.peakSeparator.visible" :x="C.peakSeparator.x" :y="C.peakSeparator.y" :style="styles.peakSeparator">{{ C.peakSeparator.text }}</text>
        <text v-show="C.peakTorque.visible" :x="C.peakTorque.x" :y="C.peakTorque.y" :style="styles.peakTorque">{{ V.peakTorque }}</text>

        <text v-show="C.power.visible" :x="C.power.x" :y="C.power.y" :style="styles.power">{{ V.power }}</text>
        <text v-show="C.separator.visible" :x="C.separator.x" :y="C.separator.y" :style="styles.separator">{{ C.separator.text }}</text>
        <text v-show="C.torque.visible" :x="C.torque.x" :y="C.torque.y" :style="styles.torque">{{ V.torque }}</text>

        <text v-show="C.gearCount.visible" :x="C.gearCount.x" :y="C.gearCount.y" :style="styles.gearCount">{{ V.gearCount }}</text>

        <text v-show="C.oilTemp.visible" :x="C.oilTemp.x" :y="C.oilTemp.y" :style="sty(C.oilTemp, V.oilTemp)">{{ V.oilTemp }}</text>
        <text v-show="C.fuelUse.visible" :x="C.fuelUse.x" :y="C.fuelUse.y" :style="sty(C.fuelUse, V.fuelUse)">{{ V.fuelUse }}</text>

        <text v-show="C.gpsSpeed.visible" :x="C.gpsSpeed.x" :y="C.gpsSpeed.y" :style="styles.gpsSpeed">{{ V.gpsSpeed }}</text>

        <text v-show="C.odometer.visible" :x="C.odometer.x" :y="C.odometer.y" :style="styles.odometer">{{ V.odometer }}</text>

        <!-- Engine load: the fraction of the torque the engine could make at
             this rpm that it is actually making. Hidden by default -- see the
             engine load section of layout.js. -->
        <text v-show="C.engineLoad.visible" :x="C.engineLoad.x" :y="C.engineLoad.y" :style="styles.engineLoad">{{ V.engineLoad }}</text>

        <!-- Hottest brake core, from electrics.wheelThermals. -->
        <text v-show="C.brakeTemp.visible" :x="C.brakeTemp.x" :y="C.brakeTemp.y" :style="styles.brakeTemp">{{ V.brakeTemp }}</text>

        <!-- Structural damage. Positioned on an arc but drawn upright --
             see arcPoint() and the ARC-PLACED section of layout.js. -->
        <text v-show="C.beamsDeformed.visible" class="et-outlined" :x="arcPoint(C.beamsDeformed).x" :y="arcPoint(C.beamsDeformed).y" :style="sty(C.beamsDeformed)">{{ V.beamsDeformed }}</text>
        <text v-show="C.beamsBroken.visible" class="et-outlined" :x="arcPoint(C.beamsBroken).x" :y="arcPoint(C.beamsBroken).y" :style="sty(C.beamsBroken)">{{ V.beamsBroken }}</text>

        <!-- Driver inputs, drawn as arcs on the dial's own curve. Each is a
             full-length path revealed by stroke-dashoffset, the same technique
             the stock gauge uses for its rev sweep -- no geometry is rebuilt
             per frame, only one number changes. -->
        <g v-show="C.brake.visible">
          <path :d="inputArcs.brake.d" fill="none" :stroke="C.brake.color" :stroke-width="C.brake.width" stroke-linecap="round"
            :stroke-dasharray="inputArcs.brake.len" :stroke-dashoffset="inputArcs.brake.len * (1 - clamp01(V.brake))" />
        </g>
        <g v-show="C.throttle.visible">
          <path :d="inputArcs.throttle.d" fill="none" :stroke="C.throttle.color" :stroke-width="C.throttle.width" stroke-linecap="round"
            :stroke-dasharray="inputArcs.throttle.len" :stroke-dashoffset="inputArcs.throttle.len * (1 - clamp01(V.throttle))" />
        </g>
        <g v-show="C.clutch.visible">
          <path :d="inputArcs.clutch.d" fill="none" :stroke="C.clutch.color" :stroke-width="C.clutch.width" stroke-linecap="round"
            :stroke-dasharray="inputArcs.clutch.len" :stroke-dashoffset="inputArcs.clutch.len * (1 - clamp01(V.clutch))" />
        </g>

        <!-- Steering: a short segment that slides either side of twelve
             o'clock, between the brake and throttle wings. -->
        <g v-show="C.steering.visible">
          <path :d="steeringMark" fill="none" :stroke="C.steering.color" :stroke-width="C.steering.width" stroke-linecap="round" />
        </g>

        <!-- Unit labels. Each one is positioned independently in layout.js so
             it lands in a gap instead of being crammed against its value, and
             each reads its text from the game's converter for that quantity.
             Toggled as a set by clicking the dial. -->
        <g :style="unitsFade">
          <!-- Captions ride the same fade as the unit labels: they are
               legends rather than readings, so they go with the set that
               clears out of the way once you are moving. -->
          <text v-show="C.engineLoadLabel.visible" :x="C.engineLoadLabel.x" :y="C.engineLoadLabel.y" :style="styles.engineLoadLabel">{{ C.engineLoadLabel.text }}</text>
          <text v-show="C.brakeTempLabel.visible" :x="C.brakeTempLabel.x" :y="C.brakeTempLabel.y" :style="styles.brakeTempLabel">{{ C.brakeTempLabel.text }}</text>
          <text v-show="C.beamsDeformedLabel.visible" class="et-outlined" :x="arcPoint(C.beamsDeformedLabel).x" :y="arcPoint(C.beamsDeformedLabel).y" :style="capSty(C.beamsDeformedLabel, 'beamsDeformed')">{{ C.beamsDeformedLabel.text }}</text>
          <text v-show="C.beamsBrokenLabel.visible" class="et-outlined" :x="arcPoint(C.beamsBrokenLabel).x" :y="arcPoint(C.beamsBrokenLabel).y" :style="capSty(C.beamsBrokenLabel, 'beamsBroken')">{{ C.beamsBrokenLabel.text }}</text>
          <text
            v-for="(u, k) in U"
            :key="k"
            v-show="u.visible && (!C[u.for] || C[u.for].visible)"
            :x="u.x"
            :y="u.y"
            :transform="u.rotate ? `rotate(${u.rotate}, ${u.x}, ${u.y})` : undefined"
            :style="unitStyles[k]">{{ V[u.for + "U"] }}</text>
        </g>

      </g>
  </svg>
</template>"""

patch("template: config-driven readouts", "  </svg>\n</template>", TPL_NEW)

# =============================================================================
# 3. Script
# =============================================================================
patch(
    "script: imports",
    'import { ref, reactive, computed, onMounted } from "vue"\nimport { lua } from "@/bridge"',
    'import { ref, reactive, computed, onMounted } from "vue"\nimport { lua, useBridge } from "@/bridge"\nimport { config as CONFIG } from "./config.js"',
)

patch(
    "script: config, units and readout state",
    "const speedUnitTextRef = ref(null)",
    """const speedUnitTextRef = ref(null)

// ===================== Enhanced Tacho: mod readouts =====================
// Layout comes from config.js -- a reactive copy of layout.js with any edits
// made in the in-game panel layered on top. Reading the reactive object rather
// than the static defaults is what makes the settings panel update the dial
// live, with no apply step and no reload.
const C = CONFIG.elements
const O = CONFIG.options
const etLayerRef = ref(null)

// Style for a value. Emitted inline so it beats the stock stylesheet, whose
// rules are nested under .layer6 and therefore outrank any flat selector.
// A caption with no colour of its own takes the colour of the readout it
// labels, `for` naming that readout exactly as it does on a unit label. One
// setting per readout instead of two that drift apart -- and the caption is
// already dimmed by its own opacity, so inheriting gives you the duller
// version of the value's colour rather than an unrelated one.
function ownerColor(c) {
  const owner = c.for && C[c.for]
  return owner && owner.color
}

const sty = (c, text) => ({
  fontSize: fitSize(c, text) + "px",
  fill: c.color || ownerColor(c) || "#ffffff",
  textAnchor: c.anchor,
  fontFamily: O.font,
  opacity: c.opacity === undefined ? 1 : c.opacity,
})

// A unit label and the figure it belongs to are one thing to the eye, so the
// label takes the value's colour unless it overrides it. That makes colour a
// single setting per readout rather than two that can drift apart.
// Captions are dimmed by default: they are a legend, and at full strength they
// compete with the number they are labelling.
const CAPTION_OPACITY = 0.75

function unitSty(u) {
  const owner = C[u.for] || {}
  return {
    fontSize: u.size + "px",
    fill: u.color || owner.color || "#ffffff",
    textAnchor: u.anchor,
    fontFamily: O.font,
    opacity: u.opacity === undefined ? CAPTION_OPACITY : u.opacity,
  }
}

// Damage captions follow the same rule, keyed to the readout they caption.
function capSty(c, ownerKey) {
  const owner = C[ownerKey] || {}
  return {
    fontSize: c.size + "px",
    fill: c.color || owner.color || "#ffffff",
    textAnchor: c.anchor,
    fontFamily: O.font,
    opacity: c.opacity === undefined ? CAPTION_OPACITY : c.opacity,
  }
}

// Keeps a readout inside the width it was laid out for. `fitDigits` is the
// digit count the position was chosen around; beyond that the glyphs are
// scaled down in proportion, so a three-digit reading occupies exactly the
// space a two-digit one did instead of pushing into its neighbour.
function fitSize(c, text) {
  if (!c.fitDigits || text === undefined || text === null) return c.size
  const digits = String(text).replace(/[^0-9]/g, "").length
  return digits > c.fitDigits ? (c.size * c.fitDigits) / digits : c.size
}

// Unit-label visibility is purely speed-driven: shown while stopped, faded
// out once moving. There is no manual override -- an earlier build cycled
// through modes on click, which was easy to leave stuck in "always" with
// nothing on screen saying so.
const U = CONFIG.units

// Presentation is a function of the config alone: it changes when a settings
// slider moves, not when the car does. Computed inline, every render rebuilt
// one style object per element and re-ran sty() for each -- around 35 objects
// a frame describing something that had not changed. Cached here they are
// built once per config change instead.
//
// What this does NOT buy: skipping the DOM write. Vue guards the class patch
// on identity (`u&2 && m.class !== h.class` in the 3.5 runtime) but the style
// patch is unguarded (`u&4 && patchProp(el, "style", ...)`), because a style
// binding is allowed to be a mutable object. So a re-render still writes every
// property back into the CSSOM whether or not the object is the same one. The
// saving here is allocation and recomputation, not DOM traffic; the way to
// avoid the DOM traffic is to not re-render, which is what etSet() is for.
//
// Readouts with fitDigits are excluded: their size depends on the value, so
// they keep calling sty() directly.
const styles = computed(() => {
  const out = {}
  for (const key in C) {
    const c = C[key]
    if (c && c.size !== undefined && !c.fitDigits) out[key] = sty(c)
  }
  return out
})

const unitStyles = computed(() => {
  const out = {}
  for (const key in U) out[key] = unitSty(U[key])
  return out
})

const iconTfs = computed(() => ({ temp: iconTf("temp"), fuel: iconTf("fuel") }))

// The oil-temperature and fuel icons are the legend for their readout, the
// same way a caption is, so they follow the same rule: the value's colour, at
// the shared caption opacity. Their stock rules painted a hard-coded white
// that ignored whatever colour the readout had been given. The paths now
// stroke `currentColor`, so setting `color` here repaints the whole glyph.
// The warning variants (.ico-temp-on / .ico-fuel-on) keep their own colour --
// a warning that adopted the readout's colour would stop being a warning.
const iconStyles = computed(() => ({
  temp: { color: C.oilTemp.color, opacity: CAPTION_OPACITY },
  fuel: { color: C.fuelUse.color, opacity: CAPTION_OPACITY },
}))

// Ground speed in m/s, kept raw so the threshold behaves identically whatever
// unit system the player runs.
const etGroundSpeed = ref(0)

// km/h -> m/s. The threshold is written in km/h in layout.js purely because
// that is the number a human wants to type.
const etSpeedLimit = computed(() => (Number(O.unitsHideAboveKmh) || 15) / 3.6)

const showUnits = computed(() => etGroundSpeed.value <= etSpeedLimit.value)

// Opacity rather than v-show: v-show sets display:none, which removes the
// element from layout and kills any CSS transition on it. Binding opacity
// keeps it rendered and lets it fade.
// The duration follows the DIRECTION of the change -- longer coming back than
// going away -- so the labels slip out unnoticed while accelerating but return
// gently as you stop.
const unitsFade = computed(() => ({
  opacity: showUnits.value ? 1 : 0,
  transition: `opacity ${showUnits.value ? O.unitsFadeInSeconds : O.unitsFadeOutSeconds}s ease`,
}))

// The gear glyph is sheared by matrix(1,0,-0.13142611,1,0,0) to give it the
// stock italic slant. A shear maps x to x - 0.13142611*y, so we add that term
// back here: layout.js can then state where the gear should APPEAR, and the
// compensation is invisible to whoever edits it.
// Builds the arc a curved readout is laid along. Angles are the readable
// convention -- degrees, 0 = right, 90 = top, anticlockwise -- and are flipped
// here into SVG space, where y grows downwards. The sweep flag follows the
// direction of travel so text always runs the way the angles were written.
const ET_CX = 330
const ET_CY = 330

// Anchor point for an arc-placed readout. Only the POSITION follows the
// circle -- the text stays upright, which is what keeps it readable away from
// the top of the dial, where curved text tilts past being comfortable.
function arcPoint(c) {
  const rad = ((c.angle || 0) * Math.PI) / 180
  return {
    x: ET_CX + (c.radius || 0) * Math.cos(rad),
    y: ET_CY - (c.radius || 0) * Math.sin(rad) + (c.dy || 0),
  }
}

function arcPath(radius, a1, a2) {
  const rad = a => (a * Math.PI) / 180
  const x1 = ET_CX + radius * Math.cos(rad(a1))
  const y1 = ET_CY - radius * Math.sin(rad(a1))
  const x2 = ET_CX + radius * Math.cos(rad(a2))
  const y2 = ET_CY - radius * Math.sin(rad(a2))
  const large = Math.abs(a2 - a1) > 180 ? 1 : 0
  // Decreasing angle is clockwise on screen once y is flipped.
  const sweep = a2 < a1 ? 1 : 0
  return `M ${x1},${y1} A ${radius},${radius} 0 ${large},${sweep} ${x2},${y2}`
}

// Scaling for the stock fuel and temperature icons.
//
// This has to be an SVG transform composed IN FRONT of each icon's own matrix.
// CSS cannot do it. Setting the `transform` property REPLACES that matrix --
// in SVG2 the property and the presentation attribute are the same thing --
// and the individual `scale` property resolves `transform-origin` in the
// icon's LOCAL space, before its matrix, so the pivot lands nowhere near where
// the icon appears. Measured on the rendered dial, asking to pivot about
// (206.5, 329.9) actually pivoted about (288.8, 461.9).
//
// translate(c) scale(s) translate(-c) placed before the icon's matrix scales
// about the visual centre exactly, whatever that matrix contains. The extra dx
// nudges each icon onto the value below it.
function iconTf(which) {
  const s = O.iconScale === undefined ? 1 : O.iconScale
  const isTemp = which === "temp"
  const c = (isTemp ? O.iconTempCenter : O.iconFuelCenter) || [330, 330]
  const dx = (isTemp ? O.iconTempDx : O.iconFuelDx) || 0
  const dy = (isTemp ? O.iconTempDy : O.iconFuelDy) || 0
  return `translate(${dx},${dy}) translate(${c[0]},${c[1]}) scale(${s}) translate(${-c[0]},${-c[1]})`
}

const GEAR_SHEAR = 0.13142611
const gearX = computed(() => C.gear.x + GEAR_SHEAR * C.gear.y)

// Displayed strings. A `U` suffix holds the matching unit, empty when the
// element has `unit: false`.
const V = reactive({
  weight: "0", weightU: "",
  peakPower: "0", peakPowerU: "",
  peakTorque: "0", peakTorqueU: "",
  power: "0", powerU: "",
  torque: "0", torqueU: "",
  oilTemp: "0", oilTempU: "",
  fuelUse: "0", fuelUseU: "",
  gpsSpeed: "0", gpsSpeedU: "",
  odometer: "0", odometerU: "",
  gearCount: "",
  beamsDeformed: "0%",
  beamsBroken: "0%",
  engineLoad: "0%",
  brakeTemp: "0",
  // Driver inputs, kept as raw 0..1 fractions: they drive rectangle widths,
  // not text, so formatting them would only throw the precision away.
  throttle: 0,
  brake: 0,
  clutch: 0,
  steering: 0,
})

// Path for an input gauge's arc, and its length.
//
// Length is computed rather than measured with getTotalLength(): the path is a
// circular arc, so radius x angle is exact, and it avoids needing a ref and a
// mounted DOM node for every gauge.
function inputArc(c) {
  return arcPath(c.radius, c.angleStart, c.angleEnd)
}

function arcLen(c) {
  return (Math.abs(c.angleEnd - c.angleStart) * Math.PI * c.radius) / 180
}

// Reveals the coloured arc from its start. A pedal reading can momentarily sit
// just outside 0..1, and an unclamped offset would either overshoot the end of
// the arc or wrap back round and draw from the wrong end.
// Cached per gauge: path and length depend only on the config, which changes
// when a settings slider moves, not every frame. Computed inline they rebuilt
// three path strings and six lengths per render for an identical result.
const inputArcs = computed(() => {
  const out = {}
  for (const key of ["throttle", "brake", "clutch"]) {
    const c = C[key]
    if (c) out[key] = { d: inputArc(c), len: arcLen(c) }
  }
  return out
})

function clamp01(value) {
  const v = Number(value)
  return isFinite(v) ? Math.max(0, Math.min(1, v)) : 0
}

// Steering.
//
// `electrics.steering` is NOT a -1..1 fraction. hydros.lua:405 computes it as
//   -toInputSpace(...) * v.data.input.steeringWheelLock
// so it is an ANGLE IN DEGREES, and it carries a minus sign relative to the
// driver's input. Two consequences, both of which showed up on the dial:
// clamping it to +/-1 saturated the marker after one degree of lock, and the
// sign made it travel the wrong way.
//
// Dividing by that same steeringWheelLock recovers the -1..1 fraction. The
// lock is vehicle data rather than telemetry, so it is queried once per
// vehicle alongside the engine specs, with the layout.js value as a fallback
// for anything that does not report one.
const etSteerLock = ref(0)

const steeringFraction = computed(() => {
  const lock = etSteerLock.value || Number(C.steering.lockDegrees) || 360
  return Math.max(-1, Math.min(1, (Number(V.steering) || 0) / lock))
})

const steeringMark = computed(() => {
  const c = C.steering
  // Angles increase anticlockwise and the raw value is already negated, so
  // adding here makes the marker follow the front wheels.
  const mid = 90 + steeringFraction.value * c.sweep
  return arcPath(c.radius, mid + c.span / 2, mid - c.span / 2)
})

// Damage as a share of the vehicle's total beam count. Percentages rather than
// raw counts: a car has thousands of beams, so "247" means nothing on its own
// while "3%" is instantly readable and comparable between vehicles.
// Writes a quantised reading into V, and only when it changed. `steps` is the
// number of quantisation steps per unit: 200 gives 0.5% on a 0..1 pedal
// (invisible on a ~300px arc), 4 gives a quarter degree on steering. Skipping
// unchanged writes is what keeps the render effect idle when nothing moves.
function etSet(key, raw, steps) {
  const v = Number(raw)
  const q = isFinite(v) ? Math.round(v * steps) / steps : 0
  if (V[key] !== q) V[key] = q
}

function etDamagePercent(count, total) {
  const n = Number(count)
  const t = Number(total)
  if (!isFinite(n) || !isFinite(t) || t <= 0) return "0%"
  const pct = (n / t) * 100
  // The first bent beams matter more than the difference between 40 and 41,
  // and plain rounding hid the whole first percent behind "0%".
  if (pct > 0 && pct < 1) return "<1%"
  return Math.round(pct) + "%"
}

// Engine load, clamped 0..1. NOT smoothed on the way here despite the name:
// for combustion engines electrics.engineLoad carries instantEngineLoad
// straight through, so it is jittery by nature -- smoothed here rather than
// trusting a Lua smoother this path never applies. On EVs it is an average of
// the motors and can go negative under regeneration.
let etLoadSmoothed = 0

function etLoadPercent(x) {
  const n = Number(x)
  if (!isFinite(n)) return "0%"
  if (n < 0) return "REGEN"
  etLoadSmoothed += (Math.min(1, n) - etLoadSmoothed) * 0.15
  return Math.round(etLoadSmoothed * 100) + "%"
}

// Convert a raw reading through the game's unit service and store the result.
// `func` names the converter: speed, power, torque, temperature, weight,
// consumptionRate or length. Each returns { val, unit } already expressed in
// whichever system the player selected, which is why no unit string is ever
// written by this mod.
function setU(key, raw, func, decimals) {
  const n = Number(raw)
  if (!isFinite(n) || !UiUnitscallback.value) {
    V[key] = "0"
    V[key + "U"] = ""
    return
  }
  const r = UiUnitscallback.value(n, func)
  if (!r) {
    V[key] = "0"
    V[key + "U"] = ""
    return
  }
  // consumptionRate can legitimately return the string "n/a" for absurd rates,
  // so guard the numeric path rather than assuming a number.
  V[key] = typeof r.val === "number" ? r.val.toFixed(decimals || 0) : String(r.val)
  // The unit is always captured, whether or not it is currently displayed:
  // the unit labels read it from here, and the odometer's converter switches
  // between m and km as distance grows, so it cannot be resolved just once.
  V[key + "U"] = r.unit
}

const { api } = useBridge()

// Peak power and torque appear in no telemetry stream, so they have to be read
// from the vehicle's own Lua state. Stored raw (metric hp / Nm) and converted
// at display time like everything else. Re-queried on every vehicle change.
const etPeakPowerRaw = ref(0)
const etPeakTorqueRaw = ref(0)

function etFetchEngineSpecs() {
  const cmd = `(function()
    local e = powertrain and powertrain.getDevicesByCategory and powertrain.getDevicesByCategory("engine")
    local lock = 0
    if v and v.data and v.data.input then lock = v.data.input.steeringWheelLock or 0 end
    if not e or not e[1] then return { maxPower = 0, maxTorque = 0, steerLock = lock } end
    return { maxPower = e[1].maxPower or 0, maxTorque = e[1].maxTorque or 0, steerLock = lock }
  end)()`
  api.activeObjectLua(cmd, res => {
    const p = Number(res && res.maxPower)
    const t = Number(res && res.maxTorque)
    etPeakPowerRaw.value = isFinite(p) && p > 0 ? p : 0
    etPeakTorqueRaw.value = isFinite(t) && t > 0 ? t : 0
    const lk = Number(res && res.steerLock)
    etSteerLock.value = isFinite(lk) && lk > 0 ? lk : 0
  })
}

// --- fuel consumption sampler ------------------------------------------------
//
// Produces litres per METRE, which is what the game's consumptionRate
// converter expects; it turns that into L/100km or MPG per the player's units.
//
// Two traps, both of which produced wildly wrong figures before being fixed:
//
//  1. engineInfo[11] is `fuelVolume * (ignitionLevel > 0 and 1 or 0)` on the
//     Lua side (vehicleController.lua). It collapses to 0 the instant the
//     ignition is cut, so differencing across that edge reports the whole tank
//     as burnt inside one window -- the source of absurd readings. Any
//     non-positive reading re-arms the sampler instead of feeding it.
//
//  2. Distance must come from the odometer, not speed x elapsed time. The
//     latter samples speed once, at the END of the window, and assumes it held
//     throughout: that overstates consumption under braking and understates it
//     under acceleration. The odometer delta is exact.
const ET_SAMPLE_SECONDS = 1 // integration window
const ET_SMOOTHING = 0.3 // exponential smoothing; 1 would disable it

let etFuelPrev = null
let etOdoPrev = null
let etFuelTimer = 0
let etFuelLastTime = null
const etFuelUseRaw = ref(0)

function etResetConsumption() {
  etFuelPrev = null
  etOdoPrev = null
  etFuelTimer = 0
  etFuelLastTime = null
  etFuelUseRaw.value = 0
}

function etUpdateConsumption(fuelVolume, odometerMetres) {
  // Ignition off, no fuel system, or no odometer: re-arm rather than sample.
  if (!(fuelVolume > 0) || !isFinite(odometerMetres)) {
    etFuelPrev = null
    etOdoPrev = null
    etFuelTimer = 0
    etFuelUseRaw.value = 0
    return
  }

  const now = performance.now()

  // First usable frame after a reset: capture a baseline, measure nothing.
  if (etFuelPrev === null || etFuelLastTime === null) {
    etFuelPrev = fuelVolume
    etOdoPrev = odometerMetres
    etFuelLastTime = now
    etFuelTimer = 0
    return
  }

  etFuelTimer += (now - etFuelLastTime) / 1000
  etFuelLastTime = now
  if (etFuelTimer < ET_SAMPLE_SECONDS) return

  const burned = etFuelPrev - fuelVolume // litres
  const metres = odometerMetres - etOdoPrev
  etFuelPrev = fuelVolume
  etOdoPrev = odometerMetres
  etFuelTimer = 0

  // burned <= 0 means refuelling or a reset; metres <= 1 means standing still,
  // where consumption per distance is undefined rather than infinite.
  if (!(burned > 0) || !(metres > 1)) {
    etFuelUseRaw.value = 0
    return
  }

  const sample = burned / metres
  // Ease towards the new sample so the readout is legible instead of jumping
  // between windows. Seed directly on the first valid sample.
  etFuelUseRaw.value =
    etFuelUseRaw.value > 0 ? etFuelUseRaw.value + (sample - etFuelUseRaw.value) * ET_SMOOTHING : sample
}""",
)

patch(
    "script: applyData fills the readouts",
    '  setStyleValue(revcurveRef.value, "strokeDashoffset", revCurveOffset, "revCurveStrokeDashoffset")\n}',
    """  setStyleValue(revcurveRef.value, "strokeDashoffset", revCurveOffset, "revCurveStrokeDashoffset")

  // ===================== Enhanced Tacho: mod readouts =====================
  // Every value goes through the game's unit service, so switching the game to
  // imperial is all it takes to get mph / bhp / lb-ft / degF / MPG / miles.
  setU("weight", data.etWeight, "weight")
  setU("peakPower", etPeakPowerRaw.value, "power")
  setU("peakTorque", etPeakTorqueRaw.value, "torque")
  setU("power", data.etPower, "power")
  setU("torque", data.etTorque, "torque")
  setU("oilTemp", data.etOilTemp, "temperature")
  setU("fuelUse", etFuelUseRaw.value, "consumptionRate")
  setU("gpsSpeed", data.etAirspeed, "speed")
  setU("odometer", data.etOdom, "length", O.odometerDecimals)
  V.gearCount = data.etGearCount ? "/" + data.etGearCount : ""
  V.beamsDeformed = etDamagePercent(data.etBeamsDeformed, data.etBeamCount)
  V.beamsBroken = etDamagePercent(data.etBeamsBroken, data.etBeamCount)
  // Gated on visibility. v-show only sets display:none -- the interpolation
  // stays subscribed, so writing a hidden readout still marks the render
  // effect dirty and re-patches the whole group. These three ship hidden, and
  // engine load in particular changes on nearly every frame, so ungated they
  // were the dial's main source of idle re-renders on a default install.
  if (C.engineLoad.visible) V.engineLoad = etLoadPercent(data.etEngineLoad)
  if (C.brakeTemp.visible) setU("brakeTemp", data.etBrakeTemp, "temperature")
}""",
)

patch(
    "script: collect readings in update()",
    "    data.rpm = (streams.electrics.rpmTacho || 0.0) / rpm_max.value\n  } else if (displayMode.value == 0) {",
    """    data.rpm = (streams.electrics.rpmTacho || 0.0) / rpm_max.value

    // ===================== Enhanced Tacho: mod readouts =====================
    // Stored RAW, in base units; conversion happens at display time.
    //   engineInfo[21] flywheel power  (metric hp, already converted Lua-side)
    //   engineInfo[8]  flywheel torque (Nm)
    //   engineInfo[6]  forward gear count
    //   engineInfo[13] gearbox type; only "manual" reports a usable gear count
    // engineInfo[20] is power at the wheels, [21] at the flywheel; the gap
    // between them is the drivetrain loss. [19] is wheel torque, [8] flywheel
    // torque -- see liveTorqueFrom in layout.js for why those two are not
    // interchangeable the way the power pair is.
    data.etPower = O.livePowerFrom === "wheels" ? streams.engineInfo[20] : streams.engineInfo[21]
    data.etTorque = O.liveTorqueFrom === "wheels" ? streams.engineInfo[19] : streams.engineInfo[8]
    data.etOilTemp = streams.electrics.oiltemp
    data.etOdom = streams.electrics.odometer
    if (streams.stats) {
      data.etWeight = streams.stats.total_weight
      // Already in the stream we subscribe to for mass, so free to read.
      data.etBeamCount = streams.stats.beam_count
      data.etBeamsDeformed = streams.stats.beams_deformed
      data.etBeamsBroken = streams.stats.beams_broken
    }
    data.etGearCount = streams.engineInfo[13] == "manual" ? streams.engineInfo[6] : 0
    data.etEngineLoad = streams.electrics.engineLoad

    // wheelThermals is a per-wheel table already carried by the electrics
    // stream, so the hottest brake costs nothing extra. It can arrive
    // serialised as an array when thermals are off, which Object.values covers.
    const wt = streams.electrics.wheelThermals
    let hottest = 0
    if (wt) {
      for (const w of Object.values(wt)) {
        const t = Number(w && w.brakeCoreTemperature)
        if (isFinite(t) && t > hottest) hottest = t
      }
    }
    data.etBrakeTemp = hottest

    // Ground speed, i.e. GPS speed: immune to wheelspin and lock-up, which is
    // why the layout gives it the dominant position over the wheel reading.
    data.etAirspeed = streams.electrics.airspeed
    etGroundSpeed.value = Number(streams.electrics.airspeed) || 0

    // Driver inputs. `steering` is the assisted value the car actually gets,
    // which is what the wheels do -- steeringUnassisted would show the raw
    // stick position instead and disagree with the front wheels on anything
    // with steering assistance.
    //
    // Quantised, and written only when the quantised value actually moved.
    // These are the one place raw floats reach a reactive object, and a float
    // jittering in its eighth decimal marks the component dirty every frame --
    // turning a dial that never re-renders (the stock one has no dynamic
    // bindings at all) into one that re-renders continuously. The step is finer
    // than the arcs can show, so nothing is lost visually.
    etSet("throttle", streams.electrics.throttle, 200)
    etSet("brake", streams.electrics.brake, 200)
    etSet("clutch", streams.electrics.clutch, 200)
    etSet("steering", streams.electrics.steering, 4)

    etUpdateConsumption(Number(streams.engineInfo[11]) || 0, Number(streams.electrics.odometer))
  } else if (displayMode.value == 0) {""",
)

patch(
    "script: vehicleChanged re-queries the engine",
    """function vehicleChanged() {
  // redo the elements
  initialized.value = false
}""",
    """function vehicleChanged() {
  // redo the elements
  initialized.value = false

  // Engine specs and the fuel baseline both belong to the outgoing vehicle.
  etPeakPowerRaw.value = 0
  etPeakTorqueRaw.value = 0
  etSteerLock.value = 0
  etResetConsumption()
  etFetchEngineSpecs()
}""",
)

patch(
    "script: initial engine spec query",
    "  lua.career_career.isActive().then(isActive => (isCareer = isActive))\n})",
    "  lua.career_career.isActive().then(isActive => (isCareer = isActive))\n  etFetchEngineSpecs()\n})",
)

patch(
    "script: readouts follow layer visibility",
    '    setDisplay(tickLayerRef.value, val, "tickLayerDisplay")',
    '    setDisplay(tickLayerRef.value, val, "tickLayerDisplay")\n    setDisplay(etLayerRef.value, val, "etLayerDisplay")',
)

# The stock fuel and temperature icons are scaled by composing a transform in
# front of their own matrix. Each anchor below carries that original matrix, so
# a game update that moves an icon stops this build instead of silently
# misplacing it.
patch(
    "stock: ico_temp scaling",
    'id="ico_temp"\n        class="ico-temp"\n        transform="matrix(0.82879177,0,0,0.82879177,40.706638,69.281349)"',
    'id="ico_temp"\n        class="ico-temp"\n        :style="iconStyles.temp"\n        :transform="`${iconTfs.temp} matrix(0.82879177,0,0,0.82879177,40.706638,69.281349)`"',
)

patch(
    "stock: ico_temp_on scaling",
    'id="ico_temp_on" class="ico-temp-on" transform="matrix(0.82879177,0,0,0.82879177,40.706638,69.281349)"',
    'id="ico_temp_on" class="ico-temp-on" :transform="`${iconTfs.temp} matrix(0.82879177,0,0,0.82879177,40.706638,69.281349)`"',
)

patch(
    "stock: ico_fuel scaling",
    'id="ico_fuel" class="ico-fuel" transform="matrix(0.88747678,0,0,0.88747678,64.601263,56.302973)"',
    'id="ico_fuel" class="ico-fuel" :style="iconStyles.fuel" :transform="`${iconTfs.fuel} matrix(0.88747678,0,0,0.88747678,64.601263,56.302973)`"',
)

patch(
    "stock: ico_fuel_on scaling",
    'id="ico_fuel_on"\n        class="ico-fuel-on"\n        transform="matrix(0.88747678,0,0,0.88747678,64.601263,56.302973)"',
    'id="ico_fuel_on"\n        class="ico-fuel-on"\n        :transform="`${iconTfs.fuel} matrix(0.88747678,0,0,0.88747678,64.601263,56.302973)`"',
)

# =============================================================================
# 4. Style -- intentionally almost empty
# =============================================================================
patch(
    "style: readout block",
    "</style>",
    """
/* ===================== Enhanced Tacho: mod readouts =====================
   No size and no colour here on purpose. Both are emitted as inline style
   from layout.js, which outranks the stock rules without any specificity
   fight. Adding anything visual below would create a second source of truth;
   change layout.js instead. */
.et-readouts {
  /* The dial is decorative: let clicks fall through to whatever is beneath. */
  pointer-events: none;
}

.et-readouts text {
  /* Values are re-laid out every frame at arbitrary scales; geometric
     precision keeps digits from jittering as the widget is resized. */
  text-rendering: geometricPrecision;
}

/* Readouts sitting over the ring or other artwork need separating from it.
   An outline drawn UNDER the glyphs does that without touching the colour
   coding -- paint-order is what puts the stroke behind the fill, otherwise the
   stroke would eat into the letterforms. */
.et-outlined {
  paint-order: stroke fill;
  stroke: rgba(0, 0, 0, 0.85);
  stroke-width: 5px;
  stroke-linejoin: round;
}


</style>""",
)

# The stock component uses CRLF. Matching it keeps `diff` against a future
# stock version readable instead of reporting every line as changed.
patch_block("icons: oil temperature follows its readout", ".ico-temp", "#ffffff", "currentColor", 8)
patch_block("icons: fuel follows its readout", ".ico-fuel", "#ffffff", "currentColor", 4)

io.open(DST, "w", encoding="utf-8", newline="\r\n").write(s)
print("Patches applied:")
for a in applied:
    print("  -", a)
print("\n%s\n%d lines" % (DST, len(s.splitlines())))
