// =============================================================================
//  ENHANCED TACHO  --  GAUGE LAYOUT CONFIGURATION
//  YDeltagon, building on the stock BeamNG.drive 0.39 "Tacho2" dial.
// =============================================================================
//
//  THIS IS THE ONLY FILE YOU NEED TO EDIT.
//
//  Every readout the mod adds -- and the four stock elements it repositions
//  (wheel speed, speed unit, gear, RPM legend) -- is driven from here. The
//  component itself (`tacho.vue`) holds no hard-coded coordinate, size or
//  colour: it reads all of them from this object at render time.
//
// -----------------------------------------------------------------------------
//  COORDINATE SYSTEM
// -----------------------------------------------------------------------------
//
//  The dial is drawn inside an SVG `viewBox` of 660 x 660 user units. Those
//  units are NOT screen pixels: the whole dial is scaled uniformly to whatever
//  size the app widget has in the HUD. `size: 120` therefore means "120/660 of
//  the widget's height", not "120 physical pixels". That is what keeps the
//  layout identical whether the app is 150 px or 600 px wide.
//
//      x = 0    left edge         x = 330   centre        x = 660   right edge
//      y = 0    top edge          y = 330   centre        y = 660   bottom edge
//
//  IMPORTANT: y grows DOWNWARDS, as in every SVG and CSS coordinate system.
//  Increasing `y` moves an element towards the bottom of the dial.
//
//  The needle pivot and the tick ring are both centred on (330, 330).
//  Useful landmarks when positioning things:
//
//      radius   0 .. 165    free inner disc
//      radius 176           fuel arc (right) and temperature arc (left); these
//                           only span y = 213..447, so directly above and below
//                           them the full width stays usable
//      radius ~223 .. ~319  the dashed tick ring
//      radius > 320         the four corners of the canvas, always empty
//
//  The gauge sweep is 270 degrees with a 90 degree opening at the bottom, so
//  the bottom centre is clear all the way out to the canvas edge.
//
// -----------------------------------------------------------------------------
//  FIELD REFERENCE
// -----------------------------------------------------------------------------
//
//  x, y      Anchor point of the text, in the 660 x 660 space above.
//            `y` is the TEXT BASELINE, not the top of the glyphs: digits sit on
//            it and extend upwards. Roughly 75% of `size` is drawn above `y`
//            and 25% below. To leave a clean gap between two stacked rows,
//            budget at least `size` between their baselines.
//
//  size      Font size, in the same 660-unit space. See the note above: this
//            scales with the widget, it is not a pixel value.
//
//  ANCHORING RULE, applied throughout
//            A label's x/y is the corner of its box NEAREST THE DIAL CENTRE,
//            sitting on the text baseline. For a label left of centre that is
//            its bottom-RIGHT corner (anchor "end"); right of centre, its
//            bottom-LEFT corner (anchor "start").
//            Two labels are mirrored when their x are equidistant from 330 --
//            you compare the anchor points, never the box centres, because box
//            width varies with the text and would make symmetry drift.
//
//  anchor    Horizontal alignment relative to `x`:
//              "middle" -- centred on x        (standalone values)
//              "end"    -- text ENDS at x      (left column: digits stay flush
//                          right as the number grows)
//              "start"  -- text BEGINS at x    (right column)
//            The power and torque pairs deliberately use "end" and "start" so
//            they grow outwards from the separator instead of drifting sideways
//            when a value gains a digit. Same reason `gearCount` uses "start":
//            it stays welded to the right of the centred gear glyph.
//
//  color     Any CSS colour: "#80ff89", "white", "rgb(0,255,0)", or
//            "rgba(255,255,255,0.6)" for a translucent readout.
//
//  opacity   0 to 1, default 1. Dims a readout without changing its colour,
//            useful for secondary information that should stay legible but
//            not compete with the primary figures.
//
//  ARC-PLACED READOUTS (damage only)
//            Instead of x/y, these take `radius` and `angle`: the anchor is
//            computed on a circle centred on the dial. Angles are in degrees,
//            0 = right, 90 = top, counting anticlockwise. A larger radius sits
//            further OUT.
//            The text is NOT rotated -- only its position follows the circle.
//            Two readouts at the same radius and different angles therefore
//            step around the dial while staying upright and level.
//  dy        Arc-placed readouts only: pushes a caption below its value.
//
//  visible   false hides the element completely. There is no measurable cost
//            either way, so use it freely to declutter the dial.
//
//  Units are NOT a field on these entries. They are separate, independently
//  positioned labels declared in the `units` block further down, so each one
//  can be placed where it is actually readable instead of being crammed
//  against its value. See that block for details.
//
//  rotate    Unit labels only. Degrees, clockwise, about the label's own
//            anchor point. 90 makes the text read downwards, -90 upwards.
//            Used on the two flank units, where a horizontal label wide enough
//            to read would overhang the arcs; turned on their side they follow
//            the arcs instead and cost no horizontal room at all.
//
//  text      Separator entries only: the literal glyph to draw ("|", "/", "-",
//            or "" to blank it while keeping the entry).
//
// -----------------------------------------------------------------------------
//  UNITS -- WHY THERE IS NOTHING TO CONFIGURE HERE
// -----------------------------------------------------------------------------
//
//  Every value is stored internally in its base unit (m/s, metric hp, Nm,
//  degrees C, kg, litres per metre, metres) and converted only at display time
//  through the game's own unit service:
//
//      wheel / GPS speed  ->  speed            km/h     or  mph
//      power, peak power  ->  power            PS       or  kW / bhp
//      torque, peak torque->  torque           Nm       or  lb-ft
//      oil temperature    ->  temperature      degC     or  degF / K
//      vehicle mass       ->  weight           kg       or  lbs
//      fuel consumption   ->  consumptionRate  L/100km  or  MPG
//      odometer           ->  length           km       or  miles
//
//  Whichever unit system the player picks in the game options is what the dial
//  shows. Never hard-code "km/h" anywhere.
//
// -----------------------------------------------------------------------------
//  WORKFLOW
// -----------------------------------------------------------------------------
//
//  While developing (mod unpacked under mods/unpacked/):
//    1. Edit and save this file.
//    2. Press F5 in game to reload the UI.
//    If the change does not show up, the CEF layer is serving a cached copy:
//    open the UI devtools, Network tab, tick "Disable cache", and leave that
//    window open. F5 then picks up JS changes reliably.
//
//  To ship: zip the `ui/` folder as-is. This file travels with it, so the
//  layout you tuned is exactly the layout your users get.
//
// =============================================================================

