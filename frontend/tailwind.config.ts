import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#0A0E1A",
          surface: "#0F1629",
          border: "#1E2D4A",
          cyan: "#00D4FF",
          red: "#FF3B5C",
          amber: "#FFB800",
          green: "#00E5A0",
          purple: "#7B61FF",
          textPrimary: "#E8F0FE",
          textSecondary: "#6B84A8",
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        display: ["var(--font-space-grotesk)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
      animation: {
        "pulse-fast": "pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glitch": "glitch 1s linear infinite",
      },
    },
  },
  plugins: [],
};
export default config;
