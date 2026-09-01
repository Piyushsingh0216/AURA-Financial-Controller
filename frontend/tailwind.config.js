/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aura: {
          bg: "#090A0F",
          panel: "#11141F",
          border: "#1E2438",
          cyan: "#00F0FF",
          amber: "#FFB800",
          red: "#FF3366",
          emerald: "#00FF85"
        }
      }
    },
  },
  plugins: [],
}