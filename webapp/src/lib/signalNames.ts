/**
 * The humanised signal names — and the one place in this app they may render.
 *
 * The copy law bans signal names everywhere else: `Amma opened WhatsApp` on a
 * reassurance screen is a behaviour profile, however gently it is phrased. The
 * tripwire health view (spec 005d) is the single exemption, because repair is
 * impossible without them — "her WhatsApp tripwire needs attention" is the whole
 * sentence. The exemption is an allowlist in `copyLaw.test.tsx` naming exactly
 * these strings and exactly that view; every other surface still fails on them.
 *
 * The values mirror `kettle/signals.py`'s SIGNAL_LABELS, and
 * product/tests/test_webapp_contract.py fails if they drift. That is not
 * housekeeping: those labels are the names of the shortcuts sitting on the
 * parent's phone (`Kettle — Amma Charger On`), so a family reading a stale name
 * here would go hunting for a shortcut that does not exist.
 */
export const SIGNAL_DISPLAY_NAMES: Record<string, string> = {
  whatsapp: "WhatsApp",
  youtube: "YouTube",
  news: "News",
  charge_on: "Charger On",
  charge_off: "Charger Off",
  device_alive: "Daily Check",
};
