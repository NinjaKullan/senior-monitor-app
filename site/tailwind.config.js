/** @type {import('tailwindcss').Config} */
// Every colour here is a `var(--token)` reference, never a literal. The values
// live in src/tokens.css and nowhere else (spec 006 AC1), so this file stays a
// map of names to names and the contrast test has exactly one file to read.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        ink: "var(--ink)",
        calm: "var(--calm)",
        clay: "var(--clay)",
        secondary: "var(--text-secondary)",
        error: "var(--error)",
      },
      // One typeface, everywhere (QUESTIONS 135). The serif family is gone,
      // not merely unused: a face that is still reachable is a face that comes
      // back.
      fontFamily: {
        sans: ["Instrument Sans", "system-ui", "sans-serif"],
      },
      // Design-language §3: five roles, each with one job — display, heading,
      // lead, body, eyebrow. Hierarchy comes from size and weight only, warmth
      // from colour. A sixth size is not a design decision to be made in a
      // className; it is an amendment to the type law.
      fontSize: {
        eyebrow: ["13px", { lineHeight: "1.5", letterSpacing: "0.05em" }],
        body: ["16px", { lineHeight: "1.5" }],
        lead: ["20px", { lineHeight: "1.5" }],
        heading: ["32px", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
        display: ["48px", { lineHeight: "1.15", letterSpacing: "-0.03em" }],
      },
      borderRadius: { card: "8px", tile: "24px", panel: "40px" },
      keyframes: {
        // Fade + rise, design-language §6. Applied only via motion-safe:.
        rise: {
          from: { opacity: "0", transform: "translateY(20px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: { rise: "rise 1s ease-out both" },
    },
  },
  plugins: [],
};