export const CONFIG = {
  // ---------------------------------------------------------------------------
  //  GLOBAL OPTIONS
  // ---------------------------------------------------------------------------
  options: {
    // Font used by every readout the mod adds. Shipped with the game and
    // therefore always available: "Squada One" (the stock dial face, condensed
    // and very legible when small), "Open Sans", "Roboto", "RobotoCondensed",
    // "Kanit", "Play", "RussoOne", "Prompt", "Genos".
    // A condensed face is strongly recommended: the inner disc is narrow and a
    // wide face will hit the arcs as soon as a value gains a digit.
    font: "Squada One",

    // Show the stock "x1000 RPM" caption under the dial centre. The original
    // mod layout does not use it, hence false.
    showRpmLegend: false,


    // Fade durations, in seconds. Asymmetric on purpose: units vanishing while
    // you accelerate should be unobtrusive, but coming back as you stop should
    // be gentle enough not to catch the eye. 0 on both disables the fade.
    unitsFadeOutSeconds: 1,
    unitsFadeInSeconds: 1.5,

    // Unit labels show while stopped and fade out once moving past this
    // ground speed, in km/h. Units are worth reading when you are studying the
    // dial at rest; at speed they only cover the figures that matter.
    // Compared against the raw ground speed, so behaviour is identical whether
    // the player runs metric or imperial.
    unitsHideAboveKmh: 15,

    // Where the LIVE power and torque figures are measured.
    //   "flywheel"  at the crankshaft, before the drivetrain
    //   "wheels"    at the contact patch, after every loss
    //
    // Power is meaningful either way, and the gap between the two IS the
    // drivetrain loss -- worth watching, and it widens with wheelspin.
    //
    // Torque is NOT. Wheel torque is crank torque multiplied by the total
    // gearing, so in first gear a 372 Nm engine reads several thousand Nm at
    // the wheels. That is leverage, not a measurement error, but shown next to
    // the peak figure above it looks like one. Hence the asymmetric default:
    // power after the drivetrain, torque before it, so both rows stay
    // comparable. Set liveTorqueFrom to "wheels" if you want raw wheel torque.
    livePowerFrom: "wheels",
    liveTorqueFrom: "flywheel",

    // Scale applied to the stock fuel and temperature icons. 1 = untouched.
    // They are drawn for a dial with empty flanks; with a figure under each
    // one they read better smaller.
    iconScale: 0.7,

    // Pivot the scaling turns about, in dial coordinates: the icons' measured
    // centres. They must be given explicitly -- each stock icon carries its own
    // placement matrix, and asking the browser for "the element's own centre"
    // resolves it in the icon's local space, before that matrix, which shifts
    // the icon by tens of units as it shrinks. Re-measure these if a game
    // update moves the icons.
    iconTempCenter: [206.5, 329.9],
    iconFuelCenter: [453.9, 329.2],

    // Horizontal nudge, so each icon ends up centred on the value below it.
    // The temperature icon already lines up; the fuel one sits 5.4 units right
    // of its figure.
    iconTempDx: 2.5,
    iconFuelDx: -2.9,

    // Vertical nudge, used to line the two icons' BOTTOM edges up with each
    // other. They are different heights, so matching their centres would leave
    // the values beneath them at different gaps.
    iconTempDy: 0,
    iconFuelDy: 2.7,

    // Decimal places on the odometer. The game's length converter already
    // switches between m and km (or ft and miles), so 1 is usually right.
    odometerDecimals: 1,
  },

  // ---------------------------------------------------------------------------
  //  ELEMENTS
  //  Defaults reproduce the original Tacho2Classic layout, extracted from its
  //  app.svg with all group transforms resolved, then adjusted where the stock
  //  0.39 dial's proportions differ from the old one.
  // ---------------------------------------------------------------------------
  elements: {
    // ---- speeds -------------------------------------------------------------

    // The large central figure: GPS speed, measured over the ground. This is
    // the accurate one -- it does not move when the wheels lock under braking
    // or spin up under power, which is why it gets the dominant position.
    gpsSpeed: { x: 328.9, y: 453.5, size: 120, anchor: "middle", color: "#ffffff", visible: true },

    // Smaller figure below: speed read at the wheels, i.e. what a real car's
    // speedometer shows. Comparing the two makes wheelspin and lock-up obvious.
    wheelSpeed: { x: 329.4, y: 495.1, size: 53.3, anchor: "middle", color: "#ffffff", visible: true },

    // Speed unit ("km/h" / "mph"), inherited from the stock dial and driven by
    // the stock component, so it always agrees with the speed readouts.
    // Anchored "start" immediately right of the wheel-speed figure so the two
    // read as one group. x is set for a two-digit reading ("50"), which spans
    // roughly 307..352 at this size -- calibrating on a rare four-digit worst
    // case would leave a permanent gap at every realistic speed.
    // This label joins the click-toggled unit group.
    speedUnit: { x: 358, y: 495.1, size: 30, anchor: "start", color: "#c8ccd0", visible: true },

    // ---- mass ---------------------------------------------------------------

    // Live vehicle mass, fuel and attached load included: it drops as the tank
    // empties and jumps when a trailer is coupled.
    weight: { x: 329.3, y: 206.8, size: 66.7, anchor: "middle", color: "#80ff89", visible: true },

    // ---- engine peak output -------------------------------------------------
    // Queried once per vehicle from its Lua state, because peak figures are
    // published in no telemetry stream. Upper row by convention, with the live
    // figures directly below for comparison.

    peakPower: { x: 317.1, y: 239.5, size: 46.7, anchor: "end", color: "#ffeb80", visible: true },
    peakSeparator: { x: 329.8, y: 238.9, size: 40.8, anchor: "middle", color: "#ffffff", text: "|", visible: true },
    peakTorque: { x: 342.3, y: 239.5, size: 46.7, anchor: "start", color: "#80d4ff", visible: true },

    // ---- instantaneous engine output ----------------------------------------
    // Both measured at the flywheel, so they are free of drivetrain losses and
    // directly comparable with the peak figures above.
    // Colour convention kept from the original mod: power warm (yellow),
    // torque cold (blue). The same two hues are reused on both rows, so
    // vertical position alone distinguishes peak from live.

    power: { x: 316.5, y: 273.4, size: 48, anchor: "end", color: "#ffeb80", visible: true },
    separator: { x: 329.8, y: 272.8, size: 40.8, anchor: "middle", color: "#ffffff", text: "|", visible: true },
    torque: { x: 342.4, y: 273.4, size: 48, anchor: "start", color: "#80d4ff", visible: true },

    // ---- gearbox ------------------------------------------------------------

    // Engaged gear, centred on the dial. Reproduces the stock italic slant,
    // applied through an SVG shear matrix; the component compensates the
    // horizontal offset that shear introduces, so the x set here is the
    // position you actually see on screen.
    gear: { x: 330, y: 347.7, size: 74.7, anchor: "middle", color: "#ffffff", visible: true },

    // Forward gear count, rendered as "/6", anchored "start" so it hangs off
    // the right of the centred gear glyph and the pair reads as one unit.
    // Manual gearboxes only: automatics report a drive mode rather than a gear
    // count, so this stays blank on them.
    gearCount: { x: 360, y: 347.7, size: 33.3, anchor: "start", color: "#ffffff", visible: true },

    // ---- flanks -------------------------------------------------------------
    // Placed just inside the temperature arc (left) and the fuel arc (right),
    // so each number sits beside the bar it relates to.

    oilTemp: { x: 209, y: 397.5, size: 53.3, fitDigits: 2, anchor: "middle", color: "#ffffff", visible: true },

    // Fuel consumption, integrated over a one-second window against odometer
    // distance. Reads 0 when stationary or with the ignition off, where
    // consumption per distance is undefined rather than infinite.
    fuelUse: { x: 451, y: 397.5, size: 53.3, fitDigits: 2, anchor: "middle", color: "#ffffff", visible: true },

    // ---- bottom -------------------------------------------------------------

    // ---- driver inputs ------------------------------------------------------
    // Arcs following the dial's own curve, outside the tick ring (whose outer
    // edge measures radius 286.7). All three grow FROM THE TOP outwards, so
    // "nothing pressed" is a clean gap at twelve o'clock and any input reads as
    // a wing opening out of it -- visible in peripheral vision without looking
    // away from the road.
    //
    // Brake goes left, throttle and clutch right, matching a pedal box seen
    // from above. Clutch sits on an inner radius rather than sharing throttle's
    // so the two can be read apart when both are partly engaged, which is
    // exactly the moment they matter.
    //
    // FIELDS
    //   radius        distance from the dial centre to the arc's centreline
    //   angleStart    where the fill begins, in degrees (0 = right, 90 = top)
    //   angleEnd      where a fully pressed pedal reaches
    //   width         stroke thickness
    //   color         the filled part (there is no track behind it)
    //
    // angleEnd may be smaller OR larger than angleStart: the fill simply grows
    // from one to the other, which is how brake mirrors throttle.

    throttle: { radius: 303, angleStart: 88, angleEnd: 34, width: 11, color: "#6ee787", visible: true },
    clutch: { radius: 288, angleStart: 88, angleEnd: 34, width: 8, color: "#80d4ff", visible: true },
    brake: { radius: 303, angleStart: 92, angleEnd: 146, width: 11, color: "#ff6b6b", visible: true },

    // Steering sits between the two, centred on twelve o'clock: a short arc
    // segment that slides either side of top. Position rather than length, so
    // straight-ahead reads as "marker centred" with nothing to interpret.
    //   sweep        how far either side of centre full lock travels
    //   span         the marker's own angular width
    //   lockDegrees  fallback steering lock, used only until the real one is
    //                read from the vehicle (see steeringFraction in tacho.vue)
    //
    // Its radius MUST differ from the pedal arcs'. Sharing one puts its dark
    // track over their fill -- it is drawn last, so it wins -- and throttle
    // then appears to fill from the wrong end.
    steering: { radius: 320, sweep: 30, span: 7, width: 8, color: "#ffffff", lockDegrees: 360, visible: true },

    // ---- structural damage --------------------------------------------------
    // Percentages of the vehicle's total beam count, read from the `stats`
    // stream the dial already subscribes to for mass -- so they cost nothing
    // extra to display.
    //
    // POSITIONED along an arc but NOT rotated: `radius` + `angle` place the
    // anchor, and the text stays upright and level. Curved text was legible
    // only near the top of the ring and fought the numbers it sits beside;
    // stepping two upright labels down the arc keeps the dial's geometry
    // without costing readability.
    //
    // Angles put them on the right flank, stacked just above the headlight
    // cluster at (604, 372) -- the only free column on that side. They do
    // graze the tick ring, whose outer edge measures radius 286.7; clearing it
    // entirely would push them off the canvas. That is what the dark outline
    // on .et-outlined is for.
    //
    // `dy` offsets the caption below its value, in the same 660-unit space.

    // Plastic deformation: panels bent but holding. Climbs gradually, a good
    // read on accumulated bodywork wear.
    beamsDeformed: { radius: 285, angle: 11, size: 32, anchor: "middle", color: "#ffb454", visible: true },
    beamsDeformedLabel: { radius: 285, angle: 21, dy: 24, size: 18, anchor: "middle", text: "DEFORMED", visible: true },

    // Outright failure: structure has let go. This is the number that matters,
    // preceding lost parts and handling going away.
    beamsBroken: { radius: 285, angle: 5, size: 32, anchor: "middle", color: "#ff6b6b", visible: true },
    beamsBrokenLabel: { radius: 285, angle: 7, dy: 24, size: 18, anchor: "middle", text: "BROKEN", visible: true },

    // Distance covered by this vehicle since it spawned. Not a persistent
    // lifetime total: respawning resets it.
    // Anchored "end" rather than centred: the reading grows from "0.4" to
    // "128.6" over a session, and a centred number would drift away from its
    // unit label. Ending at a fixed edge keeps the gap constant, the number
    // simply extending leftwards as it gains digits.
    odometer: { x: 430, y: 544.4, size: 26.7, anchor: "end", color: "#ffffff", visible: true },
  },

  // ---------------------------------------------------------------------------
  //  UNIT LABELS
  //
  //  Each unit is its own positioned label rather than a suffix glued to its
  //  value. That is deliberate: the inner disc is crowded, and a suffix large
  //  enough to read would collide with the neighbouring readout on almost
  //  every row. Placing them separately means each label can sit in whatever
  //  gap is actually free -- below a flank reading, beside a centred one.
  //
  //  CLICK THE DIAL to show or hide the whole set. The choice is remembered
  //  per profile, so it survives a reload; `showUnitsByDefault` above only
  //  decides what a first-time user sees.
  //
  //  The label TEXT is never written here. Each entry names the readout whose
  //  unit it displays, and that unit comes straight from the game's converter
  //  for that quantity -- so it reads "km/h" or "mph", "PS" or "bhp", "L/100km"
  //  or "MPG", according to the player's settings and with no work on your part.
  //  This also handles the odometer correctly, whose converter switches between
  //  m and km (or ft and miles) depending on distance covered.
  //
  //  `for` must name an element that carries a value. Fields otherwise behave
  //  exactly as in the elements block above.
  // ---------------------------------------------------------------------------
  units: {
    // NOTE: speed has no entry here. The stock dial already owns a speed-unit
    // element, declared as `speedUnit` in the elements block above and fed by
    // the stock component itself. Adding one here would draw a second label on
    // top of it. `speedUnit` joins this toggle group all the same.

    // To the right of the mass figure, tinted to match it so the pair reads
    // as one item.
    weight: { for: "weight", x: 392, y: 206.8, size: 28, anchor: "start", visible: true },

    // Flanking the live power/torque row. Anchored on the corner nearest the
    // centre per the rule above -- "end" on the left, "start" on the right --
    // so x is directly the distance from x=330: 82 units on each side, exactly
    // mirrored. "Nm" being slightly wider than "PS" then extends a little
    // further outwards, which is correct: the gap that frames the numbers is
    // what the eye reads, not the outer edge. Placing them
    // below the row instead put them straight into the gear glyph, which
    // rises to y=295. One label serves both rows, peak and live sharing a
    // quantity. Both stay clear of the arcs, which occupy x 462..506 only
    // between y 213 and 447.
    power: { for: "power", x: 248, y: 273.4, size: 24, anchor: "end", visible: true },
    torque: { for: "torque", x: 412, y: 273.4, size: 24, anchor: "start", visible: true },

    // Set on their side and tucked against the OUTER edge of their value:
    // the temperature label to the right of the left-hand reading, the
    // consumption label to the left of the right-hand one. Both therefore sit
    // between their value and the dial centre, where there is room, instead of
    // hanging outwards into the arcs.
    //
    // Rotated because horizontal they are too wide: "L/100km" alone would run
    // straight through the fuel arc. On their side they cost no horizontal
    // room at all and echo the curve of the arc they belong to. The left one
    // reads downwards, the right one upwards, so the pair mirrors.
    //
    // x values assume a two-digit reading (95, 40), which spans about 45 units
    // at size 53.3. y values run the label alongside the value rather than
    // below it.
    //
    // Same anchoring rule, but rotation moves the box relative to the anchor,
    // and in opposite directions for +90 and -90. The inner edge -- the corner
    // that counts -- lands at x+21 for the left label and x-21 for the right,
    // so x = 330 - d - 21 and x = 330 + d + 21 for a distance d. With d = 64
    // that gives 245 and 415, which look unrelated but are exactly mirrored.
    // Change one and you must recompute the other.
    oilTemp: { for: "oilTemp", x: 241.5, y: 374, rotate: 90, size: 24, anchor: "start", visible: true },
    fuelUse: { for: "fuelUse", x: 418.5, y: 423, rotate: -90, size: 24, anchor: "start", visible: true },

    // Beside the odometer, which is small enough that a label below it would
    // fall off the dial.
    odometer: { for: "odometer", x: 436, y: 544.4, size: 19, anchor: "start", visible: true },
  },
}

export default CONFIG
