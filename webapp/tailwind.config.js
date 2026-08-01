/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        calm: { DEFAULT: "hsl(var(--calm))", foreground: "hsl(var(--calm-foreground))" },
        // Amber. The darkest colour in the app, reserved for equipment that
        // stopped reporting — never for a person. There is no red token.
        attention: { DEFAULT: "hsl(var(--attention))" },
      },
      borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)" },
      keyframes: {
        // A slow, shallow breath. Applied only via `motion-safe:` and only when
        // the data says the handset is really reporting — an animation that ran
        // regardless would be a liveness indicator that indicates nothing.
        breathe: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.45", transform: "scale(0.82)" },
        },
      },
      animation: { breathe: "breathe 3.2s ease-in-out infinite" },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
