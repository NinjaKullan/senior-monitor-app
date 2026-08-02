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
      fontFamily: {
        sans: ["Instrument Sans", "system-ui", "sans-serif"],
        serif: ["Fraunces", "Georgia", "serif"],
      },
      // Design-language §3: display gets lighter as it grows, tracking tightens
      // with size, body never varies.
      fontSize: {
        eyebrow: ["13px", { lineHeight: "1.5", letterSpacing: "0.05em" }],
        body: ["16px", { lineHeight: "1.5" }],
        lead: ["20px", { lineHeight: "1.5" }],
        feature: ["18px", { lineHeight: "1.5" }],
        card: ["28px", { lineHeight: "1.05" }],
        quote: ["30px", { lineHeight: "1.5" }],
        display: ["48px", { lineHeight: "1.25", letterSpacing: "-0.03em" }],
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
