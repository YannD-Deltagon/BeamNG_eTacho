# ![enhancedTacho3Header](https://github.com/YDeltagon/BeamNG_eTacho/raw/Master/screenshots/enhancedHeader.png)

**enhancedTacho** replaces BeamNG.drive's stock *Tacho2* dial with an enriched version of the same gauge.

> Built on the work of [nutunabe](https://www.beamng.com/resources/authors/nutunabe.541038/) and [fylhtq7779](https://www.beamng.com/members/fylhtq7779.133344) — [Enhanced Tachometer and Forced Induction](https://www.beamng.com/resources/enhanced-tachometer.27289/) & [Simple power, weight, ratio](https://www.beamng.com/resources/simple-power-weight-ratio.23693/)

---

## **v5.0** — Vue rewrite

The mod was AngularJS with an external SVG. BeamNG has since rewritten its own
dial in Vue, so this version is a **fork of the stock 0.39 `tacho.vue`**: the
artwork, needle, arcs, icons and tick maths are the game's, and the mod adds its
readouts on top.

The fork is about 250 lines against the stock component and is produced by a
patch script, so a game update is re-applied rather than re-done by hand.

### 🆕 What it adds

- **Speeds** — GPS ground speed as the main figure, wheel speed beneath it. The
  gap between the two is wheelspin and lock-up, visible as it happens.
- **Power & torque** — peak and instantaneous, side by side. Power is read at
  the wheels, so the difference from the peak crank figure is the drivetrain
  loss.
- **Mass, oil temperature, consumption, odometer, gear count**
- **Structural damage** — deformed and broken beam percentages
- **Driver inputs** — throttle, brake and clutch as arcs following the dial,
  with steering position between them
- **In-game settings panel** — a gear button opens an editor for the position,
  size, colour and visibility of every readout

### ⚙️ Units

Every value goes through the game's own unit service. Switching BeamNG to
imperial gives mph, bhp, lb-ft, °F, MPG and miles with nothing to configure.

### 🎛️ Configuration

`ui/modules/apps/Tacho2/layout.js` holds every coordinate, size and colour, and
is the only file to edit. It is heavily commented: the coordinate system, the
anchoring rule and the reasoning behind each placement are documented in it.

Edits made in the in-game panel are layered on top of that file rather than
replacing it, so a mod update can ship a new default layout without discarding
what a player tuned.

---

## 📥 Download

Available on the [BeamNG repository](https://www.beamng.com/resources/enhancedtacho-stylish-interface-superior-information-real-time-vehicle-monitoring.27982)

## 📝 Feedback and Contributions

Ideas, suggestions and bug reports are welcome — open an
[Issue](https://github.com/YDeltagon/BeamNG_eTacho/issues) or a
[Pull Request](https://github.com/YDeltagon/BeamNG_eTacho/pulls), or post a
[Review](https://www.beamng.com/resources/enhancedtacho-stylish-interface-superior-information-real-time-vehicle-monitoring.27982/reviews).

## 📜 License

MIT — see [LICENSE.md](LICENSE.md). Fully open source, contributions welcome.

## 🤑 Support

[Paypal](https://www.paypal.com/donate/?hosted_button_id=ZE33LD38M4ALN)
