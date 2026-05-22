import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        guardian: {
          bg: "#0a0e17",
          panel: "#111827",
          border: "#1f2937",
          accent: "#3b82f6",
          critical: "#ef4444",
          high: "#f97316",
          medium: "#eab308",
          safe: "#22c55e",
        },
      },
      animation: {
        "pulse-alert": "pulse-alert 1s ease-in-out infinite",
        flash: "flash 0.5s ease-in-out infinite",
      },
      keyframes: {
        "pulse-alert": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(239, 68, 68, 0.7)" },
          "50%": { boxShadow: "0 0 0 12px rgba(239, 68, 68, 0)" },
        },
        flash: {
          "0%, 100%": { backgroundColor: "rgba(239, 68, 68, 0.15)" },
          "50%": { backgroundColor: "rgba(239, 68, 68, 0.4)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
