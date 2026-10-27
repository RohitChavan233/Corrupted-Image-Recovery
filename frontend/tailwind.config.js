/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        xn: {
          bg: '#181a1f',
          surface: '#21252b',
          panel: '#282c34',
          border: '#353b45',
          hover: '#2c313a',
          active: '#3e4451',
          accent: '#4d78cc',
          accentHover: '#5c8beb',
          text: '#abb2bf',
          textMuted: '#5c6370',
          textBright: '#e5e7eb'
        }
      }
    },
  },
  plugins: [],
}
