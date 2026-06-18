/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { 50: "#e8eaf6", 100: "#c5cae9", 200: "#9fa8da", 300: "#7986cb", 400: "#5c6bc0", 500: "#3f51b5", 600: "#3949ab", 700: "#303f9f", 800: "#283593", 900: "#1a237e" },
        warm: { 50: "#fdf2ed", 100: "#fbe5d9", 200: "#f7cbb3", 300: "#f2ad88", 400: "#ed8f5d", 500: "#d77757", 600: "#c56a4c", 700: "#a85a41", 800: "#8c4b36", 900: "#6f3c2b" },
        risk: { high: "#c62828", medium: "#f57c00", low: "#2e7d32" },
        surface: { DEFAULT: "#f8f9fa", card: "#ffffff", sidebar: "#f0f1f5" },
      },
      fontFamily: {
        sans: ['"SF Pro Display"', '"PingFang SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"SF Mono"', '"Courier New"', 'monospace'],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-dot": "pulseDot 1.4s infinite ease-in-out",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp: { "0%": { opacity: "0", transform: "translateY(12px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        pulseDot: { "0%, 100%": { opacity: "0.2" }, "50%": { opacity: "1" } },
      },
    },
  },
  plugins: [],
};
